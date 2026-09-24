from http.client import BadStatusLine, IncompleteRead
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import textwrap
import unittest
from unittest import mock

from league_skin_version import updater


def resolved_patch_result(
    version: str, *skins: tuple[str, str]
) -> updater.ResolvedPatchResult:
    return updater.ResolvedPatchResult(
        updater.PatchRef(version),
        tuple(
            updater.ResolvedSkin(skin_id, name, "test")
            for skin_id, name in skins
        ),
    )


def skin_catalog(names_by_id: dict[str, str]) -> updater.SkinCatalog:
    return updater.SkinCatalog(names_by_id)


def catalog_document(prefix: str = "Catalog Skin", count: int = 1000) -> str:
    return json.dumps(
        {
            str(100001 + index): {
                "id": 100001 + index,
                "name": f"{prefix} {index}",
                "chromas": [],
            }
            for index in range(count)
        },
        ensure_ascii=False,
    )


class FetchTextTests(unittest.TestCase):
    def test_retries_incomplete_response_body(self) -> None:
        incomplete = mock.MagicMock()
        incomplete.__enter__.return_value.read.side_effect = IncompleteRead(b"partial")
        complete = mock.MagicMock()
        complete.__enter__.return_value.read.return_value = b"complete"
        complete.__enter__.return_value.headers.get_content_charset.return_value = "utf-8"

        with (
            mock.patch.object(updater, "urlopen", side_effect=[incomplete, complete]),
            mock.patch.object(updater.time, "sleep") as sleep,
        ):
            result = updater.fetch_text("https://example.test/data", retries=1)

        self.assertEqual(result, "complete")
        sleep.assert_called_once()

    def test_retries_malformed_status_line(self) -> None:
        complete = mock.MagicMock()
        complete.__enter__.return_value.read.return_value = b"complete"
        complete.__enter__.return_value.headers.get_content_charset.return_value = "utf-8"

        with (
            mock.patch.object(
                updater, "urlopen", side_effect=[BadStatusLine("garbage"), complete]
            ),
            mock.patch.object(updater.time, "sleep") as sleep,
        ):
            result = updater.fetch_text("https://example.test/data", retries=1)

        self.assertEqual(result, "complete")
        sleep.assert_called_once()


