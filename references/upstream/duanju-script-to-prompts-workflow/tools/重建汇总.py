#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重建《{PROJECT_NAME}》全部汇总产物。
用法：python3 项目开发/重建汇总.py
输入：剧集/EP*/图片提示词.md（唯一真源）
输出：图片提示词索引.md、全剧资产总清单.md、全剧生成清单.xlsx、
      全剧提示词合集-去重版.md/.docx、合集分册/*.md
"""
import re, glob, os, sys, json

PROJECT_NAME = '萌娃心声'  # ← 换新项目时只改这一行（标题/合集名会全部跟着变）
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
TAIL = 'soft film grain。'


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


def collect():
    files = sorted(glob.glob('剧集/EP*/图片提示词.md'))
    cards, per_ep = {}, []
    for f in files:
        ep = re.search(r'(EP\d+)', f).group(1)
        t = open(f, encoding='utf-8').read()
        parts = re.split(r'^## (IMG-[A-Z0-9\-]+) · (.+)$', t, flags=re.M)
        for i in range(1, len(parts) - 1, 3):
            cid, name, body = parts[i], parts[i + 1].strip(), parts[i + 2].split('\n## ')[0]
            m = re.search(r'### 可复制提示词\s*\n(.*?)(?:\n## |\Z)', body, re.S)
            if not m:
                continue
            prompt = '\n'.join(l.rstrip() for l in m.group(1).split('\n') if l.strip().startswith('>'))
            note = ''
            mm = re.search(r'【图外标注】(.+)', body)
            if mm:
                note = re.split(r'[；。]\s*(?:HEX|视觉单元|色板|色板取样)', mm.group(1))[0]
                note = re.sub(r'\s+', ' ', note).strip('；; 。')[:100]
            cards[cid] = dict(id=cid, name=name, ep=ep, type=classify(cid, name),
                              body=prompt, note=note, refs=set())
        per_ep.append((ep, len(re.findall(r'^## IMG-', t, re.M)),
                       len(re.findall(r'^\| IMG-', t, re.M)), t))
    # 引用集（正文任意位置出现即算被用）
    for ep, _, _, t in per_ep:
        for cid in cards:
            if cid in t:
                cards[cid]['refs'].add(ep)
    for v in cards.values():
        v['refs'] = sorted(v['refs'] or {v['ep']}, key=lambda x: int(x[2:]))
    order = {'人物·身份基准': 0, '人物·状态变体': 1, '人物·Q版形态': 2, '人物·群像': 3, '场景': 4, '道具': 5}
    A = sorted(cards.values(), key=lambda v: (order[v['type']], int(v['ep'][2:]), v['id']))
    return A, per_ep


def fmt(uses):
    ep = [int(u[2:]) for u in uses]
    lab = ['原创' if x == 0 else str(x) for x in ep]
    return '、'.join(lab) if len(lab) <= 10 else f'{lab[0]}…{lab[-1]}（共{len(lab)}集）'


TITLES = {'人物·身份基准': '第一部分 · 人物身份基准', '人物·状态变体': '第二部分 · 人物状态变体',
          '人物·Q版形态': '第三部分 · Q版形态', '人物·群像': '第三部分之二 · 群像卡', '场景': '第四部分 · 场景', '道具': '第五部分 · 道具'}
PRIO = lambda v: ('A 必生' if ('身份基准' in v['type'] or v['type'] == '场景')
                  else 'B 高频（≥4集）' if len(v['refs']) >= 4
                  else 'C 中频（2-3集）' if len(v['refs']) >= 2 else 'D 单集专用')


def write_index(A, per_ep):
    L = ['# 《{PROJECT_NAME}》全剧图片提示词索引', '',
         f'> 共 {len(per_ep)} 集、{len(A)} 张去重资产。画风：3D 国漫半写实｜16:9｜4K。', '',
         '| 集 | 本集新卡 | 清单行数 | 文件 |', '|---|---|---|---|']
    for ep, n_new, n_row, _ in per_ep:
        L.append(f'| {ep} | {n_new} | {n_row} | 剧集/{ep}/图片提示词.md |')
    open('图片提示词索引.md', 'w', encoding='utf-8').write('\n'.join(L) + '\n')


