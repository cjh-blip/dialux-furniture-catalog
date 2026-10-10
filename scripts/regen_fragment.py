# -*- coding: utf-8 -*-
"""重生成 Moebel 片段 + CSV（清洁名称列：ASCII 首选 + 中文附注）"""
import os, re, json, csv

ROOT = r'D:\dev\DIAL GmbH\DIALux\Media\Furnitures\M3D'
data = json.load(open(r'D:\tmp\m3d_dims.json', encoding='utf-8'))
cjk = re.compile(r'[\u4e00-\u9fff]')
ascii_re = re.compile(r'^[\x20-\x7e]{4,}$')

def pick_name(rec):
    from opencc import OpenCC
    cc = OpenCC('t2s')
    names = rec.get('names') or []
    base = os.path.splitext(os.path.basename(rec['path']))[0]
    cand = [n for n in names if n != base]
    hanzi = lambda s: bool(re.search(r'[\u4e00-\u9fff]', s))
    kh = lambda s: bool(re.search(r'[\u3040-\u30ff\uac00-\ud7af]', s))
    bad = lambda s: bool(re.search(r'[^\x20-\x7e]', s)) or '_' in s
    first_tok = base.split('_')[0].split(' ')[0]
    # 1) 同源起头 + 空格 + 无疑字符
    pick = next((n for n in names if n.startswith(first_tok + ' ') and not bad(n)), None)
    # 2) names[0] 干净（含空格）
    if not pick and names and not bad(names[0]) and ' ' in names[0]:
        pick = names[0]
    # 3) 任意干净含空格
    if not pick:
        pick = next((n for n in cand if not bad(n) and ' ' in n), None)
    # 4) 任意干净
    if not pick:
        pick = next((n for n in cand if not bad(n)), None)
    out = pick or (cand[0] if cand else '—')
    # 中文（简体优先；排除日文假名/韩文）
    cand_cjk = [n for n in cand if hanzi(n) and not kh(n)]
    simp = [n for n in cand_cjk if cc.convert(n) == n]
    cjk_pick = (simp or cand_cjk or [None])[0]
    if cjk_pick and cjk_pick != out:
        out = f"{out} / {cjk_pick}"
    return out

# CJK 覆盖统计
n_cjk = sum(1 for r in data if any(cjk.search(n) for n in (r.get('names') or [])))
print(f'名称表含中文的文件: {n_cjk}/{len(data)}')

# —— 片段重生成 ——
lines = []
moebel = [r for r in data if r['path'].startswith('Moebel')]
by_sub = {}
for r in moebel:
    sub = '\\'.join(r['path'].split('\\')[1:-1]) or '(根)'
    by_sub.setdefault(sub, []).append(r)
order = ['Betten','Designklassiker\\Alvar Aalto','Designklassiker\\Gerri T. Rietveld','Designklassiker\\Le Corbusier',
         'Designklassiker\\Marcel Breuer','Designklassiker\\Mies van der Rohe','Polstermoebel','Regale','Schraenke',
         'Stuehle','Tische','Tische\\Eckschreibtische','Tische\\Graphis','Tische\\Nomos_detailliert','Tische\\Zeichentische','Werkbaenke']
for sub in order:
    items = by_sub.get(sub, [])
    if not items: continue
    lines.append(f'### {sub.replace(chr(92), " / ")}（{len(items)} 件）')
    lines.append('')
    lines.append('| 文件 | 尺寸 X×Y×Z (m) | 名称（主 / 中文） |')
    lines.append('|---|---|---|')
    for r in sorted(items, key=lambda x: x['path']):
        d = r.get('dim_m') or {}
        if d.get('z'):
            dims = f"{d.get('x')} × {d.get('y')} × {d.get('z')}"
        elif d.get('x'):
            dims = f"{d.get('x')} × {d.get('y')}" + ("（文件名）" if d.get('method')=='filename' else "")
        else:
            dims = "待解析"
        lines.append(f"| {os.path.basename(r['path'])} | {dims} | {pick_name(r)} |")
    lines.append('')
open(r'D:\tmp\moebel_md.txt', 'w', encoding='utf-8').write('\n'.join(lines))
print('fragment regenerated:', len(lines), 'lines')

# —— CSV 重生成 ——
OUT_CSV = r'D:\homework\plan\03_Resources\references\试用记录_20261003\DIALux家具库清单_20261007.csv'
rows = []
for r in data:
    parts = r['path'].split('\\')
    cat = parts[0]; sub = '\\'.join(parts[1:-1]); fname = parts[-1]
    d = r.get('dim_m') or {}
    src = 'parsed' if (d and d.get('method') not in ('filename',)) else ('filename' if d else 'pending')
    rows.append({
        'category': cat, 'subcategory': sub, 'file': fname,
        'dim_x_m': d.get('x'), 'dim_y_m': d.get('y'), 'dim_z_m': d.get('z'),
        'dim_source': src,
        'name_main': pick_name(r),
        'names_all': ' | '.join((r.get('names') or [])[:8]),
        'size_bytes': r['size'],
    })
with open(OUT_CSV, 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)
print('CSV regenerated:', len(rows), 'rows')

# 抽样
for probe in ['Armchair LC2.m3d', '100x60_standard.m3d']:
    for r in data:
        if r['path'].endswith(probe):
            print(probe, '->', pick_name(r))