class PatchVersionTests(unittest.TestCase):
    def test_normalizes_current_historical_and_seasonal_versions(self) -> None:
        cases = {
            "26.1": "26.01",
            "26-10": "26.10",
            "9.3": "9.03",
            "10.16b": "10.16b",
            "25.S1.2": "25.S1.02",
            "2025-s1-3": "25.S1.03",
            "1.0.0.152": "1.0.0.152",
            "0-9-22-4": "0.9.22.4",
            "1.0.0.94B": "1.0.0.94b",
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(updater.normalize_patch_version(raw), expected)

    def test_sorts_beta_launch_and_modern_versions_chronologically(self) -> None:
        versions = ["3.01", "1.0.0.152", "0.9.22.04", "9.01"]
        self.assertEqual(
            sorted(versions, key=updater.patch_sort_key),
            ["0.9.22.04", "1.0.0.152", "3.01", "9.01"],
        )

    def test_patch_mapping_uses_cdragon_version_directories(self) -> None:
        self.assertEqual(updater.cdragon_version_for_patch("14.12"), "14.12")
        self.assertEqual(updater.cdragon_version_for_patch("25.S1.03"), "15.3")
        self.assertEqual(updater.cdragon_version_for_patch("26.14"), "16.14")
        self.assertIsNone(updater.cdragon_version_for_patch("1.0.0.152"))

    def test_reads_cdragon_live_version_directory(self) -> None:
        self.assertEqual(
            updater.parse_cdragon_content_version(
                '{"version": "16.19.8207193+branch.releases-16-19.content.release"}'
            ),
            "16.19",
        )
        for document in ('{"version": "latest"}', "[]", "not json"):
            with self.subTest(document=document):
                with self.assertRaises(updater.UpdateError):
                    updater.parse_cdragon_content_version(document)

class WikiReleaseParserTests(unittest.TestCase):
    def test_discovers_supported_wiki_version_pages(self) -> None:
        document = """
        <li>[[V9.4|4]]</li>
        <li>[[V3.01|1]]</li>
        <li>[[V1.0.0.94(b)|94b]]</li>
        <li>[[V0.9.22.4|9.22.4]]</li>
        <li>[[V3.5 (Balance update)|(Balance Update)]]</li>
        <li>[[April 11, 2009 Patch|04-11]]</li>
        """
        refs = updater.parse_wiki_patch_refs(document)
        self.assertEqual(
            [(ref.version, ref.title) for ref in refs],
            [
                ("0.9.22.4", "V0.9.22.4"),
                ("1.0.0.94b", "V1.0.0.94(b)"),
                ("3.01", "V3.01"),
                ("9.04", "V9.4"),
            ],
        )

    def test_parses_wiki_skin_ids_and_historical_champion_alias(self) -> None:
        document = textwrap.dedent(
            """\
        -- <pre>
        return {
          ["Anivia"] = {
            ["id"] = 34,
            ["skins"] = {
              ["Original"] = {
                ["id"] = 0,
              },
              ["Papercraft"] = {
                ["id"] = 8,
              },
            },
          },
          ["Nunu & Willump"] = {
            ["id"] = 20,
            ["skins"] = {
              ["Papercraft"] = {
                ["id"] = 8,
                ["chromas"] = {
                  ["Ruby"] = {
                    ["id"] = 9,
                  },
                },
              },
            },
          },
        }
        """
        )
        catalog = updater.parse_wiki_skin_data(
            document, minimum_champions=2, minimum_skins=2
        )
        self.assertEqual(catalog.resolve("Anivia", "Papercraft"), "34008")
        self.assertEqual(catalog.resolve("Nunu", "Papercraft"), "20008")
        with self.assertRaisesRegex(updater.UpdateError, "no skin matching"):
            catalog.resolve("Anivia", "Not A Skin")

    def test_parses_next_patch_and_vpbe_upcoming_listing(self) -> None:
        maintenance = textwrap.dedent("""
        return {
          ["NextPatch"] = "26.17",
          ["Patch"] = "26.16",
        }
        """)
        self.assertEqual(
            updater.parse_wiki_maintenance_patches(maintenance),
            ("26.16", "26.17"),
        )
        skin_data = textwrap.dedent("""
        return {
          ["Jinx"] = {
            ["id"] = 222,
            ["skins"] = {
              ["Ocean Song"] = {
                ["id"] = 65,
                ["availability"] = "Upcoming",
                ["release"] = "N/A",
              },
            },
          },
        }
        """)
        wiki_catalog = updater.parse_wiki_skin_data(skin_data)
        vpbe = textwrap.dedent("""
        == New Cosmetics ==
        The following champion skins have been added:
        * {{csl|Jinx|Ocean Song}}

        The following Chroma sets have been added:
        * {{csl|Jinx|Ocean Song|chromas=true}}
        """)
        upcoming = updater.parse_wiki_upcoming_skins(
            [("VPBE", "26.17", vpbe)],
            wiki_catalog=wiki_catalog,
        )
        self.assertEqual(
            upcoming,
            ((updater.UpcomingSkin("222065", "Jinx", "Ocean Song", "26.17"),), ()),
        )

    def test_first_listing_schedules_a_skin_and_unknown_entries_only_warn(self) -> None:
        wiki_catalog = updater.WikiSkinCatalog(
            {("Jinx", "oceansong"): "222065"},
            {"jinx": "Jinx"},
            {},
            {
                "222065": updater.WikiSkinRecord(
                    "222065", "Jinx", "Ocean Song", "Available", None
                )
            },
        )
        skins, warnings = updater.parse_wiki_upcoming_skins(
            [
                ("V26.16", "26.16", "== New Cosmetics ==\n* {{csl|Jinx|Ocean Song}}"),
                (
                    "VPBE",
                    "26.17",
                    "== New Cosmetics ==\n"
                    "* {{csl|Jinx|Ocean Song}}\n"
                    "* {{csl|Jinx|Mystery}}",
                ),
            ],
            wiki_catalog=wiki_catalog,
        )
        self.assertEqual(
            skins,
            (updater.UpcomingSkin("222065", "Jinx", "Ocean Song", "26.16"),),
        )
        self.assertEqual(len(warnings), 1)
        self.assertRegex(warnings[0], r"^VPBE: .*'Mystery'")

    def test_loads_ephemeral_upcoming_snapshot(self) -> None:
        catalog = updater.WikiSkinCatalog(
            {("Jinx", "oceansong"): "222065"},
            {"jinx": "Jinx"},
            {},
            {
                "222065": updater.WikiSkinRecord(
                    "222065", "Jinx", "Ocean Song", "Upcoming", None
                )
            },
        )
        documents = {
            updater.LOL_WIKI_SKIN_DATA_TITLE.casefold(): "skin data",
            updater.LOL_WIKI_MAINTENANCE_DATA_TITLE.casefold(): textwrap.dedent("""
                return {
                  ["Patch"] = "26.16",
                  ["NextPatch"] = "26.17",
                }
            """),
            updater.LOL_WIKI_VPBE_TITLE.casefold(): "== New Cosmetics ==\n",
        }
        # The Wiki has moved the listing from VPBE to the next patch page.
        patch_pages = {
            "v26.17": "== New Cosmetics ==\n* {{csl|Jinx|Ocean Song}}",
        }
        with (
            mock.patch.object(
                updater,
                "_load_wiki_revision_documents",
                side_effect=[documents, patch_pages],
            ) as load_documents,
            mock.patch.object(
                updater,
                "parse_wiki_skin_data",
                return_value=catalog,
            ),
        ):
            snapshot = updater.load_wiki_upcoming_snapshot(fetcher=lambda _url: "")

        self.assertEqual(snapshot.wiki_catalog, catalog)
        self.assertEqual(
            snapshot.skins,
            (updater.UpcomingSkin("222065", "Jinx", "Ocean Song", "26.17"),),
        )
        self.assertEqual(snapshot.warnings, ())
        self.assertEqual(
            [call.args[0] for call in load_documents.call_args_list],
            [
                [
                    updater.LOL_WIKI_SKIN_DATA_TITLE,
                    updater.LOL_WIKI_MAINTENANCE_DATA_TITLE,
                    updater.LOL_WIKI_VPBE_TITLE,
                ],
                ["V26.16", "V26.17"],
            ],
        )

    def test_links_a_removed_skin_name_to_its_unique_renamed_id(self) -> None:
        document = textwrap.dedent(
            """\
        return {
          ["Akali"] = {
            ["id"] = 84,
            ["skins"] = {
              ["Crimson"] = {
                ["id"] = nil,
                ["release"] = "2010-05-11",
                ["cost"] = 520,
              },
              ["Infernal"] = {
                ["id"] = 32,
                ["release"] = "2010-05-11",
                ["cost"] = 520,
              },
            },
          },
        }
        """
        )
        catalog = updater.parse_wiki_skin_data(
            document, minimum_champions=1, minimum_skins=2
        )
        self.assertEqual(catalog.resolve("Akali", "Crimson"), "84032")
        self.assertEqual(catalog.resolve("Akali", "Infernal"), "84032")

    def test_release_date_uses_active_patch_and_timeline_boundaries(self) -> None:
        first = updater.WikiPatchRef("0.8.21.110", "V0.8.21.110")
        second = updater.WikiPatchRef("1.0.0.79", "V1.0.0.79")
        third = updater.WikiPatchRef("1.0.0.81", "V1.0.0.81")
        timeline = [
            ("2009-07-17", first),
            ("2010-03-16", second),
            ("2010-04-01", third),
        ]
        self.assertEqual(
            updater._wiki_ref_for_release_date("2010-03-20", timeline), second
        )
        self.assertEqual(
            updater._wiki_ref_for_release_date("2009-06-13", timeline), first
        )
        self.assertIsNone(
            updater._wiki_ref_for_release_date("2010-04-02", timeline)
        )

    def test_explicit_patch_listing_does_not_require_skin_release_date(self) -> None:
        ref = updater.WikiPatchRef("26.15", "V26.15")
        patch_document = textwrap.dedent("""
        {{Infobox patch
        |Release = July 29, 2026
        }}
        == New Cosmetics ==
        The following champion skins have been added:
        * {{csl|Kayle|Founders Silver}}
        """)
        wiki_catalog = updater.WikiSkinCatalog(
            {("Kayle", "founderssilver"): "10088"},
            {"kayle": "Kayle"},
            {},
        )

        results, _dates = updater._resolve_wiki_release_history(
            [ref],
            catalog=skin_catalog({"10088": "Founders Silver Kayle"}),
            wiki_catalog=wiki_catalog,
            page_documents={"v26.15": patch_document},
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].ref.version, "26.15")
        self.assertEqual(results[0].skins[0].skin_id, "10088")

    def test_wiki_primary_skin_is_not_filtered_by_cdragon_catalog(self) -> None:
        ref = updater.WikiPatchRef("10.22", "V10.22")
        wiki_catalog = updater.WikiSkinCatalog(
            {("Seraphine", "risingstar"): "147002"},
            {"seraphine": "Seraphine"},
            {"147002": "2020-10-29"},
            {
                "147002": updater.WikiSkinRecord(
                    "147002", "Seraphine", "Rising Star", None, "2020-10-29"
                )
            },
        )
        results, _dates = updater._resolve_wiki_release_history(
            [ref],
            catalog=skin_catalog({}),
            wiki_catalog=wiki_catalog,
            page_documents={
                "v10.22": (
                    "{{Infobox patch\n|Release = October 29, 2020\n}}\n"
                    "== New Cosmetics ==\n* {{csl|Seraphine|Rising Star}}"
                )
            },
        )
        self.assertEqual(results[0].skins[0].skin_id, "147002")
        self.assertEqual(
            results[0].skins[0].display_name,
            "Rising Star Seraphine",
        )

    def test_extracts_only_new_skins_before_other_cosmetics(self) -> None:
        document = textwrap.dedent("""
        == New Cosmetics ==
        The following [[Champion skin]]s have been added to the store:
        * {{csl|Anivia|Papercraft}} ({{RP|1350}})
        * {{csl|Nunu|Papercraft|variant=old}} ({{RP|1350}})

        The following [[Chroma]] sets have been added to the store:
        * {{csl|Anivia|Papercraft|chromas=true}}

        == Champions ==
        * {{csl|Anivia|Blackfrost}}
        """)
        self.assertEqual(
            updater.parse_wiki_skin_entries(document),
            (("Anivia", "Papercraft"), ("Nunu", "Papercraft")),
        )

    def test_stops_before_adjusted_skins(self) -> None:
        document = textwrap.dedent("""
        == New Cosmetics in the Store ==
        The following champion skins have been added to the store:
        * {{csl|Nidalee|Challenger}}

        The following champion skins have been adjusted:
        * {{csl|Lulu|Dragon Trainer|variant=old}}
        """)
        self.assertEqual(
            updater.parse_wiki_skin_entries(document),
            (("Nidalee", "Challenger"),),
        )

    def test_stops_before_updated_skins(self) -> None:
        document = textwrap.dedent("""
        == New Cosmetics ==
        The following champion skins have been added to the store:
        * {{csl|Riven|Reignited Worlds 2012}}

        The following Champion skins have been updated:
        * {{csl|Riven|Worlds 2012}}
        """)
        self.assertEqual(
            updater.parse_wiki_skin_entries(document),
            (("Riven", "Reignited Worlds 2012"),),
        )

    def test_does_not_confuse_were_released_with_rereleased(self) -> None:
        document = textwrap.dedent("""
        == New Skins ==
        The following skins were released along with this patch.
        * {{csl|LeBlanc|Prestigious|variant=old}}
        """)
        self.assertEqual(
            updater.parse_wiki_skin_entries(document),
            (("LeBlanc", "Prestigious"),),
        )

    def test_resumes_after_a_rereleased_skin_subsection(self) -> None:
        document = textwrap.dedent("""
        == New Skins in the Store ==
        The following skins were released along with this patch.
        * {{csl|Ahri|Midnight}}

        * {{csl|Caitlyn|Arctic Warfare}} (re-released for purchase)

        The following skins were also released with this patch.
        * {{csl|Katarina|Sandstorm}}
        """)
        self.assertEqual(
            updater.parse_wiki_skin_entries(document),
            (("Ahri", "Midnight"), ("Katarina", "Sandstorm")),
        )

    def test_supports_historical_new_skin_headings_at_multiple_levels(self) -> None:
        document = textwrap.dedent("""
        == League of Legends ==
        === New Skins in the Store ===
        * {{csl|Trundle|Traditional|variant=old}}

        == Other Changes ==
        * {{csl|Trundle|Lil' Slugger}}
        """)
        self.assertEqual(
            updater.parse_wiki_skin_entries(document),
            (("Trundle", "Traditional"),),
        )

    def test_supports_named_new_ultimate_skin_heading(self) -> None:
        document = textwrap.dedent("""
        == New Ultimate Skin: DJ Sona ==
        The ultimate skin, {{csl|Sona|DJ}}, has been added to the store.
        """)
        self.assertEqual(
            updater.parse_wiki_skin_entries(document),
            (("Sona", "DJ"),),
        )

    def test_extracts_skin_from_season_reward_heading(self) -> None:
        document = textwrap.dedent("""
        == End of Season 3 ==
        Eligible summoners will receive:
        * The exclusive {{csl|Elise|Victorious}} skin (Gold and above)

        == Other Changes ==
        * {{csl|Elise|Death Blossom}}
        """)
        self.assertEqual(
            updater.parse_wiki_skin_entries(document),
            (("Elise", "Victorious"),),
        )

    def test_distinguishes_infobox_launch_from_adjacent_update(self) -> None:
        document = textwrap.dedent("""
        {{Infobox patch
        |Highlights =
        * New skin: {{csl|Orianna|Victorious}}
        * {{csl|Riven|Reignited Worlds 2012}} launch &
          {{csl|Riven|Worlds 2012}} update.
        }}
        """)
        self.assertEqual(
            updater.parse_wiki_skin_entries(document),
            (
                ("Orianna", "Victorious"),
                ("Riven", "Reignited Worlds 2012"),
            ),
        )


