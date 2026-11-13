# 参考资料

## 已有的资产卡工作流（快照）

`upstream/duanju-script-to-prompts-workflow/` 是 [1476560380-eng/duanju-script-to-prompts-workflow](https://github.com/1476560380-eng/duanju-script-to-prompts-workflow) 在提交 `a76223e` 的完整拷贝，共 31 个文件，内容未改动。逐文件校验值见 `upstream/duanju-script-to-prompts-workflow.snapshot.json`。

它覆盖的范围是"剧本 → 资产提示词卡"：切集、盘点人物/场景/道具、分批写卡、登记去重、格式校验、导出。它自称在《萌娃心声》59 集上产出了 215 张卡。它不生成图片，也不包含分镜和视频。

这套东西和朋友现在的日常流程是什么关系，还没问清楚，见[待确认问题](../docs/04-待确认问题.md)第 11 条。

| 先读 | 内容 |
|---|---|
| [工作流.md](upstream/duanju-script-to-prompts-workflow/工作流.md) | 完整流程和返工经验 |
| [批量生产 Skill](upstream/duanju-script-to-prompts-workflow/skills/duanju-batch-image-prompts/SKILL.md) | 经验最多的一份：调度、返工、背景板、群像 |
| [tools/使用说明.md](upstream/duanju-script-to-prompts-workflow/tools/使用说明.md) | 四个导出脚本的用法 |

### 值得继承的做法

- **一物一卡**：同一个角色、场景、道具全剧只定义一次，后续集引用，换装和年龄变化作为变体挂在基准卡下。
- **唯一真源**：正文只在一处维护，索引、清单、导出文件全部由脚本生成。
- **不信汇报信文件**：子任务说"写完了"不算，要检查磁盘上的文件。
- **返工经验**：比如"只换颜色用户会觉得没改""整洁要逐条列出来，否则模型会加戏成凌乱"。这些可以直接写进新的审查规则。

### 读代码发现的问题

以下是读代码得出的，没有实际运行验证。

| 问题 | 位置 | 说明 |
|---|---|---|
| 中文集号识别不了 | 工作流.md 的切集正则 `^第\s*\d+\s*集` | 只认阿拉伯数字。原稿若写"第七集"会被漏掉，文档里"原稿缺第 7 集"可能就是这么来的 |
| 精简版负向词写死 | `tools/导出兼容版.py` 的 `neg_core` | 所有卡共用一串负向词，其中有"孕肚""Q版""第二人物"。孕态卡、Q版卡、群像卡会被自己的负向词否定 |
| 重建会清空进度 | `tools/重建汇总.py` | 每次新建 xlsx 并覆盖同名文件，不读取旧文件，手工打的"已生成√"会丢 |
| 查不出同集重复编号 | `scripts/qa_markdown_cards.py` 的 `split_cards` | 先按编号存进字典，同编号的卡互相覆盖，之后的重复检查看不到 |

新系统不打算直接沿用这几个脚本，所以这些问题只作记录，不安排修复。
