# League Skin Version

[简体中文](README.zh-CN.md)

A static archive for browsing League of Legends skins by release patch.

League Skin Version is an unofficial, non-commercial community project. It is not endorsed or sponsored by Riot Games.

[Open the archive](https://syy674998887.github.io/league-skin-version/)

## Features

- Groups released skins by release patch and shows the corresponding patch date. Upcoming PBE skins remain in a separate section.
- Skin details show only the individual skin release date from the Wiki, labeled Expected release for Upcoming skins. The right side of each PATCH heading shows only the patch release date. Missing dates are omitted; neither date substitutes for the other.
- Searches English and Chinese champion names, skin names, and stable IDs; filters by champion, skinline, rarity, Legacy status, and chroma availability. Rarity and Legacy options and selected values display their corresponding icons.
- Desktop filters arrange themselves according to the available container width, with search spanning two columns. Mobile layouts retain two or one column.
- Filter menus open above or below according to available space and adjust on scroll or viewport changes. Opening skin details first closes the footer information panel for both mouse and keyboard navigation.
- Provides a responsive interface, light and dark themes, Original / Focus / Loading artwork modes that resize to the loaded image's actual aspect ratio, chromas, related champion and skinline lists, and animations when available.
- Champion-name emphasis uses complete names and Latin word boundaries; filtered patch counts exclude Upcoming. Screen-reader labels include Legacy status and chroma names. Patch navigation respects reduced-motion preferences, and restored light mode also updates the browser theme color.
- Failed rarity and Legacy icons fall back to text. Failed chroma images retain the browser’s broken-image indicator and alternative text, with names and color swatches preserved. Images without a URL remain empty.
- The “Video↗” button links matched skins directly to SkinSpotlights videos; hovering shows the original video title. Unmatched skins have no video button.

## Data

| Source | Used for |
| --- | --- |
| [League of Legends Wiki](https://wiki.leagueoflegends.com/en-us/) | Release versions, patch dates, patch numbers for Upcoming skins from VPBE and upcoming patch pages, and revision-addressed static artwork |
| [CommunityDragon](https://github.com/CommunityDragon) | Stable IDs, client and localized names, skinlines, rarities, Legacy flags, chromas, fallback and animated artwork, quest tiers, and the PBE catalog of unreleased skins |

The repository tracks these generated data files:

| File | Contents |
| --- | --- |
| `skin_ids.json` | Generated directly from CommunityDragon's English client catalog; maps top-level skin and chroma IDs to current display names and excludes quest-tier forms |
| `skin_versions.json` | Released skin IDs mapped to their release patch |
| `patch_dates.json` | Recorded patches mapped to release dates |
| `skin_assets.json` | Four revision-addressed Wiki artwork records per released skin |
| `skin_spotlights.json` | Public SkinSpotlights video IDs and titles, separate from skin release data |

Upcoming data can change, be delayed, or be cancelled before release. Each build lists every unreleased skin found in CommunityDragon's PBE catalog or on the Wiki's VPBE and upcoming patch pages. Skins show the Wiki's patch number once the Wiki lists them and appear as Upcoming until then. Upcoming data is included only in the Pages artifact, separate from released history and archive totals.

A card and its detail view show a **Wiki** or **CDragon** tag when only that source lists the skin. For example, a released skin removed from the game client keeps its Wiki name and artwork and shows the Wiki tag.

## Run locally

Requires Python 3.10 or newer and [uv](https://docs.astral.sh/uv/). From the repository root:

```console
uv sync
uv run site-build
uv run python -m http.server 8000 --directory dist
```

Open <http://localhost:8000>. `site-build` reads the local released data, fetches current Upcoming data and metadata from the Wiki and CommunityDragon, and writes the static site to the ignored `dist/` directory.

## Update data

Synchronize and update the four data files:

```console
uv run skin-update
```

The updater validates the complete candidate snapshot before writing and replaces changed files atomically. Unchanged content is not rewritten; existing released history is not silently removed. Run `uv run skin-update --help` for output-path and network options.

Refresh recent SkinSpotlights entries with `uv run python -B -m league_skin_version.spotlights`, then rebuild. Matching uses the English full skin name with punctuation normalization and recognizes rework-year annotations after checking exact edition names. Separate Prestige editions are preserved. It selects the newest full spotlight before a pre-release preview and does not use fuzzy matching. On October 31, 2026, 1,750 of the 1,970 records in the refreshed local site snapshot matched, including 25 preview links; 220 had no link.

The initial video directory was imported from the channel's public Videos tab using `yt-dlp --ignore-config --no-cache-dir --flat-playlist --skip-download -J https://www.youtube.com/@SkinSpotlights/videos`. Its JSON output can be reimported with `uv run python -B -m league_skin_version.spotlights --import-catalog PATH`. yt-dlp is an optional import tool, not a project dependency. Routine updates use the public channel feed without a key. The feed currently contains only the latest 15 uploads, so a long interruption or a large upload batch can require another full import. Removed or private videos are not automatically detected by this feed.

## Automation

The [`Update data and deploy Pages`](.github/workflows/pages.yml) workflow handles updates and deployment:

| Trigger | Behavior |
| --- | --- |
| Manual dispatch | Synchronizes data, runs tests, builds the site, commits changed JSON files, and deploys Pages |
| Daily at 12:34 in `America/New_York` | Runs tests, builds the site, and deploys Pages; also synchronizes and commits data when the last successful online synchronization is at least 20 hours old |
| Push to `main` | Runs tests, fetches the current Upcoming snapshot, builds the site, and deploys Pages without changing repository data |

The 20-hour check uses successful data-sync runs in Actions, excluding runs that skip synchronization and code-only deployments. The site's **Updated** time is that run's data-sync completion time, embedded only in the deployment artifact; `generatedAt` remains an internal build timestamp. Local builds show no update time by default. After a successful manual online synchronization, its actual completion time can be supplied through `LSV_DATA_UPDATED_AT` for the local artifact. Successful checks with no data changes still refresh the site without a bot commit.

An independent SkinSpotlights refresh step runs when data synchronization is due and commits a changed video catalog. A video-source failure keeps the saved catalog and does not block skin synchronization or deployment. Builds match the saved video catalog without contacting YouTube.

Scheduled and manual synchronization waits while League Wiki lists a patch that CommunityDragon has not published yet: the run leaves a notice and still deploys the site, but changes no data and does not count as a data sync, so the next scheduled run retries.

## Development

Run the test suite with:

```console
uv run python -B -m unittest discover -s tests -q
```

The project uses only the Python standard library at runtime.

## License

Original code and documentation are licensed under the [MIT License](LICENSE). Third-party data, game content, artwork, videos, names, and trademarks are not relicensed; see [Third-Party Notices](THIRD_PARTY_NOTICES.md).
