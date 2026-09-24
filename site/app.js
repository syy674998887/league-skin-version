const PAGE_SIZE = 36;
const UNSCHEDULED_VERSION = "upcoming";
const SOURCE_LABELS = Object.freeze({
  wiki: "Wiki",
  cdragon: "CDragon",
});
const ART_IMAGE_DIMENSIONS = {
  uncentered: { width: 1215, height: 717 },
  centered: { width: 1280, height: 720 },
  loading: { width: 308, height: 560 },
  tile: { width: 380, height: 380 },
};

const TRANSLATIONS = {
  zh: {
    description: "按补丁版本浏览 League of Legends 皮肤。",
    skipToSkins: "跳到皮肤列表",
    updatedLabel: "更新：",
    loading: "载入中",
    switchLanguage: "Switch to English",
    switchToLightTheme: "切换到浅色模式",
    switchToDarkTheme: "切换到深色模式",
    githubRepository: "在 GitHub 查看 League Skin Version",
    archiveEyebrow: "LEAGUE OF LEGENDS SKIN ARCHIVE",
    pageTitle: "英雄联盟皮肤档案",
    collectionAria: "数据概览",
    collected: "已经收录",
    skinsUnit: "款皮肤",
    versionsUnit: "个版本",
    championsUnit: "位英雄",
    skinBrowserAria: "皮肤列表",
    versionNavigation: "版本快捷导航",
    searchLabel: "检索",
    searchPlaceholder: "皮肤名字、ID",
    championLabel: "英雄",
    allChampions: "全部英雄",
    skinLineLabel: "皮肤系列",
    allSkinLines: "全部系列",
    rarityLabel: "皮肤等级",
    allRarities: "全部等级",
    allLegacy: "全部",
      legacyOnly: "Legacy",
    nonLegacy: "非 Legacy",
    chromaLabel: "炫彩",
    chromaScrollAria: "炫彩列表，可横向滚动",
    allChromas: "全部",
    withChromas: "有炫彩",
    withoutChromas: "无炫彩",
    reset: "重置",
    loadErrorTitle: "数据暂时无法载入",
    loadErrorBody: "请稍后刷新页面，或检查最新一次 Pages 部署是否成功。",
    emptyTitle: "没有找到匹配的皮肤",
    emptyBody: "换一个名称、英雄或筛选条件试试。",
    loadMoreAria: "继续滚动以加载更多版本",
    backToTop: "回到顶部",
    footerSummary: "League Skin Version 是由社区独立运营的免费、非商业资料项目，未获得 Riot Games 认可或赞助。",
    footerLinksAria: "网站声明与政策",
    footerDisclaimer: "免责声明",
    footerSources: "数据来源",
    footerPrivacy: "隐私",
    riotPolicyLink: "Riot 政策",
    disclaimerTitle: "免责声明",
    disclaimerProjectTitle: "项目性质",
    disclaimerBodyOne: "League Skin Version 是免费、非商业的社区资料项目，用于整理、展示和检索 League of Legends 皮肤版本信息。",
    disclaimerBodyTwo: "本项目由社区独立运营，未获得 Riot Games 认可或赞助，也不代表 Riot Games 的观点。",
    riotPolicyBefore: "本项目依据 Riot Games 的“",
    riotPolicyName: "Legal Jibber Jabber",
    riotPolicyAfter: "”（社区内容政策）使用归 Riot Games 所有的素材；Riot Games 服务另受",
    riotTermsName: "《服务条款》",
    sentenceEnd: "约束。",
    ownershipTitle: "权利与许可",
    ownershipBodyOne: "League of Legends、Riot Games 及相关内容、名称、图像、动画、视频和商标，均归 Riot Games, Inc. 或相应权利人所有。",
    ownershipBodyTwo: "本项目的 MIT License 仅适用于原创代码和文档，不涵盖第三方数据、图像、视频、商标或其他素材，也不授予对这些内容的任何权利。",
    accuracyTitle: "准确性与可用性",
    accuracyBody: "本站内容仅供参考，可能存在遗漏、延迟、来源差异或处理错误。PBE 与 Upcoming 内容在正式发布前可能随时变更、延期或取消。本站不保证内容完整、及时或绝对准确；作出重要判断前，请核对原始来源。",
    sourcesTitle: "数据来源",
    sourcesDataTitle: "数据与素材",
    sourcesBeforeWiki: "皮肤版本记录、补丁日期和静态原画主要来自 ",
    sourcesBetween: "；客户端名称、系列、等级、Legacy 状态、炫彩和动态素材来自 ",
    sourcesAfterCdragon: "。缺失的静态素材可能回退至 CommunityDragon。",
    sourcesBodyTwo: "第三方内容受相应来源及原权利人的许可、条款和政策约束。列明来源仅用于说明出处，不代表合作、认可或担保。",
    thirdPartyTitle: "第三方网站",
    thirdPartyBody: "外部链接由独立第三方运营。访问时请查阅并遵守其条款和隐私政策；本站不控制其内容、可用性或数据处理。",
    privacyTitle: "隐私",
    privacyDataTitle: "本地数据与外部请求",
    privacyBodyOne: "本站不提供账户或提交表单，也不运行由本项目运营的分析服务；仅在浏览器本地保存语言与主题偏好。",
    privacyBodyTwo: "访问本站以及加载第三方图片或视频时，托管平台或相关资源提供方可能接收 IP 地址、浏览器请求信息等常规网络数据，并按其自身政策处理。",
    closeArtwork: "关闭原画",
    collapsePlaylist: "收起皮肤列表",
    expandPlaylist: "展开皮肤列表",
    artModesAria: "原画版本",
    uncenteredArt: "原始",
    centeredArt: "聚焦",
    animatedArt: "动态",
    patch: "PATCH",
    upcoming: "UPCOMING",
    upcomingPatch: "UPCOMING {version}",
    pbeNotice: "PBE",
    skinCount: "{count} 款皮肤",
    cardAria: "查看 {name} 原画与详情",
    cardAriaWithRarity: "查看 {name} 原画与详情，皮肤等级：{rarity}",
    skinAlt: "{name} 皮肤原画",
    artworkUnavailable: "原画暂时无法载入",
    artworkPending: "PBE 原画待同步",
    resultAll: "筛选结果：{skins} 款皮肤 {versions} 个版本",
    loadFailed: "载入失败",
    releasePatch: "版本 {version}",
    legacyBadge: "LEGACY",
    actionChampion: "{name} 皮肤",
    actionSeries: "系列：{name}",
    championDetails: "{name} 皮肤",
    seriesDetails: "{name} 系列",
    relatedSkinAria: "查看 {name} 原画与详情",
    rarityStandard: "标准",
    rarityRare: "稀有",
    rarityEpic: "史诗",
    rarityLegendary: "传说",
    rarityMythic: "神话",
    rarityUltimate: "终极",
    rarityTranscendent: "卓越",
    rarityExalted: "圣堂",
  },
  en: {
    description: "Browse League of Legends skins by patch.",
    skipToSkins: "Skip to skin browser",
    updatedLabel: "Updated:",
    loading: "Loading",
    switchLanguage: "切换到中文",
    switchToLightTheme: "Switch to light theme",
    switchToDarkTheme: "Switch to dark theme",
    githubRepository: "View League Skin Version on GitHub",
    archiveEyebrow: "英雄联盟皮肤档案",
    pageTitle: "LEAGUE OF LEGENDS SKIN ARCHIVE",
    collectionAria: "Archive summary",
    collected: "COLLECTED",
    skinsUnit: "skins",
    versionsUnit: "patches",
    championsUnit: "champions",
    skinBrowserAria: "Skin list",
    versionNavigation: "Patch navigation",
    searchLabel: "Search",
    searchPlaceholder: "Skin Name or ID",
    championLabel: "Champion",
    allChampions: "All",
    skinLineLabel: "Skinline",
    allSkinLines: "All",
    rarityLabel: "Rarity",
    allRarities: "All",
    allLegacy: "All",
    legacyOnly: "Legacy only",
    nonLegacy: "Non-Legacy",
    chromaLabel: "Chromas",
    chromaScrollAria: "Chroma list, scroll horizontally",
    allChromas: "All",
    withChromas: "Has chromas",
    withoutChromas: "No chromas",
    reset: "Reset",
    loadErrorTitle: "The archive could not be loaded",
    loadErrorBody: "Refresh this page later or check the latest Pages deployment.",
    emptyTitle: "No matching skins",
    emptyBody: "Try another name, champion, or filter.",
    loadMoreAria: "Keep scrolling to load more patches",
    backToTop: "Back to top",
    footerSummary: "League Skin Version is a free, non-commercial community reference project, independently operated and not endorsed or sponsored by Riot Games.",
    footerLinksAria: "Site notices and policies",
    footerDisclaimer: "Disclaimer",
    footerSources: "Sources",
    footerPrivacy: "Privacy",
    riotPolicyLink: "Riot policy",
    disclaimerTitle: "Disclaimer",
    disclaimerProjectTitle: "Project status",
    disclaimerBodyOne: "League Skin Version is a free, non-commercial community reference project for organizing, presenting, and searching League of Legends skin release information.",
    disclaimerBodyTwo: "This project is independently operated by the community. It is not endorsed or sponsored by Riot Games and does not represent Riot Games' views.",
    riotPolicyBefore: "This project uses Riot Games-owned assets under Riot Games' ",
    riotPolicyName: "Legal Jibber Jabber",
    riotPolicyAfter: " policy; Riot Games services are separately governed by the ",
    riotTermsName: "Terms of Service",
    sentenceEnd: ".",
    ownershipTitle: "Rights and licensing",
    ownershipBodyOne: "League of Legends, Riot Games, and related content, names, images, animations, video, and trademarks belong to Riot Games, Inc. or their respective rights holders.",
    ownershipBodyTwo: "This project's MIT License covers only its original code and documentation. It grants no rights to third-party data, images, video, trademarks, or other materials.",
    accuracyTitle: "Accuracy and availability",
    accuracyBody: "This site is for reference and may contain omissions, delays, source differences, or processing errors. PBE and Upcoming content may change at any time, be delayed, or be cancelled before release. Completeness, timeliness, and absolute accuracy are not guaranteed; verify the original source before making an important decision.",
    sourcesTitle: "Sources",
    sourcesDataTitle: "Data and assets",
    sourcesBeforeWiki: "Skin release history, patch dates, and most static artwork come from ",
    sourcesBetween: "; client names, skinlines, rarity, Legacy status, chromas, and animated assets come from ",
    sourcesAfterCdragon: ". Missing static assets may fall back to CommunityDragon.",
    sourcesBodyTwo: "Third-party content remains subject to the licenses, terms, and policies of the relevant sources and rights holders. Listing a source identifies its origin only; it does not imply partnership, endorsement, or warranty.",
    thirdPartyTitle: "Third-party websites",
    thirdPartyBody: "External links are operated by independent third parties. Review and follow their terms and privacy policies when visiting; this project does not control their content, availability, or data practices.",
    privacyTitle: "Privacy",
    privacyDataTitle: "Local data and external requests",
    privacyBodyOne: "This site has no accounts or submission forms and runs no analytics operated by this project. It stores only your language and theme preferences in the browser.",
    privacyBodyTwo: "When you visit this site or load third-party images or video, the hosting platform or relevant resource providers may receive ordinary network data such as your IP address and browser request information and process it under their own policies.",
    closeArtwork: "Close artwork",
    collapsePlaylist: "Collapse skin playlist",
    expandPlaylist: "Expand skin playlist",
    artModesAria: "Artwork variants",
    uncenteredArt: "Original",
    centeredArt: "Focus",
    animatedArt: "Animated art",
    patch: "PATCH",
    upcoming: "UPCOMING",
    upcomingPatch: "UPCOMING {version}",
    pbeNotice: "PBE",
    skinCount: "{count} skins",
    cardAria: "View artwork and details for {name}",
    cardAriaWithRarity: "View artwork and details for {name}, rarity: {rarity}",
    skinAlt: "{name} skin artwork",
    artworkUnavailable: "Artwork is temporarily unavailable",
    artworkPending: "PBE artwork pending",
    resultAll: "Filtered result: {skins} skins {versions} patches",
    loadFailed: "Load failed",
    releasePatch: "Patch {version}",
    legacyBadge: "LEGACY",
    actionChampion: "{name} Skins",
    actionSeries: "Series: {name}",
    championDetails: "{name} Skins",
    seriesDetails: "{name} Series",
    relatedSkinAria: "View artwork and details for {name}",
    rarityStandard: "Standard",
    rarityRare: "Rare",
    rarityEpic: "Epic",
    rarityLegendary: "Legendary",
    rarityMythic: "Mythic",
    rarityUltimate: "Ultimate",
    rarityTranscendent: "Transcendent",
    rarityExalted: "Exalted",
  },
};