class MergeTests(unittest.TestCase):
    def test_appends_in_chronological_page_order_without_overwriting(self) -> None:
        existing = {"1001": "26.01"}
        results = [
            resolved_patch_result(
                "26.11", ("1003", "Later Skin"), ("1001", "Existing Skin")
            ),
            resolved_patch_result("26.10", ("1002", "Earlier Skin")),
        ]
        merged = updater.merge_versions(existing, results)
        self.assertEqual(
            list(merged.merged.items()),
            [
                ("1001", "26.01"),
                ("1002", "26.10"),
                ("1003", "26.11"),
            ],
        )
        self.assertIn("ID 1001", merged.conflicts[0])

    def test_duplicate_release_is_deduplicated_by_skin_id(self) -> None:
        merged = updater.merge_versions(
            {},
            [
                resolved_patch_result("11.02", ("234011", "Lunar Beast Viego")),
                resolved_patch_result("11.03", ("234011", "Lunar Beast Viego")),
            ],
        )
        self.assertEqual(merged.additions, (("234011", "11.02"),))
        self.assertIn("appears in both 11.02 and 11.03", merged.duplicate_names[0])

    def test_atomic_writer_round_trips_unicode(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "skin_versions.json"
            expected = {"161001": "26.11", "222001": "26.12"}
            updater.write_versions_atomic(path, expected)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), expected)


