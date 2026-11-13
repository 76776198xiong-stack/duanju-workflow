#!/usr/bin/env python3
"""全季《图片提示词》去重汇总：一份清单 + 可勾选 xlsx + 提示词合集与分册。

用法：python3 build_asset_aggregate.py <项目根目录>
前提：剧集/EPxxx/图片提示词.md 已按样板产出（卡标题 `## IMG-... · 名称`，
      正文在 `### 可复制提示词` 下的 `>` 引用块里）。
产物（写入项目根目录）：全剧资产总清单.md / 全剧生成清单.xlsx /
      全剧提示词合集-去重版.md(.docx) / 合集分册/01..05
"""
import glob
import json
import os
import re
import sys

SUFFIX = r'(地点板|道具板|身份板|形态板|状态板|造型板|对照板)'
ORDER = {'人物·身份基准': 0, '人物·状态变体': 1, '人物·Q版形态': 2, '场景': 3, '道具': 4}
TITLES = {'人物·身份基准': '人物身份基准（必生）', '人物·状态变体': '人物状态变体（按需）',
          '人物·Q版形态': 'Q版形态（按需）', '场景': '场景（必生）', '道具': '道具（按需）'}
FILES = {'人物·身份基准': '01_人物身份基准', '人物·状态变体': '02_人物状态变体',
         '人物·Q版形态': '03_Q版形态', '场景': '04_场景', '道具': '05_道具'}


def classify(cid, name):
    if '-C' in cid:
        if 'Q版' in name:
            return '人物·Q版形态'
        return '人物·身份基准' if '身份' in name else '人物·状态变体'
    return '场景' if '-L' in cid else '道具'


def fmt(uses, limit=10):
    ep = [int(u[2:]) for u in uses]
    if not ep:
        return ''
    return '、'.join(map(str, ep)) if len(ep) <= limit else f'{ep[0]}…{ep[-1]}（共{len(ep)}集）'


def clean_note(note):
    note = re.split(r'[；。]\s*(?:HEX|视觉单元|色板|色板取样)', note)[0]
    return re.sub(r'\s+', ' ', note).strip('；; 。')[:90]


def collect(root):
    files = sorted(glob.glob(os.path.join(root, '剧集', 'EP*', '图片提示词.md')))
    cards, mentions = {}, {}
    for path in files:
        ep = re.search(r'(EP\d+)', path).group(1)
        text = open(path, encoding='utf-8').read()
        for m in re.finditer(r'^## (IMG-[A-Z0-9\-]+) · (.+)$', text, re.M):
            cid, name = m.group(1), m.group(2).strip()
            body = text[m.end():].split('\n## ')[0]
            block = re.search(r'### 可复制提示词\s*\n(.*?)(?:\n## |\Z)', body, re.S)
            prompt = '\n'.join(l.rstrip() for l in (block.group(1) if block else '').split('\n')
                                if l.strip().startswith('>'))
            note = ''
            mm = re.search(r'【图外标注】(.+)', body)
            if mm:
                note = clean_note(mm.group(1))
            cards[cid] = {'id': cid, 'name': name, 'debut': ep,
                          'type': classify(cid, name), 'note': note, 'prompt': prompt}
        for cid in re.findall(r'IMG-[A-Z0-9]+-[CLP]\d+', text):
            mentions.setdefault(cid, set()).add(ep)
    for cid, card in cards.items():
        uses = sorted(mentions.get(cid, {card['debut']}), key=lambda x: int(x[2:]))
        card['uses'] = uses
        n = len(uses)
        card['pri'] = ('A 必生' if ('身份基准' in card['type'] or card['type'] == '场景')
                       else 'B 高频（≥4集）' if n >= 4
                       else 'C 中频（2-3集）' if n >= 2 else 'D 单集专用')
    out = sorted(cards.values(), key=lambda v: (ORDER[v['type']], int(v['debut'][2:]), v['id']))
    return out, files


