"""Synchronize the skin catalog and League Wiki release history.

The updater mirrors the current stable skin-ID catalog, rebuilds released
skin-to-patch evidence from League Wiki patch pages and SkinData, and maintains
release dates and artwork for every released skin represented by the archive.

Only Python's standard library is required.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import html
from http.client import HTTPException
from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import re
import sys
import time
import unicodedata
from typing import Callable, Iterable, Sequence
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

PROJECT_ROOT = Path(
    os.environ.get(
        "LEAGUE_SKIN_VERSION_ROOT",
        Path(__file__).resolve().parents[2],
    )
).resolve()
SCRIPT_DIR = PROJECT_ROOT
DEFAULT_SKIN_VERSIONS_PATH = SCRIPT_DIR / "skin_versions.json"
DEFAULT_SKIN_IDS_PATH = SCRIPT_DIR / "skin_ids.json"
DEFAULT_PATCH_DATES_PATH = SCRIPT_DIR / "patch_dates.json"
DEFAULT_SKIN_ASSETS_PATH = SCRIPT_DIR / "skin_assets.json"
CDRAGON_GLOBAL_ORIGIN = (
    "https://raw.communitydragon.org/latest/plugins/"
    "rcp-be-lol-game-data/global"
)
CDRAGON_EN_SKINS_URL = f"{CDRAGON_GLOBAL_ORIGIN}/default/v1/skins.json"
CDRAGON_CONTENT_METADATA_URL = (
    "https://raw.communitydragon.org/latest/content-metadata.json"
)
LOL_WIKI_API_URL = "https://wiki.leagueoflegends.com/en-us/api.php"
LOL_WIKI_RELEASE_HISTORY_TITLE = "Template:Release history"
LOL_WIKI_SKIN_DATA_TITLE = "Module:SkinData/data"
LOL_WIKI_MAINTENANCE_DATA_TITLE = "Module:Maintenance data/data"
LOL_WIKI_VPBE_TITLE = "VPBE"

USER_AGENT = "league-skin-version/0.2 (League Wiki release-history updater)"

WIKI_ASSET_VARIANTS = {
    "uncentered": "Skin",
    "loading": "Loading",
    "centered": "Centered",
    "tile": "Tile",
}
WIKI_ASSET_DIMENSIONS = {
    "uncentered": (1215, 717),
    "loading": (308, 560),
    "centered": (1280, 720),
    "tile": (380, 380),
}

_PATCH_VALUE_RE = re.compile(
    r"^(?P<major>(?:20)?\d{1,2})"
    r"(?:[.\-]?s(?P<season>\d+))?"
    r"[.\-](?P<minor>\d{1,2})(?P<suffix>[a-z]?)$",
    re.IGNORECASE,
)
_LEGACY_PATCH_VALUE_RE = re.compile(
    r"^(?P<major>[01])[.\-](?P<minor>\d{1,2})[.\-](?P<build>\d{1,2})"
    r"[.\-](?P<revision>\d{1,3})(?P<suffix>[a-z]?)$",
    re.IGNORECASE,
)
_RETRYABLE_HTTP_CODES = {408, 425, 429, 500, 502, 503, 504}


class UpdateError(RuntimeError):
    """An expected updater failure that should be shown without a traceback."""


@dataclass(frozen=True)
class PatchRef:
    version: str

    @property
    def sort_key(self) -> tuple[int, int, int, int, str]:
        return patch_sort_key(self.version)


@dataclass(frozen=True)
class WikiPatchRef:
    version: str
    title: str

    @property
    def sort_key(self) -> tuple[int, int, int, int, str]:
        return patch_sort_key(self.version)


@dataclass(frozen=True)
class ResolvedSkin:
    skin_id: str
    display_name: str
    source: str


@dataclass(frozen=True)
class ResolvedPatchResult:
    ref: PatchRef
    skins: tuple[ResolvedSkin, ...]


@dataclass(frozen=True)
class MergeResult:
    merged: dict[str, str]
    additions: tuple[tuple[str, str], ...]
    conflicts: tuple[str, ...]
    duplicate_names: tuple[str, ...]


@dataclass(frozen=True)
class PatchDateMergeResult:
    merged: dict[str, str]
    additions: tuple[tuple[str, str], ...]
    updates: tuple[tuple[str, str, str], ...]


@dataclass(frozen=True)
class SkinCatalog:
    names_by_id: dict[str, str]

    def display_name(self, skin_id: str, fallback: str) -> str:
        return self.names_by_id.get(skin_id, fallback)


@dataclass(frozen=True)
class WikiSkinCatalog:
    ids_by_champion_skin: dict[tuple[str, str], str]
    champion_names_by_key: dict[str, str]
    release_dates_by_id: dict[str, str]
    records_by_id: dict[str, "WikiSkinRecord"] = field(default_factory=dict)

    def resolve(self, champion: str, skin: str) -> str:
        champion_key = _name_key(champion)
        canonical = self.champion_names_by_key.get(champion_key)
        if canonical is None:
            # Wiki templates accept a small number of shortened historical
            # champion names, notably Nunu and Renata. Resolve them only when
            # the prefix identifies exactly one current Wiki champion.
            candidates = {
                name
                for key, name in self.champion_names_by_key.items()
                if key.startswith(champion_key)
            }
            if len(candidates) == 1:
                canonical = next(iter(candidates))
        if canonical is None:
            raise UpdateError(f"League Wiki SkinData has no champion matching {champion!r}")

        skin_id = self.ids_by_champion_skin.get((canonical, _name_key(skin)))
        if skin_id is None:
            raise UpdateError(
                f"League Wiki SkinData has no skin matching {champion!r} / {skin!r}"
            )
        return skin_id


@dataclass(frozen=True)
class WikiSkinRecord:
    skin_id: str
    champion: str
    skin: str
    availability: str | None
    release_date: str | None


@dataclass(frozen=True)
class UpcomingSkin:
    skin_id: str
    champion: str
    name: str
    planned_patch: str
    status: str = "pbe"


@dataclass(frozen=True)
class WikiUpcomingSnapshot:
    skins: tuple[UpcomingSkin, ...]
    wiki_catalog: WikiSkinCatalog
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class WikiSourceSnapshot:
    release_results: tuple[ResolvedPatchResult, ...]
    patch_dates: dict[str, str]
    patch_pages: int
    wiki_catalog: WikiSkinCatalog


def normalize_patch_version(value: str) -> str:
    """Return the repository's canonical patch form.

    Modern patches use the zero-padded ``26.01`` form. Pre-Season-3 builds keep
    Riot's historical four-part labels, for example ``1.0.0.152``.
    """

    candidate = value.strip()
    legacy_match = _LEGACY_PATCH_VALUE_RE.fullmatch(candidate)
    if legacy_match:
        return ".".join(
            (
                str(int(legacy_match.group("major"))),
                str(int(legacy_match.group("minor"))),
                str(int(legacy_match.group("build"))),
                str(int(legacy_match.group("revision")))
                + legacy_match.group("suffix").lower(),
            )
        )

    match = _PATCH_VALUE_RE.fullmatch(candidate)
    if not match:
        raise ValueError(f"unsupported patch version: {value!r}")

    major_text = match.group("major")
    if len(major_text) == 4 and major_text.startswith("20"):
        major_text = major_text[2:]
    major = str(int(major_text))
    minor = f"{int(match.group('minor')):02d}"
    suffix = match.group("suffix").lower()
    season = match.group("season")
    if season is not None:
        return f"{major}.S{int(season)}.{minor}{suffix}"
    return f"{major}.{minor}{suffix}"


def patch_sort_key(version: str) -> tuple[int, int, int, int, str]:
    normalized = normalize_patch_version(version)
    legacy_match = _LEGACY_PATCH_VALUE_RE.fullmatch(normalized)
    if legacy_match:
        return (
            int(legacy_match.group("major")),
            int(legacy_match.group("minor")),
            int(legacy_match.group("build")),
            int(legacy_match.group("revision")),
            legacy_match.group("suffix").lower(),
        )

    match = _PATCH_VALUE_RE.fullmatch(normalized)
    assert match is not None
    return (
        int(match.group("major")),
        int(match.group("minor")),
        0,
        int(match.group("season") or 0),
        match.group("suffix").lower(),
    )


def cdragon_version_for_patch(patch: str) -> str | None:
    """Translate a public patch to CommunityDragon's version directory."""

    normalized = normalize_patch_version(patch)
    match = re.fullmatch(r"(\d+)(?:\.S\d+)?\.(\d{2})[a-z]?", normalized)
    if match is None:
        return None
    major = int(match.group(1))
    if major >= 25:
        major -= 10
    return f"{major}.{int(match.group(2))}"