class CatalogSyncTests(unittest.TestCase):
    def test_builds_top_level_and_chroma_map_but_excludes_quest_tiers(self) -> None:
        document = json.dumps({
            "1001": {
                "id": 1001,
                "name": "Goth Annie",
                "chromas": [{"id": 100101, "name": "Goth Annie (Ruby)"}],
                "questSkinInfo": {
                    "tiers": [{"id": 1002, "name": "Quest Annie"}]
                },
            }
        })
        self.assertEqual(
            updater.parse_cdragon_skin_catalog(document),
            {
                "1001": "Goth Annie",
                "100101": "Goth Annie (Ruby)",
            },
        )

class PatchDateTests(unittest.TestCase):
    def test_snapshot_verification_ignores_key_order_without_rewriting(self) -> None:
        expected = {"26.17": "2026-08-26", "26.18": "2026-09-10"}
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "patch_dates.json"
            updater.write_patch_dates_atomic(path, dict(reversed(expected.items())))
            original = path.read_bytes()
            updater.verify_patch_dates_snapshot(path, expected, versions=expected)
            self.assertEqual(path.read_bytes(), original)

    def test_snapshot_verification_still_rejects_changed_dates(self) -> None:
        expected = {"26.18": "2026-09-10"}
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "patch_dates.json"
            updater.write_patch_dates_atomic(path, {"26.18": "2026-09-09"})
            with self.assertRaisesRegex(updater.UpdateError, "post-write verification failed"):
                updater.verify_patch_dates_snapshot(path, expected, versions=expected)

    def test_reads_literal_ordinal_wiki_release_field(self) -> None:
        self.assertEqual(
            updater._parse_wiki_release_date(
                "December 1st, 2010", patch="1.0.0.106"
            ),
            "2010-12-01",
        )
        self.assertEqual(
            updater._parse_wiki_release_date(
                "July 22nd, 2010", patch="1.0.0.97"
            ),
            "2010-07-22",
        )

    def test_uses_first_release_when_wiki_records_revert_and_rerelease(self) -> None:
        self.assertEqual(
            updater._parse_wiki_release_date(
                "June 17, 2012 NA (Reverted) June 20, 2012 NA (Re-Release)",
                patch="1.0.0.141",
            ),
            "2012-06-17",
        )

    def test_merge_uses_wiki_dates_for_all_versions(self) -> None:
        existing = {"9.01": "2019-01-09", "26.14": "2026-07-14"}
        versions = {
            "1001": "9.01",
            "1002": "14.12",
            "1003": "26.14",
        }
        wiki_dates = {
            "9.01": "2019-01-09",
            "14.12": "2024-06-12",
            "26.14": "2026-07-15",
        }
        result = updater.merge_wiki_patch_dates(existing, versions, wiki_dates)

        self.assertEqual(
            result.merged,
            {
                "9.01": "2019-01-09",
                "14.12": "2024-06-12",
                "26.14": "2026-07-15",
            },
        )
        self.assertEqual(result.additions, (("14.12", "2024-06-12"),))
        self.assertEqual(
            result.updates,
            (("26.14", "2026-07-14", "2026-07-15"),),
        )

    def test_verification_rejects_missing_patch_dates(self) -> None:
        with self.assertRaisesRegex(updater.UpdateError, "missing versions: 14.12"):
            updater.verify_patch_dates_data(
                {"9.01": "2019-01-09"},
                expected_versions=("9.01", "14.12"),
            )


