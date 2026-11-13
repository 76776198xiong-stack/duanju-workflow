#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成「可直接框选复制」的纯文本卡片合集（回到 EP001 分段格式，但去掉 Markdown）。
用法：python3 项目开发/导出可复制合集.py
输出：
  全剧提示词-可复制版.txt        （205 张，一张一区块）
  可复制版/01_人物身份基准.txt … 05_道具.txt
"""
import re, glob, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
PROJECT_NAME = '萌娃心声'  # ← 换新项目时只改这一行（标题/合集名会全部跟着变）
ORDER = ['人物·身份基准', '人物·状态变体', '人物·Q版形态', '人物·群像', '场景', '道具']
LABEL_OF_FILE = {'人物·身份基准': '01_人物身份基准', '人物·状态变体': '02_人物状态变体',
                 '人物·Q版形态': '03_Q版形态', '人物·群像': '03B_群像卡', '场景': '04_场景', '道具': '05_道具'}
DIV = '═' * 58
THIN = '─' * 58


def classify(cid, name):
    if '-C' in cid:
        if ('群像' in name) or ('对照板' in name):
            return '人物·群像'
        if 'Q版' in name:
            return '人物·Q版形态'
        if '身份' in name:
            return '人物·身份基准'
        return '人物·状态变体'
    return '场景' if '-L' in cid else '道具'


def clean_label(line):
    """【基础规格与全局构图】xxx  →  基础规格与全局构图：xxx"""
    s = line.replace('**', '')
    s = re.sub(r'`([^`]*)`', r'\1', s)
    m = re.match(r'^【([^】]{2,30})】\s*(.*)$', s)
    if m:
        return m.group(1).rstrip('：') + '：' + m.group(2)
    return s.replace('：：', '：')


def collect():
    cards = {}
    for f in sorted(glob.glob('剧集/EP*/图片提示词.md')):
        ep = re.search(r'(EP\d+)', f).group(1)
        t = open(f, encoding='utf-8').read()
        for m in re.finditer(r'^## (IMG-[A-Z0-9\-]+) · (.+)$', t, re.M):
            cid, name = m.group(1), m.group(2).strip()
            body = t[m.end():].split('\n## ')[0]
            pm = re.search(r'### 可复制提示词\s*\n(.*?)(?:\n## |\Z)', body, re.S)
            if not pm:
                continue
            lines = [l.strip().lstrip('>').strip() for l in pm.group(1).split('\n') if l.strip().startswith('>')]
            lines = [clean_label(l) for l in lines if l and '【图外标注】' not in l]
            cards[cid] = dict(id=cid, name=name, ep=ep, type=classify(cid, name), lines=lines, refs=set())
    for f in sorted(glob.glob('剧集/EP*/图片提示词.md')):
        ep = re.search(r'(EP\d+)', f).group(1)
        t = open(f, encoding='utf-8').read()
        for cid in cards:
            if cid in t:
                cards[cid]['refs'].add(ep)
    for v in cards.values():
        v['refs'] = sorted(v['refs'] or {v['ep']}, key=lambda x: int(x[2:]))
    return sorted(cards.values(), key=lambda v: (ORDER.index(v['type']), int(v['ep'][2:]), v['id']))


def lab_ep(x):
    return '原创' if int(x[2:]) == 0 else str(int(x[2:]))


def fmt_refs(u):
    ep = [int(x[2:]) for x in u]
    lab = ['原创' if x == 0 else str(x) for x in ep]
    return '、'.join(lab) if len(lab) <= 10 else f'{lab[0]}…{lab[-1]}（{len(lab)}集）'


def block(v):
    debut = '原创补充' if v['ep'] == 'EP000' else v['ep']
    head = [DIV, f"{v['id']} · {v['name']}",
            f"首出 {debut}｜用于 {fmt_refs(v['refs'])}｜{v['type']}", THIN]
    body = []
    for l in v['lines']:
        body.append(l)
        body.append('')          # 每段后空一行，便于逐段看也便于整段全选
    return '\n'.join(head + body).rstrip() + '\n'


def main():
    A = collect()
    n = {k: len([v for v in A if v['type'] == k]) for k in ORDER}
    toc = [PROJECT_NAME + ' · 全剧图片提示词（可复制版）', DIV,
           f'共 {len(A)} 张：人物身份基准 {n["人物·身份基准"]}｜人物状态变体 {n["人物·状态变体"]}｜Q版 {n["人物·Q版形态"]}｜场景 {n["场景"]}｜道具 {n["道具"]}',
           '画幅 16:9｜4K｜3D 国漫半写实＋画风锁（禁真人质感）｜渲染尾逐字 3D Chinese animation style，semi-realistic，high-end CG，studio lighting，soft film grain。',
           '用法：找到要出的那张卡，从 ═ 线下方第一行选中到最后一行「负向提示词：…」整段复制；工具有单独负向框就只贴「负向提示词」那一段。',
           THIN, '目　录', '']
    cur = None
    for v in A:
        if v['type'] != cur:
            cur = v['type']
            toc.append(f'—— {cur} ——')
        toc.append(f"{v['id']}  {v['name']}   （首出 {v['ep'][2:]}｜{len(v['refs'])} 集）")
    out = ['\n'.join(toc), '']
    cur = None
    for v in A:
        if v['type'] != cur:
            cur = v['type']
            out.append('\n' + DIV + '\n' + DIV + f'\n　　　{cur}（{n[cur]} 张）\n' + DIV + '\n')
        out.append(block(v))
    open('全剧提示词-可复制版.txt', 'w', encoding='utf-8').write('\n'.join(out))

    os.makedirs('可复制版', exist_ok=True)
    for k in ORDER:
        rows = [v for v in A if v['type'] == k]
        parts = [PROJECT_NAME + f' · {k}（{len(rows)} 张 · 可复制版）', DIV,
                 '画幅 16:9｜4K｜3D 国漫半写实＋画风锁（禁真人质感）', THIN]
        for v in rows:
            parts.append(block(v))
        open(f'可复制版/{LABEL_OF_FILE[k]}.txt', 'w', encoding='utf-8').write('\n'.join(parts))
    print(f'✅ 可复制版已生成：全剧提示词-可复制版.txt（{len(A)} 张，{round(os.path.getsize("全剧提示词-可复制版.txt")/1024)} KB）＋ 可复制版/ 五份')


if __name__ == '__main__':
    main()
