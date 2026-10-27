# -*- coding: utf-8 -*-
"""M3D 家具库批量提取：SAT 包围盒（米）+ 多语言名称 + 元数据。
只读：不修改任何 .m3d 文件。输出 JSON 供清单构建。
"""
import os, re, json, sys
import olefile

ROOT = r'<DIALux 安装目录>\Media\Furnitures\M3D'
OUT = r'm3d_dims.json'

PT = re.compile(rb'point\s+\S+\s+([-\d.eE+]+)\s+([-\d.eE+]+)\s+([-\d.eE+]+)')
TXT = re.compile(rb'[\x20-\x7e\xc2-\xf4][\x20-\x7e\x80-\xbf]{4,}')

def extract(path):
    rec = {'path': os.path.relpath(path, ROOT), 'size': os.path.getsize(path)}
    try:
        ole = olefile.OleFileIO(path)
    except Exception as e:
        rec['error'] = f'ole:{e}'
        return rec
    try:
        # SAT 包围盒
        sat = ole.openstream('SATVolume').read()
        pts = PT.findall(sat)
        if pts:
            xs = [float(p[0]) for p in pts]; ys = [float(p[1]) for p in pts]; zs = [float(p[2]) for p in pts]
            rec['dim_m'] = {
                'x': round(max(xs)-min(xs), 3),
                'y': round(max(ys)-min(ys), 3),
                'z': round(max(zs)-min(zs), 3),
                'n_pts': len(pts),
            }
        else:
            rec['dim_m'] = None  # 待解析
        # Texts 多语言名称
        if ole.exists('Infos/Texts'):
            t = ole.openstream('Infos/Texts').read()
            names = []
            for m in TXT.finditer(t):
                s = m.group(0)
                try:
                    s2 = s.decode('utf-8')
                except Exception:
                    continue
                s2 = s2.strip()
                if len(s2) >= 4 and s2 not in names:
                    names.append(s2)
            rec['names'] = names
        else:
            rec['names'] = []
    finally:
        ole.close()
    return rec

files = []
for dp, dn, fn in os.walk(ROOT):
    for f in sorted(fn):
        if f.lower().endswith('.m3d'):
            files.append(os.path.join(dp, f))

print('total:', len(files))
results = []
for i, p in enumerate(files):
    results.append(extract(p))
    if (i+1) % 50 == 0:
        print(f'  ... {i+1}/{len(files)}')

json.dump(results, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
ok = sum(1 for r in results if r.get('dim_m'))
nofix = sum(1 for r in results if 'dim_m' in r and r['dim_m'] is None)
err = sum(1 for r in results if 'error' in r)
print(f'done: dims_ok={ok} 待解析={nofix} errors={err}')
print('sample:')
for r in results[:5]:
    print(' ', r['path'], r.get('dim_m'), '| names:', (r.get('names') or [])[:4])