class WikiArtworkTests(unittest.TestCase):
    def test_filename_rules_preserve_punctuation_and_use_nunu_art_alias(self) -> None:
        record = updater.WikiSkinRecord(
            "20008", "Nunu & Willump", "Space/Groove: Deluxe", None, "2024-01-01"
        )
        self.assertEqual(
            updater.wiki_asset_title(record, "uncentered"),
            "File:Nunu & Willump SpaceGroove-DeluxeSkin.jpg",
        )
        self.assertEqual(
            updater.wiki_asset_title(record, "centered"),
            "File:Nunu SpaceGroove-DeluxeCentered.jpg",
        )

    def test_resolves_all_four_revision_addressed_images(self) -> None:
        record = updater.WikiSkinRecord(
            "222065", "Jinx", "Ocean Song", "Upcoming", None
        )
        pages = []
        for variant in updater.WIKI_ASSET_VARIANTS:
            width, height = updater.WIKI_ASSET_DIMENSIONS[variant]
            pages.append({
                "title": updater.wiki_asset_title(record, variant),
                "imageinfo": [{
                    "url": f"https://wiki.leagueoflegends.com/images/{variant}.jpg?rev",
                    "sha1": f"sha-{variant}",
                    "timestamp": "2026-08-30T12:00:00Z",
                    "width": width,
                    "height": height,
                    "size": width * height,
                }],
            })
        assets = updater.resolve_wiki_skin_assets(
            [record],
            fetcher=lambda _url: json.dumps({"query": {"pages": pages}}),
        )
        self.assertEqual(set(assets["222065"]), set(updater.WIKI_ASSET_VARIANTS))
        self.assertTrue(assets["222065"]["loading"]["url"].endswith("?rev"))
        updater.verify_skin_assets_data(
            assets,
            expected_ids={"222065"},
            released_ids={"222065"},
        )

    def test_one_redirected_wiki_file_can_serve_multiple_skin_ids(self) -> None:
        original = updater.WikiSkinRecord(
            "21020", "Miss Fortune", "Prestige Bewitching", None, None
        )
        rerelease = updater.WikiSkinRecord(
            "21030", "Miss Fortune", "Prestige Bewitching (2022)", None, None
        )
        target = updater.wiki_asset_title(original, "uncentered")
        redirected = updater.wiki_asset_title(rerelease, "uncentered")
        response = {
            "query": {
                "redirects": [{"from": redirected, "to": target}],
                "pages": [{
                    "title": target,
                    "imageinfo": [{
                        "url": "https://wiki.leagueoflegends.com/images/shared.jpg?rev",
                        "sha1": "shared",
                        "timestamp": "2026-08-30T12:00:00Z",
                        "width": 1215,
                        "height": 717,
                        "size": 12345,
                    }],
                }],
            }
        }
        assets = updater.resolve_wiki_skin_assets(
            [original, rerelease],
            fetcher=lambda _url: json.dumps(response),
        )
        self.assertEqual(
            assets["21020"]["uncentered"]["url"],
            assets["21030"]["uncentered"]["url"],
        )

    def test_allows_missing_pbe_art_but_rejects_missing_released_art(self) -> None:
        assets: dict[str, dict[str, dict[str, object]]] = {"222065": {}}
        updater.verify_skin_assets_data(assets, expected_ids={"222065"})
        with self.assertRaisesRegex(updater.UpdateError, "incomplete"):
            updater.verify_skin_assets_data(
                assets,
                expected_ids={"222065"},
                released_ids={"222065"},
            )

    def test_artwork_manifest_round_trips(self) -> None:
        info = {
            "title": "File:Jinx OceanSongTile.jpg",
            "requestedTitle": "File:Jinx OceanSongTile.jpg",
            "url": "https://wiki.leagueoflegends.com/images/tile.jpg?rev",
            "sha1": "abc123",
            "timestamp": "2026-08-30T12:00:00Z",
            "width": 380,
            "height": 380,
            "bytes": 12345,
        }
        assets = {"222065": {"tile": info}}
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "skin_assets.json"
            updater.write_skin_assets_atomic(
                path,
                assets,
            )
            loaded_assets = updater.load_skin_assets_manifest(path)
            self.assertEqual(loaded_assets, assets)
            self.assertNotIn("updatedAt", json.loads(path.read_text(encoding="utf-8")))

    def test_update_writes_assets_only_when_content_changes(self) -> None:
        document = catalog_document(count=8000)
        catalog = updater.parse_cdragon_skin_catalog(document)
        assets = {"100001": {
            variant: {
                "url": f"https://example.test/{variant}.jpg",
                "sha1": "original",
                "timestamp": "2026-08-30T12:00:00Z",
                "width": dimensions[0],
                "height": dimensions[1],
                "bytes": 12345,
            }
            for variant, dimensions in updater.WIKI_ASSET_DIMENSIONS.items()
        }}
        wiki_record = updater.WikiSkinRecord("100001", "Test", "Skin", None, None)
        snapshot = updater.WikiSourceSnapshot(
            (resolved_patch_result("26.18", ("100001", catalog["100001"])),),
            {"26.18": "2026-09-10"},
            1,
            updater.WikiSkinCatalog({}, {}, {}, {"100001": wiki_record}),
        )
        for changed in (False, True):
            with self.subTest(changed=changed), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                ids = root / "skin_ids.json"
                versions = root / "skin_versions.json"
                dates = root / "patch_dates.json"
                manifest = root / "skin_assets.json"
                ids.write_bytes(updater.encode_skin_catalog(catalog))
                updater.write_versions_atomic(versions, {"100001": "26.18"})
                updater.write_patch_dates_atomic(dates, snapshot.patch_dates)
                updater.write_skin_assets_atomic(manifest, assets)
                if not changed:
                    content = json.loads(manifest.read_text(encoding="utf-8"))
                    manifest.write_text(json.dumps(content, indent=4), encoding="utf-8")
                candidate = json.loads(json.dumps(assets))
                if changed:
                    candidate["100001"]["tile"]["sha1"] = "new-revision"
                before = manifest.stat().st_mtime_ns
                with (
                    mock.patch.object(updater, "DEFAULT_SKIN_IDS_PATH", ids),
                    mock.patch.object(updater, "fetch_text", return_value=document),
                    mock.patch.object(updater, "load_wiki_source_snapshot", return_value=snapshot),
                    mock.patch.object(updater, "resolve_wiki_skin_assets", return_value=candidate),
                    mock.patch.object(updater, "_write_bytes_atomic", wraps=updater._write_bytes_atomic) as write,
                    redirect_stdout(io.StringIO()),
                ):
                    result = updater.run([
                        "--versions", str(versions), "--patch-dates", str(dates),
                        "--assets", str(manifest),
                    ])
                self.assertEqual(result, 0)
                self.assertEqual(write.call_count, int(changed))
                self.assertEqual(updater.load_skin_assets_manifest(manifest), candidate)
                if not changed:
                    self.assertEqual(manifest.stat().st_mtime_ns, before)