def fetch_text(url: str, *, timeout: float = 30.0, retries: int = 3) -> str:
    """Fetch UTF text with bounded exponential retry for transient failures."""

    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            with urlopen(request, timeout=timeout) as response:
                payload = response.read()
                charset = response.headers.get_content_charset() or "utf-8"
                return payload.decode(charset, errors="strict")
        except UnicodeDecodeError as exc:
            raise UpdateError(
                f"failed to decode {url} as {charset}: {exc}"
            ) from exc
        except HTTPError as exc:
            last_error = exc
            if exc.code not in _RETRYABLE_HTTP_CODES or attempt >= retries:
                break
        except (URLError, TimeoutError, OSError, HTTPException) as exc:
            last_error = exc
            if attempt >= retries:
                break
        time.sleep(min(2**attempt, 8))
    raise UpdateError(f"failed to fetch {url}: {last_error}")


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def parse_skin_catalog(
    document: str,
    *,
    source: str,
    minimum_entries: int = 1,
) -> dict[str, str]:
    """Validate the flat skin-id -> display-name catalog schema."""

    try:
        data = json.loads(document)
    except json.JSONDecodeError as exc:
        raise UpdateError(f"invalid skin catalog from {source}: {exc}") from exc
    if not isinstance(data, dict):
        raise UpdateError(f"skin catalog from {source} must contain a JSON object")
    invalid = [
        key
        for key, value in data.items()
        if not isinstance(key, str)
        or not key.isdigit()
        or not isinstance(value, str)
        or not value.strip()
    ]
    if invalid:
        raise UpdateError(
            f"skin catalog from {source} has invalid entries: {invalid[:5]}"
        )
    if len(data) < minimum_entries:
        raise UpdateError(
            f"skin catalog from {source} has only {len(data)} entries; "
            f"expected at least {minimum_entries}"
        )
    return data


def parse_cdragon_skin_catalog(
    document: str,
    *,
    source: str = CDRAGON_EN_SKINS_URL,
    minimum_entries: int = 1,
) -> dict[str, str]:
    """Build the stable ID/name map from CommunityDragon's client catalog.

    The public ``skin_ids.json`` contract intentionally matches the client
    catalog's top-level skins plus their nested chromas. Quest-form tiers are
    richer site metadata, but are not part of this compatibility map.
    """

    try:
        payload = json.loads(document)
    except json.JSONDecodeError as exc:
        raise UpdateError(f"invalid CommunityDragon skin JSON from {source}: {exc}") from exc
    if not isinstance(payload, dict):
        raise UpdateError(
            f"CommunityDragon skin catalog from {source} must contain a JSON object"
        )

    catalog: dict[str, str] = {}

    def add(raw_id: object, raw_name: object, *, context: str) -> None:
        skin_id = str(raw_id)
        if (
            isinstance(raw_id, bool)
            or not skin_id.isdigit()
            or not isinstance(raw_name, str)
            or not raw_name.strip()
        ):
            raise UpdateError(
                f"CommunityDragon skin catalog from {source} has an invalid {context}"
            )
        previous = catalog.get(skin_id)
        if previous is not None and previous != raw_name:
            raise UpdateError(
                f"CommunityDragon skin ID {skin_id} has conflicting names "
                f"{previous!r} and {raw_name!r}"
            )
        catalog[skin_id] = raw_name

    for raw_key, entry in payload.items():
        if not isinstance(entry, dict):
            raise UpdateError(
                f"CommunityDragon skin catalog from {source} has a non-object entry "
                f"for {raw_key!r}"
            )
        raw_id = entry.get("id", raw_key)
        if str(raw_id) != str(raw_key):
            raise UpdateError(
                f"CommunityDragon skin key {raw_key!r} disagrees with ID {raw_id!r}"
            )
        add(raw_id, entry.get("name"), context=f"skin entry {raw_key!r}")
        chromas = entry.get("chromas", [])
        if chromas is None:
            chromas = []
        if not isinstance(chromas, list):
            raise UpdateError(
                f"CommunityDragon skin {raw_key!r} has a non-list chroma field"
            )
        for index, chroma in enumerate(chromas):
            if not isinstance(chroma, dict):
                raise UpdateError(
                    f"CommunityDragon skin {raw_key!r} has an invalid chroma at {index}"
                )
            add(
                chroma.get("id"),
                chroma.get("name"),
                context=f"chroma {index} of skin {raw_key!r}",
            )

    if len(catalog) < minimum_entries:
        raise UpdateError(
            f"CommunityDragon skin catalog from {source} has only {len(catalog)} "
            f"entries; expected at least {minimum_entries}"
        )
    return dict(sorted(catalog.items(), key=lambda item: int(item[0])))


def parse_cdragon_content_version(document: str) -> str:
    """Return the version directory CommunityDragon currently serves as latest."""

    try:
        payload = json.loads(document)
    except json.JSONDecodeError as exc:
        raise UpdateError(f"invalid CommunityDragon content metadata: {exc}") from exc
    version = payload.get("version") if isinstance(payload, dict) else None
    match = re.match(r"(\d+)\.(\d+)\b", version) if isinstance(version, str) else None
    if match is None:
        raise UpdateError(f"unsupported CommunityDragon content version: {version!r}")
    return f"{int(match.group(1))}.{int(match.group(2))}"