def check(cards, files):
    ids = {c['id'] for c in cards}
    dangling = sorted({i for c in cards for i in re.findall(r'IMG-[A-Z0-9]+-[CLP]\d+', c['prompt']) if i not in ids})
    names = {}
    for c in cards:
        names.setdefault(re.sub(SUFFIX + '$', '', c['name']), []).append(c['id'])
    dups = {k: v for k, v in names.items() if len(v) > 1}
    print(f'去重体检 · 悬空引用: {dangling or "无"}')
    print(f'去重体检 · 疑似重名: {dups or "无"}')


def write_md(root, cards):
    lines = ['# 全剧资产总清单（去重版）\n',
             '> 每张卡只出现一次。「首出集」= 卡正文所在集；「引用集」= 该编号在剧本里被引用的全部集（含变体卡的【基准锁定】）。\n']
    stats = {t: [c for c in cards if c['type'] == t] for t in ORDER}
    lines += ['## 要生成多少张\n', '| 类别 | 数量 |', '|---|---|']
    for t, rows in stats.items():
        lines.append(f'| {TITLES[t]} | **{len(rows)}** |')
    lines.append(f'| 合计 | **{len(cards)}** |')
    lines.append('')
    for t, rows in stats.items():
        lines += [f'## {TITLES[t]}\n', '| 编号 | 名称 | 首出集 | 引用集数 | 用于（集） | 锁定要点 |',
                  '|---|---|---|---|---|---|']
        for c in rows:
            lines.append(f"| {c['id']} | {c['name']} | {c['debut'][2:]} | {len(c['uses'])} | "
                         f"{fmt(c['uses'])} | {c['note'].replace('|', '／')} |")
        lines.append('')
    lines += ['## 生成顺序建议\n',
              '1. 先出「地基约 10 张」：主角团身份基准 + 主要府邸正厅/外景。',
              '2. 场景全量一次定死（场景返工代价最高）。',
              '3. 其余身份基准随集推进。',
              '4. 变体 / Q版 / 道具跟分镜走，台词里点名的才生。']
    open(os.path.join(root, '全剧资产总清单.md'), 'w', encoding='utf-8').write('\n'.join(lines) + '\n')


def write_xlsx(root, cards, files):
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill
    except ImportError:
        print('未装 openpyxl，跳过 xlsx'); return
    head, fill = Font(bold=True, color='FFFFFF'), PatternFill('solid', fgColor='2F5597')
    wb = Workbook()
    ws = wb.active; ws.title = '汇总'; ws.append(['类别', '数量', '口径'])
    for t in ORDER:
        ws.append([TITLES[t], len([c for c in cards if c['type'] == t]),
                   '必生' if ORDER[t] in (0, 3) else '按需'])
    ws.append(['合计', len(cards), ''])
    for cell in ws[1]:
        cell.font, cell.fill = head, fill
    for title in ORDER:
        rows = [c for c in cards if c['type'] == title]
        if not rows:
            continue
        s = wb.create_sheet(FILES[title][3:])
        s.append(['编号', '名称', '类型', '首出集', '引用集数', '用于（集）', '优先级', '锁定要点', '已生成√'])
        for c in rows:
            s.append([c['id'], c['name'], c['type'], c['debut'][2:], len(c['uses']),
                      fmt(c['uses']), c['pri'], c['note'][:100], ''])
        for cell in s[1]:
            cell.font, cell.fill = head, fill
        for i, w in enumerate([20, 30, 16, 8, 9, 20, 18, 55, 10], 1):
            s.column_dimensions[chr(64 + i)].width = w
        s.freeze_panes, s.auto_filter.ref = 'A2', s.dimensions
    s = wb.create_sheet('按集进度')
    s.append(['集', '本集新卡', '清单行数', '本集已全部生成√'])
    for path in files:
        ep = re.search(r'(EP\d+)', path).group(1)
        text = open(path, encoding='utf-8').read()
        s.append([ep, len(re.findall(r'^## IMG-', text, re.M)),
                  len(re.findall(r'^\| IMG-', text, re.M)), ''])
    for cell in s[1]:
        cell.font, cell.fill = head, fill
    s.freeze_panes = 'A2'
    wb.save(os.path.join(root, '全剧生成清单.xlsx'))


