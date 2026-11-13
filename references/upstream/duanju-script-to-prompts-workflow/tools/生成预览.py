#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成可在浏览器/聊天里预览的提示词页：全剧提示词预览.html
用法：python3 项目开发/生成预览.py
输入：剧集/EP*/图片提示词.md（唯一真源）
"""
import re, glob, os, html, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

PROJECT_NAME = '萌娃心声'  # ← 换新项目时只改这一行（标题/合集名会全部跟着变）
ORDER = ['人物·身份基准', '人物·状态变体', '人物·Q版形态', '人物·群像', '场景', '道具']


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
            cards[cid] = dict(id=cid, name=name, ep=ep, type=classify(cid, name),
                              lines=lines, refs=set())
    for f in sorted(glob.glob('剧集/EP*/图片提示词.md')):
        ep = re.search(r'(EP\d+)', f).group(1)
        t = open(f, encoding='utf-8').read()
        for cid in cards:
            if cid in t:
                cards[cid]['refs'].add(ep)
    for v in cards.values():
        v['refs'] = sorted(v['refs'] or {v['ep']}, key=lambda x: int(x[2:]))
    return sorted(cards.values(), key=lambda v: (ORDER.index(v['type']), int(v['ep'][2:]), v['id']))


def fmt_refs(u):
    ep = [int(x[2:]) for x in u]
    return '、'.join(map(str, ep)) if len(ep) <= 10 else f'{ep[0]}…{ep[-1]}（{len(ep)}集）'


def md_inline(s):
    s = html.escape(s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'`(.+?)`', r'<code>\1</code>', s)
    return s


def build(A):
    n = {k: len([v for v in A if v['type'] == k]) for k in ORDER}
    total = len(A)
    rows = []
    sep = '\n\n'
    for v in A:
        blocks = [md_inline(l) for l in v['lines'] if l]
        body = ''.join('<p>' + b + '</p>' for b in blocks)
        copy_txt = ''
        search_blob = html.escape((v['id'] + ' ' + v['name'] + ' ' + v['ep'] + ' ' + ' '.join(v['lines'])[:240]).lower(), quote=True)
        tag = v['type'].split('·')[-1]
        rows.append(
            '<details class="card" data-type="' + v['type'] + '" data-search="' + search_blob + '">\n'
            '<summary><span class="id">' + v['id'] + '</span><span class="nm">' + html.escape(v['name']) + '</span>\n'
            '<span class="meta">首出 ' + v['ep'][2:] + '｜用于 ' + fmt_refs(v['refs']) + '</span>'
            '<span class="tag">' + tag + '</span></summary>\n'
            '<div class="prompt">' + body + '</div>\n'
            '<div class="actions"><button class="copy">复制这段提示词</button>'
            '<span class="hint">点开可读全文，复制后直接贴进出图工具</span></div>\n'
            '</details>')

    chips = ''.join(f'<button class="chip" data-f="{k}">{k.split("·")[-1]} <em>{n[k]}</em></button>' for k in ORDER)
    return f'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>{PROJECT_NAME} · 提示词预览</title>
<style>
:root{{color-scheme:light dark}}
*{{box-sizing:border-box}}
body{{margin:0;font-family:var(--font,system-ui,-apple-system,"PingFang SC","Microsoft YaHei"),sans-serif;color:var(--foreground,#e8e8ea);background:transparent}}
header{{position:sticky;top:0;z-index:5;padding:14px 16px 10px;background:color-mix(in srgb,var(--card,#15161a) 88%,transparent);backdrop-filter:blur(8px);border-bottom:1px solid var(--border,#2a2b31)}}
h1{{margin:0 0 4px;font-size:17px;font-weight:650;letter-spacing:.02em}}
.sub{{font-size:12px;color:var(--muted-foreground,#9aa0a6)}}
.bar{{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px;align-items:center}}
input[type=search]{{flex:1 1 240px;min-width:180px;padding:8px 10px;border:1px solid var(--border,#2a2b31);border-radius:9px;background:transparent;color:inherit;font-size:13px}}
.chip{{padding:5px 10px;border:1px solid var(--border,#2a2b31);border-radius:999px;background:transparent;color:inherit;font-size:12px;cursor:pointer}}
.chip em{{font-style:normal;color:var(--muted-foreground,#9aa0a6);margin-left:2px}}
.chip.on{{border-color:var(--accent,#4c8bf5);color:var(--accent,#4c8bf5)}}
.list{{padding:10px 12px 18px;max-height:66vh;overflow:auto}}
.card{{border:1px solid var(--border,#2a2b31);border-radius:11px;margin:0 0 8px;padding:0 12px;background:color-mix(in srgb,var(--card,#15161a) 60%,transparent)}}
.card summary{{list-style:none;cursor:pointer;display:flex;gap:10px;align-items:baseline;flex-wrap:wrap;padding:10px 0}}
.card summary::-webkit-details-marker{{display:none}}
.id{{font:600 12px/1 ui-monospace,SFMono-Regular,Menlo,monospace;color:var(--accent,#4c8bf5)}}
.nm{{font-size:14px;font-weight:600}}
.meta{{font-size:11.5px;color:var(--muted-foreground,#9aa0a6)}}
.tag{{margin-left:auto;font-size:11px;padding:2px 8px;border:1px solid var(--border,#2a2b31);border-radius:999px;color:var(--muted-foreground,#9aa0a6)}}
.prompt{{border-top:1px dashed var(--border,#2a2b31);padding:10px 0 4px;font-size:12.5px;line-height:1.75}}
.prompt p{{margin:0 0 8px}}
.prompt strong{{color:var(--foreground,#fff);font-weight:650}}
.prompt code{{font:11.5px ui-monospace,Menlo,monospace;padding:1px 4px;border-radius:4px;background:color-mix(in srgb,var(--accent,#4c8bf5) 14%,transparent)}}
.actions{{display:flex;gap:10px;align-items:center;padding:0 0 12px}}
.copy{{padding:6px 12px;border-radius:8px;border:1px solid var(--accent,#4c8bf5);background:transparent;color:var(--accent,#4c8bf5);font-size:12px;cursor:pointer}}
.copy:active{{transform:translateY(1px)}}
.hint{{font-size:11px;color:var(--muted-foreground,#9aa0a6)}}
.hidden{{display:none}}
footer{{padding:0 16px 16px;font-size:11px;color:var(--muted-foreground,#9aa0a6)}}
</style></head><body>
<header>
<h1>{PROJECT_NAME} · 全剧图片提示词预览</h1>
<div class="sub">共 {total} 张 · 人物基准 {n['人物·身份基准']} / 变体 {n['人物·状态变体']} / Q版 {n['人物·Q版形态']} / 场景 {n['场景']} / 道具 {n['道具']} · 全部已带 3D 画风锁（禁真人质感）</div>
<div class="bar"><input type="search" id="q" placeholder="搜索编号 / 人物名 / 关键词，例如「李丝柔」「半扎」「金桂」"><button class="chip" id="all">全部 {total}</button>{chips}</div>
</header>
<div class="list" id="list">
{''.join(rows)}
</div>
<footer>提示：点卡片标题展开正文 → 点「复制这段提示词」→ 贴进出图工具。画风锁在第一段之后，复制时别删。</footer>
<script>
const q=document.getElementById('q'),cards=[...document.querySelectorAll('.card')],chips=[...document.querySelectorAll('.chip[data-f]')];
let active=null;
function apply(){{const s=q.value.trim().toLowerCase();
 cards.forEach(c=>{{const okType=!active||c.dataset.type===active;const okText=!s||c.dataset.search.includes(s);c.classList.toggle('hidden',!(okType&&okText));}});}}
q.addEventListener('input',apply);
document.getElementById('all').addEventListener('click',()=>{{active=null;chips.forEach(c=>c.classList.remove('on'));apply();}});
chips.forEach(b=>b.addEventListener('click',()=>{{active=(active===b.dataset.f)?null:b.dataset.f;chips.forEach(c=>c.classList.toggle('on',c===b));apply();}}));
document.querySelectorAll('.copy').forEach(btn=>btn.addEventListener('click',async()=>{{
 const box=btn.closest('.card').querySelector('.prompt');const txt=[...box.querySelectorAll('p')].map(p=>p.textContent).join('\n\n'); try{{await navigator.clipboard.writeText(txt);}}catch(e){{const ta=document.createElement('textarea');ta.value=txt;document.body.appendChild(ta);ta.select();document.execCommand('copy');ta.remove();}}
 btn.textContent='已复制 ✓';setTimeout(()=>btn.textContent='复制这段提示词',1400);}}));
</script></body></html>'''


if __name__ == '__main__':
    A = collect()
    out = build(A)
    open('全剧提示词预览.html', 'w', encoding='utf-8').write(out)
    print(f'✅ 预览已生成：全剧提示词预览.html（{len(A)} 张，{round(os.path.getsize("全剧提示词预览.html")/1024)} KB）')
