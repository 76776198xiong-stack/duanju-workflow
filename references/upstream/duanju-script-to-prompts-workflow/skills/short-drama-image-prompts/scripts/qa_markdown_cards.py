#!/usr/bin/env python3
"""校验批量生产的《图片提示词.md》卡片是否与样板口径一致。

用法：
    python3 scripts/qa_markdown_cards.py <项目根目录> [--tail "<渲染尾原句>"]

默认扫描 <根目录>/剧集/EP*/图片提示词.md。只做机械项（存在性/计数/唯一性），
文字质量仍由创作者审。退出码 0 = 全过，1 = 有错，2 = 用法/路径错误。
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

DEFAULT_TAIL = (
    "3D Chinese animation style，semi-realistic，high-end CG，"
    "studio lighting，soft film grain。"
)
CARD_RE = re.compile(r"^## (IMG-[A-Za-z0-9\-]+) \u00b7 (.+)$", re.M)
ROWS_RE = re.compile(r"^\|\s*(IMG-[A-Za-z0-9\-]+)\s*\|", re.M)
COUNT_RE = re.compile(r"## 本集资产清单（\s*(\d+)\s*张卡）")
HEX_RE = re.compile(r"#[0-9A-Fa-f]{6}\b")
EP_RE = re.compile(r"^(EP\d{3,})")


def split_cards(text: str) -> dict[str, str]:
    """返回 {IMG 编号: 该卡正文段}。以 '## IMG-' 标题切分。"""
    starts = [(m.start(), m.group(1)) for m in CARD_RE.finditer(text)]
    cards: dict[str, str] = {}
    for index, (pos, cid) in enumerate(starts):
        end = starts[index + 1][0] if index + 1 < len(starts) else len(text)
        cards[cid] = text[pos:end]
    return cards


def check_episode(path: Path, tail: str) -> tuple[list[str], dict[str, str], int]:
    text = path.read_text(encoding="utf-8")
    ep = EP_RE.match(path.parent.name)
    ep_id = ep.group(1) if ep else path.parent.name
    problems: list[str] = []

    if f"# {ep_id} 本集图片提示词" not in text:
        problems.append(f"缺标题 '# {ep_id} 本集图片提示词'")
    if "## 本集资产清单" not in text:
        problems.append("缺 '## 本集资产清单' 段")

    rows = ROWS_RE.findall(text)
    declared = COUNT_RE.search(text)
    if declared:
        if int(declared.group(1)) != len(rows):
            problems.append(
                f"清单表头写 {declared.group(1)} 张，实际 {len(rows)} 行"
            )
    elif rows:
        problems.append("有清单行但没有「## 本集资产清单（N 张卡）」表头")

    cards = split_cards(text)
    bodies: dict[str, str] = {}
    for cid, seg in cards.items():
        if not cid.startswith(f"IMG-{ep_id}-"):
            problems.append(f"{cid}: 正文卡编号不属于本集（沿用资产不得写正文）")
            continue
        bodies[cid] = seg
        if "- 参考：" not in seg:
            problems.append(f"{cid}: 缺 '- 参考：' 行")
        tail_hits = seg.count(tail)
        if tail_hits != 1:
            problems.append(f"{cid}: 渲染尾出现 {tail_hits} 次（应为 1）")
        if "【负向提示词】" not in seg:
            problems.append(f"{cid}: 缺【负向提示词】段")
        if re.search(r"IMG-[A-Za-z0-9\-]*-C\d", cid) and "AI演员声明" not in seg:
            problems.append(f"{cid}: 人物卡缺 AI演员声明整句")
        hexes = set(HEX_RE.findall(seg))
        if len(hexes) < 5:
            problems.append(f"{cid}: HEX 色板只有 {len(hexes)} 色（应≥5）")

    duplicated = {cid for cid in cards if list(cards).count(cid) > 1}
    if duplicated:
        problems.append(f"编号重复：{', '.join(sorted(duplicated))}")

    return problems, bodies, len(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="校验批量图片提示词卡片")
    parser.add_argument("root", nargs="?", default=".", help="项目根目录")
    parser.add_argument("--tail", default=DEFAULT_TAIL, help="渲染尾原句（逐字）")
    args = parser.parse_args()

    root = Path(args.root).expanduser()
    files = sorted((root / "剧集").glob("EP*/图片提示词.md"))
    if not files:
        print(f"找不到 {root}/剧集/EP*/图片提示词.md", file=sys.stderr)
        return 2

    errors = 0
    seen_names: dict[str, list[str]] = defaultdict(list)
    total_bodies = 0
    for path in files:
        problems, bodies, rows = check_episode(path, args.tail)
        total_bodies += len(bodies)
        for cid in bodies:
            seen_names[cid].append(path.parent.name)
        mark = "OK " if not problems else "ERR"
        print(f"[{mark}] {path.parent.name}: 正文卡 {len(bodies)} / 清单行 {rows}")
        for problem in problems[:8]:
            print(f"       - {problem}")
        errors += len(problems)

    # 同一编号在多集都写了正文 = 同一资产被重复出卡（并行波次的典型症状）
    duplicated = {cid: eps for cid, eps in seen_names.items() if len(eps) > 1}
    for cid, eps in sorted(duplicated.items()):
        print(f"[WARN] {cid} 在 {', '.join(eps)} 都写了正文 —— 保留先落盘一张，其余改沿用")

    print(
        f"\n共 {len(files)} 集，{total_bodies} 张正文卡，"
        f"机械错误 {errors} 项，重复卡 {len(duplicated)} 组"
    )
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
