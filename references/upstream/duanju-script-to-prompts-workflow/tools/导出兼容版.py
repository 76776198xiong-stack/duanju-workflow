#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把某张卡导出成「出图工具兼容版」纯文本（去 Markdown、去分段标签、控长度）。
用法：
    python3 项目开发/导出兼容版.py IMG-EP006-C02
    python3 项目开发/导出兼容版.py IMG-EP006-C02 --all     # 同时导出全部卡
输出：出图兼容版/<编号>.txt（标准版）+ 出图兼容版/<编号>_精简.txt
"""
import re, glob, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
OUT = '出图兼容版'


def load(cid):
    for f in glob.glob('剧集/EP*/图片提示词.md'):
        t = open(f, encoding='utf-8').read()
        if '## ' + cid not in t:
            continue
        body = t.split('## ' + cid, 1)[1].split('\n## ')[0]
        name = body.split('\n', 1)[0].split('·')[-1].strip()
        pm = re.search(r'### 可复制提示词\s*\n(.*?)(?:\n## |\Z)', body, re.S)
        lines = [l.strip().lstrip('>').strip() for l in pm.group(1).split('\n') if l.strip().startswith('>')]
        lines = [l for l in lines if l and not l.startswith('【图外标注】')]
        return cid, name, lines
    return None


def plain(line):
    """去掉 Markdown 强调符与分段标签，压成可粘贴中文。"""
    s = line.replace('**', '')
    s = re.sub(r'`([^`]*)`', r'\1', s)
    s = re.sub(r'^【[^】]{2,12}】', '', s).strip()
    return s


def join_ok(parts, limit=None):
    s = '。'.join(p.rstrip('。；;') for p in parts if p) + '。'
    s = s.replace('。。', '。').replace('；。', '。')
    if limit and len(s) > limit:
        s = s[:limit].rsplit('，', 1)[0] + '。'
    return s


def build_standard(lines):
    """标准版：正文按原段落顺序压平，负向词单独一段。"""
    pos, neg = [], []
    for l in lines:
        p = plain(l)
        if not p:
            continue
        if '负向提示词' in l and not pos:
            # 该行带标签被剥掉了，判断靠标签前是否存在负向标记
            pass
        (neg if is_negative(l) else pos).append(p)
    return join_ok(pos), join_ok(neg)


def is_negative(line):
    return '【负向提示词】' in line


def build_lite(lines):
    """精简版：只保留 画风锁 + 主体身份/外观 + 版式要点 + 负向核心，控制在 ~700 字。"""
    keep_keys = ('画风锁', '人物身份', '外貌与服装', '本体锁定', '基础规格与全局构图', '全局规格与画幅')
    pos = []
    for l in lines:
        if any(k in l for k in keep_keys):
            pos.append(plain(l))
    neg_core = ('真人，实拍照片，photorealistic，皮肤毛孔，影楼写真，影视剧照，换脸，孕肚，满头珠翠，'
                '现代服装，欧美面孔，可读文字乱码，假字，低幼卡通，Q版，黑色背景，水印，'
                '合图，第二人物，四视图造型变化，两个侧面朝向相同，缺少背面，裁切头顶或脚部，裁剪')
    return join_ok(pos, limit=1400), neg_core


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    all_mode = '--all' in sys.argv
    ids = sorted(set(re.findall(r'IMG-[A-Z0-9]+-[CLP]\d+',
                                '\n'.join(open(f, encoding='utf-8').read() for f in glob.glob('剧集/EP*/图片提示词.md'))))) if all_mode else args
    if not ids:
        print(__doc__)
        sys.exit(1)
    for cid in ids:
        got = load(cid)
        if not got:
            print('未找到:', cid)
            continue
        _, name, lines = got
        std_pos, std_neg = build_standard(lines)
        lite_pos, lite_neg = build_lite(lines)
        base = os.path.join(OUT, cid)
        open(base + '.txt', 'w', encoding='utf-8').write(
            '【正向提示词】\n' + std_pos + '\n\n【负向提示词】\n' + std_neg + '\n')
        open(base + '_精简.txt', 'w', encoding='utf-8').write(
            '【正向提示词·精简】\n' + lite_pos + '\n\n【负向提示词】\n' + lite_neg + '\n')
        print(f'{cid} {name}: 标准 {len(std_pos)} 字 / 负向 {len(std_neg)} 字 ｜ 精简 {len(lite_pos)} 字')
