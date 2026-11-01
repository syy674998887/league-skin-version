"""Match public SkinSpotlights titles; refresh recent entries without an API key."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET

from . import updater

CHANNEL_ID = "UC0NwzCHb8Fg89eTB5eYX17Q"
CATALOG_PATH = updater.PROJECT_ROOT / "skin_spotlights.json"
FEED_URL = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"
VIDEO_ID = re.compile(r"[A-Za-z0-9_-]{11}")


def name_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKD", value).lower())


def parse_title(title: str) -> tuple[str, bool] | None:
    title = re.sub(r"\s+", " ", title).strip()
    match = re.fullmatch(r"(.+?) Skin Spotlight(.*)", title, re.IGNORECASE)
    if not match:
        return None
    name, suffix = match.groups()
    suffix = re.sub(r"^ \(20\d{2}(?: Update)?\)", "", suffix).strip()
    suffix = re.sub(r"\s+-\s*", " - ", suffix).strip()
    if suffix not in {
        "", "League of Legends", "- League of Legends",
        "- Pre-Release - League of Legends",
        "- Pre-Release - PBE Preview - League of Legends",
        "- Pre-Release - PBE Preview",
    }:
        return None
    return re.sub(r" League of Legends$", "", name, flags=re.IGNORECASE), "Pre-Release" in suffix


def catalog(videos: list[dict[str, str]]) -> dict:
    """Input is newest first; retain the newest full spotlight for each title identity."""
    selected = {}
    for video in videos:
        if not VIDEO_ID.fullmatch(video["id"]):
            raise ValueError("Invalid SkinSpotlights video ID")
        parsed = parse_title(video["title"])
        if not parsed:
            continue
        name, preview = parsed
        key = name_key(name)
        if key not in selected or (selected[key][1] and not preview):
            selected[key] = ({"id": video["id"], "title": video["title"]}, preview)
    chosen = {video["id"] for video, _ in selected.values()}
    result = []
    for video in videos:
        if video["id"] in chosen:
            result.append({"id": video["id"], "title": video["title"]})
            chosen.remove(video["id"])
    return {"channelId": CHANNEL_ID, "videos": result}


def load_catalog(path: Path = CATALOG_PATH) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data["channelId"] != CHANNEL_ID:
        raise ValueError("Unexpected SkinSpotlights channel")
    return catalog(data["videos"])


def attach_spotlights(skins: list[dict], data: dict) -> None:
    if data["channelId"] != CHANNEL_ID:
        raise ValueError("Unexpected SkinSpotlights channel")
    counts = Counter(name_key(skin["name"]) for skin in skins)
    by_name = {
        name_key(skin["name"]): skin
        for skin in skins if counts[name_key(skin["name"])] == 1
    }
    for skin in skins:
        skin.pop("spotlight", None)
    for video in data["videos"]:
        if not VIDEO_ID.fullmatch(video["id"]):
            raise ValueError("Invalid SkinSpotlights video ID")
        parsed = parse_title(video["title"])
        if not parsed:
            continue
        name, preview = parsed
        key = name_key(name)
        # Exact names preserve distinct editions such as Prestige skins (2022).
        if key not in counts and not name.casefold().startswith("prestige "):
            key = name_key(re.sub(r" \(20\d{2}(?: (?:Rework|Update|ASU|VGU))?\)$", "", name))
        skin = by_name.get(key)
        if skin is None:
            continue
        current = skin.get("spotlight")
        if current is None or (current["preview"] and not preview):
            skin["spotlight"] = {"videoId": video["id"], "title": video["title"], "preview": preview}


def merge_feed(data: dict, xml: str) -> dict:
    namespaces = {"atom": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}
    feed = ET.fromstring(xml)
    feed_channel = feed.findtext("yt:channelId", namespaces=namespaces)
    if data["channelId"] != CHANNEL_ID or feed_channel not in {CHANNEL_ID, CHANNEL_ID[2:]}:
        raise ValueError("Unexpected SkinSpotlights feed channel")
    incoming = []
    for entry in feed.findall("atom:entry", namespaces):
        if entry.findtext("yt:channelId", namespaces=namespaces) != CHANNEL_ID:
            raise ValueError("Unexpected SkinSpotlights video owner")
        incoming.append({"id": entry.findtext("yt:videoId", namespaces=namespaces) or "",
                         "title": entry.findtext("atom:title", namespaces=namespaces) or ""})
    ids = {video["id"] for video in incoming}
    return catalog(incoming + [video for video in data["videos"] if video["id"] not in ids])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--import-catalog", type=Path, help="Import yt-dlp --flat-playlist -J channel metadata")
    args = parser.parse_args()
    try:
        if args.import_catalog:
            raw = json.loads(args.import_catalog.read_text(encoding="utf-8-sig"))
            if raw["channel_id"] != CHANNEL_ID:
                raise ValueError("Unexpected SkinSpotlights import channel")
            result = catalog(raw["entries"])
        else:
            result = merge_feed(load_catalog(), updater.fetch_text(FEED_URL, timeout=20, retries=1))
        encoded = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        if not CATALOG_PATH.exists() or CATALOG_PATH.read_bytes() != encoded:
            updater._write_bytes_atomic(CATALOG_PATH, encoded)
        print(f"SkinSpotlights: {len(result['videos'])} video identities saved.")
    except (OSError, ValueError, KeyError, TypeError, ET.ParseError, updater.UpdateError) as error:
        print(f"SkinSpotlights refresh failed; saved catalog kept: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