const RARITY_ORDER = [
  "Standard",
  "Rare",
  "Epic",
  "Legendary",
  "Mythic",
  "Ultimate",
  "Transcendent",
  "Exalted",
];

const RARITY_ICON_ORIGIN = (
  "https://raw.communitydragon.org/latest/plugins/"
  + "rcp-be-lol-game-data/global/default/v1/rarity-gem-icons"
);
const RARITY_ICON_FILES = Object.freeze({
  Epic: "epic.png",
  Legendary: "legendary.png",
  Mythic: "mythic.png",
  Ultimate: "ultimate.png",
  Transcendent: "transcendent.png",
  Exalted: "exalted.png",
});
const LEGACY_ICON_URL = (
  "https://raw.communitydragon.org/latest/plugins/"
  + "rcp-fe-lol-collections/global/default/images/skins-viewer/icon-legacy.png"
);

const elements = {
  updatedAt: document.querySelector("#updated-at"),
  totalSkins: document.querySelector("#total-skins"),
  totalVersions: document.querySelector("#total-versions"),
  totalChampions: document.querySelector("#total-champions"),
  languageToggle: document.querySelector("#language-toggle"),
  languageActive: document.querySelector("#language-active"),
  languageNext: document.querySelector("#language-next"),
  themeToggle: document.querySelector("#theme-toggle"),
  search: document.querySelector("#skin-search"),
  championFilter: document.querySelector("#champion-filter"),
  seriesFilter: document.querySelector("#series-filter"),
  rarityFilter: document.querySelector("#rarity-filter"),
  legacyFilter: document.querySelector("#legacy-filter"),
  chromaFilter: document.querySelector("#chroma-filter"),
  clearFilters: document.querySelector("#clear-filters"),
  versionStrip: document.querySelector("#version-strip"),
  resultSummary: document.querySelector("#result-summary"),
  grid: document.querySelector("#skin-grid"),
  empty: document.querySelector("#empty-state"),
  error: document.querySelector("#error-panel"),
  scrollSentinel: document.querySelector("#scroll-sentinel"),
  backToTop: document.querySelector("#back-to-top"),
  siteFooter: document.querySelector("#site-footer"),
  footerDrawer: document.querySelector("#footer-drawer"),
  footerDrawerInner: document.querySelector(".footer-drawer-inner"),
  footerDrawerTriggers: [...document.querySelectorAll("[data-footer-panel-target]")],
  footerDrawerPanels: [...document.querySelectorAll("[data-footer-panel]")],
  template: document.querySelector("#skin-card-template"),
  artViewer: document.querySelector("#art-viewer"),
  artViewerClose: document.querySelector("#art-viewer-close"),
  artViewerModes: document.querySelector("#art-viewer-modes"),
  artViewerMedia: document.querySelector("#art-viewer-media"),
  artViewerCaption: document.querySelector(".art-viewer-caption"),
  artViewerImage: document.querySelector("#art-viewer-image"),
  artViewerVideo: document.querySelector("#art-viewer-video"),
  artViewerTitle: document.querySelector("#art-viewer-title"),
  artViewerMeta: document.querySelector("#art-viewer-meta"),
  artViewerActions: document.querySelector("#art-viewer-actions"),
  artViewerDetails: document.querySelector("#art-viewer-details"),
  artViewerDetailsGrid: document.querySelector("#art-viewer-details-grid"),
  artViewerPlaylist: document.querySelector("#art-viewer-playlist"),
  artViewerPlaylistHeading: document.querySelector(".art-viewer-playlist-heading"),
  artViewerPlaylistTitle: document.querySelector("#art-viewer-playlist-title"),
  artViewerPlaylistList: document.querySelector("#art-viewer-playlist-list"),
  artViewerPlaylistToggle: document.querySelector("#art-viewer-playlist-toggle"),
};

const state = {
  data: null,
  lang: "zh",
  query: "",
  champion: "all",
  series: "all",
  rarity: "all",
  legacy: "all",
  chromas: "all",
  visible: PAGE_SIZE,
  loadingMore: false,
  releaseDates: new Map(),
  upcomingVersions: new Set(),
  skinLinesById: new Map(),
};

let infiniteScrollObserver = null;
let imageLazyObserver = null;
let artViewerTrigger = null;
let activeSkin = null;
let activeArtMode = "uncentered";
let activePlaylist = null;
let activeMediaDimensions = null;
let artViewerSkinSwitchTimer = null;
let artViewerOpeningFrame = null;
let activeVersion = null;
let playlistCollapsed = false;
let trackedVersionSections = [];
let versionPositionFrame = null;
let versionActivationOffset = 82;
let backToTopFrame = null;
let activeFooterPanel = null;
let footerDrawerTrigger = null;
let viewportHeightFrame = null;

function syncVisualViewportHeight() {
  if (viewportHeightFrame !== null) cancelAnimationFrame(viewportHeightFrame);
  viewportHeightFrame = requestAnimationFrame(() => {
    viewportHeightFrame = null;
    const height = Math.max(window.innerHeight, window.visualViewport?.height || 0);
    document.documentElement.style.setProperty("--visual-viewport-height", `${height}px`);
  });
}

function t(key, values = {}) {
  const template = TRANSLATIONS[state.lang][key] || TRANSLATIONS.zh[key] || key;
  return template.replace(/\{(\w+)\}/g, (_match, name) => String(values[name] ?? ""));
}

function numberText(value) {
  return new Intl.NumberFormat(state.lang === "zh" ? "zh-CN" : "en-US").format(value);
}

function localizedCollator() {
  return new Intl.Collator(state.lang === "zh" ? "zh-CN" : "en", {
    sensitivity: "base",
    numeric: true,
  });
}

function normalized(value) {
  return String(value ?? "").normalize("NFKD").toLocaleLowerCase().replace(/\s+/g, " ").trim();
}

