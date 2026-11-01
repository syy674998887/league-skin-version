# League Skin Version

[English](README.md)

一个按发布补丁浏览 League of Legends 皮肤的静态档案。

League Skin Version 是非官方、非商业社区项目，未获得 Riot Games 认可或赞助。

[在线浏览](https://syy674998887.github.io/league-skin-version/)

## 功能

- 按发布补丁归档正式皮肤，并显示对应补丁日期；PBE 待上线皮肤单独展示。
- 皮肤详情只显示该款皮肤的 Wiki 上线日期，即将上线的皮肤标为“预计上线”；PATCH 标题右侧只显示补丁上线日期。对应日期缺失时不显示，不互相替代。
- 检索中英文英雄名、皮肤名和稳定 ID，并按英雄、系列、等级、Legacy 状态和炫彩进行筛选；等级和 Legacy 筛选的选项及当前值显示对应图标。
- 桌面筛选栏按实际可用宽度自动排列，搜索框占两列；手机端保持两列或单列布局。
- 筛选菜单按上下可用空间选择展开方向，并随滚动和视口变化调整；打开皮肤详情时先收起页脚说明面板，鼠标和键盘操作一致。
- 提供响应式界面、浅色与深色主题、原始／聚焦／加载界面图片切换（按图片加载后的真实宽高比调整窗口）、炫彩、英雄与系列关联列表，以及可用的动态内容。
- 名称中的英雄名按完整名称及英文单词边界强调；筛选统计只计算正式版本。Legacy 状态和炫彩名称提供读屏描述，版本跳转遵循减少动态效果设置，恢复浅色主题时同步浏览器主题色。
- 等级／Legacy 图标加载失败时回退为文字；炫彩图加载失败时沿用浏览器的破图标记和替代文字，保留名称和色块；没有图片地址时留空。
- 已匹配的皮肤通过“视频↗”按钮直达 SkinSpotlights 视频；悬停显示原视频标题，未匹配的皮肤不显示按钮。

## 数据

| 来源 | 用途 |
| --- | --- |
| [League of Legends Wiki](https://wiki.leagueoflegends.com/en-us/) | 发布版本、补丁日期、即将上线皮肤的补丁号（来自 VPBE 与即将发布的补丁页面），以及带修订版本的静态原画 |
| [CommunityDragon](https://github.com/CommunityDragon) | 稳定 ID、客户端及本地化名称、系列、等级、Legacy、炫彩、回退与动态原画、任务皮肤阶段，以及未发布皮肤的 PBE 目录 |

仓库维护以下生成的数据文件：

| 文件 | 内容 |
| --- | --- |
| `skin_ids.json` | 直接由 CommunityDragon 英文客户端目录生成；映射顶层皮肤及炫彩 ID 到当前展示名称，不包含任务皮肤阶段形态 |
| `skin_versions.json` | 正式皮肤 ID 到发布补丁的映射 |
| `patch_dates.json` | 已记录补丁到发布日期的映射 |
| `skin_assets.json` | 每款正式皮肤四种带修订版本的 Wiki 原画记录 |
| `skin_spotlights.json` | SkinSpotlights 公开视频编号与标题，独立于皮肤上线数据 |

Upcoming 数据在正式发布前可能变更、延期或取消。每次构建都会列出 CommunityDragon PBE 目录，以及 Wiki 的 VPBE 和即将发布补丁页面中所有尚未发布的皮肤；Wiki 列出后显示其补丁号，在此之前显示为 Upcoming。Upcoming 只写入 Pages 构建产物，与正式历史分离，也不计入档案统计。

只有一方收录的皮肤，卡片左上角和详情中会显示 **Wiki** 或 **CDragon** 标签。例如已从游戏客户端移除的正式皮肤，只保留 Wiki 的名称和原画，并显示 Wiki 标签。

## 本地运行

需要 Python 3.10 或更高版本，以及 [uv](https://docs.astral.sh/uv/)。在仓库根目录运行：

```console
uv sync
uv run site-build
uv run python -m http.server 8000 --directory dist
```

打开 <http://localhost:8000>。`site-build` 读取本地正式数据，从 Wiki 与 CommunityDragon 获取当前 Upcoming 数据和元数据，并将静态网页写入已忽略的 `dist/` 目录。

## 更新数据

联网同步并更新四份数据文件：

```console
uv run skin-update
```

更新器先验证完整的候选快照，再原子替换有变化的文件。内容不变则不重写，也不会静默删除已有的正式皮肤历史。运行 `uv run skin-update --help` 可查看输出路径与网络选项。

视频目录单独运行 `uv run python -B -m league_skin_version.spotlights` 更新，然后重新构建。按皮肤英文全名匹配，统一标点，并在完整名称匹配之后识别重做年份注记；不同至臻年份版本保持独立，不做模糊匹配。优先最新完整展示，其次预发布预览。2026-10-31 联网更新后的本地站点共 1,970 条记录，匹配 1,750 条，其中 25 条为预览，220 条不显示视频按钮。

首次目录使用 `yt-dlp --ignore-config --no-cache-dir --flat-playlist --skip-download -J https://www.youtube.com/@SkinSpotlights/videos` 读取频道公开视频标题和编号；该 JSON 输出可通过 `uv run python -B -m league_skin_version.spotlights --import-catalog PATH` 重新导入。yt-dlp 仅为可选的完整导入工具，不是项目依赖。日常更新读取无需密钥的公开频道订阅源，目前仅返回最近 15 条上传；长时间中断或集中大量上传时，可能需要重新完整导入。订阅源不能自动识别旧视频被删除或转为私密。

## 自动化

[`Update data and deploy Pages`](.github/workflows/pages.yml) 工作流负责更新与部署：

| 触发方式 | 行为 |
| --- | --- |
| 手动运行 | 同步数据、运行测试、构建网页、提交有变化的 JSON 并部署 Pages |
| 每天 12:34（`America/New_York`） | 运行测试、构建网页并部署 Pages；距离上次成功在线同步达到 20 小时时，还会同步并提交数据 |
| 推送到 `main` | 运行测试、获取当前 Upcoming 快照、构建网页并部署 Pages，不修改仓库数据 |

20 小时间隔取自 Actions 中成功的数据同步运行，排除未执行同步的运行和仅部署代码的运行。网页的「更新」采用该运行中数据同步步骤的完成时间，只写入部署产物；`generatedAt` 仍是内部构建时间。普通本地构建不显示更新时间；手动联网同步成功后，可通过 `LSV_DATA_UPDATED_AT` 将实际同步完成时间写入本地产物。成功检查但数据未变化时，仍刷新网页，不产生 bot 提交。

需要同步数据时，另一个独立步骤会刷新 SkinSpotlights 目录，并提交有变化的视频数据。频道更新失败保留已保存目录，不阻断皮肤同步与部署；构建只匹配本地视频目录，不请求 YouTube。

如果 League Wiki 已列出 CommunityDragon 尚未发布的补丁，定时和手动同步会等待：该次运行留下提示并照常部署网页，但不修改数据，也不计为数据同步，下一次定时运行会自动重试。

## 开发

运行测试：

```console
uv run python -B -m unittest discover -s tests -q
```

项目运行时仅使用 Python 标准库。

## 许可

原创代码与文档采用 [MIT License](LICENSE)。第三方数据、游戏内容、原画、视频、名称和商标不因此重新授权；详见[第三方声明](THIRD_PARTY_NOTICES.md)。
