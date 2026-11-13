#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""通用：把 <项目>/剧集/EP*/图片提示词.md 生成一页可预览的 HTML。

用法：
    python3 build_prompt_preview.py [项目根目录] [输出文件名]
默认：项目根 = 当前目录，输出 = 全剧提示词预览.html

特性：搜索（编号/名称/集/正文前240字）、分类 chip 筛选、details 折叠、一键复制、跟随主题明暗。
设计要点（踩过的坑）：
  * 不把全文重复写进 data-copy —— 复制时从 .prompt p 的 textContent 拼 '\n\n'（体积减半）。
  * data-search 只放正文前 240 字。
  * 构建 HTML 行不用含反斜杠的 f-string 表达式，改用字符串拼接。
"""
import re, glob, os, sys, html

ORDER = ['人物·身份基准', '人物·状态变体', '人物·Q版形态', '场景', '道具']


def classify(cid, name):
    if '-C' in cid:
        if 'Q版' in name:
            return '人物·Q版形态'
        if '身份' in name:
            return '人物·身份基准'
        return '人物·状态变体'
    return '场景' if '-L' in cid else '道具'


def collect(root):
    os.chdir(root)
    cards = {}
    files = sorted(glob.glob('剧集/EP*/图片提示词.md'))
    for f in files:
        ep = re.search(r'(EP\d+)', f).group(1)
        t = open(f, encoding='utf-8').read()
        for m in re.finditer(r'^## (IMG-[A-Z0-9\-]+) · (.+)$', t, re.M):
            cid, name = m.group(1), m.group(2).strip()
            body = t[m.end():].split('\n## ')[0]
            pm = re.search(r'### 可复制提示词\s*\n(.*?)(?:\n## |\Z)', body, re.S)
            if not pm:
                continue
            lines = [l.strip().lstrip('>').strip()
                     for l in pm.group(1).split('\n') if l.strip().startswith('>')]
            cards[cid] = dict(id=cid, name=name, ep=ep, type=classify(cid, name),
                              lines=lines, refs=set())
    for f in files:
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
    return '、'.join(map(str, ep)) if len(ep) <= 10 else '%d…%d（%d集）' % (ep[0], ep[-1], len(ep))


def md_inline(s):
    s = html.escape(s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'`(.+?)`', r'<code>\1</code>', s)
    return s


def build(A, title):
    n = {k: len([v for v in A if v['type'] == k]) for k in ORDER}
    rows = []
    for v in A:
        body = ''.join('<p>' + md_inline(l) + '</p>' for l in v['lines'] if l)
        blob = html.escape((v['id'] + ' ' + v['name'] + ' ' + v['ep'] + ' ' +
                            ' '.join(v['lines'])[:240]).lower(), quote=True)
        rows.append(
            '<details class="card" data-type="' + v['type'] + '" data-search="' + blob + '">\n'
            '<summary><span class="id">' + v['id'] + '</span><span class="nm">' + html.escape(v['name']) + '</span>'
            '<span class="meta">首出 ' + v['ep'][2:] + '｜用于 ' + fmt_refs(v['refs']) + '</span>'
            '<span class="tag">' + v['type'].split('·')[-1] + '</span></summary>\n'
            '<div class="prompt">' + body + '</div>\n'
            '<div class="actions"><button class="copy">复制这段提示词</button>'
            '<span class="hint">展开可读全文，复制后直接贴进出图工具</span></div>\n'
            '</details>')
    chips = ''.join('<button class="chip" data-f="' + k + '">' + k.split('·')[-1] +
                    ' <em>' + str(n[k]) + '</em></button>' for k in ORDER)
    total = len(A)
    head = ('<!DOCTYPE html>\n<html lang="zh-CN"><head><meta charset="utf-8"><title>' + title + ' · 提示词预览</title>\n'
            '<style>\n'
            ':root{color-scheme:light dark}\n'
            '*{box-sizing:border-box}\n'
            'body{margin:0;font-family:var(--font,system-ui,-apple-system,"PingFang SC",sans-serif);color:var(--foreground,#e8e8ea);background:transparent}\n'
            'header{position:sticky;top:0;z-index:5;padding:14px 16px 10px;background:color-mix(in srgb,var(--card,#15161a) 88%,transparent);backdrop-filter:blur(8px);border-bottom:1px solid var(--border,#2a2b31)}\n'
            'h1{margin:0 0 4px;font-size:17px;font-weight:650}\n'
            '.sub{font-size:12px;color:var(--muted-foreground,#9aa0a6)}\n'
            '.bar{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px;align-items:center}\n'
            'input[type=search]{flex:1 1 240px;min-width:180px;padding:8px 10px;border:1px solid var(--border,#2a2b31);border-radius:9px;background:transparent;color:inherit;font-size:13px}\n'
            '.chip{padding:5px 10px;border:1px solid var(--border,#2a2b31);border-radius:999px;background:transparent;color:inherit;font-size:12px;cursor:pointer}\n'
            '.chip em{font-style:normal;color:var(--muted-foreground,#9aa0a6);margin-left:2px}\n'
            '.chip.on{border-color:var(--accent,#4c8bf5);color:var(--accent,#4c8bf5)}\n'
            '.list{padding:10px 12px 18px;max-height:66vh;overflow:auto}\n'
            '.card{border:1px solid var(--border,#2a2b31);border-radius:11px;margin:0 0 8px;padding:0 12px;background:color-mix(in srgb,var(--card,#15161a) 60%,transparent)}\n'
            '.card summary{list-style:none;cursor:pointer;display:flex;gap:10px;align-items:baseline;flex-wrap:wrap;padding:10px 0}\n'
            '.card summary::-webkit-details-marker{display:none}\n'
            '.id{font:600 12px/1 ui-monospace,Menlo,monospace;color:var(--accent,#4c8bf5)}\n'
            '.nm{font-size:14px;font-weight:600}\n'
            '.meta{font-size:11.5px;color:var(--muted-foreground,#9aa0a6)}\n'
            '.tag{margin-left:auto;font-size:11px;padding:2px 8px;border:1px solid var(--border,#2a2b31);border-radius:999px;color:var(--muted-foreground,#9aa0a6)}\n'
            '.prompt{border-top:1px dashed var(--border,#2a2b31);padding:10px 0 4px;font-size:12.5px;line-height:1.75}\n'
            '.prompt p{margin:0 0 8px}\n'
            '.prompt strong{color:var(--foreground,#fff);font-weight:650}\n'
            '.prompt code{font:11.5px ui-monospace,Menlo,monospace;padding:1px 4px;border-radius:4px;background:color-mix(in srgb,var(--accent,#4c8bf5) 14%,transparent)}\n'
            '.actions{display:flex;gap:10px;align-items:center;padding:0 0 12px}\n'
            '.copy{padding:6px 12px;border-radius:8px;border:1px solid var(--accent,#4c8bf5);background:transparent;color:var(--accent,#4c8bf5);font-size:12px;cursor:pointer}\n'
            '.hint{font-size:11px;color:var(--muted-foreground,#9aa0a6)}\n'
            '.hidden{display:none}\n'
            'footer{padding:0 16px 16px;font-size:11px;color:var(--muted-foreground,#9aa0a6)}\n'
            '</style></head><body>\n'
            '<header><h1>' + title + ' · 全剧图片提示词预览</h1>\n'
            '<div class="sub">共 ' + str(total) + ' 张 · 人物基准 ' + str(n['人物·身份基准']) +
            ' / 变体 ' + str(n['人物·状态变体']) + ' / Q版 ' + str(n['人物·Q版形态']) +
            ' / 场景 ' + str(n['场景']) + ' / 道具 ' + str(n['道具']) + '</div>\n'
            '<div class="bar"><input type="search" id="q" placeholder="搜索编号 / 人物名 / 关键词">'
            '<button class="chip" id="all">全部 ' + str(total) + '</button>' + chips + '</div>\n'
            '</header>\n<div class="list" id="list">\n' + '\n'.join(rows) + '\n</div>\n'
            '<footer>点标题展开 → 点“复制这段提示词”→ 贴进出图工具。画风锁在第一段之后，复制时别删。</footer>\n')
    tail = ("<script>\n"
            "const q=document.getElementById('q'),cards=[...document.querySelectorAll('.card')],chips=[...document.querySelectorAll('.chip[data-f]')];\n"
            "let active=null;\n"
            "function apply(){const s=q.value.trim().toLowerCase();\n"
            " cards.forEach(c=>{const okType=!active||c.dataset.type===active;const okText=!s||c.dataset.search.includes(s);c.classList.toggle('hidden',!(okType&&okText));});}\n"
            "q.addEventListener('input',apply);\n"
            "document.getElementById('all').addEventListener('click',()=>{active=null;chips.forEach(c=>c.classList.remove('on'));apply();});\n"
            "chips.forEach(b=>b.addEventListener('click',()=>{active=(active===b.dataset.f)?null:b.dataset.f;chips.forEach(c=>c.classList.toggle('on',c===b));apply();}));\n"
            "document.querySelectorAll('.copy').forEach(btn=>btn.addEventListener('click',async()=>{\n"
            " const box=btn.closest('.card').querySelector('.prompt');\n"
            " const txt=[...box.querySelectorAll('p')].map(p=>p.textContent).join(String.fromCharCode(10,10));\n"
            " try{await navigator.clipboard.writeText(txt);}catch(e){const ta=document.createElement('textarea');ta.value=txt;document.body.appendChild(ta);ta.select();document.execCommand('copy');ta.remove();}\n"
            " btn.textContent='已复制 ✓';setTimeout(()=>btn.textContent='复制这段提示词',1400);}));\n"
            "</script></body></html>")
    return head + tail


if __name__ == '__main__':
    root = sys.argv[1] if len(sys.argv) > 1 else '.'
    out = sys.argv[2] if len(sys.argv) > 2 else '全剧提示词预览.html'
    A = collect(root)
    if not A:
        sys.exit('未找到 剧集/EP*/图片提示词.md')
    title = os.path.basename(os.path.abspath(root))
    open(out, 'w', encoding='utf-8').write(build(A, title))
    print('✅ %s（%d 张，%d KB）' % (out, len(A), round(os.path.getsize(out) / 1024)))
