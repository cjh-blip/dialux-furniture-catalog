# -*- coding: utf-8 -*-
"""修复 Texts 名称解析（自校验长度步进）+ 重生成 家具片段/CSV"""
import os, re, json, csv
import olefile

ROOT = r'D:\dev\DIAL GmbH\DIALux\Media\Furnitures\M3D'
data = json.load(open(r'D:\tmp\m3d_dims.json', encoding='utf-8'))

def parse_texts(raw: bytes):
    """自校验步进：读 [len][utf8 text][00] 模式"""
    names = []
    i = 0
    n = len(raw)
    while i < n - 2:
        L = raw[i]
        if 4 <= L <= 120 and i + 1 + L < n:
            chunk = raw[i+1:i+1+L]
            try:
                s = chunk.decode('utf-8')
                if all(c.isprintable() and c not in '\x00' for c in s):
                    # 后面应是 00（或串结束）
                    nxt = raw[i+1+L] if i+1+L < n else 0
                    if nxt == 0 or nxt == 0x1b or nxt < 0x20:
                        if s not in names:
                            names.append(s)
                        i += 1 + L
                        continue
            except UnicodeDecodeError:
                pass
        i += 1
    return names

fixed = 0
for rec in data:
    p = os.path.join(ROOT, rec['path'])
    ole = olefile.OleFileIO(p)
    raw = ole.openstream('Infos/Texts').read()
    ole.close()
    ns = parse_texts(raw)
    if ns != rec.get('names'):
        fixed += 1
    rec['names'] = ns
json.dump(data, open(r'D:\tmp\m3d_dims.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('names updated for', fixed, 'files')

# 抽样验证
for probe in ['Moebel\\Designklassiker\\Le Corbusier\\Armchair LC2.m3d', 'Moebel\\Tische\\100x60_standard.m3d', 'Moebel\\Betten\\Bett1_breit.m3d']:
    for r in data:
        if r['path'] == probe:
            print('\n', probe)
            for nm in r['names'][:10]:
                print('    ', repr(nm))

# —— 重点修复：LC2 一致性检查 ——
c = [r for r in data if 'Le Corbusier' in r['path']]
print('\nLe Corbusier 名称抽查:')
for r in c[:6]:
    print(' ', os.path.basename(r['path']), '->', r['names'][:4])
