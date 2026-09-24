from contextlib import redirect_stderr
import io
import json
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from league_skin_version import site_builder, updater


def wiki_asset_info(skin_id: str, variant: str) -> dict[str, object]:
    width, height = updater.WIKI_ASSET_DIMENSIONS[variant]
    return {
        "title": f"File:{skin_id}-{variant}.jpg",
        "requestedTitle": f"File:{skin_id}-{variant}.jpg",
        "url": (
            "https://wiki.leagueoflegends.com/images/"
            f"{skin_id}-{variant}.jpg?revision"
        ),
        "sha1": f"sha-{skin_id}-{variant}",
        "timestamp": "2026-08-30T12:00:00Z",
        "width": width,
        "height": height,
        "bytes": width * height,
    }


def complete_wiki_assets(*skin_ids: str) -> dict[str, dict[str, dict[str, object]]]:
    return {
        skin_id: {
            variant: wiki_asset_info(skin_id, variant)
            for variant in updater.WIKI_ASSET_VARIANTS
        }
        for skin_id in skin_ids
    }


class SitePayloadTests(unittest.TestCase):
    def setUp(self) -> None:
        self.live_en = {
            "13000": {
                "id": 13000,
                "name": "Ryze",
                "splashPath": (
                    "/lol-game-data/assets/ASSETS/Characters/Ryze/"
                    "Skins/Base/Images/ryze_splash_centered_0.jpg"
                ),
            },
            "13050": {
                "id": 13050,
                "name": "Quest Ryze",
                "rarity": "kEpic",
                "isLegacy": True,
                "skinLines": [{"id": 7}],
                "questSkinInfo": {
                    "tiers": [{
                        "id": 13011,
                        "name": "Championship Ryze",
                        "splashPath": (
                            "/lol-game-data/assets/ASSETS/Characters/Ryze/"
                            "Skins/Skin11/Images/ryze_centered.jpg"
                        ),
                        "uncenteredSplashPath": (
                            "/lol-game-data/assets/ASSETS/Characters/Ryze/"
                            "Skins/Skin11/Images/ryze_uncentered.jpg"
                        ),
                        "loadScreenPath": (
                            "/lol-game-data/assets/ASSETS/Characters/Ryze/"
                            "Skins/Skin11/RyzeLoadScreen_11.jpg"
                        ),
                        "tilePath": (
                            "/lol-game-data/assets/ASSETS/Characters/Ryze/"
                            "Skins/Skin11/Images/ryze_tile.jpg"
                        ),
                    }]
                },
            },
            "222000": {
                "id": 222000,
                "name": "Jinx",
                "splashPath": (
                    "/lol-game-data/assets/ASSETS/Characters/Jinx/"
                    "Skins/Base/Images/jinx_splash_centered_0.jpg"
                ),
            },
            "222001": {
                "id": 222001,
                "name": "Crime City Jinx",
                "rarity": "kNoRarity",
                "isLegacy": False,
                "loadScreenPath": (
                    "/lol-game-data/assets/ASSETS/Characters/Jinx/"
                    "Skins/Skin01/JinxLoadScreen_1.jpg"
                ),
                "skinLines": [{"id": 7}],
                "chromas": [{
                    "id": 222002,
                    "name": "Crime City Jinx (Ruby)",
                    "colors": ["#D33528", "#111111"],
                    "chromaPath": (
                        "/lol-game-data/assets/v1/champion-chroma-images/"
                        "222/222002.png"
                    ),
                }],
            },
            "86000": {
                "id": 86000,
                "name": "Garen",
                "splashPath": (
                    "/lol-game-data/assets/ASSETS/Characters/Garen/"
                    "Skins/Base/Images/garen_splash_centered_0.jpg"
                ),
            },
        }
        self.live_zh = {
            "13000": {"id": 13000, "name": "符文法师"},
            "13050": {
                "id": 13050,
                "name": "任务 瑞兹",
                "questSkinInfo": {
                    "tiers": [{"id": 13011, "name": "冠军之志 瑞兹"}]
                },
            },
            "222000": {"id": 222000, "name": "暴走萝莉"},
            "222001": {
                "id": 222001,
                "name": "黑帮狂花 金克丝",
                "chromas": [{
                    "id": 222002,
                    "name": "黑帮狂花 金克丝（红宝石）",
                }],
            },
            "86000": {"id": 86000, "name": "德玛西亚之力"},
        }
        self.live_champions_zh = [
            {"id": 13, "name": "符文法师", "description": "瑞兹"},
            {"id": 86, "name": "德玛西亚之力", "description": "盖伦"},
            {"id": 222, "name": "暴走萝莉", "description": "金克丝"},
        ]
        self.pbe_en = {
            "222065": {
                "id": 222065,
                "name": "Ocean Song Jinx",
                "rarity": "kEpic",
                "isLegacy": False,
                "splashPath": (
                    "/lol-game-data/assets/ASSETS/Characters/Jinx/"
                    "Skins/Skin65/Images/jinx_centered.jpg"
                ),
                "uncenteredSplashPath": (
                    "/lol-game-data/assets/ASSETS/Characters/Jinx/"
                    "Skins/Skin65/Images/jinx_uncentered.jpg"
                ),
                "loadScreenPath": (
                    "/lol-game-data/assets/ASSETS/Characters/Jinx/"
                    "Skins/Skin65/JinxLoadScreen_65.jpg"
                ),
                "tilePath": (
                    "/lol-game-data/assets/ASSETS/Characters/Jinx/"
                    "Skins/Skin65/Images/jinx_tile.jpg"
                ),
                "skinLines": [{"id": 159}],
                "chromas": [],
            }
        }
        self.pbe_zh = {
            "222065": {"id": 222065, "name": "海之歌 金克丝"}
        }
        self.pbe_champions_zh = list(self.live_champions_zh)
        self.documents = {
            site_builder.CDRAGON_EN_SKINS_URL: json.dumps(self.live_en),
            site_builder.CDRAGON_ZH_SKINS_URL: json.dumps(
                self.live_zh, ensure_ascii=False
            ),
            site_builder.CDRAGON_ZH_CHAMPION_SUMMARY_URL: json.dumps(
                self.live_champions_zh, ensure_ascii=False
            ),
            site_builder.CDRAGON_EN_SKINLINES_URL: json.dumps([
                {"id": 7, "name": "Test Skinline"}
            ]),
            site_builder.CDRAGON_ZH_SKINLINES_URL: json.dumps([
                {"id": 7, "name": "测试系列"}
            ], ensure_ascii=False),
            site_builder.CDRAGON_PBE_EN_SKINS_URL: json.dumps(self.pbe_en),
            site_builder.CDRAGON_PBE_ZH_SKINS_URL: json.dumps(
                self.pbe_zh, ensure_ascii=False
            ),
            site_builder.CDRAGON_PBE_ZH_CHAMPION_SUMMARY_URL: json.dumps(
                self.pbe_champions_zh, ensure_ascii=False
            ),
            site_builder.CDRAGON_PBE_EN_SKINLINES_URL: json.dumps([
                {"id": 159, "name": "Ocean Song"}
            ]),
            site_builder.CDRAGON_PBE_ZH_SKINLINES_URL: json.dumps([
                {"id": 159, "name": "海之歌"}
            ], ensure_ascii=False),
        }

    def fetch(self, url: str) -> str:
        return self.documents[url]

    def write_inputs(
        self,
        root: Path,
        *,
        versions: dict[str, str],
        upcoming: dict[str, dict[str, str]] | None = None,
        assets: dict[str, dict[str, dict[str, object]]] | None = None,
    ) -> tuple[Path, Path, Path, Path]:
        skin_ids = root / "skin_ids.json"
        versions_path = root / "skin_versions.json"
        patch_dates = root / "patch_dates.json"
        assets_path = root / "skin_assets.json"
        skin_ids.write_text(json.dumps({
            "13000": "Ryze",
            "222000": "Jinx",
            "222001": "Crime City Jinx",
            "86000": "Garen",
        }), encoding="utf-8")
        versions_path.write_text(json.dumps(versions), encoding="utf-8")
        patch_dates.write_text(json.dumps({
            patch: f"20{index + 19:02d}-01-01"
            for index, patch in enumerate(dict.fromkeys(versions.values()))
        }), encoding="utf-8")
        source_assets = assets if assets is not None else complete_wiki_assets(
            *versions,
            *(upcoming or {}),
        )
        updater.write_skin_assets_atomic(
            assets_path,
            {
                skin_id: source_assets[skin_id]
                for skin_id in versions
            },
        )
        return (
            skin_ids,
            versions_path,
            patch_dates,
            assets_path,
        )

    def build_payload(
        self,
        root: Path,
        *,
        versions: dict[str, str],
        upcoming: dict[str, dict[str, str]] | None = None,
        assets: dict[str, dict[str, dict[str, object]]] | None = None,
        fetcher=None,
        data_updated_at: str | None = None,
    ) -> dict[str, object]:
        paths = self.write_inputs(
            root,
            versions=versions,
            upcoming=upcoming,
            assets=assets,
        )
        upcoming_data = upcoming or {}
        upcoming_skins = tuple(
            updater.UpcomingSkin(
                skin_id,
                record["champion"],
                record["name"],
                record["plannedPatch"],
                record["status"],
            )
            for skin_id, record in upcoming_data.items()
        )
        upcoming_snapshot = updater.WikiUpcomingSnapshot(
            upcoming_skins,
            updater.WikiSkinCatalog(
                {},
                {},
                {},
                {
                    skin.skin_id: updater.WikiSkinRecord(
                        skin.skin_id,
                        skin.champion,
                        skin.name,
                        "Upcoming",
                        None,
                    )
                    for skin in upcoming_skins
                },
            ),
        )
        source_assets = assets if assets is not None else complete_wiki_assets(
            *versions,
            *upcoming_data,
        )
        upcoming_assets = {
            skin_id: source_assets[skin_id]
            for skin_id in upcoming_data
        }
        with (
            mock.patch.object(
                updater,
                "load_wiki_upcoming_snapshot",
                return_value=upcoming_snapshot,
            ),
            mock.patch.object(
                updater,
                "resolve_wiki_skin_assets",
                return_value=upcoming_assets,
            ),
        ):
            return site_builder.build_site_payload(
                paths[0],
                paths[1],
                paths[2],
                assets_path=paths[3],
                fetcher=fetcher or self.fetch,
                generated_at=datetime(2026, 8, 20, 12, 30, tzinfo=timezone.utc),
                data_updated_at=data_updated_at,
                minimum_catalog_entries=1,
            )

    def test_flattens_quest_tiers_and_inherits_classification(self) -> None:
        flattened = site_builder._flatten_cdragon_skins(
            {"13050": self.live_en["13050"]},
            asset_origin="https://assets.example",
            source_label="test",
        )
        tier = flattened["13011"]
        self.assertEqual(tier["name"], "Championship Ryze")
        self.assertEqual(tier["rarity"], "kEpic")
        self.assertTrue(tier["isLegacy"])
        self.assertEqual(tier["skinLines"], [{"id": 7}])

    def test_joins_wiki_art_with_cdragon_metadata_and_fallbacks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            payload = self.build_payload(
                Path(temporary),
                versions={"13011": "9.19", "222001": "10.13"},
                data_updated_at="2026-08-20T12:00:00Z",
            )

        self.assertEqual(payload["schemaVersion"], 4)
        self.assertNotIn("dataDragonVersion", payload)
        self.assertEqual(payload["generatedAt"], "2026-08-20T12:30:00Z")
        self.assertEqual(payload["dataUpdatedAt"], "2026-08-20T12:00:00Z")
        self.assertEqual(payload["totalSkins"], 2)
        self.assertEqual(payload["totalChampions"], 2)
        self.assertEqual(payload["communityDragonMatchedSkins"], 2)
        self.assertEqual(payload["leagueWikiArtworkSkins"], 2)
        self.assertEqual(payload["artworkSources"], {
            "primary": "League Wiki",
            "fallback": "CommunityDragon",
        })
        self.assertIn(
            {
                "id": "7",
                "name": "Test Skinline",
                "nameZh": "测试系列",
                "count": 2,
            },
            payload["skinLines"],
        )

        by_id = {entry["id"]: entry for entry in payload["skins"]}
        jinx = by_id["222001"]
        self.assertEqual(jinx["nameZh"], "黑帮狂花 金克丝")
        self.assertEqual(jinx["nameSource"], "CommunityDragon live")
        self.assertEqual(jinx["rarity"], "Standard")
        self.assertFalse(jinx["legacy"])
        self.assertEqual(jinx["championZh"], "金克丝")
        self.assertTrue(jinx["image"].endswith("222001-loading.jpg?revision"))
        self.assertIn("222001-uncentered", jinx["art"]["uncentered"])
        self.assertIn(
            "raw.communitydragon.org",
            jinx["artFallback"]["loading"],
        )
        self.assertEqual(
            jinx["chromas"][0]["nameZh"],
            "黑帮狂花 金克丝（红宝石）",
        )
        self.assertEqual(jinx["sources"], ["wiki", "cdragon"])

        ryze = by_id["13011"]
        self.assertEqual(ryze["name"], "Championship Ryze")
        self.assertEqual(ryze["nameZh"], "冠军之志 瑞兹")
        self.assertEqual(ryze["rarity"], "Epic")
        self.assertTrue(ryze["legacy"])
        self.assertIn("ryze_uncentered", ryze["artFallback"]["uncentered"])

    def test_released_skin_removed_from_cdragon_keeps_wiki_data(self) -> None:
        snapshot = updater.WikiUpcomingSnapshot((), updater.WikiSkinCatalog({}, {}, {}, {
            "86043": updater.WikiSkinRecord("86043", "Garen", "Pengu", "Limited", None),
        }))
        with tempfile.TemporaryDirectory() as temporary:
            paths = self.write_inputs(
                Path(temporary), versions={"222001": "10.13", "86043": "25.07"}
            )
            with mock.patch.object(
                updater, "load_wiki_upcoming_snapshot", return_value=snapshot
            ):
                payload = site_builder.build_site_payload(
                    *paths[:3],
                    assets_path=paths[3],
                    fetcher=self.fetch,
                    minimum_catalog_entries=1,
                )

        by_id = {skin["id"]: skin for skin in payload["skins"]}
        pengu = by_id["86043"]
        self.assertEqual(pengu["name"], "Pengu Garen")
        self.assertEqual(pengu["nameZh"], "Pengu Garen")
        self.assertEqual(pengu["championZh"], "盖伦")
        self.assertEqual(pengu["nameSource"], "League Wiki SkinData")
        self.assertIsNone(pengu["rarity"])
        self.assertEqual(pengu["chromas"], [])
        self.assertTrue(pengu["image"].endswith("86043-loading.jpg?revision"))
        self.assertIsNone(pengu["imageFallback"])
        self.assertEqual(pengu["sources"], ["wiki"])
        self.assertEqual(by_id["222001"]["sources"], ["wiki", "cdragon"])
        self.assertEqual(by_id["222065"]["sources"], ["cdragon"])
        self.assertEqual(payload["communityDragonMatchedSkins"], 1)

    def test_adds_pbe_skin_with_wiki_primary_and_cdragon_fallback(self) -> None:
        upcoming = {
            "222065": {
                "champion": "Jinx",
                "name": "Ocean Song",
                "plannedPatch": "26.17",
                "status": "pbe",
            }
        }
        with tempfile.TemporaryDirectory() as temporary:
            payload = self.build_payload(
                Path(temporary),
                versions={"222001": "10.13"},
                upcoming=upcoming,
            )

        self.assertEqual(payload["totalSkins"], 1)
        self.assertEqual(payload["upcoming"], [{"version": "26.17", "count": 1}])
        record = next(
            skin for skin in payload["skins"] if skin["status"] == "upcoming"
        )
        self.assertEqual(record["nameZh"], "海之歌 金克丝")
        self.assertIn("222065-loading", record["image"])
        self.assertIn("/pbe/", record["imageFallback"])
        self.assertEqual(record["artSource"], "League Wiki")
        self.assertFalse(record["artPending"])
        self.assertEqual(payload["communityDragonPbeMatchedSkins"], 1)

    def test_keeps_pbe_skin_when_both_art_sources_are_missing(self) -> None:
        upcoming = {
            "222065": {
                "champion": "Jinx",
                "name": "Ocean Song",
                "plannedPatch": "26.17",
                "status": "pbe",
            }
        }
        documents = dict(self.documents)
        documents[site_builder.CDRAGON_PBE_EN_SKINS_URL] = json.dumps({
            "1": {"id": 1, "name": "Unused"}
        })
        documents[site_builder.CDRAGON_PBE_ZH_SKINS_URL] = json.dumps({
            "1": {"id": 1, "name": "未使用"}
        }, ensure_ascii=False)

        with tempfile.TemporaryDirectory() as temporary:
            payload = self.build_payload(
                Path(temporary),
                versions={"222001": "10.13"},
                upcoming=upcoming,
                assets={
                    **complete_wiki_assets("222001"),
                    "222065": {},
                },
                fetcher=lambda url: documents[url],
            )

        record = next(
            skin for skin in payload["skins"] if skin["status"] == "upcoming"
        )
        self.assertEqual(record["name"], "Ocean Song Jinx")
        self.assertIsNone(record["image"])
        self.assertEqual(record["art"], {})
        self.assertTrue(record["artPending"])
        self.assertEqual(record["sources"], ["wiki"])
        self.assertEqual(payload["communityDragonPbeMatchedSkins"], 0)

    def test_ignores_pbe_fetch_failures_for_upcoming_enrichment(self) -> None:
        upcoming = {
            "222065": {
                "champion": "Jinx",
                "name": "Ocean Song",
                "plannedPatch": "26.17",
                "status": "pbe",
            }
        }

        def fetch(url: str) -> str:
            if url.startswith(site_builder.CDRAGON_PBE_GLOBAL_ORIGIN):
                raise updater.UpdateError("PBE unavailable")
            return self.fetch(url)

        with tempfile.TemporaryDirectory() as temporary:
            payload = self.build_payload(
                Path(temporary),
                versions={"222001": "10.13"},
                upcoming=upcoming,
                fetcher=fetch,
            )

        record = next(
            skin for skin in payload["skins"] if skin["status"] == "upcoming"
        )
        self.assertEqual(record["name"], "Ocean Song Jinx")
        self.assertEqual(record["artSource"], "League Wiki")
        # Unreadable PBE data cannot show the skin is Wiki-only.
        self.assertEqual(record["sources"], ["wiki", "cdragon"])
        self.assertEqual(payload["communityDragonPbeMatchedSkins"], 0)

    def test_uses_pbe_base_metadata_for_an_upcoming_new_champion(self) -> None:
        upcoming = {
            "999001": {
                "champion": "Aurora",
                "name": "Primordian",
                "plannedPatch": "26.18",
                "status": "pbe",
            }
        }
        documents = dict(self.documents)
        documents[site_builder.CDRAGON_PBE_EN_SKINS_URL] = json.dumps({
            **self.pbe_en,
            "999000": {
                "id": 999000,
                "name": "Aurora",
                "splashPath": (
                    "/lol-game-data/assets/ASSETS/Characters/Aurora/"
                    "Skins/Base/Images/aurora_splash_centered_0.jpg"
                ),
            },
            "999001": {
                "id": 999001,
                "name": "Primordian Aurora",
                "loadScreenPath": (
                    "/lol-game-data/assets/ASSETS/Characters/Aurora/"
                    "Skins/Skin01/AuroraLoadScreen_1.jpg"
                ),
            },
        })
        documents[site_builder.CDRAGON_PBE_ZH_SKINS_URL] = json.dumps({
            **self.pbe_zh,
            "999000": {"id": 999000, "name": "双界灵兔"},
            "999001": {"id": 999001, "name": "原初 阿萝拉"},
        }, ensure_ascii=False)
        documents[site_builder.CDRAGON_PBE_ZH_CHAMPION_SUMMARY_URL] = json.dumps([
            *self.pbe_champions_zh,
            {"id": 999, "name": "双界灵兔", "description": "阿萝拉"},
        ], ensure_ascii=False)

        with tempfile.TemporaryDirectory() as temporary:
            payload = self.build_payload(
                Path(temporary),
                versions={"222001": "10.13"},
                upcoming=upcoming,
                fetcher=lambda url: documents[url],
            )

        record = next(skin for skin in payload["skins"] if skin["id"] == "999001")
        self.assertEqual(record["champion"], "Aurora")
        self.assertEqual(record["championZh"], "阿萝拉")
        self.assertEqual(record["championAlias"], "Aurora")

    def test_lists_unreleased_pbe_skins_without_a_wiki_patch(self) -> None:
        documents = dict(self.documents)
        documents[site_builder.CDRAGON_PBE_EN_SKINS_URL] = json.dumps({
            **self.pbe_en,
            "222000": {"id": 222000, "name": "Jinx"},
            "222001": {"id": 222001, "name": "Crime City Jinx"},
            "222099": {"id": 222099, "name": ""},
            "60222000": {"id": 60222000, "name": "Jinx"},
            "60222301": {"id": 60222301, "name": "Classic Jinx"},
        })

        with tempfile.TemporaryDirectory() as temporary:
            payload = self.build_payload(
                Path(temporary),
                versions={"222001": "10.13"},
                fetcher=lambda url: documents[url],
            )

        upcoming = [skin for skin in payload["skins"] if skin["status"] == "upcoming"]
        self.assertEqual([skin["id"] for skin in upcoming], ["222065"])
        self.assertEqual(upcoming[0]["version"], site_builder.UNSCHEDULED_VERSION)
        self.assertEqual(upcoming[0]["nameZh"], "海之歌 金克丝")
        self.assertEqual(upcoming[0]["artSource"], "CommunityDragon PBE")
        self.assertEqual(upcoming[0]["sources"], ["cdragon"])
        self.assertEqual(payload["upcoming"], [{"version": "upcoming", "count": 1}])
        self.assertEqual(payload["totalSkins"], 1)

    def test_wiki_patch_numbers_label_the_skins_it_lists(self) -> None:
        upcoming = {
            "222065": {
                "champion": "Jinx",
                "name": "Ocean Song",
                "plannedPatch": "26.17",
                "status": "pbe",
            }
        }
        documents = dict(self.documents)
        documents[site_builder.CDRAGON_PBE_EN_SKINS_URL] = json.dumps({
            **self.pbe_en,
            "86050": {"id": 86050, "name": "Test Garen"},
        })

        with tempfile.TemporaryDirectory() as temporary:
            payload = self.build_payload(
                Path(temporary),
                versions={"222001": "10.13"},
                upcoming=upcoming,
                fetcher=lambda url: documents[url],
            )

        self.assertEqual(
            [(skin["id"], skin["version"]) for skin in payload["skins"]],
            [("86050", "upcoming"), ("222065", "26.17"), ("222001", "10.13")],
        )
        self.assertEqual(payload["upcoming"], [
            {"version": "upcoming", "count": 1},
            {"version": "26.17", "count": 1},
        ])

    def test_released_skin_named_by_no_source_fails_the_build(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            paths = self.write_inputs(Path(temporary), versions={"86043": "25.07"})
            with (
                mock.patch.object(
                    updater,
                    "load_wiki_upcoming_snapshot",
                    side_effect=updater.UpdateError("Wiki is down"),
                ),
                redirect_stderr(io.StringIO()),
                self.assertRaisesRegex(site_builder.SiteBuildError, "86043"),
            ):
                site_builder.build_site_payload(
                    *paths[:3],
                    assets_path=paths[3],
                    fetcher=self.fetch,
                    minimum_catalog_entries=1,
                )

    def test_wiki_schedule_failure_keeps_pbe_upcoming_skins(self) -> None:
        stderr = io.StringIO()
        with tempfile.TemporaryDirectory() as temporary:
            paths = self.write_inputs(Path(temporary), versions={"222001": "10.13"})
            with (
                mock.patch.object(
                    updater,
                    "load_wiki_upcoming_snapshot",
                    side_effect=updater.UpdateError("VPBE is mid-edit"),
                ),
                redirect_stderr(stderr),
            ):
                payload = site_builder.build_site_payload(
                    *paths[:3],
                    assets_path=paths[3],
                    fetcher=self.fetch,
                    minimum_catalog_entries=1,
                )

        self.assertIn(
            "League Wiki Upcoming schedule unavailable: VPBE is mid-edit",
            stderr.getvalue(),
        )
        self.assertEqual(payload["upcoming"], [{"version": "upcoming", "count": 1}])
        # Unreadable Wiki data cannot show the skin is CDragon-only.
        record = next(skin for skin in payload["skins"] if skin["id"] == "222065")
        self.assertEqual(record["sources"], ["wiki", "cdragon"])

    def test_wiki_listing_and_artwork_problems_only_warn(self) -> None:
        snapshot = updater.WikiUpcomingSnapshot(
            (updater.UpcomingSkin("222065", "Jinx", "Ocean Song", "26.17"),),
            updater.WikiSkinCatalog({}, {}, {}, {
                "222065": updater.WikiSkinRecord(
                    "222065", "Jinx", "Ocean Song", "Upcoming", None
                ),
            }),
            ("VPBE: League Wiki SkinData has no skin matching 'Jinx' / 'Mystery'",),
        )
        stderr = io.StringIO()
        with tempfile.TemporaryDirectory() as temporary:
            paths = self.write_inputs(Path(temporary), versions={"222001": "10.13"})
            with (
                mock.patch.object(
                    updater, "load_wiki_upcoming_snapshot", return_value=snapshot
                ),
                mock.patch.object(
                    updater,
                    "resolve_wiki_skin_assets",
                    side_effect=updater.UpdateError("file API is down"),
                ),
                redirect_stderr(stderr),
            ):
                payload = site_builder.build_site_payload(
                    *paths[:3],
                    assets_path=paths[3],
                    fetcher=self.fetch,
                    minimum_catalog_entries=1,
                )

        self.assertIn("warning: VPBE: League Wiki SkinData", stderr.getvalue())
        self.assertIn(
            "League Wiki Upcoming artwork unavailable: file API is down",
            stderr.getvalue(),
        )
        record = next(skin for skin in payload["skins"] if skin["id"] == "222065")
        self.assertEqual(record["version"], "26.17")
        self.assertEqual(record["artSource"], "CommunityDragon PBE")

    def test_local_build_does_not_report_build_time_as_update_time(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            payload = self.build_payload(Path(temporary), versions={"222001": "10.13"})
        self.assertIsNone(payload["dataUpdatedAt"])
        self.assertEqual(payload["generatedAt"], "2026-08-20T12:30:00Z")

    def test_rejects_invalid_actions_timestamp(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(site_builder.SiteBuildError, "timestamp"):
                self.build_payload(
                    Path(temporary), versions={"222001": "10.13"},
                    data_updated_at="not-a-timestamp",
                )

    def test_build_copies_static_files_and_writes_data(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "site"
            output = root / "dist"
            source.mkdir()
            (source / "index.html").write_text("<h1>Site</h1>", encoding="utf-8")
            paths = self.write_inputs(root, versions={"222001": "10.13"})

            original = site_builder.build_site_payload
            try:
                site_builder.build_site_payload = lambda *_args, **_kwargs: {
                    "schemaVersion": site_builder.SITE_SCHEMA_VERSION,
                    "generatedAt": "2026-08-20T12:30:00Z",
                    "dataUpdatedAt": "2026-08-20T12:00:00Z",
                    "totalSkins": 1,
                    "totalChampions": 1,
                    "versions": [],
                    "upcoming": [],
                    "skins": [],
                }
                payload = site_builder.build_site(
                    output,
                    skin_ids_path=paths[0],
                    versions_path=paths[1],
                    patch_dates_path=paths[2],
                    assets_path=paths[3],
                    site_source=source,
                    fetcher=self.fetch,
                )
            finally:
                site_builder.build_site_payload = original

            self.assertEqual(payload["totalSkins"], 1)
            self.assertEqual((output / "index.html").read_text(), "<h1>Site</h1>")
            self.assertTrue((output / ".nojekyll").exists())
            written = json.loads((output / "data" / "skins.json").read_text())
            self.assertEqual(written["schemaVersion"], site_builder.SITE_SCHEMA_VERSION)

    def test_source_contains_no_data_dragon_dependency(self) -> None:
        source = Path(site_builder.__file__).read_text(encoding="utf-8").casefold()
        self.assertNotIn("ddragon", source)
        self.assertNotIn("data dragon", source)

    def test_frontend_accepts_the_builder_schema_version(self) -> None:
        frontend = (
            updater.PROJECT_ROOT / "site" / "app.js"
        ).read_text(encoding="utf-8")
        self.assertIn(
            f"payload.schemaVersion === {site_builder.SITE_SCHEMA_VERSION}",
            frontend,
        )


if __name__ == "__main__":
    unittest.main()