class VerificationTests(unittest.TestCase):
    def test_historical_catalog_exceptions_are_reported_without_failure(self) -> None:
        catalog = skin_catalog({"1001": "Current Skin"})
        self.assertEqual(
            updater.catalog_history_exceptions(
                {"1001": "26.14", "1002": "25.01"}, catalog
            ),
            ("1002",),
        )

    def test_versions_validation_rejects_bad_patch_and_invalid_id(self) -> None:
        with self.assertRaises(updater.UpdateError):
            updater.verify_versions_data({"1001": "patch 26.14"})
        with self.assertRaises(updater.UpdateError):
            updater.verify_versions_data({"Known Skin": "26.14"})
        with self.assertRaises(updater.UpdateError):
            updater.verify_versions_data({"001001": "26.14"})
        with self.assertRaises(updater.UpdateError):
            updater.verify_versions_data({"1000": "26.14"})

    def test_written_snapshot_is_reloaded_and_verified(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "skin_versions.json"
            versions = {"1001": "26.14"}
            updater.write_versions_atomic(path, versions)
            updater.verify_versions_snapshot(path, versions)
            with self.assertRaises(updater.UpdateError):
                updater.verify_versions_snapshot(path, {"1002": "26.14"})


class SourceIsolationTests(unittest.TestCase):
    def test_updater_contains_no_riot_patch_note_crawler(self) -> None:
        source = Path(updater.__file__).read_text(encoding="utf-8")
        forbidden_markers = (
            "www.leagueoflegends.com/en-us/news",
            "/news/game-updates/",
            "patch-schedule",
            "SITEMAP_URL",
            "discover_patch_refs",
            "parse_official_patch_schedule",
            "LeagueSkins",
            "ddragon.leagueoflegends.com",
            "DataDragonBuildResolver",
        )
        for marker in forbidden_markers:
            with self.subTest(marker=marker):
                self.assertNotIn(marker, source)


class CommandLineTests(unittest.TestCase):
    def test_default_files_follow_project_ownership(self) -> None:
        self.assertEqual(
            updater.DEFAULT_SKIN_VERSIONS_PATH,
            updater.PROJECT_ROOT / "skin_versions.json",
        )
        self.assertEqual(
            updater.DEFAULT_SKIN_IDS_PATH,
            updater.PROJECT_ROOT / "skin_ids.json",
        )
        self.assertEqual(
            updater.DEFAULT_PATCH_DATES_PATH,
            updater.PROJECT_ROOT / "patch_dates.json",
        )
        self.assertEqual(
            updater.DEFAULT_SKIN_ASSETS_PATH,
            updater.PROJECT_ROOT / "skin_assets.json",
        )

    def test_skin_ids_option_has_been_removed(self) -> None:
        parser = updater.build_argument_parser()
        options = {
            option
            for action in parser._actions
            for option in action.option_strings
        }
        self.assertNotIn("--skin-ids", options)
        self.assertNotIn("--wiki-backfill", options)
        self.assertNotIn("--since", options)
        self.assertNotIn("--all", options)
        self.assertNotIn("--upcoming", options)
        self.assertIn("--assets", options)

if __name__ == "__main__":
    unittest.main()