def write_master(A):
    g = lambda t: [v for v in A if v['type'] == t]
    base, var, q, loc, prp = g('人物·身份基准'), g('人物·状态变体'), g('人物·Q版形态'), g('场景'), g('道具')
    L = ['# 《{PROJECT_NAME}》全剧资产总清单（去重版）', '',
         '> 由各集《图片提示词》逐卡合并：**同一资产只出现一次**。「首出集」= 卡正文所在那一集；「引用集」= 剧本里实际用到该卡的全部集。', '',
         '## 一、要生成多少张', '', '| 类别 | 数量 | 口径 |', '|---|---|---|',
         f'| 人物·身份基准 | **{len(base)}** | 必生：一人一张，定死长相 |',
         f'| 人物·状态变体 | **{len(var)}** | 按需：同一张脸换造型/状态/年龄 |',
         f'| 人物·Q版形态 | **{len(q)}** | 按需：剧本标（Q版）才用 |',
         f'| 场景 | **{len(loc)}** | 必生：一个地点一张（四格视角） |',
         f'| 道具 | **{len(prp)}** | 按需：反复出镜的实物 |',
         f'| **合计** | **{len(A)}** | 全剧只生这 {len(A)} 张 |', '']

    def tab(title, rows, extra=''):
        L.append(f'## {title}\n')
        if extra:
            L.append(extra + '\n')
        L.append('| 编号 | 名称 | 首出集 | 引用集数 | 用于（集） | 锁定要点 |')
        L.append('|---|---|---|---|---|---|')
        for v in rows:
            L.append(f"| {v['id']} | {v['name']} | {v['ep'][2:]} | {len(v['refs'])} | {fmt(v['refs'])} | {v['note'].replace('|', '／')} |")
        L.append('')
    tab('二、人物 · 身份基准（必生）', base, '一人一卡，先出这批，所有变体靠它锁脸。')
    tab('三、人物 · 状态变体（按需）', var, '卡内【基准锁定】写明沿用哪张身份卡。')
    tab('四、人物 · Q版形态（按需）', q)
    tab('五、场景（必生）', loc, '同一地点只出一次，四格视角。')
    tab('六、道具（按需）', prp)
    open('全剧资产总清单.md', 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    return base, var, q, loc, prp


def write_promptbook(A):
    L = ['# 《{PROJECT_NAME}》全剧图片提示词合集（去重版 · 直接复制）', '',
         f'> 全剧所有卡去重后的**完整可复制正文**，共 **{len(A)}** 张。`用于` 列出该卡在剧本里被引用的集。', '',
         '> 画风：3D 国漫半写实｜16:9 横屏｜4K｜渲染尾逐字 `3D Chinese animation style，semi-realistic，high-end CG，studio lighting，soft film grain`', '',
         '> 用法：找到要出图的那张 → 复制它的提示词整段 → 贴进出图工具。变体卡的【基准锁定】行说明这张脸沿用哪张身份卡。', '',
         '## 目录', '']
    cur = None
    for v in A:
        if v['type'] != cur:
            cur = v['type']
            L.append(f'\n**{TITLES[cur]}**\n')
            L.append('| 编号 | 名称 | 首出集 | 用于（集） |')
            L.append('|---|---|---|---|')
        L.append(f"| {v['id']} | {v['name']} | {v['ep'][2:]} | {fmt(v['refs'])} |")
    L.append('')
    cur = None
    for v in A:
        if v['type'] != cur:
            cur = v['type']
            L.append(f'\n---\n\n# {TITLES[cur]}\n')
        L.append(f"## {v['id']} · {v['name']}\n")
        L.append(f"> 首出：{v['ep']}｜用于：{fmt(v['refs'])}｜类型：{v['type']}\n")
        L.append(v['body'] + '\n')
    md = '\n'.join(L) + '\n'
    open('全剧提示词合集-去重版.md', 'w', encoding='utf-8').write(md)

    # 分册
    os.makedirs('合集分册', exist_ok=True)
    names = {'人物·身份基准': '01_人物身份基准', '人物·状态变体': '02_人物状态变体',
             '人物·Q版形态': '03_Q版形态', '人物·群像': '03B_群像卡', '场景': '04_场景', '道具': '05_道具'}
    for t, fn in names.items():
        rows = [v for v in A if v['type'] == t]
        parts = [f'# 《{PROJECT_NAME}》{TITLES[t].split("· ")[-1]}（{len(rows)} 张）', '',
                 '> 取自全剧去重合集。复制每张的提示词整段直接用。', '']
        for v in rows:
            parts.append(f"## {v['id']} · {v['name']}\n")
            parts.append(f"> 首出：{v['ep']}｜用于：{fmt(v['refs'])}\n")
            parts.append(v['body'] + '\n')
        open(f'合集分册/{fn}.md', 'w', encoding='utf-8').write('\n'.join(parts) + '\n')

    # docx
    try:
        from docx import Document
        from docx.shared import Pt
        d = Document()
        d.styles['Normal'].font.name = 'PingFang SC'
        d.styles['Normal'].font.size = Pt(10)
        d.add_heading('《{PROJECT_NAME}》全剧图片提示词合集（去重版）', 0)
        d.add_paragraph(f'共 {len(A)} 张，按「身份基准 → 状态变体 → Q版 → 场景 → 道具」排列。画风：3D 国漫半写实｜16:9｜4K。')
        for t in ['人物·身份基准', '人物·状态变体', '人物·Q版形态', '人物·群像', '场景', '道具']:
            rows = [v for v in A if v['type'] == t]
            if not rows:
                continue
            d.add_heading(f'{TITLES[t]}（{len(rows)} 张）', 1)
            for v in rows:
                d.add_heading(f"{v['id']} · {v['name']}", 2)
                d.add_paragraph(f"首出：{v['ep']}｜用于：{fmt(v['refs'])}")
                for l in v['body'].split('\n'):
                    para = d.add_paragraph(l.lstrip('> ').strip())
                    para.paragraph_format.space_after = Pt(3)
        d.save('全剧提示词合集-去重版.docx')
    except Exception as e:  # docx 缺失不阻塞其他产物
        print('docx 跳过:', e)


def write_xlsx(A, per_ep, groups):
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill
    H = Font(bold=True, color='FFFFFF')
    F = PatternFill('solid', fgColor='2F5597')
    wb = Workbook()
    ws = wb.active
    ws.title = '汇总'
    ws.append(['类别', '数量', '口径'])
    base, var, q, loc, prp = groups
    for r in [('人物·身份基准', len(base), '必生'), ('人物·状态变体', len(var), '按需'),
              ('人物·Q版形态', len(q), '按需'), ('场景', len(loc), '必生'),
              ('道具', len(prp), '按需'), ('合计', len(A), '')]:
        ws.append(list(r))
    for c in ws[1]:
        c.font, c.fill = H, F
    for i, w in enumerate([22, 10, 10], 1):
        ws.column_dimensions[chr(64 + i)].width = w

    def sh(title, rows):
        s = wb.create_sheet(title)
        s.append(['编号', '名称', '类型', '首出集', '引用集数', '用于（集）', '优先级', '锁定要点', '已生成√'])
        for v in rows:
            s.append([v['id'], v['name'], v['type'], v['ep'][2:], len(v['refs']),
                      fmt(v['refs']), PRIO(v), v['note'][:100], ''])
        for c in s[1]:
            c.font, c.fill = H, F
        for i, w in enumerate([20, 32, 16, 8, 9, 22, 18, 55, 10], 1):
            s.column_dimensions[chr(64 + i)].width = w
        s.freeze_panes = 'A2'
        s.auto_filter.ref = s.dimensions
    sh('人物_身份基准', base)
    sh('人物_状态变体', var)
    sh('人物_Q版', q)
    sh('场景', loc)
    sh('道具', prp)
    s = wb.create_sheet('按集进度')
    s.append(['集', '本集新卡', '清单行数', '本集已全部生成√'])
    for ep, n_new, n_row, _ in per_ep:
        s.append([ep, n_new, n_row, ''])
    for c in s[1]:
        c.font, c.fill = H, F
    for i, w in enumerate([8, 12, 14, 18], 1):
        s.column_dimensions[chr(64 + i)].width = w
    s.freeze_panes = 'A2'
    wb.save('全剧生成清单.xlsx')


if __name__ == '__main__':
    A, per_ep = collect()
    bad = [v['id'] for v in A if TAIL not in v['body']]
    if bad:
        print('⚠️ 缺渲染尾:', bad[:10])
        sys.exit(1)
    write_index(A, per_ep)
    groups = write_master(A)
    write_promptbook(A)
    write_xlsx(A, per_ep, groups)
    from collections import Counter
    c = Counter(v['type'] for v in A)
    print(f'✅ 重建完成：{len(per_ep)} 集 / {len(A)} 张', dict(c))