function comparableName(value) {
  let compact = "";
  const ranges = [];
  let offset = 0;
  for (const character of value) {
    const start = offset;
    offset += character.length;
    let normalizedCharacter = character
      .normalize("NFKC")
      .toLocaleLowerCase()
      .replace(/[’‘`´]/g, "'")
      .replace(/[•・]/g, "·");
    if (/\s/u.test(normalizedCharacter)) continue;
    for (const normalizedPart of normalizedCharacter) {
      compact += normalizedPart;
      ranges.push({ start, end: offset });
    }
  }
  return { compact, ranges };
}

function renderSkinName(target, name, champion) {
  const comparableSkin = comparableName(name);
  const comparableChampion = comparableName(champion).compact;
  const matchStart = comparableSkin.compact.indexOf(comparableChampion);
  if (matchStart === -1 || !comparableChampion) {
    target.textContent = name;
    return;
  }
  const start = comparableSkin.ranges[matchStart].start;
  const end = comparableSkin.ranges[matchStart + comparableChampion.length - 1].end;
  const championPart = document.createElement("span");
  championPart.className = "skin-name-champion";
  championPart.textContent = name.slice(start, end);
  target.append(
    document.createTextNode(name.slice(0, start)),
    championPart,
    document.createTextNode(name.slice(end)),
  );
}

function skinName(skin) {
  return state.lang === "zh" ? (skin.nameZh || skin.name) : skin.name;
}

function championName(skin) {
  return state.lang === "zh" ? (skin.championZh || skin.champion) : skin.champion;
}

function chromaName(chroma) {
  return state.lang === "zh" ? (chroma.nameZh || chroma.name) : chroma.name;
}

function cleanChromaVariantName(name) {
  return String(name || "")
    .replace(/^[\s·:：\-—–()（）]+|[\s·:：\-—–()（）]+$/g, "")
    .trim();
}

function removeChromaNamePart(name, part) {
  if (!part) return "";
  const index = name.indexOf(part);
  if (index === -1) return "";
  return cleanChromaVariantName(name.slice(0, index) + " " + name.slice(index + part.length));
}

function chromaVariantName(chroma, skin) {
  const fullName = String(chromaName(chroma) || "").trim();
  if (!fullName) return "";

  const parentheticalVariant = fullName.match(/[（(]([^()（）]+)[)）]\s*$/);
  if (parentheticalVariant) {
    return cleanChromaVariantName(parentheticalVariant[1]) || fullName;
  }

  const baseName = String(skinName(skin) || "").trim();
  const withoutBaseName = removeChromaNamePart(fullName, baseName);
  if (withoutBaseName) return withoutBaseName;

  if (state.lang === "zh") {
    const baseNameParts = baseName.split(/\s+/).filter(Boolean);
    const championProperName = baseNameParts.at(-1) || "";
    if (baseNameParts.length > 1 && championProperName) {
      const championIndex = fullName.indexOf(championProperName);
      if (championIndex !== -1) {
        const trailingVariant = cleanChromaVariantName(
          fullName.slice(championIndex + championProperName.length),
        );
        if (trailingVariant) return trailingVariant;

        const leadingVariant = cleanChromaVariantName(fullName.slice(0, championIndex));
        const baseNameWithoutChampion = cleanChromaVariantName(
          baseNameParts.slice(0, -1).join(" "),
        );
        return removeChromaNamePart(leadingVariant, baseNameWithoutChampion) || leadingVariant || fullName;
      }
    }
  }

  return fullName;
}

function skinLineName(line) {
  return state.lang === "zh" ? (line.nameZh || line.name) : line.name;
}

function rarityLabel(rarity) {
  const key = "rarity" + String(rarity || "Standard");
  return TRANSLATIONS[state.lang][key] || rarity || t("rarityStandard");
}

function rarityIconUrl(rarity) {
  const fileName = RARITY_ICON_FILES[rarity];
  return fileName ? RARITY_ICON_ORIGIN + "/" + fileName : null;
}

function getSavedLanguage() {
  try {
    return window.localStorage.getItem("league-skin-version-language");
  } catch (_error) {
    return null;
  }
}

function saveLanguage() {
  try {
    window.localStorage.setItem("league-skin-version-language", state.lang);
  } catch (_error) {
    // The URL still preserves the language when storage is unavailable.
  }
}

function currentTheme() {
  return document.documentElement.dataset.theme === "light" ? "light" : "dark";
}

function updateThemeToggle() {
  const nextThemeLabel = currentTheme() === "dark"
    ? t("switchToLightTheme")
    : t("switchToDarkTheme");
  elements.themeToggle.setAttribute("aria-label", nextThemeLabel);
  elements.themeToggle.title = nextThemeLabel;
}

function setTheme(theme, { persist = false } = {}) {
  const nextTheme = theme === "light" ? "light" : "dark";
  document.documentElement.dataset.theme = nextTheme;
  document.querySelector("meta[name='theme-color']")?.setAttribute(
    "content",
    nextTheme === "light" ? "#f4f6f8" : "#0b0d11",
  );
  updateThemeToggle();
  if (!persist) return;
  try {
    window.localStorage.setItem("league-skin-version-theme", nextTheme);
  } catch (_error) {
    // The selected theme remains active for this page when storage is unavailable.
  }
}

function readFiltersFromUrl(payload, { useSavedLanguage = false } = {}) {
  const params = new URLSearchParams(window.location.search);
  const requestedLanguage = params.get("lang") || (useSavedLanguage ? getSavedLanguage() : "zh");
  state.lang = requestedLanguage === "en" ? "en" : "zh";

  const validChampions = new Set(payload.skins.map((skin) => String(skin.championId)));
  const requestedChampion = params.get("champion");
  state.champion = validChampions.has(requestedChampion) ? requestedChampion : "all";

  const validLines = new Set(payload.skinLines.map((entry) => entry.id));
  const requestedSeries = params.get("series");
  state.series = validLines.has(requestedSeries) ? requestedSeries : "all";

  const validRarities = new Set(
    payload.skins.map((skin) => skin.rarity).filter((value) => typeof value === "string"),
  );
  const requestedRarity = params.get("rarity");
  state.rarity = validRarities.has(requestedRarity) ? requestedRarity : "all";

  const requestedLegacy = params.get("legacy");
  state.legacy = requestedLegacy === "true" || requestedLegacy === "false"
    ? requestedLegacy
    : "all";

  const requestedChromas = params.get("chromas");
  state.chromas = requestedChromas === "true" || requestedChromas === "false"
    ? requestedChromas
    : "all";
  state.query = params.get("q")?.trim() ?? "";
}

function writeFiltersToUrl() {
  const url = new URL(window.location.href);
  const setOrDelete = (name, value, defaultValue = "all") => {
    if (value && value !== defaultValue) url.searchParams.set(name, value);
    else url.searchParams.delete(name);
  };
  url.searchParams.delete("version");
  setOrDelete("champion", state.champion);
  setOrDelete("series", state.series);
  setOrDelete("rarity", state.rarity);
  setOrDelete("legacy", state.legacy);
  setOrDelete("chromas", state.chromas);
  setOrDelete("q", state.query, "");
  if (state.lang === "en") url.searchParams.set("lang", "en");
  else url.searchParams.delete("lang");
  window.history.replaceState(null, "", url);
}

function formatUpdatedAt(value) {
  const date = new Date(value);
  if (Number.isNaN(date.valueOf())) return value;
  const pad = (part) => String(part).padStart(2, "0");
  return `${date.getFullYear()}/${pad(date.getMonth() + 1)}/${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function formatPatchDate(value) {
  const date = new Date(String(value) + "T00:00:00Z");
  if (Number.isNaN(date.valueOf())) return value;
  return new Intl.DateTimeFormat(state.lang === "zh" ? "zh-CN" : "en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
    timeZone: "UTC",
  }).format(date);
}

function applyTranslations() {
  document.documentElement.lang = state.lang === "zh" ? "zh-CN" : "en";
  document.title = state.lang === "zh" ? "皮肤版本档案 · League Skin Version" : "League Skin Version";
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    node.textContent = t(node.dataset.i18n);
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((node) => {
    node.placeholder = t(node.dataset.i18nPlaceholder);
  });
  document.querySelectorAll("[data-i18n-aria-label]").forEach((node) => {
    node.setAttribute("aria-label", t(node.dataset.i18nAriaLabel));
  });
  for (const meta of document.querySelectorAll("meta[name='description'], meta[property='og:description']")) {
    meta.content = t("description");
  }
  elements.languageActive.textContent = state.lang === "zh" ? "中文" : "EN";
  elements.languageNext.textContent = state.lang === "zh" ? "EN" : "中文";
  elements.languageToggle.setAttribute("aria-label", t("switchLanguage"));
  updateThemeToggle();
  elements.artViewerMedia.dataset.errorText = viewerArtworkMessage(activeSkin);

  if (state.data) {
    const updatedAt = state.data.dataUpdatedAt;
    elements.updatedAt.textContent = updatedAt ? formatUpdatedAt(updatedAt) : "—";
    if (updatedAt) elements.updatedAt.dateTime = updatedAt;
    else elements.updatedAt.removeAttribute("datetime");
    elements.totalSkins.textContent = numberText(state.data.totalSkins);
    elements.totalVersions.textContent = numberText(state.data.versions.length);
    elements.totalChampions.textContent = numberText(state.data.totalChampions);
  } else {
    elements.updatedAt.textContent = t("loading");
  }
}

function customSelectParts(select) {
  return {
    trigger: select.querySelector(".custom-select-trigger"),
    value: select.querySelector(".custom-select-value"),
    menu: select.querySelector(".custom-select-menu"),
  };
}

function closeCustomSelect(select, { restoreFocus = false } = {}) {
  const { trigger, menu } = customSelectParts(select);
  select.classList.remove("is-open");
  trigger.setAttribute("aria-expanded", "false");
  menu.hidden = true;
  if (restoreFocus) trigger.focus({ preventScroll: true });
}

function closeAllCustomSelects(except = null) {
  for (const select of document.querySelectorAll(".custom-select.is-open")) {
    if (select !== except) closeCustomSelect(select);
  }
}

function openCustomSelect(select, { focusSelected = false } = {}) {
  closeAllCustomSelects(select);
  const { trigger, menu } = customSelectParts(select);
  if (trigger.disabled) return;
  menu.hidden = false;
  select.classList.add("is-open");
  trigger.setAttribute("aria-expanded", "true");
  const selected = menu.querySelector('[aria-selected="true"]');
  selected?.scrollIntoView({ block: "nearest" });
  if (focusSelected) (selected || menu.querySelector(".custom-select-option"))?.focus();
}

function selectCustomValue(select, selected, { emit = false } = {}) {
  const { value, menu } = customSelectParts(select);
  let selectedOption = null;
  for (const option of menu.querySelectorAll(".custom-select-option")) {
    const isSelected = option.dataset.value === selected;
    option.setAttribute("aria-selected", String(isSelected));
    option.classList.toggle("is-selected", isSelected);
    if (isSelected) selectedOption = option;
  }
  if (!selectedOption) selectedOption = menu.querySelector(".custom-select-option");
  if (!selectedOption) return;
  select.dataset.value = selectedOption.dataset.value;
  value.textContent = selectedOption.textContent;
  if (emit) {
    select.dispatchEvent(new CustomEvent("customchange", {
      detail: { value: selectedOption.dataset.value },
    }));
  }
}

function populateSelect(select, options, selected) {
  const { trigger, menu } = customSelectParts(select);
  closeCustomSelect(select);
  const optionNodes = options.map(([value, label], index) => {
    const option = document.createElement("button");
    option.type = "button";
    option.className = "custom-select-option";
    option.id = select.id + "-option-" + index;
    option.dataset.value = value;
    option.setAttribute("role", "option");
    option.setAttribute("aria-selected", "false");
    option.tabIndex = -1;
    option.textContent = label;
    return option;
  });
  menu.replaceChildren(...optionNodes);
  selectCustomValue(select, selected);
  trigger.disabled = false;
}

function setupControls() {
  elements.search.disabled = false;
  elements.search.value = state.query;

  const champions = new Map(
    state.data.skins.map((skin) => [String(skin.championId), championName(skin)]),
  );
  populateSelect(
    elements.championFilter,
    [
      ["all", t("allChampions")],
      ...[...champions].sort((left, right) => localizedCollator().compare(left[1], right[1])),
    ],
    state.champion,
  );

  const lines = [...state.data.skinLines].sort((left, right) => (
    localizedCollator().compare(skinLineName(left), skinLineName(right))
  ));
  populateSelect(
    elements.seriesFilter,
    [["all", t("allSkinLines")], ...lines.map((line) => [line.id, skinLineName(line)])],
    state.series,
  );

  const rarities = [...new Set(
    state.data.skins.map((skin) => skin.rarity).filter((value) => typeof value === "string"),
  )].sort((left, right) => {
    const leftIndex = RARITY_ORDER.indexOf(left);
    const rightIndex = RARITY_ORDER.indexOf(right);
    if (leftIndex === -1 || rightIndex === -1) return localizedCollator().compare(left, right);
    return leftIndex - rightIndex;
  });
  populateSelect(
    elements.rarityFilter,
    [["all", t("allRarities")], ...rarities.map((rarity) => [rarity, rarityLabel(rarity)])],
    state.rarity,
  );
  populateSelect(elements.legacyFilter, [
    ["all", t("allLegacy")],
    ["true", t("legacyOnly")],
    ["false", t("nonLegacy")],
  ], state.legacy);
  populateSelect(elements.chromaFilter, [
    ["all", t("allChromas")],
    ["true", t("withChromas")],
    ["false", t("withoutChromas")],
  ], state.chromas);
}

function versionTargetId(version) {
  return "version-" + version.replace(/[^a-zA-Z0-9_-]/g, "-");
}

function versionLabel(version) {
  return version === UNSCHEDULED_VERSION ? t("upcoming") : version;
}

function createVersionAnchor(version) {
  const anchor = document.createElement("a");
  anchor.className = "version-chip";
  if (version.length >= 8) anchor.classList.add("is-long-version");
  anchor.dataset.version = version;
  anchor.href = "#" + versionTargetId(version);
  if (state.upcomingVersions.has(version)) anchor.classList.add("is-upcoming");

  const label = document.createElement("span");
  label.className = "version-chip-label";
  label.textContent = versionLabel(version);
  anchor.append(label);
  return anchor;
}

function matchingSkins() {
  const terms = normalized(state.query).split(" ").filter(Boolean);
  return state.data.skins.filter((skin) => {
    if (state.champion !== "all" && String(skin.championId) !== state.champion) return false;
    if (state.series !== "all" && !skin.skinLineIds.includes(state.series)) return false;
    if (state.rarity !== "all" && skin.rarity !== state.rarity) return false;
    if (state.legacy !== "all" && String(skin.legacy) !== state.legacy) return false;
    if (state.chromas === "true" && skin.chromas.length === 0) return false;
    if (state.chromas === "false" && skin.chromas.length !== 0) return false;
    if (!terms.length) return true;

    const lineNames = skin.skinLineIds.flatMap((lineId) => {
      const line = state.skinLinesById.get(lineId);
      return line ? [line.name, line.nameZh] : [];
    });
    const haystack = normalized([
      skin.name,
      skin.nameZh,
      skin.champion,
      skin.championZh,
      skin.id,
      skin.version,
      ...lineNames,
    ].join(" "));
    return terms.every((term) => haystack.includes(term));
  });
}

function showCardArtworkPlaceholder(media, fallback, skin, displayChampion) {
  media.classList.remove("is-loading", "is-loaded");
  media.classList.add("image-missing");
  fallback.replaceChildren();
  if (skin.status === "upcoming") {
    media.classList.add("art-pending");
    fallback.classList.add("is-pbe");
    const mark = document.createElement("span");
    mark.className = "skin-fallback-mark";
    mark.textContent = "PBE";
    const note = document.createElement("span");
    note.className = "skin-fallback-note";
    note.textContent = t("artworkPending");
    fallback.append(mark, note);
    return;
  }
  fallback.classList.remove("is-pbe");
  fallback.textContent = displayChampion.slice(0, 2).toUpperCase();
}

function artworkCandidates(...sources) {
  return sources.filter((source, index, values) => (
    typeof source === "string"
    && source.length > 0
    && values.indexOf(source) === index
  ));
}

function createSkinCard(skin, index) {
  const card = elements.template.content.firstElementChild.cloneNode(true);
  const displayName = skinName(skin);
  const displayChampion = championName(skin);
  card.style.animationDelay = String(Math.min(index, 12) * 22) + "ms";
  card.tabIndex = 0;
  card.setAttribute("role", "button");
  card.setAttribute("aria-label", t("cardAria", { name: displayName }));
  if (skin.status === "upcoming") card.classList.add("is-upcoming");
  card.addEventListener("dragstart", (event) => event.preventDefault());
  card.addEventListener("click", () => openArtViewer(skin, card));
  card.addEventListener("keydown", (event) => {
    if (event.key !== "Enter" && event.key !== " ") return;
    event.preventDefault();
    openArtViewer(skin, card);
  });

  const media = card.querySelector(".skin-media");
  const image = card.querySelector("img");
  const fallback = card.querySelector(".skin-fallback");
  const portraitSources = artworkCandidates(
    skin.art?.loading,
    skin.image,
    skin.artFallback?.loading,
    skin.imageFallback,
    skin.artFallback?.uncentered,
  );
  const portraitImage = portraitSources[0] || null;
  let portraitSourceIndex = 0;
  image.loading = imageLazyObserver ? "eager" : "lazy";
  image.alt = t("skinAlt", { name: displayName });
  image.referrerPolicy = "no-referrer";
  image.addEventListener("load", () => {
    media.classList.remove("is-loading");
    media.classList.add("is-loaded");
  }, { once: true });
  image.addEventListener("error", () => {
    portraitSourceIndex += 1;
    if (portraitSources[portraitSourceIndex]) {
      image.src = portraitSources[portraitSourceIndex];
      return;
    }
    image.removeAttribute("src");
    showCardArtworkPlaceholder(media, fallback, skin, displayChampion);
  });
  if (!portraitImage) {
    showCardArtworkPlaceholder(media, fallback, skin, displayChampion);
  } else if (imageLazyObserver) {
    image.dataset.src = portraitImage;
    imageLazyObserver.observe(image);
  } else {
    media.classList.add("is-loading");
    image.src = portraitImage;
  }
  const raritySource = rarityIconUrl(skin.rarity);
  if (raritySource) {
    const rarity = card.querySelector(".skin-rarity");
    const rarityIcon = document.createElement("img");
    const displayRarity = rarityLabel(skin.rarity);
    rarity.title = displayRarity;
    rarityIcon.src = raritySource;
    rarityIcon.alt = "";
    rarityIcon.decoding = "async";
    rarityIcon.draggable = false;
    rarityIcon.referrerPolicy = "no-referrer";
    rarityIcon.width = 35;
    rarityIcon.height = 35;
    rarityIcon.addEventListener("error", () => { rarity.hidden = true; }, { once: true });
    rarity.append(rarityIcon);
    rarity.hidden = false;
    card.setAttribute("aria-label", t("cardAriaWithRarity", {
      name: displayName,
      rarity: displayRarity,
    }));
  }
  if (skin.legacy === true) {
    const legacy = card.querySelector(".skin-legacy");
    const legacyIcon = document.createElement("img");
    legacy.title = t("legacyBadge");
    legacyIcon.src = LEGACY_ICON_URL;
    legacyIcon.alt = "";
    legacyIcon.decoding = "async";
    legacyIcon.draggable = false;
    legacyIcon.referrerPolicy = "no-referrer";
    legacyIcon.width = 35;
    legacyIcon.height = 35;
    legacyIcon.addEventListener("error", () => { legacy.hidden = true; }, { once: true });
    legacy.append(legacyIcon);
    legacy.hidden = false;
  }
  if (skin.sources.length === 1) {
    const sourceTag = card.querySelector(".skin-source-tag");
    sourceTag.textContent = SOURCE_LABELS[skin.sources[0]];
    sourceTag.hidden = false;
  }
  renderSkinName(card.querySelector(".skin-name"), displayName, displayChampion);
  return card;
}

function syncVersionNavigation({ reveal = false, immediate = false } = {}) {
  if (immediate) elements.versionStrip.classList.add("is-syncing");
  let current = null;
  for (const anchor of elements.versionStrip.querySelectorAll(".version-chip")) {
    const isCurrent = anchor.dataset.version === activeVersion;
    if (isCurrent) {
      anchor.setAttribute("aria-current", "true");
      current = anchor;
    } else {
      anchor.removeAttribute("aria-current");
    }
  }
  if (reveal && current) {
    const centeredTop = current.offsetTop
      + current.offsetHeight / 2
      - elements.versionStrip.clientHeight / 2;
    const maximumTop = Math.max(
      0,
      elements.versionStrip.scrollHeight - elements.versionStrip.clientHeight,
    );
    elements.versionStrip.scrollTop = Math.min(Math.max(centeredTop, 0), maximumTop);
  }
  if (immediate) {
    elements.versionStrip.getBoundingClientRect();
    elements.versionStrip.classList.remove("is-syncing");
  }
}

function updateBackToTopVisibility() {
  backToTopFrame = null;
  const visible = window.scrollY > Math.max(window.innerHeight * 0.75, 480);
  elements.backToTop.classList.toggle("is-visible", visible);
  elements.backToTop.tabIndex = visible ? 0 : -1;
  elements.backToTop.setAttribute("aria-hidden", String(!visible));
}

function scheduleBackToTopVisibility() {
  if (backToTopFrame !== null) return;
  backToTopFrame = requestAnimationFrame(updateBackToTopVisibility);
}

function setActiveVersion(version, { reveal = false } = {}) {
  if (activeVersion === version) return;
  activeVersion = version;
  syncVersionNavigation({ reveal, immediate: true });
}

function renderVersionNavigation(groups) {
  const versions = groups.map((group) => group.version);
  if (!versions.includes(activeVersion)) activeVersion = versions[0] || null;
  elements.versionStrip.replaceChildren(...versions.map(createVersionAnchor));
  syncVersionNavigation();
}

function syncVersionFromScroll() {
  versionPositionFrame = null;
  if (!trackedVersionSections.length) {
    setActiveVersion(null);
    return;
  }
  const pageBottom = window.scrollY + window.innerHeight;
  const documentBottom = document.documentElement.scrollHeight;
  if (pageBottom >= documentBottom - 4) {
    setActiveVersion(trackedVersionSections.at(-1).dataset.version, { reveal: true });
    return;
  }

  const referenceY = versionActivationOffset;
  let low = 0;
  let high = trackedVersionSections.length - 1;
  let activeIndex = 0;
  while (low <= high) {
    const middle = Math.floor((low + high) / 2);
    if (trackedVersionSections[middle].getBoundingClientRect().top <= referenceY) {
      activeIndex = middle;
      low = middle + 1;
    } else {
      high = middle - 1;
    }
  }
  setActiveVersion(trackedVersionSections[activeIndex].dataset.version, { reveal: true });
}

function updateVersionActivationOffset() {
  const firstSection = trackedVersionSections[0];
  const sectionOffset = firstSection
    ? Number.parseFloat(getComputedStyle(firstSection).scrollMarginTop)
    : Number.NaN;
  if (Number.isFinite(sectionOffset)) {
    versionActivationOffset = sectionOffset + 1;
    return;
  }
  const barHeight = Number.parseFloat(
    getComputedStyle(document.documentElement).getPropertyValue("--site-bar-height"),
  ) || 48;
  versionActivationOffset = barHeight + 32;
}

function scheduleVersionPositionSync() {
  if (versionPositionFrame !== null) return;
  versionPositionFrame = requestAnimationFrame(syncVersionFromScroll);
}

function setupVersionSectionTracking() {
  trackedVersionSections = [...elements.grid.querySelectorAll(".version-section")];
  updateVersionActivationOffset();
  scheduleVersionPositionSync();
}

function ensureVersionRendered(version) {
  const targetId = versionTargetId(version);
  const existing = document.getElementById(targetId);
  if (existing) return existing;
  const groups = groupSkinsByVersion(matchingSkins());
  let requiredSkinCount = 0;
  for (const group of groups) {
    requiredSkinCount += group.skins.length;
    if (group.version !== version) continue;
    state.visible = Math.max(state.visible, requiredSkinCount);
    render({ append: true });
    return document.getElementById(targetId);
  }
  return null;
}

function versionFromHash() {
  if (!window.location.hash) return null;
  const anchor = [...elements.versionStrip.querySelectorAll("a[data-version]")].find(
    (candidate) => candidate.getAttribute("href") === window.location.hash,
  );
  return anchor?.dataset.version || null;
}

function scrollToHashVersion({ behavior = "auto" } = {}) {
  const version = versionFromHash();
  if (!version) return;
  const target = ensureVersionRendered(version);
  if (!target) return;
  setActiveVersion(version, { reveal: true });
  target.scrollIntoView({ behavior, block: "start" });
}

function groupSkinsByVersion(skins) {
  const groups = [];
  for (const skin of skins) {
    const current = groups.at(-1);
    if (current?.version === skin.version) current.skins.push(skin);
    else groups.push({ version: skin.version, skins: [skin] });
  }
  const collator = localizedCollator();
  for (const group of groups) {
    group.skins.sort((left, right) => (
      collator.compare(skinName(left), skinName(right))
      || String(left.id).localeCompare(String(right.id), "en", { numeric: true })
    ));
  }
  return groups;
}

function createVersionSection(group, startIndex) {
  const section = document.createElement("section");
  section.className = "version-section";
  section.dataset.version = group.version;
  section.id = versionTargetId(group.version);
  const isUpcoming = group.skins.every((skin) => skin.status === "upcoming");
  if (isUpcoming) section.classList.add("is-upcoming");

  const heading = document.createElement("div");
  heading.className = "version-section-heading";
  const title = document.createElement("h3");
  title.id = section.id + "-heading";
  const label = document.createElement("span");
  label.textContent = isUpcoming ? t("upcoming") : t("patch");
  const version = document.createElement("strong");
  version.textContent = group.version;
  const count = document.createElement("span");
  count.className = "version-skin-count";
  count.textContent = t("skinCount", { count: numberText(group.skins.length) });
  const releaseDateValue = state.releaseDates.get(group.version);
  const releaseDate = document.createElement(isUpcoming ? "span" : "time");
  releaseDate.className = "version-release-date";
  if (isUpcoming) {
    releaseDate.classList.add("upcoming-notice");
    releaseDate.textContent = t("pbeNotice");
  } else {
    releaseDate.dateTime = releaseDateValue;
    releaseDate.textContent = formatPatchDate(releaseDateValue);
  }
  title.append(label);
  if (group.version !== UNSCHEDULED_VERSION) title.append(version);
  heading.append(title, count, releaseDate);

  const grid = document.createElement("div");
  grid.className = "skin-grid";
  group.skins.forEach((skin, index) => grid.append(createSkinCard(skin, startIndex + index)));
  section.setAttribute("aria-labelledby", title.id);
  section.append(heading, grid);
  return section;
}

function hasActiveFilters() {
  return state.query
    || state.champion !== "all"
    || state.series !== "all"
    || state.rarity !== "all"
    || state.legacy !== "all"
    || state.chromas !== "all";
}

function render({ append = false } = {}) {
  if (!append && imageLazyObserver) {
    for (const image of elements.grid.querySelectorAll(".skin-card img")) {
      imageLazyObserver.unobserve(image);
    }
  }
  const matches = matchingSkins();
  const groups = groupSkinsByVersion(matches);
  if (!append) renderVersionNavigation(groups);
  const shownGroups = [];
  let shownCount = 0;
  for (const group of groups) {
    if (shownCount >= state.visible) break;
    shownGroups.push(group);
    shownCount += group.skins.length;
  }

  const fragment = document.createDocumentFragment();
  const renderedGroupCount = append ? elements.grid.children.length : 0;
  let cardIndex = append ? elements.grid.querySelectorAll(".skin-card").length : 0;
  for (const group of shownGroups.slice(renderedGroupCount)) {
    fragment.append(createVersionSection(group, cardIndex));
    cardIndex += group.skins.length;
  }
  if (append) elements.grid.append(fragment);
  else elements.grid.replaceChildren(fragment);
  elements.grid.setAttribute("aria-busy", "false");
  setupVersionSectionTracking();

  elements.resultSummary.textContent = t("resultAll", {
    skins: numberText(matches.length),
    versions: numberText(groups.length),
  });
  elements.resultSummary.hidden = !hasActiveFilters();
  elements.empty.hidden = matches.length !== 0;
  elements.scrollSentinel.hidden = shownCount >= matches.length;
  elements.scrollSentinel.setAttribute("aria-busy", "false");
  elements.clearFilters.disabled = !hasActiveFilters();
  writeFiltersToUrl();
}

function resetAndRender() {
  state.visible = PAGE_SIZE;
  state.loadingMore = false;
  elements.grid.setAttribute("aria-busy", "true");
  render();
  if (infiniteScrollObserver) {
    infiniteScrollObserver.disconnect();
    if (!elements.scrollSentinel.hidden) infiniteScrollObserver.observe(elements.scrollSentinel);
  }
}

function setupInfiniteScroll() {
  if (!("IntersectionObserver" in window)) {
    state.visible = Number.MAX_SAFE_INTEGER;
    render();
    return;
  }
  infiniteScrollObserver = new IntersectionObserver(
    (entries) => {
      if (
        !entries.some((entry) => entry.isIntersecting)
        || elements.scrollSentinel.hidden
        || state.loadingMore
      ) return;
      state.loadingMore = true;
      elements.scrollSentinel.setAttribute("aria-busy", "true");
      infiniteScrollObserver.unobserve(elements.scrollSentinel);
      requestAnimationFrame(() => {
        state.visible += PAGE_SIZE;
        render({ append: true });
        state.loadingMore = false;
        if (!elements.scrollSentinel.hidden) {
          infiniteScrollObserver.observe(elements.scrollSentinel);
        }
      });
    },
    { rootMargin: "500px 0px" },
  );
  if (!elements.scrollSentinel.hidden) infiniteScrollObserver.observe(elements.scrollSentinel);
}

function setupImageLazyLoading() {
  if (!("IntersectionObserver" in window)) return;
  imageLazyObserver = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue;
        const image = entry.target;
        imageLazyObserver.unobserve(image);
        const source = image.dataset.src;
        delete image.dataset.src;
        if (source) {
          image.closest(".skin-media")?.classList.add("is-loading");
          image.src = source;
        }
      }
    },
    { rootMargin: "500px 0px" },
  );
}

function clearViewerMedia() {
  elements.artViewerImage.onload = null;
  elements.artViewerImage.onerror = null;
  elements.artViewerImage.removeAttribute("src");
  elements.artViewerImage.hidden = true;
  elements.artViewerVideo.pause();
  elements.artViewerVideo.onloadedmetadata = null;
  elements.artViewerVideo.oncanplay = null;
  elements.artViewerVideo.onerror = null;
  elements.artViewerVideo.removeAttribute("src");
  elements.artViewerVideo.load();
  elements.artViewerVideo.hidden = true;
  elements.artViewerMedia.classList.remove("is-loading", "image-error", "art-pending");
  elements.artViewerMedia.setAttribute("aria-busy", "false");
}

function adaptArtViewerToMedia(width, height) {
  if (!Number.isFinite(width) || !Number.isFinite(height) || width <= 0 || height <= 0) return;
  activeMediaDimensions = { width, height };
  const viewportHeight = window.visualViewport?.height || window.innerHeight;
  const maximumWidth = Math.min(window.innerWidth * 0.92, 1440);
  const viewerStyle = getComputedStyle(elements.artViewer);
  const viewerBorderWidth = Number.parseFloat(viewerStyle.borderLeftWidth)
    + Number.parseFloat(viewerStyle.borderRightWidth);
  const viewerBorderHeight = Number.parseFloat(viewerStyle.borderTopWidth)
    + Number.parseFloat(viewerStyle.borderBottomWidth);
  const maximumViewerHeight = Math.max(1, viewportHeight - 32);

  const applyFit = () => {
    const captionHeight = elements.artViewerCaption.getBoundingClientRect().height;
    const detailsHeight = elements.artViewerDetails.hidden
      ? 0
      : elements.artViewerDetails.getBoundingClientRect().height;
    const nonMediaHeight = captionHeight + detailsHeight + viewerBorderHeight;
    const maximumMediaHeight = Math.max(
      1,
      Math.min(viewportHeight - 120, maximumViewerHeight - nonMediaHeight),
    );
    const maximumMediaWidth = Math.max(1, maximumWidth - viewerBorderWidth);
    const fittedMediaWidth = Math.min(
      maximumMediaWidth,
      maximumMediaHeight * (width / height),
    );
    const fittedMediaHeight = fittedMediaWidth * (height / width);
    elements.artViewer.style.setProperty(
      "--art-viewer-width",
      Math.round(fittedMediaWidth + viewerBorderWidth) + "px",
    );
    elements.artViewer.style.setProperty(
      "--art-viewer-height",
      Math.round(fittedMediaHeight + nonMediaHeight) + "px",
    );
    elements.artViewer.style.setProperty(
      "--art-media-height",
      Math.round(fittedMediaHeight) + "px",
    );
    elements.artViewer.style.setProperty("--art-media-aspect", width + " / " + height);
  };

  applyFit();
  applyFit();
  if (playlistLayerIsOpen()) positionSkinPlaylist();
}

function resetArtViewerSizing() {
  activeMediaDimensions = null;
  elements.artViewer.style.removeProperty("--art-viewer-width");
  elements.artViewer.style.removeProperty("--art-viewer-height");
  elements.artViewer.style.removeProperty("--art-media-height");
  elements.artViewer.style.removeProperty("--art-media-aspect");
}

function prepareArtViewerOpening() {
  if (artViewerOpeningFrame !== null) cancelAnimationFrame(artViewerOpeningFrame);
  artViewerOpeningFrame = null;
  elements.artViewer.classList.add("is-opening");
  elements.artViewer.setAttribute("aria-busy", "true");
}

function revealArtViewer() {
  if (!elements.artViewer.classList.contains("is-opening")) return;
  if (artViewerOpeningFrame !== null) cancelAnimationFrame(artViewerOpeningFrame);
  artViewerOpeningFrame = requestAnimationFrame(() => {
    artViewerOpeningFrame = null;
    elements.artViewer.getBoundingClientRect();
    elements.artViewer.classList.remove("is-opening");
    elements.artViewer.setAttribute("aria-busy", "false");
  });
}

function cancelArtViewerOpening() {
  if (artViewerOpeningFrame !== null) cancelAnimationFrame(artViewerOpeningFrame);
  artViewerOpeningFrame = null;
  elements.artViewer.classList.remove("is-opening");
  elements.artViewer.removeAttribute("aria-busy");
}

function prepareArtViewerSkinSwitch() {
  if (artViewerSkinSwitchTimer !== null) {
    window.clearTimeout(artViewerSkinSwitchTimer);
    artViewerSkinSwitchTimer = null;
  }
  const currentHeight = elements.artViewer.getBoundingClientRect().height;
  elements.artViewer.style.setProperty("--art-viewer-height", currentHeight + "px");
  elements.artViewer.classList.add("is-switching-skin");
}

function finishArtViewerSkinSwitch() {
  if (!elements.artViewer.classList.contains("is-switching-skin")) return;
  if (artViewerSkinSwitchTimer !== null) window.clearTimeout(artViewerSkinSwitchTimer);
  artViewerSkinSwitchTimer = window.setTimeout(() => {
    elements.artViewer.classList.remove("is-switching-skin");
    artViewerSkinSwitchTimer = null;
  }, 300);
}

function cancelArtViewerSkinSwitch() {
  if (artViewerSkinSwitchTimer !== null) window.clearTimeout(artViewerSkinSwitchTimer);
  artViewerSkinSwitchTimer = null;
  elements.artViewer.classList.remove("is-switching-skin");
}

function showViewerPlaceholder(message) {
  clearViewerMedia();
  resetArtViewerSizing();
  adaptArtViewerToMedia(
    ART_IMAGE_DIMENSIONS.uncentered.width,
    ART_IMAGE_DIMENSIONS.uncentered.height,
  );
  elements.artViewerMedia.dataset.errorText = message;
  elements.artViewerMedia.classList.add("image-error", "art-pending");
  finishArtViewerSkinSwitch();
  revealArtViewer();
}

function showViewerImage(source, fallbacks, alt, dimensions) {
  clearViewerMedia();
  elements.artViewerImage.hidden = false;
  elements.artViewerImage.alt = alt;
  elements.artViewerMedia.classList.add("is-loading");
  elements.artViewerMedia.setAttribute("aria-busy", "true");
  adaptArtViewerToMedia(dimensions.width, dimensions.height);
  revealArtViewer();
  const sources = artworkCandidates(source, ...(fallbacks || []));
  let sourceIndex = 0;
  elements.artViewerImage.onload = () => {
    elements.artViewerMedia.classList.remove("is-loading");
    elements.artViewerMedia.setAttribute("aria-busy", "false");
    finishArtViewerSkinSwitch();
  };
  elements.artViewerImage.onerror = () => {
    sourceIndex += 1;
    if (sources[sourceIndex]) {
      elements.artViewerImage.src = sources[sourceIndex];
      return;
    }
    elements.artViewerMedia.classList.remove("is-loading");
    elements.artViewerMedia.classList.add("image-error");
    elements.artViewerMedia.setAttribute("aria-busy", "false");
    finishArtViewerSkinSwitch();
    revealArtViewer();
  };
  elements.artViewerImage.src = sources[0];
}

function showViewerVideo(source) {
  clearViewerMedia();
  elements.artViewerVideo.hidden = false;
  elements.artViewerMedia.classList.add("is-loading");
  elements.artViewerMedia.setAttribute("aria-busy", "true");
  elements.artViewerVideo.onloadedmetadata = () => {
    adaptArtViewerToMedia(
      elements.artViewerVideo.videoWidth,
      elements.artViewerVideo.videoHeight,
    );
    revealArtViewer();
  };
  elements.artViewerVideo.oncanplay = () => {
    elements.artViewerMedia.classList.remove("is-loading");
    elements.artViewerMedia.setAttribute("aria-busy", "false");
    finishArtViewerSkinSwitch();
  };
  elements.artViewerVideo.onerror = () => {
    elements.artViewerMedia.classList.remove("is-loading");
    elements.artViewerMedia.classList.add("image-error");
    elements.artViewerMedia.setAttribute("aria-busy", "false");
    finishArtViewerSkinSwitch();
    revealArtViewer();
  };
  elements.artViewerVideo.src = source;
  elements.artViewerVideo.load();
  elements.artViewerVideo.play().catch(() => {});
}

function artSources(skin) {
  return {
    uncentered: (
      skin.art?.uncentered
      || skin.artFallback?.uncentered
      || skin.image
      || skin.imageFallback
    ),
    centered: (
      skin.art?.centered
      || skin.artFallback?.centered
      || skin.image
      || skin.imageFallback
    ),
    video: skin.art?.videoUncentered || skin.art?.videoCentered || null,
  };
}

function artImageDimensions(skin, mode, source) {
  for (const [variant, dimensions] of Object.entries(ART_IMAGE_DIMENSIONS)) {
    if (skin.art?.[variant] === source || skin.artFallback?.[variant] === source) {
      return dimensions;
    }
  }
  return ART_IMAGE_DIMENSIONS[mode] || ART_IMAGE_DIMENSIONS.uncentered;
}

function artImageFallbacks(skin, mode) {
  return artworkCandidates(
    skin.artFallback?.[mode],
    skin.imageFallback,
    skin.art?.loading,
    skin.artFallback?.loading,
    skin.image,
  );
}

function viewerArtworkMessage(skin) {
  if (!skin) return t("artworkUnavailable");
  const sources = artSources(skin);
  const hasArtwork = Boolean(sources.uncentered || sources.centered || sources.video);
  return skin.status === "upcoming" && !hasArtwork
    ? t("artworkPending")
    : t("artworkUnavailable");
}

function updateArtModeButtons(skin) {
  const sources = artSources(skin);
  for (const button of elements.artViewerModes.querySelectorAll("[data-view-mode]")) {
    const mode = button.dataset.viewMode;
    button.hidden = mode === "video"
      ? !sources.video
      : mode === "centered" && !sources.centered;
    button.disabled = !sources[mode];
    button.setAttribute("aria-pressed", String(mode === activeArtMode));
  }
}

function selectArtMode(mode) {
  if (!activeSkin) return;
  const sources = artSources(activeSkin);
  if (!sources[mode]) {
    showViewerPlaceholder(viewerArtworkMessage(activeSkin));
    return;
  }
  if (mode !== activeArtMode) prepareArtViewerSkinSwitch();
  activeArtMode = mode;
  renderArtViewerTitle(activeSkin);
  updateArtModeButtons(activeSkin);
  if (mode === "video") {
    showViewerVideo(sources.video);
    return;
  }
  showViewerImage(
    sources[mode],
    artImageFallbacks(activeSkin, mode),
    t("skinAlt", { name: skinName(activeSkin) }),
    artImageDimensions(activeSkin, mode, sources[mode]),
  );
}

function createMetaBadge(text, modifier = "", iconSource = null) {
  const badge = document.createElement("span");
  badge.className = "art-viewer-badge" + (modifier ? " " + modifier : "");
  if (iconSource) {
    const icon = document.createElement("img");
    icon.className = "art-viewer-badge-icon";
    icon.src = iconSource;
    icon.alt = "";
    icon.decoding = "async";
    icon.draggable = false;
    icon.referrerPolicy = "no-referrer";
    icon.addEventListener("error", () => { icon.remove(); }, { once: true });
    badge.append(icon, document.createTextNode(text));
  } else {
    badge.textContent = text;
  }
  return badge;
}

function renderArtViewerTitle(skin) {
  elements.artViewerTitle.replaceChildren();
  renderSkinName(elements.artViewerTitle, skinName(skin), championName(skin));
}

function configurePlaylistAction(button, type, key) {
  button.dataset.playlistType = type;
  button.dataset.playlistKey = String(key);
  const isActive = activePlaylist?.type === type && activePlaylist.key === String(key);
  button.setAttribute("aria-pressed", String(isActive));
}

function syncPlaylistActions() {
  for (const button of elements.artViewerActions.querySelectorAll("[data-playlist-type]")) {
    const isActive = activePlaylist?.type === button.dataset.playlistType
      && activePlaylist.key === button.dataset.playlistKey;
    button.setAttribute("aria-pressed", String(isActive));
  }
}

function renderArtViewerInfo(skin) {
  renderArtViewerTitle(skin);
  elements.artViewerMeta.replaceChildren();
  if (skin.rarity && skin.rarity !== "Standard") {
    elements.artViewerMeta.append(createMetaBadge(
      rarityLabel(skin.rarity),
      "rarity-badge",
      rarityIconUrl(skin.rarity),
    ));
  }
  if (skin.legacy === true) {
    elements.artViewerMeta.append(createMetaBadge(
      t("legacyBadge"),
      "legacy-badge",
      LEGACY_ICON_URL,
    ));
  }
  if (skin.status === "upcoming") {
    elements.artViewerMeta.append(createMetaBadge(
      skin.version === UNSCHEDULED_VERSION
        ? t("upcoming")
        : t("upcomingPatch", { version: skin.version }),
      "patch-badge upcoming-badge",
    ));
  } else {
    elements.artViewerMeta.append(createMetaBadge(
      t("releasePatch", { version: skin.version }),
      "patch-badge",
    ));
    const releaseDate = state.releaseDates.get(skin.version);
    if (releaseDate) elements.artViewerMeta.append(createMetaBadge(formatPatchDate(releaseDate)));
  }
  if (skin.sources.length === 1) {
    elements.artViewerMeta.append(createMetaBadge(
      SOURCE_LABELS[skin.sources[0]],
      "source-badge",
    ));
  }
  elements.artViewerActions.replaceChildren();
  const championKey = skin.championAlias || skin.champion;
  const championButton = document.createElement("button");
  championButton.type = "button";
  championButton.className = "art-viewer-action";
  championButton.textContent = t("actionChampion", { name: championName(skin) });
  configurePlaylistAction(championButton, "champion", championKey);
  championButton.addEventListener("click", () => showChampionPlaylist(skin));
  elements.artViewerActions.append(championButton);
  for (const lineId of skin.skinLineIds) {
    const line = state.skinLinesById.get(lineId);
    if (!line) continue;
    const button = document.createElement("button");
    button.type = "button";
    button.className = "art-viewer-action";
    button.textContent = t("actionSeries", { name: skinLineName(line) });
    configurePlaylistAction(button, "series", lineId);
    button.addEventListener("click", () => showSkinLinePlaylist(lineId));
    elements.artViewerActions.append(button);
  }
}

function relatedSkinImages(skin) {
  return artworkCandidates(
    skin.art?.tile,
    skin.art?.loading,
    skin.image,
    skin.artFallback?.tile,
    skin.artFallback?.loading,
    skin.imageFallback,
  );
}

function createRelatedSkinCard(skin) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "detail-card playlist-card";
  button.dataset.skinId = String(skin.id);
  button.setAttribute("aria-label", t("relatedSkinAria", { name: skinName(skin) }));
  const media = document.createElement("span");
  media.className = "detail-card-media";
  const sources = relatedSkinImages(skin);
  if (sources.length) {
    const image = document.createElement("img");
    image.loading = "lazy";
    image.decoding = "async";
    image.draggable = false;
    image.referrerPolicy = "no-referrer";
    let sourceIndex = 0;
    image.src = sources[sourceIndex];
    image.alt = "";
    image.addEventListener("error", () => {
      sourceIndex += 1;
      if (sources[sourceIndex]) {
        image.src = sources[sourceIndex];
        return;
      }
      image.remove();
      media.classList.add("image-missing");
      media.textContent = skin.status === "upcoming" ? "PBE" : "";
    });
    media.append(image);
  } else {
    media.classList.add("image-missing");
    media.textContent = skin.status === "upcoming" ? "PBE" : "";
  }
  const label = document.createElement("span");
  label.className = "detail-card-name";
  renderSkinName(label, skinName(skin), championName(skin));
  button.append(media, label);
  button.addEventListener("dragstart", (event) => event.preventDefault());
  button.addEventListener("click", () => setArtViewerSkin(skin, { animateResize: true }));
  return button;
}

