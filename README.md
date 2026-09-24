# League Skin Version

[简体中文](README.zh-CN.md)

A static archive for browsing League of Legends skins by release patch.

League Skin Version is an unofficial, non-commercial community project. It is not endorsed or sponsored by Riot Games.

[Open the archive](https://syy674998887.github.io/league-skin-version/)

## Features

- Groups released skins by release patch and shows the corresponding patch date. Upcoming PBE skins remain in a separate section.
- Searches English and Chinese champion names, skin names, and stable IDs; filters by champion, skinline, rarity, Legacy status, and chroma availability.
- Provides a responsive interface, light and dark themes, artwork previews, chromas, related champion and skinline lists, and animations when available.

## Data

| Source | Used for |
| --- | --- |
| [League of Legends Wiki](https://wiki.leagueoflegends.com/en-us/) | Release versions, patch dates, patch numbers for Upcoming skins from VPBE and upcoming patch pages, and revision-addressed static artwork |
| [CommunityDragon](https://github.com/CommunityDragon) | Stable IDs, client and localized names, skinlines, rarities, Legacy flags, chromas, fallback and animated artwork, quest tiers, and the PBE catalog of unreleased skins |

The repository tracks four generated data files:

| File | Contents |
| --- | --- |
| `skin_ids.json` | Generated directly from CommunityDragon's English client catalog; maps top-level skin and chroma IDs to current display names and excludes quest-tier forms |
| `skin_versions.json` | Released skin IDs mapped to their release patch |
| `patch_dates.json` | Recorded patches mapped to release dates |
| `skin_assets.json` | Four revision-addressed Wiki artwork records per released skin |

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

## Automation

The [`Update data and deploy Pages`](.github/workflows/pages.yml) workflow handles updates and deployment:

| Trigger | Behavior |
| --- | --- |
| Manual dispatch | Synchronizes data, runs tests, builds the site, commits changed JSON files, and deploys Pages |
| Daily at 12:34 in `America/New_York` | Runs tests, builds the site, and deploys Pages; also synchronizes and commits data when the last successful online synchronization is at least 20 hours old |
| Push to `main` | Runs tests, fetches the current Upcoming snapshot, builds the site, and deploys Pages without changing repository data |

The 20-hour check uses successful data-sync runs in Actions, excluding runs that skip synchronization and code-only deployments. The site's **Updated** time is that run's data-sync completion time, embedded only in the deployment artifact; `generatedAt` remains an internal build timestamp. Local builds show no update time. Successful checks with no data changes still refresh the site without a bot commit.

Scheduled and manual synchronization waits while League Wiki lists a patch that CommunityDragon has not published yet: the run leaves a notice and still deploys the site, but changes no data and does not count as a data sync, so the next scheduled run retries.

## Development

Run the test suite with:

```console
uv run python -B -m unittest discover -s tests -q
```

The project uses only the Python standard library at runtime.

## License

Original code and documentation are licensed under the [MIT License](LICENSE). Third-party data, game content, artwork, videos, names, and trademarks are not relicensed; see [Third-Party Notices](THIRD_PARTY_NOTICES.md).