def write_compendium(root, cards):
    parts = ['# 全剧图片提示词合集（去重版 · 直接复制）\n',
             f'> 共 {len(cards)} 张。找到要出图的那张，复制它整段正文即可；变体卡的【基准锁定】行写明沿用哪张身份基准卡。\n',
             '## 目录\n']
    cur = None
    for c in cards:
        if c['type'] != cur:
            cur = c['type']
            parts.append(f'\n**{TITLES[cur]}**\n')
            parts.append('| 编号 | 名称 | 首出集 | 用于（集） |')
            parts.append('|---|---|---|---|')
        parts.append(f"| {c['id']} | {c['name']} | {c['debut'][2:]} | {fmt(c['uses'])} |")
    cur = None
    for c in cards:
        if c['type'] != cur:
            cur = c['type']
            parts.append(f'\n---\n\n# {TITLES[cur]}\n')
        parts.append(f"## {c['id']} · {c['name']}\n")
        parts.append(f"> 首出：{c['debut']}｜用于：{fmt(c['uses'])}｜类型：{c['type']}\n")
        parts.append(c['prompt'] + '\n')
    text = '\n'.join(parts) + '\n'
    open(os.path.join(root, '全剧提示词合集-去重版.md'), 'w', encoding='utf-8').write(text)

    sub = os.path.join(root, '合集分册')
    os.makedirs(sub, exist_ok=True)
    chunks = re.split(r'\n---\n\n# ', text)
    for chunk in chunks[1:]:
        title = chunk.split('\n', 1)[0].strip()
        body = chunk.split('\n', 1)[1] if '\n' in chunk else ''
        key = next((t for t in ORDER if TITLES[t] == title), None)
        if not key:
            continue
        n = len(re.findall(r'^## IMG-', body, re.M))
        open(os.path.join(sub, FILES[key] + '.md'), 'w', encoding='utf-8').write(
            f'# 《全剧》{title}\n\n> 取自全剧去重合集，共 {n} 张；复制每张的正文整段直接用。\n' + body)
    try:
        from docx import Document
        from docx.shared import Pt
    except ImportError:
        print('未装 python-docx，跳过 docx'); return
    doc = Document()
    doc.styles['Normal'].font.size = Pt(10)
    doc.add_heading('全剧图片提示词合集（去重版）', 0)
    doc.add_paragraph(f'共 {len(cards)} 张，按人物身份基准 → 状态变体 → Q版 → 场景 → 道具排列。')
    for chunk in chunks[1:]:
        title = chunk.split('\n', 1)[0].strip()
        doc.add_heading(title, 1)
        for block in re.split(r'\n## ', chunk.split('\n', 1)[1]):
            block = block.strip()
            if not block.startswith('IMG-'):
                continue
            rows = block.split('\n')
            doc.add_heading(rows[0], 2)
            for line in rows[1:]:
                line = line.strip().lstrip('> ').strip()
                if line:
                    doc.add_paragraph(line).paragraph_format.space_after = Pt(3)
    doc.save(os.path.join(root, '全剧提示词合集-去重版.docx'))


def main():
    root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else '.')
    cards, files = collect(root)
    if not cards:
        sys.exit('没读到任何 IMG 卡，检查剧集/EPxxx/图片提示词.md 是否存在')
    check(cards, files)
    write_md(root, cards)
    write_xlsx(root, cards, files)
    write_compendium(root, cards)
    from collections import Counter
    print('合计', len(cards), dict(Counter(c['type'] for c in cards)))
    print('产物：全剧资产总清单.md / 全剧生成清单.xlsx / 全剧提示词合集-去重版.md(.docx) / 合集分册/')


if __name__ == '__main__':
    main()