function syncPlaylistSelection(skin) {
  for (const button of elements.artViewerPlaylistList.querySelectorAll("[data-skin-id]")) {
    const isCurrent = button.dataset.skinId === String(skin.id);
    button.classList.toggle("is-current", isCurrent);
    if (isCurrent) button.setAttribute("aria-current", "true");
    else button.removeAttribute("aria-current");
  }
}

function playlistLayerIsOpen() {
  return !elements.artViewerPlaylist.hidden;
}

function setPlaylistCollapsed(collapsed) {
  const canCollapse = elements.artViewerPlaylist.classList.contains("is-overlapping");
  playlistCollapsed = canCollapse && collapsed;
  elements.artViewerPlaylist.classList.toggle("is-collapsed", playlistCollapsed);
  elements.artViewerPlaylistToggle.setAttribute("aria-expanded", String(!playlistCollapsed));
  elements.artViewerPlaylistToggle.setAttribute(
    "aria-label",
    t(playlistCollapsed ? "expandPlaylist" : "collapsePlaylist"),
  );
  elements.artViewerPlaylistList.inert = playlistCollapsed;
  if (playlistCollapsed) elements.artViewerPlaylistList.setAttribute("aria-hidden", "true");
  else elements.artViewerPlaylistList.removeAttribute("aria-hidden");
}

