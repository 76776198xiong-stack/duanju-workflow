# 参考资料与材料清单

朋友一共给了三样东西。

| 材料 | 在哪 | 状态 |
|---|---|---|
| 他的 GitHub 仓库 | `upstream/duanju-script-to-prompts-workflow/`（完整快照） | 已读 |
| 压缩包"做漫剧分镜" | 只在负责人本地 | **待 Codex 清点**，索引写入本目录的 `材料索引.md` |
| 两份七海画布的文件 | 只在负责人本地 | **待 Codex 清点**。这是朋友在别人那里看到、觉得不错的参考，不是他自己的流程 |

压缩包和七海画布文件的原件不提交到本仓库（本仓库是公开的），只提交索引。

## 朋友的 GitHub 仓库

来源：[1476560380-eng/duanju-script-to-prompts-workflow](https://github.com/1476560380-eng/duanju-script-to-prompts-workflow)，提交 `a76223e`，共 31 个文件，内容未改动。2026-11-13 核对时原仓库仍是这个版本。逐文件校验值见 `upstream/duanju-script-to-prompts-workflow.snapshot.json`。

它覆盖的范围是"剧本 → 资产提示词卡"：切集、盘点人物/场景/道具、分批写卡、登记去重、格式校验、导出。仓库自述在《萌娃心声》59 集上产出了 215 张卡。

它**不包含**：分镜工作提示词、视频工作提示词，也不生成图片。2026-11-13 把 31 个文件逐个查过，换任何叫法都没有。审查方面只有一份针对资产提示词的审查量表（`skills/short-drama-image-prompts/references/review-and-fixtures.md`）和几个格式检查脚本。

**重要**：仓库里的主技能 `short-drama-image-prompts` 来自开源套件 drama-skills，那个套件里有分镜、视频提示词、审查、生产、剪辑等另外 11 个技能。见[开源套件 drama-skills](开源套件-drama-skills.md)。

| 先读 | 内容 |
|---|---|
| [工作流.md](upstream/duanju-script-to-prompts-workflow/工作流.md) | 完整流程和返工经验 |
| [批量生产 Skill](upstream/duanju-script-to-prompts-workflow/skills/duanju-batch-image-prompts/SKILL.md) | 经验最多的一份：调度、返工、背景板、群像 |
| [出卡总纲 Skill](upstream/duanju-script-to-prompts-workflow/skills/short-drama-image-prompts/SKILL.md) | 卡的格式、参考图绑定 |
| [tools/使用说明.md](upstream/duanju-script-to-prompts-workflow/tools/使用说明.md) | 四个导出脚本的用法 |

### 一处对不上的地方

仓库里的流程是用本地 Agent 跑的：多个子代理并行、读写本地文件、运行 Python 脚本。而朋友的日常做法是 Gemini 网页版手动复制粘贴。这两者是什么关系，需要问朋友，见[待确认问题](../docs/04-待确认问题.md)。

### 值得继承的做法

- **一物一卡**：同一个角色、场景、道具全剧只定义一次，后续集引用，换装和年龄变化作为变体挂在基准卡下。
- **唯一真源**：正文只在一处维护，索引、清单、导出文件全部由脚本生成。
- **不信汇报信文件**：子任务说"写完了"不算，要检查磁盘上的文件。
- **返工经验**：比如"只换颜色用户会觉得没改""整洁要逐条列出来，否则模型会加戏成凌乱""整张重画必换脸，保脸靠图生图"。

### 读代码发现的问题

以下是读代码得出的，没有实际运行验证。

| 问题 | 位置 | 说明 |
|---|---|---|
| 中文集号识别不了 | 工作流.md 的切集正则 `^第\s*\d+\s*集` | 只认阿拉伯数字。原稿若写"第七集"会被漏掉，文档里"原稿缺第 7 集"可能就是这么来的 |
| 精简版负向词写死 | `tools/导出兼容版.py` 的 `neg_core` | 所有卡共用一串负向词，其中有"孕肚""Q版""第二人物"。孕态卡、Q版卡、群像卡会被自己的负向词否定 |
| 重建会清空进度 | `tools/重建汇总.py` | 每次新建 xlsx 并覆盖同名文件，不读取旧文件，手工打的"已生成√"会丢 |
| 查不出同集重复编号 | `scripts/qa_markdown_cards.py` 的 `split_cards` | 先按编号存进字典，同编号的卡互相覆盖，之后的重复检查看不到 |
