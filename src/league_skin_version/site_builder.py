"""Build the static GitHub Pages artifact from the repository data files."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import sys
from typing import Callable, Sequence
from urllib.parse import quote

from . import updater


SITE_SOURCE_DIR = updater.PROJECT_ROOT / "site"
DEFAULT_OUTPUT_DIR = updater.PROJECT_ROOT / "dist"
SITE_SCHEMA_VERSION = 4
# Upcoming skins the Wiki has not assigned to a patch yet use this version.
UNSCHEDULED_VERSION = "upcoming"
# Regular champions use IDs below 1000. Mode-specific variants such as
# Jade_Annie (60001) carry client-only skins the Wiki never lists.
REGULAR_CHAMPION_ID_LIMIT = 1000
CDRAGON_GLOBAL_ORIGIN = updater.CDRAGON_GLOBAL_ORIGIN
CDRAGON_ASSET_ORIGIN = f"{CDRAGON_GLOBAL_ORIGIN}/default"
CDRAGON_EN_SKINS_URL = updater.CDRAGON_EN_SKINS_URL
CDRAGON_ZH_SKINS_URL = f"{CDRAGON_GLOBAL_ORIGIN}/zh_cn/v1/skins.json"
CDRAGON_ZH_CHAMPION_SUMMARY_URL = (
    f"{CDRAGON_GLOBAL_ORIGIN}/zh_cn/v1/champion-summary.json"
)
CDRAGON_EN_SKINLINES_URL = f"{CDRAGON_GLOBAL_ORIGIN}/default/v1/skinlines.json"
CDRAGON_ZH_SKINLINES_URL = f"{CDRAGON_GLOBAL_ORIGIN}/zh_cn/v1/skinlines.json"
CDRAGON_PBE_GLOBAL_ORIGIN = (
    "https://raw.communitydragon.org/pbe/plugins/"
    "rcp-be-lol-game-data/global"
)
CDRAGON_PBE_ASSET_ORIGIN = f"{CDRAGON_PBE_GLOBAL_ORIGIN}/default"
CDRAGON_PBE_EN_SKINS_URL = f"{CDRAGON_PBE_GLOBAL_ORIGIN}/default/v1/skins.json"
CDRAGON_PBE_ZH_SKINS_URL = f"{CDRAGON_PBE_GLOBAL_ORIGIN}/zh_cn/v1/skins.json"
CDRAGON_PBE_ZH_CHAMPION_SUMMARY_URL = (
    f"{CDRAGON_PBE_GLOBAL_ORIGIN}/zh_cn/v1/champion-summary.json"
)
CDRAGON_PBE_EN_SKINLINES_URL = (
    f"{CDRAGON_PBE_GLOBAL_ORIGIN}/default/v1/skinlines.json"
)
CDRAGON_PBE_ZH_SKINLINES_URL = (
    f"{CDRAGON_PBE_GLOBAL_ORIGIN}/zh_cn/v1/skinlines.json"
)


class SiteBuildError(updater.UpdateError):
    """A validated site-data or artifact build failure."""


def _warn(message: str) -> None:
    print(f"warning: {message}", file=sys.stderr)


def _version_sort_key(version: str) -> tuple[bool, tuple[int | str, ...]]:
    if version == UNSCHEDULED_VERSION:
        return True, ()
    return False, updater.patch_sort_key(version)


def _decode_json(document: str, *, source: str) -> object:
    try:
        return json.loads(document)
    except json.JSONDecodeError as exc:
        raise SiteBuildError(f"invalid JSON from {source}: {exc}") from exc


def _load_cdragon_skins(
    url: str, fetcher: Callable[[str], str]
) -> dict[str, dict[str, object]]:
    document = _decode_json(fetcher(url), source=url)
    if not isinstance(document, dict):
        raise SiteBuildError(f"invalid CommunityDragon skin schema: {url}")
    skins = {
        str(raw_id): entry
        for raw_id, entry in document.items()
        if isinstance(entry, dict)
    }
    if not skins:
        raise SiteBuildError(f"CommunityDragon skin data is empty: {url}")
    return skins


def _flatten_cdragon_skins(
    skins: dict[str, dict[str, object]],
    *,
    asset_origin: str,
    source_label: str,
) -> dict[str, dict[str, object]]:
    """Index selectable skins and nested quest-form tiers by stable ID."""

    flattened: dict[str, dict[str, object]] = {}
    for skin_id, entry in skins.items():
        current = dict(entry)
        current["__assetOrigin"] = asset_origin
        current["__sourceLabel"] = source_label
        flattened[skin_id] = current

    inherited_fields = ("rarity", "isLegacy", "skinLines")
    for parent in skins.values():
        quest_info = parent.get("questSkinInfo")
        tiers = quest_info.get("tiers") if isinstance(quest_info, dict) else None
        if not isinstance(tiers, list):
            continue
        inherited = {
            key: parent[key]
            for key in inherited_fields
            if key in parent
        }
        for tier in tiers:
            if not isinstance(tier, dict):
                continue
            raw_id = tier.get("id")
            if isinstance(raw_id, bool) or not isinstance(raw_id, (str, int)):
                continue
            tier_id = str(raw_id)
            if not tier_id.isdigit():
                continue
            merged = dict(inherited)
            merged.update(tier)
            merged["__assetOrigin"] = asset_origin
            merged["__sourceLabel"] = source_label
            flattened.setdefault(tier_id, merged)
    return flattened


def _load_indexed_cdragon_skins(
    url: str,
    fetcher: Callable[[str], str],
    *,
    asset_origin: str,
    source_label: str,
) -> dict[str, dict[str, object]]:
    return _flatten_cdragon_skins(
        _load_cdragon_skins(url, fetcher),
        asset_origin=asset_origin,
        source_label=source_label,
    )


def _load_cdragon_skinlines(
    url: str, fetcher: Callable[[str], str]
) -> dict[str, dict[str, object]]:
    document = _decode_json(fetcher(url), source=url)
    if not isinstance(document, list):
        raise SiteBuildError(f"invalid CommunityDragon skinline schema: {url}")
    skinlines: dict[str, dict[str, object]] = {}
    for entry in document:
        if not isinstance(entry, dict):
            continue
        raw_id = entry.get("id")
        name = entry.get("name")
        if isinstance(raw_id, (str, int)) and isinstance(name, str) and name:
            skinlines[str(raw_id)] = entry
    if not skinlines:
        raise SiteBuildError(f"CommunityDragon skinline data is empty: {url}")
    return skinlines


def _load_cdragon_champion_names(
    url: str, fetcher: Callable[[str], str]
) -> dict[str, str]:
    document = _decode_json(fetcher(url), source=url)
    if not isinstance(document, list):
        raise SiteBuildError(f"invalid CommunityDragon champion schema: {url}")
    names: dict[str, str] = {}
    for entry in document:
        if not isinstance(entry, dict):
            continue
        raw_id = entry.get("id")
        name = entry.get("description")
        if (
            isinstance(raw_id, int)
            and not isinstance(raw_id, bool)
            and raw_id > 0
            and isinstance(name, str)
            and name.strip()
        ):
            names[str(raw_id)] = name.strip()
    if not names:
        raise SiteBuildError(f"CommunityDragon champion data is empty: {url}")
    return names


def _load_optional_cdragon_skins(
    url: str,
    fetcher: Callable[[str], str],
    *,
    asset_origin: str,
    source_label: str,
) -> dict[str, dict[str, object]]:
    """Load optional PBE enrichment without making it a build requirement."""

    try:
        return _load_indexed_cdragon_skins(
            url,
            fetcher,
            asset_origin=asset_origin,
            source_label=source_label,
        )
    except (OSError, updater.UpdateError):
        return {}


def _unreleased_pbe_skin_ids(
    pbe: dict[str, dict[str, object]],
    live: dict[str, dict[str, object]],
    released: dict[str, str],
) -> set[str]:
    """Select named, unreleased PBE skins that belong to regular champions."""

    selected: set[str] = set()
    for skin_id, entry in pbe.items():
        if not skin_id.isdigit() or skin_id in released:
            continue
        champion_id, skin_number = divmod(int(skin_id), 1000)
        base_id = str(champion_id * 1000)
        if (
            skin_number
            and 0 < champion_id < REGULAR_CHAMPION_ID_LIMIT
            and (base_id in pbe or base_id in live)
            and _entry_name(entry)
        ):
            selected.add(skin_id)
    return selected


def _load_optional_cdragon_skinlines(
    url: str, fetcher: Callable[[str], str]
) -> dict[str, dict[str, object]]:
    try:
        return _load_cdragon_skinlines(url, fetcher)
    except (OSError, updater.UpdateError):
        return {}


def _load_optional_cdragon_champion_names(
    url: str, fetcher: Callable[[str], str]
) -> dict[str, str]:
    try:
        return _load_cdragon_champion_names(url, fetcher)
    except (OSError, updater.UpdateError):
        return {}


def _cdragon_asset_url(
    path: object,
    *,
    asset_origin: str = CDRAGON_ASSET_ORIGIN,
) -> str | None:
    if not isinstance(path, str) or not path:
        return None
    prefix = "/lol-game-data/assets/"
    if not path.lower().startswith(prefix):
        return path if path.startswith(("https://", "http://")) else None
    relative = path[len(prefix):].lower()
    return f"{asset_origin}/{quote(relative, safe='/._-')}"


def _rarity_name(value: object) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    normalized = value[1:] if value.startswith("k") else value
    return "Standard" if normalized == "NoRarity" else normalized


def _skin_line_ids(entry: dict[str, object] | None) -> list[str]:
    if entry is None:
        return []
    raw_lines = entry.get("skinLines")
    if not isinstance(raw_lines, list):
        return []
    result: list[str] = []
    for raw_line in raw_lines:
        if not isinstance(raw_line, dict):
            continue
        raw_id = raw_line.get("id")
        if isinstance(raw_id, (str, int)):
            line_id = str(raw_id)
            if line_id not in result:
                result.append(line_id)
    return result


def _chroma_records(
    english: dict[str, object] | None,
    chinese: dict[str, object] | None,
    *,
    asset_origin: str = CDRAGON_ASSET_ORIGIN,
) -> list[dict[str, object]]:
    if english is None or not isinstance(english.get("chromas"), list):
        return []
    chinese_chromas = {
        str(entry.get("id")): entry
        for entry in (chinese or {}).get("chromas", [])
        if isinstance(entry, dict) and isinstance(entry.get("id"), (str, int))
    } if isinstance((chinese or {}).get("chromas"), list) else {}
    records: list[dict[str, object]] = []
    for entry in english["chromas"]:
        if not isinstance(entry, dict):
            continue
        raw_id = entry.get("id")
        name = entry.get("name")
        if not isinstance(raw_id, (str, int)) or not isinstance(name, str) or not name:
            continue
        chroma_id = str(raw_id)
        localized = chinese_chromas.get(chroma_id, {})
        localized_name = localized.get("name")
        colors = entry.get("colors")
        image = _cdragon_asset_url(
            entry.get("chromaPath") or entry.get("tilePath"),
            asset_origin=asset_origin,
        )
        record: dict[str, object] = {
            "id": chroma_id,
            "name": name,
            "nameZh": localized_name if isinstance(localized_name, str) and localized_name else name,
            "colors": [color for color in colors if isinstance(color, str)]
            if isinstance(colors, list)
            else [],
        }
        if image:
            record["image"] = image
        records.append(record)
    return records


def _fallback_alias(display_name: str) -> str:
    return re.sub(r"[^0-9A-Za-z]", "", display_name)


def _sources(*, wiki: bool, cdragon: bool) -> list[str]:
    """Name the sources listing a skin; a lone source becomes a card tag."""

    return [name for name, listed in (("wiki", wiki), ("cdragon", cdragon)) if listed]


def _entry_name(entry: dict[str, object] | None) -> str | None:
    name = entry.get("name") if entry is not None else None
    return name if isinstance(name, str) and name else None


def _champion_alias(
    champion_detail: dict[str, object] | None,
    skin_detail: dict[str, object] | None,
    fallback_name: str,
) -> str:
    for entry in (champion_detail, skin_detail):
        if entry is None:
            continue
        for key in (
            "splashPath",
            "uncenteredSplashPath",
            "loadScreenPath",
            "tilePath",
        ):
            path = entry.get(key)
            if not isinstance(path, str):
                continue
            match = re.search(r"/characters/([^/]+)/", path, flags=re.IGNORECASE)
            if match is not None:
                return match.group(1)
    return _fallback_alias(fallback_name)


def _cdragon_art(
    detail: dict[str, object] | None,
) -> tuple[dict[str, str], dict[str, str]]:
    if detail is None:
        return {}, {}
    origin = detail.get("__assetOrigin")
    asset_origin = origin if isinstance(origin, str) else CDRAGON_ASSET_ORIGIN
    static: dict[str, str] = {}
    video: dict[str, str] = {}
    for output_key, source_key in (
        ("centered", "splashPath"),
        ("uncentered", "uncenteredSplashPath"),
        ("tile", "tilePath"),
        ("loading", "loadScreenPath"),
    ):
        url = _cdragon_asset_url(detail.get(source_key), asset_origin=asset_origin)
        if url:
            static[output_key] = url
    for output_key, source_key in (
        ("videoCentered", "splashVideoPath"),
        ("videoUncentered", "collectionSplashVideoPath"),
    ):
        url = _cdragon_asset_url(detail.get(source_key), asset_origin=asset_origin)
        if url:
            video[output_key] = url
    return static, video


def _wiki_art(
    assets: dict[str, dict[str, dict[str, object]]], skin_id: str
) -> dict[str, str]:
    result: dict[str, str] = {}
    for variant, info in assets.get(skin_id, {}).items():
        url = info.get("url")
        if isinstance(url, str) and url:
            result[variant] = url
    return result


def _preferred_image(art: dict[str, str]) -> str | None:
    return (
        art.get("loading")
        or art.get("uncentered")
        or art.get("centered")
        or art.get("tile")
    )


def build_site_payload(
    skin_ids_path: Path,
    versions_path: Path,
    patch_dates_path: Path,
    *,
    assets_path: Path | None = None,
    fetcher: Callable[[str], str],
    generated_at: datetime | None = None,
    data_updated_at: str | None = None,
    minimum_catalog_entries: int = 1000,
) -> dict[str, object]:
    """Join Wiki history/artwork with CommunityDragon client metadata."""

    if data_updated_at is not None:
        try:
            datetime.strptime(data_updated_at, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError as exc:
            raise SiteBuildError("invalid Actions data-sync timestamp") from exc

    try:
        skin_ids_document = skin_ids_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SiteBuildError(f"cannot read {skin_ids_path}: {exc}") from exc
    skin_ids = updater.parse_skin_catalog(
        skin_ids_document,
        source=str(skin_ids_path),
        minimum_entries=minimum_catalog_entries,
    )
    versions = updater.load_versions(versions_path)
    updater.verify_versions_data(versions)
    patch_dates = updater.load_patch_dates(patch_dates_path)
    updater.verify_patch_dates_data(
        patch_dates,
        expected_versions=versions.values(),
    )
    # A source that is unavailable for this build cannot prove a skin is
    # one-sided, so skins are only tagged when both sources were read.
    wiki_available = True
    try:
        wiki_upcoming = updater.load_wiki_upcoming_snapshot(fetcher=fetcher)
    except (OSError, updater.UpdateError) as exc:
        _warn(f"League Wiki Upcoming schedule unavailable: {exc}")
        wiki_available = False
        wiki_upcoming = updater.WikiUpcomingSnapshot(
            (), updater.WikiSkinCatalog({}, {}, {})
        )
    wiki_records = wiki_upcoming.wiki_catalog.records_by_id
    for message in wiki_upcoming.warnings:
        _warn(message)
    scheduled = {
        skin.skin_id: skin
        for skin in wiki_upcoming.skins
        if skin.skin_id not in versions
    }

    resolved_assets_path = (
        assets_path.resolve()
        if assets_path is not None
        else updater.DEFAULT_SKIN_ASSETS_PATH.resolve()
    )
    wiki_assets = updater.load_skin_assets_manifest(
        resolved_assets_path
    )
    missing_released_assets = sorted(set(versions) - set(wiki_assets), key=int)
    if missing_released_assets:
        raise SiteBuildError(
            "Wiki artwork manifest is missing released skin IDs: "
            + ", ".join(missing_released_assets)
        )
    updater.verify_skin_assets_data(
        wiki_assets,
        released_ids=versions,
    )

    response_cache: dict[str, str] = {}

    def cached_fetch(url: str) -> str:
        if url not in response_cache:
            response_cache[url] = fetcher(url)
        return response_cache[url]

    cdragon_en = _load_indexed_cdragon_skins(
        CDRAGON_EN_SKINS_URL,
        cached_fetch,
        asset_origin=CDRAGON_ASSET_ORIGIN,
        source_label="CommunityDragon live",
    )
    cdragon_zh = _load_indexed_cdragon_skins(
        CDRAGON_ZH_SKINS_URL,
        cached_fetch,
        asset_origin=CDRAGON_ASSET_ORIGIN,
        source_label="CommunityDragon live",
    )
    cdragon_champion_names_zh = _load_cdragon_champion_names(
        CDRAGON_ZH_CHAMPION_SUMMARY_URL,
        cached_fetch,
    )
    cdragon_lines_en = _load_cdragon_skinlines(
        CDRAGON_EN_SKINLINES_URL,
        cached_fetch,
    )
    cdragon_lines_zh = _load_cdragon_skinlines(
        CDRAGON_ZH_SKINLINES_URL,
        cached_fetch,
    )

    pbe_en = _load_optional_cdragon_skins(
        CDRAGON_PBE_EN_SKINS_URL,
        cached_fetch,
        asset_origin=CDRAGON_PBE_ASSET_ORIGIN,
        source_label="CommunityDragon PBE",
    )
    pbe_available = bool(pbe_en)
    pbe_zh = _load_optional_cdragon_skins(
        CDRAGON_PBE_ZH_SKINS_URL,
        cached_fetch,
        asset_origin=CDRAGON_PBE_ASSET_ORIGIN,
        source_label="CommunityDragon PBE",
    )
    pbe_lines_en = _load_optional_cdragon_skinlines(
        CDRAGON_PBE_EN_SKINLINES_URL,
        cached_fetch,
    )
    pbe_lines_zh = _load_optional_cdragon_skinlines(
        CDRAGON_PBE_ZH_SKINLINES_URL,
        cached_fetch,
    )
    pbe_champion_names_zh = _load_optional_cdragon_champion_names(
        CDRAGON_PBE_ZH_CHAMPION_SUMMARY_URL,
        cached_fetch,
    )
    # Either source can reveal an Upcoming skin first; only the Wiki knows
    # which patch will ship it.
    upcoming_ids = sorted(
        set(scheduled) | _unreleased_pbe_skin_ids(pbe_en, cdragon_en, versions),
        key=int,
    )
    upcoming_asset_records = [
        wiki_records[skin_id] for skin_id in upcoming_ids if skin_id in wiki_records
    ]
    try:
        wiki_assets.update(
            updater.resolve_wiki_skin_assets(
                upcoming_asset_records,
                fetcher=fetcher,
            )
        )
    except (OSError, updater.UpdateError) as exc:
        _warn(f"League Wiki Upcoming artwork unavailable: {exc}")

    def champion_metadata(
        champion_id: int,
        skin_detail: dict[str, object] | None,
        *,
        prefer_pbe: bool = False,
        fallback_name: str | None = None,
    ) -> tuple[str, str, str]:
        base_id = str(champion_id * 1000)
        english_base = (
            pbe_en.get(base_id) if prefer_pbe else None
        ) or cdragon_en.get(base_id)
        chinese_base = (
            pbe_zh.get(base_id) if prefer_pbe else None
        ) or cdragon_zh.get(base_id)
        champion_name = (
            _entry_name(english_base) or skin_ids.get(base_id) or fallback_name
        )
        if champion_name is None:
            raise SiteBuildError(
                f"CommunityDragon has no champion ID {champion_id}"
            )
        localized_name = (
            pbe_champion_names_zh.get(str(champion_id)) if prefer_pbe else None
        ) or cdragon_champion_names_zh.get(str(champion_id))
        localized_name = (
            localized_name or _entry_name(chinese_base) or champion_name
        )
        alias = _champion_alias(english_base, skin_detail, champion_name)
        if not alias:
            raise SiteBuildError(
                f"cannot resolve a champion alias for ID {champion_id}"
            )
        return champion_name, localized_name, alias

    records: list[dict[str, object]] = []
    cdragon_matched = 0
    wiki_art_matched = 0
    for skin_id, patch in versions.items():
        numeric_id = int(skin_id)
        champion_id, skin_number = divmod(numeric_id, 1000)
        # A skin removed from the live client keeps only its Wiki data.
        english_detail = cdragon_en.get(skin_id)
        chinese_detail = cdragon_zh.get(skin_id)
        wiki_record = wiki_records.get(skin_id)
        if english_detail is not None:
            cdragon_matched += 1

        display_name = (
            _entry_name(english_detail)
            or (f"{wiki_record.skin} {wiki_record.champion}" if wiki_record else None)
            or skin_ids.get(skin_id)
        )
        if display_name is None:
            raise SiteBuildError(
                f"neither CommunityDragon nor League Wiki names released skin ID {skin_id}"
            )
        localized_name = _entry_name(chinese_detail) or display_name
        champion_name, localized_champion_name, champion_alias = champion_metadata(
            champion_id,
            english_detail,
            fallback_name=wiki_record.champion if wiki_record else None,
        )

        primary_art = _wiki_art(wiki_assets, skin_id)
        fallback_art, video_art = _cdragon_art(english_detail)
        if primary_art:
            wiki_art_matched += 1
        art = dict(primary_art)
        art.update(video_art)
        primary_image = _preferred_image(primary_art)
        fallback_image = _preferred_image(fallback_art)
        raw_legacy = (
            english_detail.get("isLegacy") if english_detail is not None else None
        )
        asset_origin = (
            english_detail.get("__assetOrigin") if english_detail is not None else None
        )
        records.append(
            {
                "id": skin_id,
                "name": display_name,
                "nameZh": localized_name,
                "champion": champion_name,
                "championZh": localized_champion_name,
                "championAlias": champion_alias,
                "championId": champion_id,
                "skinNumber": skin_number,
                "version": patch,
                "status": "released",
                "image": primary_image or fallback_image,
                "imageFallback": fallback_image
                if fallback_image != primary_image
                else None,
                "nameSource": english_detail.get(
                    "__sourceLabel", "CommunityDragon"
                )
                if english_detail is not None
                else "League Wiki SkinData",
                "artSource": "League Wiki",
                "artPending": primary_image is None and fallback_image is None,
                "rarity": _rarity_name(
                    english_detail.get("rarity")
                    if english_detail is not None
                    else None
                ),
                "legacy": raw_legacy if isinstance(raw_legacy, bool) else None,
                "skinLineIds": _skin_line_ids(english_detail),
                "chromas": _chroma_records(
                    english_detail,
                    chinese_detail,
                    asset_origin=asset_origin
                    if isinstance(asset_origin, str)
                    else CDRAGON_ASSET_ORIGIN,
                ),
                "art": art,
                "artFallback": fallback_art,
                "sources": _sources(wiki=True, cdragon=english_detail is not None),
            }
        )

    pbe_matched = 0
    for skin_id in upcoming_ids:
        scheduled_skin = scheduled.get(skin_id)
        numeric_id = int(skin_id)
        champion_id, skin_number = divmod(numeric_id, 1000)
        english_detail = pbe_en.get(skin_id)
        chinese_detail = pbe_zh.get(skin_id)
        if english_detail is not None:
            pbe_matched += 1
        display_name = _entry_name(english_detail)
        if display_name is None:
            # PBE-only skins are selected by name, so this skin is scheduled.
            display_name = f"{scheduled_skin.name} {scheduled_skin.champion}"
        localized_name = _entry_name(chinese_detail) or display_name
        champion_name, localized_champion_name, champion_alias = champion_metadata(
            champion_id,
            english_detail,
            prefer_pbe=True,
            fallback_name=scheduled_skin.champion if scheduled_skin else None,
        )

        primary_art = _wiki_art(wiki_assets, skin_id)
        fallback_art, video_art = _cdragon_art(english_detail)
        if primary_art:
            wiki_art_matched += 1
        art = dict(primary_art)
        art.update(video_art)
        primary_image = _preferred_image(primary_art)
        fallback_image = _preferred_image(fallback_art)
        raw_legacy = (
            english_detail.get("isLegacy") if english_detail is not None else None
        )
        asset_origin = (
            english_detail.get("__assetOrigin")
            if english_detail is not None
            else CDRAGON_PBE_ASSET_ORIGIN
        )
        if primary_art:
            art_source: str | None = "League Wiki"
        elif fallback_art:
            art_source = "CommunityDragon PBE"
        else:
            art_source = None
        records.append(
            {
                "id": skin_id,
                "name": display_name,
                "nameZh": localized_name,
                "champion": champion_name,
                "championZh": localized_champion_name,
                "championAlias": champion_alias,
                "championId": champion_id,
                "skinNumber": skin_number,
                "version": scheduled_skin.planned_patch
                if scheduled_skin is not None
                else UNSCHEDULED_VERSION,
                "status": "upcoming",
                "image": primary_image or fallback_image,
                "imageFallback": fallback_image
                if fallback_image != primary_image
                else None,
                "nameSource": english_detail.get(
                    "__sourceLabel", "CommunityDragon PBE"
                )
                if english_detail is not None
                else "League Wiki SkinData",
                "artSource": art_source,
                "artPending": primary_image is None and fallback_image is None,
                "rarity": _rarity_name(
                    english_detail.get("rarity")
                    if english_detail is not None
                    else None
                ),
                "legacy": raw_legacy if isinstance(raw_legacy, bool) else None,
                "skinLineIds": _skin_line_ids(english_detail),
                "chromas": _chroma_records(
                    english_detail,
                    chinese_detail,
                    asset_origin=asset_origin
                    if isinstance(asset_origin, str)
                    else CDRAGON_PBE_ASSET_ORIGIN,
                ),
                "art": art,
                "artFallback": fallback_art,
                "sources": _sources(
                    wiki=scheduled_skin is not None
                    or skin_id in wiki_records
                    or not wiki_available,
                    cdragon=english_detail is not None or not pbe_available,
                ),
            }
        )

    records.sort(
        key=lambda item: (
            str(item["champion"]).casefold(),
            str(item["name"]).casefold(),
        )
    )
    records.sort(
        key=lambda item: _version_sort_key(str(item["version"])),
        reverse=True,
    )
    released_records = [item for item in records if item["status"] == "released"]
    counts = Counter(str(item["version"]) for item in released_records)
    skin_line_counts = Counter(
        line_id
        for record in records
        for line_id in record["skinLineIds"]
    )
    skin_lines: list[dict[str, object]] = []
    for line_id, count in skin_line_counts.items():
        english_line = pbe_lines_en.get(line_id) or cdragon_lines_en.get(line_id, {})
        chinese_line = pbe_lines_zh.get(line_id) or cdragon_lines_zh.get(line_id, {})
        english_name = english_line.get("name")
        chinese_name = chinese_line.get("name")
        if not isinstance(english_name, str) or not english_name:
            english_name = f"Skinline {line_id}"
        if not isinstance(chinese_name, str) or not chinese_name:
            chinese_name = english_name
        skin_lines.append(
            {
                "id": line_id,
                "name": english_name,
                "nameZh": chinese_name,
                "count": count,
            }
        )
    skin_lines.sort(key=lambda item: str(item["name"]).casefold())

    ordered_versions = sorted(counts, key=updater.patch_sort_key, reverse=True)
    timestamp = generated_at or datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    generated_text = (
        timestamp.astimezone(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
    upcoming_counts = Counter(
        str(item["version"]) for item in records if item["status"] == "upcoming"
    )
    upcoming_payload = [
        {"version": version, "count": upcoming_counts[version]}
        for version in sorted(upcoming_counts, key=_version_sort_key, reverse=True)
    ]

    return {
        "schemaVersion": SITE_SCHEMA_VERSION,
        "generatedAt": generated_text,
        "dataUpdatedAt": data_updated_at,
        "catalogSource": "CommunityDragon",
        "artworkSources": {
            "primary": "League Wiki",
            "fallback": "CommunityDragon",
        },
        "communityDragonMatchedSkins": cdragon_matched,
        "communityDragonPbeMatchedSkins": pbe_matched,
        "leagueWikiArtworkSkins": wiki_art_matched,
        "totalSkins": len(released_records),
        "totalChampions": len(
            {int(item["championId"]) for item in released_records}
        ),
        "versions": [
            {
                "version": patch,
                "count": counts[patch],
                "releaseDate": patch_dates[patch],
            }
            for patch in ordered_versions
        ],
        "upcoming": upcoming_payload,
        "skinLines": skin_lines,
        "skins": records,
    }


def build_site(
    output_dir: Path,
    *,
    skin_ids_path: Path = updater.DEFAULT_SKIN_IDS_PATH,
    versions_path: Path = updater.DEFAULT_SKIN_VERSIONS_PATH,
    patch_dates_path: Path = updater.DEFAULT_PATCH_DATES_PATH,
    assets_path: Path = updater.DEFAULT_SKIN_ASSETS_PATH,
    site_source: Path = SITE_SOURCE_DIR,
    fetcher: Callable[[str], str] = updater.fetch_text,
    data_updated_at: str | None = None,
) -> dict[str, object]:
    source = site_source.resolve()
    output = output_dir.resolve()
    if source == output:
        raise SiteBuildError("site source and output directory must be different")
    if not source.is_dir():
        raise SiteBuildError(f"site source directory does not exist: {source}")

    payload = build_site_payload(
        skin_ids_path.resolve(),
        versions_path.resolve(),
        patch_dates_path.resolve(),
        assets_path=assets_path.resolve(),
        fetcher=fetcher,
        data_updated_at=data_updated_at,
    )
    output.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, output, dirs_exist_ok=True)
    data_dir = output / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    encoded = (
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    ).encode("utf-8")
    updater._write_bytes_atomic(data_dir / "skins.json", encoded)
    (output / ".nojekyll").touch()
    return payload


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the static League Skin Version GitHub Pages artifact."
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--skin-ids", type=Path, default=updater.DEFAULT_SKIN_IDS_PATH)
    parser.add_argument(
        "--versions", type=Path, default=updater.DEFAULT_SKIN_VERSIONS_PATH
    )
    parser.add_argument(
        "--patch-dates", type=Path, default=updater.DEFAULT_PATCH_DATES_PATH
    )
    parser.add_argument(
        "--assets", type=Path, default=updater.DEFAULT_SKIN_ASSETS_PATH
    )
    parser.add_argument("--site-source", type=Path, default=SITE_SOURCE_DIR)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--retries", type=int, default=3, choices=range(0, 7))
    return parser


def run(argv: Sequence[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)

    def configured_fetch(url: str) -> str:
        return updater.fetch_text(url, timeout=args.timeout, retries=args.retries)

    payload = build_site(
        args.output,
        skin_ids_path=args.skin_ids,
        versions_path=args.versions,
        patch_dates_path=args.patch_dates,
        assets_path=args.assets,
        site_source=args.site_source,
        fetcher=configured_fetch,
        data_updated_at=os.environ.get("LSV_DATA_UPDATED_AT") or None,
    )
    upcoming_count = sum(entry["count"] for entry in payload["upcoming"])
    print(
        f"Built {payload['totalSkins']} skins across "
        f"{len(payload['versions'])} patches"
        + (f" plus {upcoming_count} Upcoming" if upcoming_count else "")
        + f" in {args.output.resolve()}"
    )
    return 0


def main() -> None:
    try:
        raise SystemExit(run())
    except (updater.UpdateError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