function setPlaylistOverlapping(overlapping) {
  elements.artViewerPlaylist.classList.toggle("is-overlapping", overlapping);
  elements.artViewerPlaylistToggle.hidden = !overlapping;
  setPlaylistCollapsed(overlapping && playlistCollapsed);
}

function positionSkinPlaylist() {
  if (!playlistLayerIsOpen() || !elements.artViewer.open) return;
  const viewerRect = elements.artViewer.getBoundingClientRect();
  const visualViewport = window.visualViewport;
  const viewportLeft = visualViewport?.offsetLeft || 0;
  const viewportTop = visualViewport?.offsetTop || 0;
  const viewportWidth = visualViewport?.width || window.innerWidth;
  const viewportHeight = visualViewport?.height || window.innerHeight;
  const viewportRight = viewportLeft + viewportWidth;
  const viewportBottom = viewportTop + viewportHeight;
  const edge = 12;
  const gap = 12;
  const desiredWidth = Math.min(300, viewportWidth - edge * 2);
  const minimumSideWidth = 210;
  const rightSpace = viewportRight - edge - viewerRect.right - gap;
  const leftSpace = viewerRect.left - gap - (viewportLeft + edge);

  let width = desiredWidth;
  let left = viewportRight - edge - width;
  let overlapping = true;
  if (rightSpace >= minimumSideWidth) {
    width = Math.min(desiredWidth, rightSpace);
    left = viewerRect.right + gap;
    overlapping = false;
  } else if (leftSpace >= minimumSideWidth) {
    width = Math.min(desiredWidth, leftSpace);
    left = viewerRect.left - gap - width;
    overlapping = false;
  }

  elements.artViewerPlaylist.style.setProperty("--playlist-left", Math.round(left) + "px");
  elements.artViewerPlaylist.style.setProperty("--playlist-width", Math.round(width) + "px");
  setPlaylistOverlapping(overlapping);
  const availableHeight = Math.max(1, viewportHeight - edge * 2);
  const maximumHeight = Math.min(720, availableHeight);
  elements.artViewerPlaylist.style.setProperty("--playlist-max-height", Math.round(maximumHeight) + "px");
  const expandedHeight = Math.min(
    elements.artViewerPlaylistHeading.offsetHeight
      + elements.artViewerPlaylistList.scrollHeight
      + 2,
    maximumHeight,
  );
  if (overlapping) {
    elements.artViewerPlaylist.style.setProperty("--playlist-expanded-height", Math.round(expandedHeight) + "px");
  } else {
    elements.artViewerPlaylist.style.removeProperty("--playlist-expanded-height");
  }
  const renderedHeight = overlapping
    ? expandedHeight
    : Math.min(elements.artViewerPlaylist.getBoundingClientRect().height, maximumHeight);
  const top = viewportTop + Math.max(edge, (viewportHeight - renderedHeight) / 2);
  elements.artViewerPlaylist.style.setProperty("--playlist-top", Math.round(top) + "px");
}