def encode_skin_catalog(data: dict[str, str]) -> bytes:
    """Return the repository's stable, rebaser-compatible catalog encoding."""

    ordered = dict(sorted(data.items(), key=lambda item: int(item[0])))
    return (json.dumps(ordered, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def load_patch_dates(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise UpdateError(f"cannot read {path}: {exc}") from exc
    if not isinstance(data, dict) or any(
        not isinstance(key, str) or not isinstance(value, str)
        for key, value in data.items()
    ):
        raise UpdateError(f"{path} must be a JSON object of patch -> ISO date strings")
    verify_patch_dates_data(data)
    return data


def verify_patch_dates_data(
    patch_dates: dict[str, str],
    *,
    expected_versions: Iterable[str] | None = None,
) -> None:
    invalid_patches: list[str] = []
    invalid_dates: list[str] = []
    for patch, release_date in patch_dates.items():
        try:
            normalized_patch = normalize_patch_version(patch)
        except ValueError:
            normalized_patch = ""
        if normalized_patch != patch:
            invalid_patches.append(repr(patch))
        try:
            parsed_date = datetime.strptime(release_date, "%Y-%m-%d").date()
        except ValueError:
            parsed_date = None
        if parsed_date is None or parsed_date.isoformat() != release_date:
            invalid_dates.append(f"{patch!r}: {release_date!r}")

    if invalid_patches:
        raise UpdateError(
            "patch date verification found noncanonical patch values: "
            + ", ".join(invalid_patches)
        )
    if invalid_dates:
        raise UpdateError(
            "patch date verification found invalid ISO dates: "
            + ", ".join(invalid_dates)
        )

    if expected_versions is not None:
        expected = {normalize_patch_version(version) for version in expected_versions}
        missing = sorted(expected - patch_dates.keys(), key=patch_sort_key)
        if missing:
            raise UpdateError(
                "patch date verification is missing versions: " + ", ".join(missing)
            )


def verify_upcoming_skins(skins: Iterable[UpcomingSkin]) -> None:
    seen: set[str] = set()
    invalid: list[str] = []
    for skin in skins:
        try:
            normalized_patch = normalize_patch_version(skin.planned_patch)
        except ValueError:
            normalized_patch = ""
        if (
            re.fullmatch(r"[1-9]\d*", skin.skin_id) is None
            or int(skin.skin_id) % 1000 == 0
            or skin.skin_id in seen
            or not skin.champion.strip()
            or not skin.name.strip()
            or normalized_patch != skin.planned_patch
            or skin.status != "pbe"
        ):
            invalid.append(skin.skin_id)
        seen.add(skin.skin_id)
    if invalid:
        raise UpdateError(
            "Upcoming verification found invalid records: " + ", ".join(invalid)
        )


def _wiki_asset_filename_component(value: str) -> str:
    """Apply League Wiki's skin-art filename substitutions."""

    return value.replace(":", "-").replace("/", "")


def wiki_asset_title(record: WikiSkinRecord, variant: str) -> str:
    """Return the canonical Wiki file title for one primary skin artwork."""

    suffix = WIKI_ASSET_VARIANTS.get(variant)
    if suffix is None:
        raise ValueError(f"unsupported Wiki artwork variant: {variant!r}")
    champion = _wiki_asset_filename_component(record.champion)
    if variant in {"centered", "tile"} and champion == "Nunu & Willump":
        champion = "Nunu"
    skin = _wiki_asset_filename_component(record.skin).replace(" ", "")
    return f"File:{champion} {skin}{suffix}.jpg"


def _wiki_title_key(value: str) -> str:
    return re.sub(r"[ _]+", " ", value.strip()).casefold()


def resolve_wiki_skin_assets(
    records: Iterable[WikiSkinRecord],
    *,
    fetcher: Callable[[str], str],
    batch_size: int = 50,
) -> dict[str, dict[str, dict[str, object]]]:
    """Resolve revision-addressed URLs for all four primary Wiki artworks.

    Missing pages are retained as an empty/partial skin record so PBE entries
    can remain visible before their artwork lands. Callers decide which skin
    IDs require complete artwork during snapshot verification.
    """

    if batch_size < 1 or batch_size > 50:
        raise ValueError("batch_size must be between 1 and 50")
    ordered_records = sorted(records, key=lambda item: int(item.skin_id))
    if len({record.skin_id for record in ordered_records}) != len(ordered_records):
        raise UpdateError("League Wiki artwork input repeats a stable skin ID")

    requests: list[tuple[str, str, str]] = []
    assets: dict[str, dict[str, dict[str, object]]] = {
        record.skin_id: {} for record in ordered_records
    }
    for record in ordered_records:
        for variant in WIKI_ASSET_VARIANTS:
            requests.append((record.skin_id, variant, wiki_asset_title(record, variant)))

    for offset in range(0, len(requests), batch_size):
        batch = requests[offset : offset + batch_size]
        requested_by_key: dict[str, tuple[str, str, str]] = {}
        for request in batch:
            title_key = _wiki_title_key(request[2])
            if title_key in requested_by_key:
                raise UpdateError(
                    f"League Wiki artwork title is ambiguous: {request[2]!r}"
                )
            requested_by_key[title_key] = request
        query = urlencode(
            {
                "action": "query",
                "format": "json",
                "formatversion": "2",
                "prop": "imageinfo",
                "iiprop": "url|size|sha1|timestamp",
                "iilimit": "1",
                "redirects": "1",
                "titles": "|".join(request[2] for request in batch),
            }
        )
        url = f"{LOL_WIKI_API_URL}?{query}"
        try:
            document = json.loads(fetcher(url))
        except json.JSONDecodeError as exc:
            raise UpdateError(f"invalid League Wiki image JSON from {url}: {exc}") from exc
        raw_query = document.get("query") if isinstance(document, dict) else None
        pages = raw_query.get("pages") if isinstance(raw_query, dict) else None
        if not isinstance(pages, list):
            raise UpdateError("League Wiki image query returned an invalid schema")

        aliases: dict[str, list[tuple[str, str, str]]] = {
            title_key: [request]
            for title_key, request in requested_by_key.items()
        }
        for mapping_name in ("normalized", "redirects"):
            mappings = raw_query.get(mapping_name, [])
            if not isinstance(mappings, list):
                raise UpdateError(
                    f"League Wiki image query returned invalid {mapping_name} data"
                )
            for mapping in mappings:
                if not isinstance(mapping, dict):
                    continue
                source_title = mapping.get("from")
                target_title = mapping.get("to")
                if not isinstance(source_title, str) or not isinstance(target_title, str):
                    continue
                source_requests = aliases.get(_wiki_title_key(source_title), [])
                target_key = _wiki_title_key(target_title)
                target_requests = aliases.setdefault(target_key, [])
                for request in source_requests:
                    if request not in target_requests:
                        target_requests.append(request)

        for page in pages:
            if not isinstance(page, dict) or page.get("missing") is True:
                continue
            title = page.get("title")
            if not isinstance(title, str):
                raise UpdateError("League Wiki image page is missing its title")
            page_requests = aliases.get(_wiki_title_key(title))
            if not page_requests:
                raise UpdateError(
                    f"League Wiki returned an unexpected image title: {title!r}"
                )
            image_info = page.get("imageinfo")
            info = image_info[0] if isinstance(image_info, list) and image_info else None
            if not isinstance(info, dict):
                continue
            image_url = info.get("url")
            sha1 = info.get("sha1")
            timestamp = info.get("timestamp")
            width = info.get("width")
            height = info.get("height")
            byte_size = info.get("size")
            if (
                not isinstance(image_url, str)
                or not image_url.startswith("https://")
                or not isinstance(sha1, str)
                or not sha1
                or not isinstance(timestamp, str)
                or not timestamp
                or not isinstance(width, int)
                or not isinstance(height, int)
                or not isinstance(byte_size, int)
                or byte_size <= 0
            ):
                raise UpdateError(
                    f"League Wiki image metadata is incomplete for {title!r}"
                )
            for skin_id, variant, requested_title in page_requests:
                expected_dimensions = WIKI_ASSET_DIMENSIONS[variant]
                if (width, height) != expected_dimensions:
                    raise UpdateError(
                        f"League Wiki {variant} image for skin {skin_id} is "
                        f"{width}x{height}; expected "
                        f"{expected_dimensions[0]}x{expected_dimensions[1]}"
                    )
                assets[skin_id][variant] = {
                    "title": title,
                    "requestedTitle": requested_title,
                    "url": image_url,
                    "sha1": sha1,
                    "timestamp": timestamp,
                    "width": width,
                    "height": height,
                    "bytes": byte_size,
                }
    return assets


def verify_skin_assets_data(
    assets: dict[str, dict[str, dict[str, object]]],
    *,
    expected_ids: Iterable[str] | None = None,
    released_ids: Iterable[str] = (),
) -> None:
    released = {str(value) for value in released_ids}
    if expected_ids is not None:
        expected = {str(skin_id) for skin_id in expected_ids}
        actual = set(assets)
        if actual != expected:
            missing = sorted(expected - actual, key=int)
            extra = sorted(actual - expected, key=int)
            details = []
            if missing:
                details.append("missing " + ", ".join(missing))
            if extra:
                details.append("unexpected " + ", ".join(extra))
            raise UpdateError("Wiki artwork snapshot ID mismatch: " + "; ".join(details))

    incomplete_released: list[str] = []
    for skin_id, variants in assets.items():
        if re.fullmatch(r"[1-9]\d*", skin_id) is None or int(skin_id) % 1000 == 0:
            raise UpdateError(f"Wiki artwork snapshot has invalid skin ID {skin_id!r}")
        if not isinstance(variants, dict):
            raise UpdateError(f"Wiki artwork snapshot has invalid record for {skin_id}")
        unknown = set(variants) - set(WIKI_ASSET_VARIANTS)
        if unknown:
            raise UpdateError(
                f"Wiki artwork snapshot has unknown variants for {skin_id}: "
                + ", ".join(sorted(unknown))
            )
        for variant, info in variants.items():
            if not isinstance(info, dict):
                raise UpdateError(
                    f"Wiki artwork snapshot has invalid {variant} metadata for {skin_id}"
                )
            width, height = WIKI_ASSET_DIMENSIONS[variant]
            if (
                info.get("width") != width
                or info.get("height") != height
                or not isinstance(info.get("url"), str)
                or not str(info["url"]).startswith("https://")
                or not isinstance(info.get("sha1"), str)
                or not info["sha1"]
                or not isinstance(info.get("timestamp"), str)
                or not info["timestamp"]
                or not isinstance(info.get("bytes"), int)
                or info["bytes"] <= 0
            ):
                raise UpdateError(
                    f"Wiki artwork snapshot has invalid {variant} metadata for {skin_id}"
                )
        if skin_id in released and set(variants) != set(WIKI_ASSET_VARIANTS):
            incomplete_released.append(skin_id)
    if incomplete_released:
        raise UpdateError(
            "Wiki artwork snapshot is incomplete for released skin IDs: "
            + ", ".join(sorted(incomplete_released, key=int))
        )


def encode_skin_assets(
    assets: dict[str, dict[str, dict[str, object]]],
) -> bytes:
    ordered = {
        skin_id: {
            variant: variants[variant]
            for variant in WIKI_ASSET_VARIANTS
            if variant in variants
        }
        for skin_id, variants in sorted(assets.items(), key=lambda item: int(item[0]))
    }
    payload: dict[str, object] = {
        "schemaVersion": 1,
        "source": "League Wiki imageinfo",
    }
    payload["skins"] = ordered
    return (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def load_skin_assets_manifest(
    path: Path,
) -> dict[str, dict[str, dict[str, object]]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise UpdateError(f"cannot read {path}: {exc}") from exc
    if (
        not isinstance(payload, dict)
        or payload.get("schemaVersion") != 1
        or payload.get("source") != "League Wiki imageinfo"
        or not isinstance(payload.get("skins"), dict)
    ):
        raise UpdateError(f"{path} has an invalid Wiki artwork manifest schema")
    assets = payload["skins"]
    verify_skin_assets_data(assets)
    return assets


def write_skin_assets_atomic(
    path: Path,
    assets: dict[str, dict[str, dict[str, object]]],
) -> None:
    verify_skin_assets_data(assets)
    _write_bytes_atomic(path, encode_skin_assets(assets))


def verify_skin_assets_snapshot(
    path: Path,
    expected: dict[str, dict[str, dict[str, object]]],
    *,
    released_ids: Iterable[str],
) -> None:
    actual = load_skin_assets_manifest(path)
    if actual != expected:
        raise UpdateError(f"post-write verification failed for {path}")
    verify_skin_assets_data(
        actual,
        expected_ids=expected,
        released_ids=released_ids,
    )


def _wiki_patch_version(title: str) -> str:
    candidate = title.strip()
    if not candidate.casefold().startswith("v"):
        raise ValueError(f"unsupported League Wiki patch title: {title!r}")
    candidate = candidate[1:].strip()
    candidate = re.sub(r"\(([a-z])\)$", r"\1", candidate, flags=re.IGNORECASE)
    return normalize_patch_version(candidate)


def parse_wiki_patch_refs(document: str) -> list[WikiPatchRef]:
    """Read canonical version pages from Wiki's release-history template."""

    by_version: dict[str, WikiPatchRef] = {}
    for match in re.finditer(r"\[\[([^|\]\n]+)(?:\|[^\]]*)?\]\]", document):
        title = _clean_text(match.group(1))
        try:
            version = _wiki_patch_version(title)
        except ValueError:
            continue
        previous = by_version.get(version)
        if previous is not None and previous.title.casefold() != title.casefold():
            raise UpdateError(
                f"League Wiki release history maps {version} to both "
                f"{previous.title!r} and {title!r}"
            )
        by_version[version] = WikiPatchRef(version, title)
    if not by_version:
        raise UpdateError("League Wiki release history contains no usable patch pages")
    return sorted(by_version.values(), key=lambda ref: ref.sort_key)


def _decode_lua_key(value: str) -> str:
    try:
        decoded = json.loads(f'"{value}"')
    except json.JSONDecodeError as exc:
        raise UpdateError(f"unsupported quoted key in League Wiki SkinData: {value!r}") from exc
    if not isinstance(decoded, str) or not decoded:
        raise UpdateError(f"invalid quoted key in League Wiki SkinData: {value!r}")
    return decoded


def _lua_brace_delta(line: str) -> int:
    """Count table braces outside quoted strings and line comments."""

    delta = 0
    in_string = False
    escaped = False
    index = 0
    while index < len(line):
        character = line[index]
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
        else:
            if character == '"':
                in_string = True
            elif character == "-" and line[index : index + 2] == "--":
                break
            elif character == "{":
                delta += 1
            elif character == "}":
                delta -= 1
        index += 1
    return delta


def parse_wiki_skin_data(
    document: str,
    *,
    minimum_champions: int = 1,
    minimum_skins: int = 1,
) -> WikiSkinCatalog:
    """Parse stable IDs plus the small metadata subset used by this project."""

    table_key = re.compile(r'^\s*\["((?:\\.|[^"\\])+)"\]\s*=\s*\{\s*$')
    numeric_id = re.compile(r'^\s*\["id"\]\s*=\s*(\d+)\s*,?\s*$')
    scalar_field = re.compile(
        r'^\s*\["(id|release|cost|retired|availability)"\]\s*=\s*'
        r'(nil|\d+|"(?:\\.|[^"\\])*")\s*,?\s*$'
    )
    champion: str | None = None
    champion_id: int | None = None
    in_skins = False
    skin: str | None = None
    skin_fields: dict[str, object] = {}
    metadata: dict[tuple[str, str], dict[str, object]] = {}
    depth = 0
    ids_by_champion_skin: dict[tuple[str, str], str] = {}
    champion_names_by_key: dict[str, str] = {}

    for line in document.splitlines():
        expanded = line.expandtabs(4)
        key_match = table_key.fullmatch(expanded)
        if depth == 1 and key_match:
            champion = _decode_lua_key(key_match.group(1))
            champion_id = None
            in_skins = False
            skin = None
            champion_key = _name_key(champion)
            previous = champion_names_by_key.get(champion_key)
            if previous is not None and previous != champion:
                raise UpdateError(
                    f"League Wiki SkinData repeats champion key {champion_key!r}"
                )
            champion_names_by_key[champion_key] = champion
        elif champion is not None and depth == 2 and key_match and _name_key(
            _decode_lua_key(key_match.group(1))
        ) == "skins":
            in_skins = True
            skin = None
        elif champion is not None and depth == 3 and in_skins and key_match:
            skin = _decode_lua_key(key_match.group(1))
            skin_fields = {"__name": skin}

        id_match = numeric_id.fullmatch(expanded)
        if champion is not None and depth == 2 and not in_skins and id_match:
            champion_id = int(id_match.group(1))
        elif (
            depth == 4
            and in_skins
            and skin is not None
            and champion_id is not None
            and id_match
        ):
            local_id = int(id_match.group(1))
            if local_id == 0:
                continue
            full_id = str(champion_id * 1000 + local_id)
            key = (champion, _name_key(skin))
            previous_id = ids_by_champion_skin.get(key)
            if previous_id is not None and previous_id != full_id:
                raise UpdateError(
                    f"League Wiki SkinData repeats {champion!r} / {skin!r} "
                    f"with IDs {previous_id} and {full_id}"
            )
            ids_by_champion_skin[key] = full_id

        field_match = scalar_field.fullmatch(expanded)
        if depth == 4 and skin is not None and field_match:
            field_name = field_match.group(1)
            raw_value = field_match.group(2)
            if raw_value == "nil":
                field_value: object = None
            elif raw_value.isdigit():
                field_value = int(raw_value)
            else:
                field_value = _decode_lua_key(raw_value[1:-1])
            skin_fields[field_name] = field_value

        next_depth = depth + _lua_brace_delta(expanded)
        if skin is not None and depth >= 4 and next_depth <= 3 and champion is not None:
            metadata[(champion, _name_key(skin))] = dict(skin_fields)
            skin_fields = {}
        depth = next_depth
        if depth <= 3:
            skin = None
        if depth <= 2:
            in_skins = False
        if depth <= 1:
            champion = None
            champion_id = None

    # Removed historical names sometimes have ``id = nil`` after Riot renamed
    # the same underlying skin. Link them without a name override only when
    # release date, cost, and any retirement date identify one numeric sibling.
    for (historical_champion, historical_skin), fields in metadata.items():
        if fields.get("id") is not None or not fields.get("release"):
            continue
        signature_fields = [
            field
            for field in ("release", "cost", "retired")
            if fields.get(field) is not None
        ]
        if len(signature_fields) < 2:
            continue
        candidates = []
        for (candidate_champion, candidate_skin), candidate_fields in metadata.items():
            if candidate_champion != historical_champion:
                continue
            candidate_id = candidate_fields.get("id")
            if not isinstance(candidate_id, int) or candidate_id <= 0:
                continue
            if all(candidate_fields.get(field) == fields[field] for field in signature_fields):
                candidate_key = (candidate_champion, candidate_skin)
                candidate_full_id = ids_by_champion_skin.get(candidate_key)
                if candidate_full_id is not None:
                    candidates.append(candidate_full_id)
        if len(set(candidates)) == 1:
            ids_by_champion_skin[(historical_champion, historical_skin)] = candidates[0]

    release_dates_by_id: dict[str, str] = {}
    for key, full_id in ids_by_champion_skin.items():
        release_date = metadata.get(key, {}).get("release")
        if not isinstance(release_date, str):
            continue
        try:
            canonical_date = datetime.strptime(release_date, "%Y-%m-%d").date().isoformat()
        except ValueError:
            continue
        previous_date = release_dates_by_id.get(full_id)
        if previous_date is not None and previous_date != canonical_date:
            raise UpdateError(
                f"League Wiki SkinData gives skin ID {full_id} conflicting release "
                f"dates {previous_date} and {canonical_date}"
            )
        release_dates_by_id[full_id] = canonical_date

    records_by_id: dict[str, WikiSkinRecord] = {}
    for (record_champion, record_skin_key), full_id in ids_by_champion_skin.items():
        fields = metadata.get((record_champion, record_skin_key), {})
        # Historical aliases with ``id = nil`` resolve to their renamed
        # sibling above, but they are not separate selectable skin records.
        if not isinstance(fields.get("id"), int):
            continue
        record_skin = fields.get("__name")
        if not isinstance(record_skin, str) or not record_skin:
            continue
        availability = fields.get("availability")
        if not isinstance(availability, str) or not availability:
            availability = None
        record = WikiSkinRecord(
            full_id,
            record_champion,
            record_skin,
            availability,
            release_dates_by_id.get(full_id),
        )
        previous = records_by_id.get(full_id)
        if previous is not None and previous != record:
            raise UpdateError(
                f"League Wiki SkinData repeats skin ID {full_id} with "
                f"{previous.champion!r} / {previous.skin!r} and "
                f"{record.champion!r} / {record.skin!r}"
            )
        records_by_id[full_id] = record

    if len(champion_names_by_key) < minimum_champions:
        raise UpdateError(
            "League Wiki SkinData has only "
            f"{len(champion_names_by_key)} champions; expected at least {minimum_champions}"
        )
    if len(ids_by_champion_skin) < minimum_skins:
        raise UpdateError(
            f"League Wiki SkinData has only {len(ids_by_champion_skin)} skins; "
            f"expected at least {minimum_skins}"
        )
    return WikiSkinCatalog(
        ids_by_champion_skin,
        champion_names_by_key,
        release_dates_by_id,
        records_by_id,
    )


_WIKI_NEW_SKIN_HEADINGS = {
    "newcosmetics",
    "newcosmeticsinthestore",
    "newskins",
    "newskinsinstore",
    "newskinsinthestore",
}
_WIKI_CSL_RE = re.compile(r"\{\{\s*csl\s*\|([^{}\n]+?)\}\}", re.IGNORECASE)


def parse_wiki_skin_entries(document: str) -> tuple[tuple[str, str], ...]:
    """Extract Wiki SkinData keys for skins explicitly added in a patch."""

    headings = list(
        re.finditer(
            r"^(={2,6})\s*([^=\n]+?)\s*\1\s*$",
            document,
            re.MULTILINE,
        )
    )
    entries: list[tuple[str, str]] = []

    def append_template(template: re.Match[str]) -> None:
        positional = [
            _clean_text(part)
            for part in template.group(1).split("|")
            if "=" not in part
        ]
        if len(positional) < 2 or not positional[0] or not positional[1]:
            raise UpdateError(
                "unsupported csl template in League Wiki patch page: "
                f"{template.group(0)!r}"
            )
        entry = (positional[0], positional[1])
        if entry not in entries:
            entries.append(entry)

    for index, heading in enumerate(headings):
        heading_key = _name_key(heading.group(2))
        if (
            heading_key not in _WIKI_NEW_SKIN_HEADINGS
            and not heading_key.startswith("newultimateskin")
        ):
            continue
        heading_level = len(heading.group(1))
        end = next(
            (
                following.start()
                for following in headings[index + 1 :]
                if len(following.group(1)) <= heading_level
            ),
            len(document),
        )
        section = document[heading.end() : end]
        collecting = True
        for line in section.splitlines():
            marker_text = _clean_text(
                re.sub(r"\{\{.*?\}\}|\[\[|\]\]", "", line)
            )
            marker = _name_key(marker_text)
            has_skin_template = _WIKI_CSL_RE.search(line) is not None
            skin_change_marker = ("skin" in marker or has_skin_template) and any(
                verb in marker
                for verb in ("adjusted", "updated", "received")
            )
            skin_change_marker = skin_change_marker or (
                ("skin" in marker or has_skin_template)
                and re.search(
                    r"\bre(?:\s|-)*released\b",
                    marker_text,
                    flags=re.IGNORECASE,
                )
                is not None
            )
            non_skin_marker = (
                "followingchrom" in marker
                or "followingwardskin" in marker
                or "followingsummonericon" in marker
            )
            new_skin_marker = (
                "skin" in marker
                and not skin_change_marker
                and any(
                    verb in marker
                    for verb in ("added", "released", "distributed")
                )
            )
            if non_skin_marker or skin_change_marker:
                collecting = False
                continue
            if new_skin_marker:
                collecting = True
            if not collecting:
                continue
            for template in _WIKI_CSL_RE.finditer(line):
                append_template(template)
        break

    # Ranked-reward skins live outside the cosmetics section on older pages.
    # Their season headings are explicit release evidence, not balance notes.
    for index, heading in enumerate(headings):
        heading_key = _name_key(heading.group(2))
        if not (
            "season" in heading_key
            and (
                "ended" in heading_key
                or heading_key.startswith("endofseason")
                or "rewards" in heading_key
            )
        ):
            continue
        heading_level = len(heading.group(1))
        end = next(
            (
                following.start()
                for following in headings[index + 1 :]
                if len(following.group(1)) <= heading_level
            ),
            len(document),
        )
        for template in _WIKI_CSL_RE.finditer(document[heading.end() : end]):
            append_template(template)

    # A few special releases are recorded only in the patch infobox, using
    # either ``New skin:`` before the template or ``launch`` immediately after
    # it.  Inspect each template's own clause so an adjacent ``update`` entry
    # on the same line is not mistaken for a launch.
    for line in document.splitlines():
        templates = list(_WIKI_CSL_RE.finditer(line))
        previous_end = 0
        for template_index, template in enumerate(templates):
            next_start = (
                templates[template_index + 1].start()
                if template_index + 1 < len(templates)
                else len(line)
            )
            prefix = line[previous_end : template.start()]
            suffix = line[template.end() : next_start]
            if re.search(r"\bnew\s+skin\b", prefix, re.IGNORECASE) or re.search(
                r"\blaunch(?:ed|es|ing)?\b", suffix, re.IGNORECASE
            ):
                append_template(template)
            previous_end = template.end()
    return tuple(entries)


def _load_wiki_revision_documents(
    titles: Sequence[str],
    *,
    fetcher: Callable[[str], str],
    batch_size: int = 40,
) -> dict[str, str]:
    if batch_size < 1 or batch_size > 50:
        raise ValueError("batch_size must be between 1 and 50")
    documents: dict[str, str] = {}
    for offset in range(0, len(titles), batch_size):
        batch = titles[offset : offset + batch_size]
        query = urlencode(
            {
                "action": "query",
                "prop": "revisions",
                "rvprop": "content",
                "rvslots": "main",
                "redirects": "1",
                "format": "json",
                "formatversion": "2",
                "titles": "|".join(batch),
            }
        )
        url = f"{LOL_WIKI_API_URL}?{query}"
        try:
            payload = json.loads(fetcher(url))
        except json.JSONDecodeError as exc:
            raise UpdateError(f"invalid League Wiki JSON from {url}: {exc}") from exc
        query_data = payload.get("query") if isinstance(payload, dict) else None
        pages = query_data.get("pages") if isinstance(query_data, dict) else None
        if not isinstance(pages, list):
            raise UpdateError(f"invalid League Wiki response schema: {url}")
        for page in pages:
            if not isinstance(page, dict) or page.get("missing"):
                continue
            title = page.get("title")
            revisions = page.get("revisions")
            revision = revisions[0] if isinstance(revisions, list) and revisions else None
            slots = revision.get("slots") if isinstance(revision, dict) else None
            main = slots.get("main") if isinstance(slots, dict) else None
            content = main.get("content") if isinstance(main, dict) else None
            if isinstance(title, str) and isinstance(content, str):
                documents[title.casefold()] = content
    return documents


def _wiki_ref_for_release_date(
    release_date: str,
    timeline: Sequence[tuple[str, WikiPatchRef]],
) -> WikiPatchRef | None:
    """Return the patch active on a SkinData release date.

    A skin predating Wiki's first numbered build is assigned to that first
    build; a skin newer than the inspected timeline is left for a future run.
    """

    if not timeline:
        return None
    ordered = sorted(timeline, key=lambda item: (item[0], item[1].sort_key))
    if release_date > ordered[-1][0]:
        return None
    eligible = [item for item in ordered if item[0] <= release_date]
    if eligible:
        return max(eligible, key=lambda item: (item[0], item[1].sort_key))[1]
    return ordered[0][1]


def _resolve_wiki_release_history(
    refs: Sequence[WikiPatchRef],
    *,
    catalog: SkinCatalog,
    wiki_catalog: WikiSkinCatalog,
    page_documents: dict[str, str],
) -> tuple[tuple[ResolvedPatchResult, ...], dict[str, str]]:
    """Resolve released stable IDs and dates from one Wiki page snapshot."""

    if not refs:
        return (), {}

    def display_name(skin_id: str) -> str:
        catalog_name = catalog.names_by_id.get(skin_id)
        if catalog_name is not None:
            return catalog_name
        record = wiki_catalog.records_by_id.get(skin_id)
        if record is None:
            return f"League Wiki skin {skin_id}"
        return f"{record.skin} {record.champion}"

    missing_pages: list[str] = []
    patch_release_dates: dict[str, str] = {}
    candidates_by_id: dict[
        str, list[tuple[WikiPatchRef, ResolvedSkin, str, str]]
    ] = {}
    for ref in refs:
        document = page_documents.get(ref.title.casefold())
        if document is None:
            missing_pages.append(ref.title)
            continue
        patch_release_date = extract_wiki_patch_release_date(document, patch=ref.version)
        if patch_release_date is not None:
            patch_release_dates[ref.version] = patch_release_date
        seen_ids: set[str] = set()
        for champion, skin in parse_wiki_skin_entries(document):
            if _name_key(skin) == "original":
                continue
            try:
                skin_id = wiki_catalog.resolve(champion, skin)
            except UpdateError as exc:
                raise UpdateError(f"{ref.title}: {exc}") from exc
            if skin_id in seen_ids:
                continue
            seen_ids.add(skin_id)
            skin_release_date = wiki_catalog.release_dates_by_id.get(skin_id)
            if patch_release_date is None:
                raise UpdateError(
                    f"League Wiki cannot date {display_name(skin_id)!r} "
                    f"(ID {skin_id}) in {ref.title}"
                )
            # A newly-added SkinData row can briefly lack its release field.
            # The explicit patch listing remains sufficient evidence; using
            # that patch's own date makes duplicate candidates fall back to
            # their earliest explicit appearance.
            if skin_release_date is None:
                skin_release_date = patch_release_date
            identity = ResolvedSkin(
                skin_id,
                display_name(skin_id),
                "League Wiki patch history + SkinData",
            )
            candidates_by_id.setdefault(skin_id, []).append(
                (ref, identity, patch_release_date, skin_release_date)
            )
    if missing_pages:
        raise UpdateError(
            "League Wiki has no revision data for: " + ", ".join(missing_pages)
        )

    selected_by_version: dict[str, list[ResolvedSkin]] = {}
    for skin_id, candidates in candidates_by_id.items():
        def candidate_score(
            candidate: tuple[WikiPatchRef, ResolvedSkin, str, str],
        ) -> tuple[int, bool, tuple[int, int, int, int, str]]:
            patch_date = datetime.fromisoformat(candidate[2]).date()
            skin_date = datetime.fromisoformat(candidate[3]).date()
            offset = (patch_date - skin_date).days
            return (abs(offset), offset > 0, candidate[0].sort_key)

        chosen = min(
            candidates,
            key=candidate_score,
        )
        selected_by_version.setdefault(chosen[0].version, []).append(chosen[1])

    timeline = [
        (patch_release_dates[ref.version], ref)
        for ref in refs
        if ref.version in patch_release_dates
    ]
    if not timeline:
        raise UpdateError("League Wiki patch history contains no release dates")
    for skin_id, skin_release_date in wiki_catalog.release_dates_by_id.items():
        if skin_id in candidates_by_id:
            continue
        ref = _wiki_ref_for_release_date(skin_release_date, timeline)
        if ref is None:
            continue
        selected_by_version.setdefault(ref.version, []).append(
            ResolvedSkin(
                skin_id,
                display_name(skin_id),
                "League Wiki SkinData release timeline",
            )
        )

    results: list[ResolvedPatchResult] = []
    for version, resolved in selected_by_version.items():
        results.append(
            ResolvedPatchResult(PatchRef(version), tuple(resolved))
        )
    ordered_dates = {
        ref.version: patch_release_dates[ref.version]
        for ref in refs
        if ref.version in patch_release_dates
    }
    return (
        tuple(sorted(results, key=lambda result: result.ref.sort_key)),
        ordered_dates,
    )


def parse_wiki_maintenance_patches(document: str) -> tuple[str, str]:
    """Return Wiki's current and next numbered League patches."""

    values: dict[str, str] = {}
    for key in ("Patch", "NextPatch"):
        match = re.search(
            rf'^\s*\["{key}"\]\s*=\s*"([^"]+)"\s*,?\s*$',
            document,
            flags=re.MULTILINE,
        )
        if match is None:
            raise UpdateError(f"League Wiki maintenance data has no {key} value")
        try:
            values[key] = normalize_patch_version(match.group(1))
        except ValueError as exc:
            raise UpdateError(
                f"League Wiki maintenance data has invalid {key}: {match.group(1)!r}"
            ) from exc
    current = values["Patch"]
    upcoming = values["NextPatch"]
    if patch_sort_key(upcoming) <= patch_sort_key(current):
        raise UpdateError(
            f"League Wiki NextPatch {upcoming} is not newer than Patch {current}"
        )
    return current, upcoming


def load_wiki_current_patch(*, fetcher: Callable[[str], str]) -> str:
    """Fetch the patch League Wiki currently marks as live."""

    documents = _load_wiki_revision_documents(
        [LOL_WIKI_MAINTENANCE_DATA_TITLE],
        fetcher=fetcher,
    )
    document = documents.get(LOL_WIKI_MAINTENANCE_DATA_TITLE.casefold())
    if document is None:
        raise UpdateError(
            f"League Wiki has no revision data for: {LOL_WIKI_MAINTENANCE_DATA_TITLE}"
        )
    current, _ = parse_wiki_maintenance_patches(document)
    return current


def parse_wiki_upcoming_skins(
    listings: Sequence[tuple[str, str, str]],
    *,
    wiki_catalog: WikiSkinCatalog,
) -> tuple[tuple[UpcomingSkin, ...], tuple[str, ...]]:
    """Assign listed skins to the patch of the first Wiki page naming them.

    Each listing is ``(title, patch, document)``, most specific page first.
    SkinData can trail new listings, so entries it cannot resolve yet are
    returned as warnings instead of failing the snapshot.
    """

    upcoming: dict[str, UpcomingSkin] = {}
    warnings: list[str] = []
    for title, patch, document in listings:
        planned_patch = normalize_patch_version(patch)
        try:
            entries = parse_wiki_skin_entries(document)
        except UpdateError as exc:
            warnings.append(f"{title}: {exc}")
            continue
        for champion, skin in entries:
            if _name_key(skin) == "original":
                continue
            try:
                skin_id = wiki_catalog.resolve(champion, skin)
            except UpdateError as exc:
                warnings.append(f"{title}: {exc}")
                continue
            record = wiki_catalog.records_by_id.get(skin_id)
            if record is None:
                warnings.append(
                    f"{title}: League Wiki SkinData has no record for skin ID {skin_id}"
                )
                continue
            upcoming.setdefault(
                skin_id,
                UpcomingSkin(skin_id, record.champion, record.skin, planned_patch),
            )
    return (
        tuple(sorted(upcoming.values(), key=lambda item: int(item.skin_id))),
        tuple(warnings),
    )


def load_wiki_upcoming_snapshot(
    *,
    fetcher: Callable[[str], str],
) -> WikiUpcomingSnapshot:
    """Fetch the Wiki's patch assignments for an ephemeral site build.

    VPBE lists next-patch cosmetics until release week, when the Wiki moves
    them to the upcoming patch page. The current and next patch pages keep
    those skins scheduled until their release history is synchronized.
    """

    source_titles = [
        LOL_WIKI_SKIN_DATA_TITLE,
        LOL_WIKI_MAINTENANCE_DATA_TITLE,
        LOL_WIKI_VPBE_TITLE,
    ]
    source_documents = _load_wiki_revision_documents(
        source_titles,
        fetcher=fetcher,
        batch_size=len(source_titles),
    )
    missing_sources = [
        title for title in source_titles if title.casefold() not in source_documents
    ]
    if missing_sources:
        raise UpdateError(
            "League Wiki Upcoming snapshot is missing: " + ", ".join(missing_sources)
        )

    wiki_catalog = parse_wiki_skin_data(
        source_documents[LOL_WIKI_SKIN_DATA_TITLE.casefold()],
        minimum_champions=150,
        minimum_skins=1000,
    )
    current_patch, next_patch = parse_wiki_maintenance_patches(
        source_documents[LOL_WIKI_MAINTENANCE_DATA_TITLE.casefold()]
    )
    patch_titles = {patch: f"V{patch}" for patch in (current_patch, next_patch)}
    patch_documents = _load_wiki_revision_documents(
        list(patch_titles.values()),
        fetcher=fetcher,
    )
    listings = [
        (title, patch, patch_documents[title.casefold()])
        for patch, title in patch_titles.items()
        if title.casefold() in patch_documents
    ]
    listings.append(
        (
            LOL_WIKI_VPBE_TITLE,
            next_patch,
            source_documents[LOL_WIKI_VPBE_TITLE.casefold()],
        )
    )
    skins, warnings = parse_wiki_upcoming_skins(listings, wiki_catalog=wiki_catalog)
    verify_upcoming_skins(skins)
    return WikiUpcomingSnapshot(skins, wiki_catalog, warnings)


def load_wiki_source_snapshot(
    *,
    catalog: SkinCatalog,
    fetcher: Callable[[str], str],
) -> WikiSourceSnapshot:
    """Fetch one complete, internally consistent Wiki update snapshot."""

    source_titles = [
        LOL_WIKI_RELEASE_HISTORY_TITLE,
        LOL_WIKI_SKIN_DATA_TITLE,
        LOL_WIKI_MAINTENANCE_DATA_TITLE,
    ]
    source_documents = _load_wiki_revision_documents(
        source_titles,
        fetcher=fetcher,
        batch_size=len(source_titles),
    )
    missing_sources = [
        title for title in source_titles if title.casefold() not in source_documents
    ]
    if missing_sources:
        raise UpdateError(
            "League Wiki source snapshot is missing: " + ", ".join(missing_sources)
        )

    refs = parse_wiki_patch_refs(
        source_documents[LOL_WIKI_RELEASE_HISTORY_TITLE.casefold()]
    )
    wiki_catalog = parse_wiki_skin_data(
        source_documents[LOL_WIKI_SKIN_DATA_TITLE.casefold()],
        minimum_champions=150,
        minimum_skins=1000,
    )
    current_patch, _ = parse_wiki_maintenance_patches(
        source_documents[LOL_WIKI_MAINTENANCE_DATA_TITLE.casefold()]
    )
    latest_ref = max(refs, key=lambda ref: ref.sort_key)
    if latest_ref.version != current_patch:
        raise UpdateError(
            "League Wiki release history ends at "
            f"{latest_ref.version}, but maintenance data says {current_patch}"
        )

    page_documents = _load_wiki_revision_documents(
        [ref.title for ref in refs],
        fetcher=fetcher,
    )
    release_results, patch_dates = _resolve_wiki_release_history(
        refs,
        catalog=catalog,
        wiki_catalog=wiki_catalog,
        page_documents=page_documents,
    )
    return WikiSourceSnapshot(
        release_results,
        patch_dates,
        len(refs),
        wiki_catalog,
    )


def _parse_wiki_release_date(value: str, *, patch: str) -> str:
    cleaned = re.sub(
        r"\{\{\s*NumberSup\s*\|\s*(\d{1,2})\s*\}\}",
        r"\1",
        value,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"<!--.*?-->", "", cleaned, flags=re.DOTALL)
    cleaned = _clean_text(re.sub(r"<[^>]+>", "", cleaned))
    cleaned = re.sub(
        r"\b(\d{1,2})(?:st|nd|rd|th)\b",
        r"\1",
        cleaned,
        flags=re.IGNORECASE,
    )
    date_values = re.findall(
        r"\b(?:January|February|March|April|May|June|July|August|"
        r"September|October|November|December)\s+\d{1,2},\s+\d{4}\b",
        cleaned,
        flags=re.IGNORECASE,
    )
    try:
        dates = [
            datetime.strptime(date_value, "%B %d, %Y").date()
            for date_value in date_values
        ]
    except ValueError as exc:
        raise UpdateError(
            f"unsupported League Wiki release date for patch {patch}: {value!r}"
        ) from exc
    if not dates:
        raise UpdateError(
            f"unsupported League Wiki release date for patch {patch}: {value!r}"
        )
    return min(dates).isoformat()


def extract_wiki_patch_release_date(document: str, *, patch: str) -> str | None:
    match = re.search(
        r"^\|\s*Release\s*=\s*(.+?)\s*$",
        document,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    if match is None:
        return None
    return _parse_wiki_release_date(match.group(1), patch=patch)


def merge_wiki_patch_dates(
    existing: dict[str, str],
    versions: dict[str, str],
    wiki_patch_dates: dict[str, str],
) -> PatchDateMergeResult:
    """Select represented release dates from the already-fetched Wiki snapshot."""

    verify_patch_dates_data(existing)
    verify_patch_dates_data(wiki_patch_dates)
    target_versions = sorted(set(versions.values()), key=patch_sort_key)
    missing = [patch for patch in target_versions if patch not in wiki_patch_dates]
    if missing:
        raise UpdateError(
            "League Wiki snapshot has no release date for represented patches: "
            + ", ".join(missing)
        )
    ordered = {patch: wiki_patch_dates[patch] for patch in target_versions}
    verify_patch_dates_data(ordered, expected_versions=target_versions)
    additions = tuple(
        (patch, ordered[patch])
        for patch in target_versions
        if patch not in existing
    )
    updates = tuple(
        (patch, existing[patch], ordered[patch])
        for patch in target_versions
        if patch in existing and existing[patch] != ordered[patch]
    )
    return PatchDateMergeResult(ordered, additions, updates)


def _write_bytes_atomic(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _skin_catalog_from_data(data: dict[str, str]) -> SkinCatalog:
    return SkinCatalog({
        key: value
        for key, value in data.items()
        if int(key) % 1000 != 0
    })


def _name_key(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).casefold()
    return "".join(character for character in normalized if character.isalnum())


def load_versions(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise UpdateError(f"cannot read {path}: {exc}") from exc
    if not isinstance(data, dict) or any(
        not isinstance(key, str) or not isinstance(value, str)
        for key, value in data.items()
    ):
        raise UpdateError(
            f"{path} must be a JSON object of skin identity -> version strings"
        )
    return data


def merge_versions(
    existing: dict[str, str], results: Sequence[ResolvedPatchResult]
) -> MergeResult:
    merged = dict(existing)
    additions: list[tuple[str, str]] = []
    conflicts: list[str] = []
    duplicates: list[str] = []
    seen_scraped: dict[str, str] = {}

    for result in sorted(results, key=lambda item: item.ref.sort_key):
        for skin in result.skins:
            skin_id = skin.skin_id
            previous_version = seen_scraped.get(skin_id)
            if previous_version is not None:
                if previous_version != result.ref.version:
                    duplicates.append(
                        f"{skin.display_name!r} (ID {skin_id}) appears in both "
                        f"{previous_version} and {result.ref.version}; keeping "
                        f"{previous_version}"
                    )
                continue
            seen_scraped[skin_id] = result.ref.version

            if skin_id in merged:
                if merged[skin_id] != result.ref.version:
                    conflicts.append(
                        f"{skin.display_name!r} (ID {skin_id}): keeping existing "
                        f"{merged[skin_id]!r}, scraped {result.ref.version!r}"
                    )
                continue

            merged[skin_id] = result.ref.version
            additions.append((skin_id, result.ref.version))

    return MergeResult(
        merged,
        tuple(additions),
        tuple(conflicts),
        tuple(duplicates),
    )


def catalog_history_exceptions(
    versions: dict[str, str], catalog: SkinCatalog
) -> tuple[str, ...]:
    """Report historical IDs no longer present in the current upstream catalog."""

    return tuple(skin_id for skin_id in versions if skin_id not in catalog.names_by_id)


def verify_versions_data(versions: dict[str, str]) -> None:
    """Validate canonical full skin IDs and normalized patch values."""

    invalid_ids: list[str] = []
    invalid_versions: list[str] = []
    for skin_id, version in versions.items():
        if (
            re.fullmatch(r"[1-9]\d*", skin_id) is None
            or int(skin_id) % 1000 == 0
        ):
            invalid_ids.append(repr(skin_id))
        try:
            normalized = normalize_patch_version(version)
        except ValueError:
            normalized = ""
        if normalized != version:
            invalid_versions.append(f"{skin_id!r}: {version!r}")

    if invalid_ids:
        raise UpdateError(
            "versions verification found invalid full skin IDs: "
            + ", ".join(invalid_ids)
        )
    if invalid_versions:
        raise UpdateError(
            "versions verification found invalid patch values: "
            + ", ".join(invalid_versions)
        )


def verify_versions_snapshot(path: Path, expected: dict[str, str]) -> None:
    """Reload the written file and verify its content and order."""

    actual = load_versions(path)
    if list(actual.items()) != list(expected.items()):
        raise UpdateError(f"post-write verification failed for {path}")
    verify_versions_data(actual)


def write_versions_atomic(path: Path, versions: dict[str, str]) -> None:
    text = json.dumps(versions, ensure_ascii=False, indent=2)
    _write_bytes_atomic(path, text.encode("utf-8"))


def write_patch_dates_atomic(path: Path, patch_dates: dict[str, str]) -> None:
    text = json.dumps(patch_dates, ensure_ascii=False, indent=2)
    _write_bytes_atomic(path, text.encode("utf-8"))


def verify_patch_dates_snapshot(
    path: Path,
    expected: dict[str, str],
    *,
    versions: Iterable[str],
) -> None:
    actual = load_patch_dates(path)
    if actual != expected:
        raise UpdateError(f"post-write verification failed for {path}")
    verify_patch_dates_data(actual, expected_versions=versions)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Synchronize skin_ids.json, rebuild released skin evidence and "
            "patch dates from League Wiki, and update released artwork."
        )
    )
    parser.add_argument(
        "--versions",
        type=Path,
        default=DEFAULT_SKIN_VERSIONS_PATH,
        help="skin versions JSON path (default: %(default)s)",
    )
    parser.add_argument(
        "--patch-dates",
        type=Path,
        default=DEFAULT_PATCH_DATES_PATH,
        help="patch release dates JSON path (default: %(default)s)",
    )
    parser.add_argument(
        "--assets",
        type=Path,
        default=DEFAULT_SKIN_ASSETS_PATH,
        help="League Wiki artwork manifest path (default: %(default)s)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="per-request timeout in seconds (default: %(default)s)",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=3,
        choices=range(0, 7),
        metavar="N",
        help="retries for transient request errors, 0-6 (default: %(default)s)",
    )
    return parser


def run(argv: Sequence[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    versions_path = args.versions.resolve()
    patch_dates_path = args.patch_dates.resolve()
    skin_assets_path = args.assets.resolve()

    def configured_fetch(url: str) -> str:
        return fetch_text(url, timeout=args.timeout, retries=args.retries)

    skin_ids_path = DEFAULT_SKIN_IDS_PATH.resolve()
    remote_catalog_document = configured_fetch(CDRAGON_EN_SKINS_URL)
    remote_catalog_data = parse_cdragon_skin_catalog(
        remote_catalog_document,
        source=CDRAGON_EN_SKINS_URL,
        minimum_entries=8000,
    )
    remote_catalog_bytes = encode_skin_catalog(remote_catalog_data)
    try:
        local_catalog_bytes = skin_ids_path.read_bytes()
    except FileNotFoundError:
        local_catalog_bytes = b""
    except OSError as exc:
        raise UpdateError(f"cannot read {skin_ids_path}: {exc}") from exc
    skin_ids_changed = local_catalog_bytes != remote_catalog_bytes
    catalog = _skin_catalog_from_data(remote_catalog_data)
    existing = load_versions(versions_path)
    existing_patch_dates = load_patch_dates(patch_dates_path)
    verify_versions_data(existing)
    historical_exceptions = catalog_history_exceptions(existing, catalog)
    if historical_exceptions:
        print(
            "warning: released Wiki skin IDs absent from the current "
            "CommunityDragon compatibility catalog: "
            + ", ".join(
                f"{skin_id} ({existing[skin_id]})"
                for skin_id in historical_exceptions
            ),
            file=sys.stderr,
        )

    snapshot = load_wiki_source_snapshot(
        catalog=catalog,
        fetcher=configured_fetch,
    )
    resolved_count = sum(len(result.skins) for result in snapshot.release_results)
    explicit_count = sum(
        skin.source == "League Wiki patch history + SkinData"
        for result in snapshot.release_results
        for skin in result.skins
    )
    timeline_count = resolved_count - explicit_count
    print(
        f"League Wiki snapshot: {snapshot.patch_pages} patch pages, "
        f"{resolved_count} released stable skin IDs "
        f"({explicit_count} explicit, {timeline_count} release-date fallback)."
    )
    merge = merge_versions(existing, snapshot.release_results)
    if merge.duplicate_names:
        print("Duplicate release listings:", file=sys.stderr)
        for message in merge.duplicate_names:
            print(f"  - {message}", file=sys.stderr)
    if merge.conflicts:
        raise UpdateError(
            f"merge verification failed; {versions_path.name} was not written:\n  - "
            + "\n  - ".join(merge.conflicts)
        )

    verify_versions_data(merge.merged)
    source_released_ids = {
        skin.skin_id
        for result in snapshot.release_results
        for skin in result.skins
    }
    expected_source_ids = set(existing)
    missing_source_ids = sorted(expected_source_ids - source_released_ids, key=int)
    if missing_source_ids:
        raise UpdateError(
            "League Wiki rebuild does not cover existing released skin IDs: "
            + ", ".join(missing_source_ids)
        )
    patch_date_merge = merge_wiki_patch_dates(
        existing_patch_dates,
        merge.merged,
        snapshot.patch_dates,
    )
    expected_asset_ids = set(merge.merged)
    missing_asset_records = sorted(
        expected_asset_ids - snapshot.wiki_catalog.records_by_id.keys(),
        key=int,
    )
    if missing_asset_records:
        raise UpdateError(
            "League Wiki SkinData has no artwork identity for skin IDs: "
            + ", ".join(missing_asset_records)
        )
    asset_records = [
        snapshot.wiki_catalog.records_by_id[skin_id]
        for skin_id in sorted(expected_asset_ids, key=int)
    ]
    skin_assets = resolve_wiki_skin_assets(
        asset_records,
        fetcher=configured_fetch,
    )
    verify_skin_assets_data(
        skin_assets,
        expected_ids=expected_asset_ids,
        released_ids=merge.merged,
    )
    existing_skin_assets = (
        load_skin_assets_manifest(skin_assets_path)
        if skin_assets_path.exists()
        else None
    )
    skin_assets_changed = existing_skin_assets != skin_assets
    print(
        f"Verified {len(merge.additions)} new stable skin ID(s) from "
        "League Wiki release evidence."
    )
    print(
        f"Verified release dates for {len(patch_date_merge.merged)} patch(es): "
        f"{len(patch_date_merge.additions)} added, "
        f"{len(patch_date_merge.updates)} updated."
    )
    complete_asset_count = sum(
        set(variants) == set(WIKI_ASSET_VARIANTS)
        for variants in skin_assets.values()
    )
    print(
        f"Verified League Wiki artwork for {complete_asset_count}/"
        f"{len(skin_assets)} skin(s); all released skins have four variants."
    )
    identities_by_id = {
        skin.skin_id: skin
        for result in snapshot.release_results
        for skin in result.skins
    }
    if merge.additions:
        print(f"New entries: {len(merge.additions)}")
        for skin_id, version in merge.additions:
            identity = identities_by_id[skin_id]
            print(
                f"  {json.dumps(skin_id)}: {json.dumps(version)}  "
                f"# {identity.display_name} [{identity.source}]"
            )
    else:
        print(f"{versions_path.name} is already up to date.")

    if skin_ids_changed:
        _write_bytes_atomic(skin_ids_path, remote_catalog_bytes)
        print(f"Updated {skin_ids_path}")
    synchronized_bytes = skin_ids_path.read_bytes()
    if synchronized_bytes != remote_catalog_bytes:
        raise UpdateError(f"post-write verification failed for {skin_ids_path}")
    parse_skin_catalog(
        synchronized_bytes.decode("utf-8"),
        source=str(skin_ids_path),
        minimum_entries=1000,
    )
    if merge.additions:
        write_versions_atomic(versions_path, merge.merged)
        print(f"Updated {versions_path}")
    verify_versions_snapshot(versions_path, merge.merged)

    patch_dates_changed = patch_date_merge.merged != existing_patch_dates
    if patch_dates_changed:
        write_patch_dates_atomic(patch_dates_path, patch_date_merge.merged)
        print(f"Updated {patch_dates_path}")
    verify_patch_dates_snapshot(
        patch_dates_path,
        patch_date_merge.merged,
        versions=merge.merged.values(),
    )
    if skin_assets_changed:
        write_skin_assets_atomic(
            skin_assets_path,
            skin_assets,
        )
        print(f"Updated {skin_assets_path}")
    verify_skin_assets_snapshot(
        skin_assets_path,
        skin_assets,
        released_ids=merge.merged,
    )
    if (
        not skin_ids_changed
        and not merge.additions
        and not patch_dates_changed
        and not skin_assets_changed
    ):
        print("Data files are already up to date.")
    print("Post-write verification passed.")
    return 0


def main() -> None:
    try:
        raise SystemExit(run())
    except (UpdateError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
