from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from league_skin_version import updater, workflow_policy as policy


def jobs(conclusion="success", timestamp="2026-09-20T12:34:00Z"):
    return {"jobs": [{"steps": [{
        "name": "Update skin data", "conclusion": conclusion, "completed_at": timestamp,
    }]}]}


def upstream(wiki_patch, cdragon_version):
    def fetch(url):
        if url == updater.CDRAGON_CONTENT_METADATA_URL:
            return json.dumps({"version": f"{cdragon_version}.8207193+branch.content.release"})
        content = f'return {{\n  ["Patch"] = "{wiki_patch}",\n  ["NextPatch"] = "26.20",\n}}'
        return json.dumps({"query": {"pages": [{
            "title": updater.LOL_WIKI_MAINTENANCE_DATA_TITLE,
            "revisions": [{"slots": {"main": {"content": content}}}],
        }]}})
    return fetch


class WorkflowPolicyTests(unittest.TestCase):
    def test_20_hour_boundary_and_manual_bypass(self):
        now = datetime(2026, 9, 20, 12, 34, tzinfo=timezone.utc)
        # 23:59:20 is a punctual daily run checking just before the previous
        # sync's completion time comes around again.
        for seconds, due in [(71999, False), (72000, True), (86360, True)]:
            timestamp = (now - timedelta(seconds=seconds)).isoformat()
            self.assertEqual(policy.update_policy("schedule", timestamp, now), due)
            self.assertTrue(policy.update_policy("workflow_dispatch", timestamp, now))
            self.assertFalse(policy.update_policy("push", timestamp, now))
        self.assertTrue(policy.update_policy("schedule", None, now))

    def test_skipped_checks_failed_runs_and_pushes_do_not_count_as_syncs(self):
        fetch = mock.Mock(side_effect=[
            {"workflow_runs": [
                {"id": 4, "event": "push", "conclusion": "success"},
                {"id": 3, "event": "workflow_dispatch", "conclusion": "failure"},
                {"id": 2, "event": "schedule", "conclusion": "success"},
                {"id": 1, "event": "workflow_dispatch", "conclusion": "success"},
            ]},
            jobs("skipped"),
            jobs(),
        ])
        self.assertEqual(policy.latest_successful_sync(fetch), "2026-09-20T12:34:00Z")
        self.assertEqual(fetch.call_count, 3)
        self.assertIn("runs/2/jobs", fetch.call_args_list[1].args[0])
        self.assertIn("runs/1/jobs", fetch.call_args_list[2].args[0])

    def test_successful_scheduled_sync_without_a_commit_still_counts(self):
        fetch = mock.Mock(side_effect=[
            {"workflow_runs": [{"id": 1, "event": "schedule", "conclusion": "success"}]},
            jobs(),
        ])
        self.assertEqual(policy.latest_successful_sync(fetch), "2026-09-20T12:34:00Z")

    def test_paginates_past_code_only_deployments(self):
        fetch = mock.Mock(side_effect=[
            {"workflow_runs": [
                {"id": index, "event": "push", "conclusion": "success"}
                for index in range(100)
            ]},
            {"workflow_runs": [{"id": 1, "event": "schedule", "conclusion": "success"}]},
            jobs(),
        ])
        self.assertEqual(policy.latest_successful_sync(fetch), "2026-09-20T12:34:00Z")
        self.assertIn("page=2", fetch.call_args_list[1].args[0])

    def test_no_previous_sync_has_no_timestamp(self):
        self.assertIsNone(policy.latest_successful_sync(lambda _path: {"workflow_runs": []}))

    def test_api_errors_are_not_treated_as_empty_history(self):
        with self.assertRaises(OSError):
            policy.latest_successful_sync(mock.Mock(side_effect=OSError("unavailable")))

    def test_manual_policy_does_not_require_a_history_lookup(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "output"
            with (
                mock.patch.dict(os.environ, {
                    "GITHUB_EVENT_NAME": "workflow_dispatch", "GITHUB_OUTPUT": str(output),
                }),
                mock.patch("sys.argv", ["workflow_policy.py"]),
                mock.patch.object(policy, "github_json") as fetch,
                mock.patch.object(policy, "cdragon_wait_reason", return_value=None),
            ):
                policy.main()
            fetch.assert_not_called()
            self.assertEqual(
                output.read_text(encoding="utf-8"),
                "update=true\ndata_updated_at=\n",
            )

    def test_sync_waits_until_communitydragon_serves_the_wiki_patch(self):
        self.assertEqual(
            policy.cdragon_wait_reason(upstream("26.19", "16.18")),
            "League Wiki lists patch 26.19, but CommunityDragon latest is 16.18; "
            "deferring the data sync until CommunityDragon publishes 16.19.",
        )
        for cdragon_version in ("16.19", "16.20"):
            self.assertIsNone(policy.cdragon_wait_reason(upstream("26.19", cdragon_version)))

    def test_waiting_sync_defers_only_the_data_update(self):
        for event in ("schedule", "workflow_dispatch"):
            with self.subTest(event=event), tempfile.TemporaryDirectory() as temporary:
                output = Path(temporary) / "output"
                with (
                    mock.patch.dict(os.environ, {
                        "GITHUB_EVENT_NAME": event, "GITHUB_OUTPUT": str(output),
                    }),
                    mock.patch("sys.argv", ["workflow_policy.py"]),
                    mock.patch.object(
                        policy, "latest_successful_sync", return_value="2026-09-20T12:34:00Z",
                    ),
                    mock.patch.object(policy, "cdragon_wait_reason", return_value="Waiting."),
                    redirect_stdout(io.StringIO()) as stdout,
                ):
                    policy.main()
                self.assertIn(
                    "::notice title=Waiting for CommunityDragon::Waiting.", stdout.getvalue(),
                )
                self.assertEqual(
                    output.read_text(encoding="utf-8"),
                    "update=false\ndata_updated_at=2026-09-20T12:34:00Z\n",
                )

    def test_code_only_deployments_do_not_check_communitydragon(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "output"
            with (
                mock.patch.dict(os.environ, {
                    "GITHUB_EVENT_NAME": "push", "GITHUB_OUTPUT": str(output),
                }),
                mock.patch("sys.argv", ["workflow_policy.py"]),
                mock.patch.object(
                    policy, "latest_successful_sync", return_value="2026-09-20T12:34:00Z",
                ),
                mock.patch.object(policy, "cdragon_wait_reason") as wait_reason,
                redirect_stdout(io.StringIO()),
            ):
                policy.main()
            wait_reason.assert_not_called()
            self.assertEqual(
                output.read_text(encoding="utf-8"),
                "update=false\ndata_updated_at=2026-09-20T12:34:00Z\n",
            )

    def test_current_run_uses_completed_sync_step_time(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "output"
            with (
                mock.patch.dict(os.environ, {"GITHUB_RUN_ID": "7", "GITHUB_OUTPUT": str(output)}),
                mock.patch("sys.argv", ["workflow_policy.py", "--current-sync"]),
                mock.patch.object(policy, "github_json", return_value=jobs()),
            ):
                policy.main()
            self.assertEqual(output.read_text(encoding="utf-8"), "data_updated_at=2026-09-20T12:34:00Z\n")


if __name__ == "__main__":
    unittest.main()