function showSkinPlaylistLayer() {
  const playlist = elements.artViewerPlaylist;
  playlist.hidden = false;
  if (typeof playlist.showPopover === "function") {
    try {
      if (!playlist.matches(":popover-open")) playlist.showPopover();
    } catch (_error) {
      playlist.classList.add("is-fallback-open");
    }
  } else {
    playlist.classList.add("is-fallback-open");
  }
  positionSkinPlaylist();
}

function hideSkinPlaylistLayer() {
  const playlist = elements.artViewerPlaylist;
  if (typeof playlist.hidePopover === "function") {
    try {
      if (playlist.matches(":popover-open")) playlist.hidePopover();
    } catch (_error) {
      // The fallback layer is removed below.
    }
  }
  playlist.classList.remove("is-fallback-open");
  playlist.classList.remove("is-overlapping");
  setPlaylistCollapsed(false);
  elements.artViewerPlaylistToggle.hidden = true;
  playlist.hidden = true;
  for (const property of [
    "--playlist-left",
    "--playlist-top",
    "--playlist-width",
    "--playlist-max-height",
    "--playlist-expanded-height",
  ]) {
    playlist.style.removeProperty(property);
  }
}

function renderActivePlaylist() {
  if (!activePlaylist) {
    hideSkinPlaylistLayer();
    elements.artViewerPlaylistTitle.textContent = "";
    elements.artViewerPlaylistList.replaceChildren();
    syncPlaylistActions();
    return;
  }

  let title = "";
  let members = [];
  if (activePlaylist.type === "champion") {
    members = state.data.skins.filter(
      (candidate) => String(candidate.championAlias || candidate.champion) === activePlaylist.key,
    );
    const reference = members[0];
    if (reference) title = t("championDetails", { name: championName(reference) });
  } else if (activePlaylist.type === "series") {
    const line = state.skinLinesById.get(activePlaylist.key);
    if (line) {
      title = t("seriesDetails", { name: skinLineName(line) });
      members = state.data.skins.filter((skin) => skin.skinLineIds.includes(activePlaylist.key));
    }
  }

  if (!members.length) {
    closeSkinPlaylist();
    return;
  }
  members.sort((left, right) => localizedCollator().compare(skinName(left), skinName(right)));
  elements.artViewerPlaylistTitle.textContent = title;
  elements.artViewerPlaylistList.replaceChildren(...members.map(createRelatedSkinCard));
  showSkinPlaylistLayer();
  if (activeSkin) syncPlaylistSelection(activeSkin);
  syncPlaylistActions();
}

function showChampionPlaylist(skin) {
  playlistCollapsed = false;
  activePlaylist = {
    type: "champion",
    key: String(skin.championAlias || skin.champion),
  };
  renderActivePlaylist();
}

function showSkinLinePlaylist(lineId) {
  if (!state.skinLinesById.has(lineId)) return;
  playlistCollapsed = false;
  activePlaylist = { type: "series", key: String(lineId) };
  renderActivePlaylist();
}

function closeSkinPlaylist() {
  activePlaylist = null;
  hideSkinPlaylistLayer();
  elements.artViewerPlaylistTitle.textContent = "";
  elements.artViewerPlaylistList.replaceChildren();
  syncPlaylistActions();
}

function createChromaCard(chroma, skin) {
  const card = document.createElement("article");
  card.className = "detail-card chroma-card";
  const media = document.createElement("span");
  media.className = "detail-card-media chroma-card-media";
  if (chroma.image) {
    const image = document.createElement("img");
    image.loading = "lazy";
    image.decoding = "async";
    image.draggable = false;
    image.referrerPolicy = "no-referrer";
    image.src = chroma.image;
    image.alt = "";
    media.append(image);
  }
  const label = document.createElement("span");
  label.className = "detail-card-name";
  label.textContent = chromaVariantName(chroma, skin);
  const colors = document.createElement("span");
  colors.className = "chroma-colors";
  const uniqueColors = chroma.colors.filter(
    (color, index, values) =>
      values.findIndex((value) => value.toLowerCase() === color.toLowerCase()) === index,
  );
  for (const color of uniqueColors) {
    const swatch = document.createElement("span");
    swatch.style.backgroundColor = color;
    colors.append(swatch);
  }
  const meta = document.createElement("span");
  meta.className = "chroma-card-meta";
  meta.append(label, colors);
  card.append(media, meta);
  return card;
}

function renderChromaDetails(skin) {
  elements.artViewerDetailsGrid.replaceChildren(
    ...skin.chromas.map((chroma) => createChromaCard(chroma, skin)),
  );
  elements.artViewerDetails.hidden = skin.chromas.length === 0;
}

function clearChromaDetails() {
  elements.artViewerDetails.hidden = true;
  elements.artViewerDetailsGrid.replaceChildren();
}

function setArtViewerSkin(skin, { animateResize = false } = {}) {
  if (animateResize && activeSkin && String(activeSkin.id) !== String(skin.id)) {
    prepareArtViewerSkinSwitch();
  }
  activeSkin = skin;
  activeArtMode = "uncentered";
  elements.artViewerMedia.dataset.errorText = viewerArtworkMessage(skin);
  renderArtViewerInfo(skin);
  renderChromaDetails(skin);
  syncPlaylistSelection(skin);
  updateArtModeButtons(skin);
  selectArtMode("uncentered");
  elements.artViewer.scrollTop = 0;
}

function openArtViewer(skin, trigger) {
  artViewerTrigger = trigger;
  document.body.classList.add("art-viewer-open");
  if (!elements.artViewer.open) {
    prepareArtViewerOpening();
    elements.artViewer.showModal();
  }
  closeSkinPlaylist();
  setArtViewerSkin(skin);
}

function closeArtViewer() {
  if (elements.artViewer.open) elements.artViewer.close();
}

function setupArtViewer() {
  elements.artViewerClose.addEventListener("click", closeArtViewer);
  elements.artViewerModes.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-view-mode]");
    if (button) selectArtMode(button.dataset.viewMode);
  });
  elements.artViewerPlaylistToggle.addEventListener("click", () => {
    setPlaylistCollapsed(!playlistCollapsed);
  });
  elements.artViewer.addEventListener("click", (event) => {
    if (event.target === elements.artViewer) {
      closeArtViewer();
      return;
    }
    if (event.target.closest("#art-viewer-close, [data-playlist-type]")) return;
    if (playlistLayerIsOpen() && event.target.closest(".art-viewer-panel")) {
      setPlaylistCollapsed(true);
    }
  });
  elements.artViewer.addEventListener("close", () => {
    document.body.classList.remove("art-viewer-open");
    cancelArtViewerOpening();
    cancelArtViewerSkinSwitch();
    clearViewerMedia();
    resetArtViewerSizing();
    clearChromaDetails();
    closeSkinPlaylist();
    activeSkin = null;
    activeArtMode = "uncentered";
    if (artViewerTrigger?.isConnected) artViewerTrigger.focus({ preventScroll: true });
    artViewerTrigger = null;
  });
  elements.artViewer.addEventListener("transitionend", (event) => {
    if (event.target !== elements.artViewer || event.propertyName !== "width") return;
    if (!elements.artViewer.open || !activeMediaDimensions) return;
    // Caption wrapping and playlist placement depend on the settled width.
    adaptArtViewerToMedia(activeMediaDimensions.width, activeMediaDimensions.height);
    finishArtViewerSkinSwitch();
  });
  window.addEventListener("resize", () => {
    if (elements.artViewer.open && activeMediaDimensions) {
      adaptArtViewerToMedia(activeMediaDimensions.width, activeMediaDimensions.height);
    }
    if (playlistLayerIsOpen()) positionSkinPlaylist();
  });
}

function footerDrawerIsOpen() {
  return activeFooterPanel !== null;
}

function closeFooterDrawer({ restoreFocus = false } = {}) {
  if (!footerDrawerIsOpen()) return;
  elements.siteFooter.classList.remove("is-drawer-open");
  elements.footerDrawer.setAttribute("aria-hidden", "true");
  document.body.classList.remove("footer-drawer-open");
  for (const trigger of elements.footerDrawerTriggers) {
    trigger.setAttribute("aria-expanded", "false");
  }
  const triggerToRestore = footerDrawerTrigger;
  activeFooterPanel = null;
  footerDrawerTrigger = null;
  if (restoreFocus && triggerToRestore?.isConnected) {
    triggerToRestore.focus({ preventScroll: true });
  }
}

function toggleFooterDrawer(panelName, trigger) {
  if (activeFooterPanel === panelName) {
    closeFooterDrawer();
    return;
  }

  const matchingPanel = elements.footerDrawerPanels.find(
    (panel) => panel.dataset.footerPanel === panelName,
  );
  if (!matchingPanel) return;

  activeFooterPanel = panelName;
  footerDrawerTrigger = trigger;
  for (const panel of elements.footerDrawerPanels) {
    panel.hidden = panel !== matchingPanel;
  }
  for (const candidate of elements.footerDrawerTriggers) {
    candidate.setAttribute("aria-expanded", String(candidate === trigger));
  }
  elements.siteFooter.classList.add("is-drawer-open");
  elements.footerDrawer.setAttribute("aria-hidden", "false");
  document.body.classList.add("footer-drawer-open");
  elements.footerDrawerInner.scrollTop = 0;
}

function setupFooterDrawer() {
  for (const trigger of elements.footerDrawerTriggers) {
    trigger.addEventListener("click", () => {
      toggleFooterDrawer(trigger.dataset.footerPanelTarget, trigger);
    });
  }
  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape" || !footerDrawerIsOpen()) return;
    event.preventDefault();
    closeFooterDrawer({ restoreFocus: true });
  });
}

function bindFilter(select, stateKey) {
  const { trigger, menu } = customSelectParts(select);
  trigger.addEventListener("click", () => {
    if (select.classList.contains("is-open")) closeCustomSelect(select);
    else openCustomSelect(select);
  });
  trigger.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && select.classList.contains("is-open")) {
      event.preventDefault();
      closeCustomSelect(select);
      return;
    }
    if (event.key !== "ArrowDown" && event.key !== "ArrowUp") return;
    event.preventDefault();
    openCustomSelect(select, { focusSelected: true });
  });
  menu.addEventListener("click", (event) => {
    const option = event.target.closest(".custom-select-option");
    if (!option) return;
    selectCustomValue(select, option.dataset.value, { emit: true });
    closeCustomSelect(select, { restoreFocus: true });
  });
  menu.addEventListener("keydown", (event) => {
    const options = [...menu.querySelectorAll(".custom-select-option")];
    const current = options.indexOf(document.activeElement);
    let next = null;
    if (event.key === "ArrowDown") next = Math.min(current + 1, options.length - 1);
    if (event.key === "ArrowUp") next = Math.max(current - 1, 0);
    if (event.key === "Home") next = 0;
    if (event.key === "End") next = options.length - 1;
    if (event.key === "Escape") {
      event.preventDefault();
      closeCustomSelect(select, { restoreFocus: true });
      return;
    }
    if (next === null) return;
    event.preventDefault();
    options[next]?.focus();
    options[next]?.scrollIntoView({ block: "nearest" });
  });
  select.addEventListener("customchange", (event) => {
    state[stateKey] = event.detail.value;
    resetAndRender();
  });
  select.addEventListener("focusout", () => {
    requestAnimationFrame(() => {
      if (!select.contains(document.activeElement)) closeCustomSelect(select);
    });
  });
}

function bindEvents() {
  document.addEventListener("click", (event) => {
    if (!event.target.closest(".custom-select")) closeAllCustomSelects();
    if (footerDrawerIsOpen() && !elements.siteFooter.contains(event.target)) {
      closeFooterDrawer();
    }
  });
  window.addEventListener("scroll", () => {
    scheduleVersionPositionSync();
    scheduleBackToTopVisibility();
  }, { passive: true });
  window.addEventListener("resize", () => {
    syncVisualViewportHeight();
    updateVersionActivationOffset();
    scheduleVersionPositionSync();
    scheduleBackToTopVisibility();
  });
  window.visualViewport?.addEventListener("resize", syncVisualViewportHeight, { passive: true });
  elements.backToTop.addEventListener("click", () => {
    const behavior = window.matchMedia("(prefers-reduced-motion: reduce)").matches
      ? "auto"
      : "smooth";
    const url = new URL(window.location.href);
    url.hash = "";
    window.history.replaceState(null, "", url);
    window.scrollTo({ top: 0, behavior });
  });
  scheduleBackToTopVisibility();
  elements.search.addEventListener("input", (event) => {
    state.query = event.currentTarget.value.trim();
    resetAndRender();
  });
  elements.search.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && state.query) {
      event.currentTarget.value = "";
      state.query = "";
      resetAndRender();
    }
  });
  bindFilter(elements.championFilter, "champion");
  bindFilter(elements.seriesFilter, "series");
  bindFilter(elements.rarityFilter, "rarity");
  bindFilter(elements.legacyFilter, "legacy");
  bindFilter(elements.chromaFilter, "chromas");
  elements.versionStrip.addEventListener("click", (event) => {
    const anchor = event.target.closest("a[data-version]");
    if (!anchor) return;
    setActiveVersion(anchor.dataset.version, { reveal: true });
    if (document.getElementById(versionTargetId(anchor.dataset.version))) return;
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    const target = ensureVersionRendered(anchor.dataset.version);
    if (!target) return;
    window.history.pushState(null, "", anchor.href);
    target.scrollIntoView({ behavior: "smooth", block: "start" });
  });
  window.addEventListener("popstate", () => {
    const keys = ["lang", "query", "champion", "series", "rarity", "legacy", "chromas"];
    const previous = keys.map((key) => state[key]);
    readFiltersFromUrl(state.data);
    const languageChanged = state.lang !== previous[0];
    if (keys.some((key, index) => state[key] !== previous[index])) {
      if (languageChanged) applyTranslations();
      setupControls();
      resetAndRender();
    }
    if (languageChanged && activeSkin && elements.artViewer.open) {
      setArtViewerSkin(activeSkin);
      renderActivePlaylist();
    }
    scrollToHashVersion();
  });
  elements.clearFilters.addEventListener("click", () => {
    state.query = "";
    state.champion = "all";
    state.series = "all";
    state.rarity = "all";
    state.legacy = "all";
    state.chromas = "all";
    setupControls();
    resetAndRender();
  });
  elements.languageToggle.addEventListener("click", () => {
    state.lang = state.lang === "zh" ? "en" : "zh";
    saveLanguage();
    applyTranslations();
    setupControls();
    resetAndRender();
    if (activeSkin && elements.artViewer.open) {
      setArtViewerSkin(activeSkin);
      renderActivePlaylist();
    }
  });
  elements.themeToggle.addEventListener("click", () => {
    setTheme(currentTheme() === "dark" ? "light" : "dark", { persist: true });
  });
  setupFooterDrawer();
}

function validatePayload(payload) {
  return payload
    && payload.schemaVersion === 4
    && (payload.dataUpdatedAt === null || typeof payload.dataUpdatedAt === "string")
    && Array.isArray(payload.versions)
    && payload.versions.every((entry) => (
      typeof entry.version === "string"
      && typeof entry.releaseDate === "string"
      && /^\d{4}-\d{2}-\d{2}$/.test(entry.releaseDate)
    ))
    && Array.isArray(payload.skinLines)
    && Array.isArray(payload.upcoming)
    && payload.upcoming.every((entry) => (
      typeof entry.version === "string"
      && Number.isInteger(entry.count)
      && entry.count >= 0
    ))
    && Array.isArray(payload.skins)
    && payload.skins.every((skin) => (
      typeof skin.id === "string"
      && typeof skin.name === "string"
      && typeof skin.nameZh === "string"
      && Array.isArray(skin.skinLineIds)
      && Array.isArray(skin.chromas)
      && Array.isArray(skin.sources)
      && skin.sources.every((source) => source in SOURCE_LABELS)
      && typeof skin.art === "object"
      && (skin.status === "released" || skin.status === "upcoming")
    ))
    && typeof payload.totalSkins === "number"
    && typeof payload.totalChampions === "number";
}

async function initialize() {
  syncVisualViewportHeight();
  try {
    const dataUrl = new URL("./data/skins.json", import.meta.url);
    const response = await fetch(dataUrl, { cache: "no-cache" });
    if (!response.ok) throw new Error("HTTP " + response.status);
    const payload = await response.json();
    if (!validatePayload(payload)) throw new Error("Unsupported data schema");
    state.data = payload;
    state.releaseDates = new Map(
      payload.versions.map((entry) => [entry.version, entry.releaseDate]),
    );
    state.upcomingVersions = new Set(payload.upcoming.map((entry) => entry.version));
    state.skinLinesById = new Map(payload.skinLines.map((entry) => [entry.id, entry]));
    readFiltersFromUrl(payload, { useSavedLanguage: true });
    setupImageLazyLoading();
    applyTranslations();
    setupControls();
    setupArtViewer();
    bindEvents();
    render();
    setupInfiniteScroll();
    requestAnimationFrame(() => scrollToHashVersion());
  } catch (error) {
    console.error("Failed to initialize skin archive", error);
    applyTranslations();
    elements.grid.setAttribute("aria-busy", "false");
    elements.resultSummary.textContent = t("loadFailed");
    elements.resultSummary.hidden = false;
    elements.error.hidden = false;
  }
}

initialize();
