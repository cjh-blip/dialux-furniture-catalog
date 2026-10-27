# -*- coding: utf-8 -*-
"""生成 05g 交付物：主清单 md + UI 条目清单 md"""
import json, re, os

DIR = r'试用记录_20261003'
disk = json.load(open(r'm3d_dims.json', encoding='utf-8'))
ui = json.load(open(r'ui_categories.json', encoding='utf-8'))
frag = open(r'moebel_md.txt', encoding='utf-8').read()

CN = {
 'Moebel': '家具', 'Shop': '商铺/店面', 'Gebaeude': '建筑', 'Verkehrseinrichtungen': '交通设施',
 'Personen': '人物', 'Stadtmobiliar': '街道家具', 'Buerozubehoer': '办公附件', 'Sanitaer': '卫浴',
 'Fahrzeuge': '车辆', 'Baeume': '树', 'Treppen': '楼梯', 'Pflanzen': '植物', 'Sportstaetten': '体育设施',
}

def fmt_dims(d):
    if not d: return '待解析'
    if d.get('z') and d.get('method') != 'filename':
        return f"{d['x']}×{d['y']}×{d['z']}"
    if d.get('x'):
        s = f"{d.get('x')}×{d.get('y')}"
        if d.get('method') == 'filename': s += '（文件名）'
        return s
    return '待解析'

# —— 大类表 ——
from collections import defaultdict
cls = defaultdict(list)
for r in disk:
    cls[r['path'].split('\\')[0]].append(r)

lines = []
lines.append('| # | 类别（原名） | 中文 | 件数 | 尺寸获取 | 代表件（名称 × 尺寸 m） |')
lines.append('|---|------------|------|-----:|---------|------------------------|')
for i, (k, recs) in enumerate(sorted(cls.items(), key=lambda x: -len(x[1])), 1):
    okn = sum(1 for r in recs if r.get('dim_m'))
    samples = []
    for r in recs[:4]:
        fn = os.path.splitext(os.path.basename(r['path']))[0]
        samples.append(f"{fn}（{fmt_dims(r.get('dim_m'))}）")
    lines.append(f"| {i} | {k} | {CN.get(k,'')} | {len(recs)} | {okn}/{len(recs)} | {'；'.join(samples)} |")
TOP_TABLE = '\n'.join(lines)

# Moebel 子类高度范围
sub = defaultdict(list)
for r in disk:
    if r['path'].startswith('Moebel'):
        parts = r['path'].split('\\')
        sub['\\'.join(parts[1:-1])].append(r)
lines2 = []
lines2.append('| 子类 | 件数 | 高度 Z 范围 (m) | 平面上限 (m) | 说明 |')
lines2.append('|------|-----:|----------------|---------------|------|')
subdesc = {
 'Betten': '病床/双人床，Z 含床头', 'Designklassiker\\Alvar Aalto': 'Aalto 经典', 'Designklassiker\\Gerri T. Rietveld': '红蓝椅/ ZigZag',
 'Designklassiker\\Le Corbusier': 'LC2/LC3 沙发与扶手椅', 'Designklassiker\\Marcel Breuer': '瓦西里椅等', 'Designklassiker\\Mies van der Rohe': '巴塞隆那系列',
 'Polstermoebel': '沙发族', 'Regale': '架类', 'Schraenke': '柜类（含滑门/双门/抽屉）', 'Stuehle': '椅类',
 'Tische': '桌类（140×80 等）', 'Tische\\Eckschreibtische': '转角桌', 'Tische\\Graphis': 'Graphis 系列', 'Tische\\Nomos_detailliert': 'Nomos 系列',
 'Tische\\Zeichentische': '绘图桌', 'Werkbaenke': '工作台/台钳',
}
for k, recs in sorted(sub.items()):
    zs = [r['dim_m']['z'] for r in recs if r.get('dim_m') and r['dim_m'].get('z')]
    xys = [(r['dim_m']['x'], r['dim_m']['y']) for r in recs if r.get('dim_m') and r['dim_m'].get('x')]
    zr = f"{min(zs)}–{max(zs)}" if zs else '—'
    xyr = f"最大 {max(x for x,_ in xys)}×{max(y for _,y in xys)}" if xys else '—'
    lines2.append(f"| {k.replace(chr(92), ' / ')} | {len(recs)} | {zr} | {xyr} | {subdesc.get(k,'')} |")
SUB_TABLE = '\n'.join(lines2)

# —— UI 条目清单 md ——
ui_lines = ['# DIALux 对象目录 · 七分类全量条目清单（2026-10-07）', '',
            '> 来源：DIALux evo 14.0 对象目录（UIA ScrollPattern 确定性扫掠，覆盖率完整）',
            '> 名称 = UI 中文显示名；与磁盘文件的对应关系见 05g §3 与 CSV', '']
ui_counts = {k: len(v) for k, v in ui.items()}
ui_lines.append('| 分类 | 条目数 |')
ui_lines.append('|------|-------:|')
for k, n in sorted(ui_counts.items(), key=lambda x: -x[1]):
    ui_lines.append(f'| {k} | {n} |')
ui_lines.append(f'| **合计（含重叠）** | **{sum(ui_counts.values())}** |')
ui_lines.append('')
for k in ['家居家具','办公家具','卫生间','店面設計','外部規劃','道路規劃','其他']:
    names = ui.get(k, [])
    ui_lines.append(f'## {k}（{len(names)} 项）')
    ui_lines.append('')
    for i, nm in enumerate(names, 1):
        ui_lines.append(f'{i}. {nm}')
    ui_lines.append('')
open(os.path.join(DIR, 'DIALux对象目录条目清单_20261007.md'), 'w', encoding='utf-8').write('\n'.join(ui_lines))
print('UI 清单 saved:', len(ui_lines), 'lines')

# —— 05g 主件 ——
HEAD = f'''# 05g · DIALux 家具库全量清单 + 对象目录映射（2026-10-07）

> 分发来源：照明项目枢纽（家具库全量清点任务）
> 边界遵守：全程只读，未修改 DIALux 安装目录任何文件；基线 `.evo` 未触碰
> 交付件：本文 + `DIALux家具库清单_20261007.csv`（494 行全量机读）+ `DIALux对象目录条目清单_20261007.md`

## 〇、结论速览

1. **库本体**：`<DIALux 安装目录>\\Media\\Furnitures\\M3D\\` —— **13 大类、67 子目录、494 个 `.m3d`**（枚举数字与枢纽起点完全一致）。
2. **格式解剖（新发现）**：`.m3d` = **OLE2 复合文档**（微软结构化存储，同旧版 doc 容器）。内部流：`SATVolume`（ACIS 13.0 几何体，文本格式）、`Infos/Texts`（多语言名称表，每件约 15–20 语种，**494/494 全含中文条目**，与 UI 显示名一致）、`Previews/64`（内置预览图）、`Attributes`（原始路径+版本）。
3. **尺寸提取**：SAT 点云包围盒**直接可用，单位 = 米**（验证：`100x60_standard` → 1.0×0.6×0.72 m，与品名吻合）。**484/494 自动解析 + 6 件文件名推断 + 4 件待解析**（唯四条无尺寸线索的 Mode1_F/G 系列）。
4. **UI 映射**：对象目录 7 分类 = 磁盘 13 大类的重组，**三组精确相等**（卫生间 12=12；道路規劃 72=64+8；其他 42=28+5+5+3+1），其余近精确。**全部内置件均可经 7 分类浏览到，无需导入**。
5. **导入通道**：`[导入]` = **第三方/自定义文件入库通道**（内嵌视图：左「用户」栏 + 右「指定对象」+ [添加文件][删除文件][类别名称][导入][取消]）→ 自定义类别落入「用户」区。先例：`Cad_furniture`。**不是**内置库的浏览入口。
6. **搜索框**：**分类内即时过滤、认中文名**（「桌」17 命中）；英文（standard）/德文（Tisch）/跨分类（马桶）均 0 命中。
7. **选件路径**：主路径 = 本文清单/CSV 查表（磁盘角度，全字段）→ 回 UI 分类内中文搜索；导入通道仅用于第三方件。

## 一、磁盘全量清单（494 件）

### 1.1 十三大类总览

{TOP_TABLE}

### 1.2 家具类 Moebel 单件明细（159 件，单件粒度）

尺寸 = SAT 包围盒 X×Y×Z，单位 m；「名称（主）」= 名称表首个非文件名条目（多语言表中的代表项）。

{frag}

### 1.3 Moebel 子类尺寸概览

{SUB_TABLE}

### 1.4 其他 12 类

单件明细见 CSV（全 494 行）；代表件及尺寸见上表 1.1。完整 CSV 列：`category, subcategory, file, dim_x_m, dim_y_m, dim_z_m, dim_source, name_main, names_all, size_bytes`。

## 二、解析方法（可复现）

- 环境：`python` + `olefile 0.47`（本次任务安装）
- 链路：OLE2 流探察 → `Infos/Texts` 多语言名提取（UTF-8 长度前缀结构）→ `SATVolume` 正则提取 `point` 行 → min/max 得包围盒
- 单位校验：三个样本与原物尺寸逐项吻合（100x60 桌 1.0×0.6×0.72；LC2 扶手椅 0.76×0.70×0.67；LC2 沙发按型号 1.3–2.0 级）
- 脚本（已随交付拷贝）：`05g_scripts\\` 目录 —— m3d_extract.py（批量提取）、fix_names.py（名称表精解）、regen_fragment.py（清单/CSV 生成）、gen_05g.py（本文生成）、catalog_probe4.ps1（UI 扫掠）
- 局限：包围盒 = 顶点快照轴向值；个别模型带变换矩阵未做旋转校正（抽样未发现影响）；4 件待解析（见下）
- **待解析 4 件**：`Shop\\Mode\\Regal F\\Mode Typ F\\Mode1_F_100.m3d`、`Mode1_F_150.m3d`、`Shop\\Mode\\Regal G\\Mode Typ G\\Mode1_G_100.m3d`、`Mode1_G_50.m3d`（无 point 实体、文件名无尺寸。推测为「货品排列模式」组合件，尺寸以布置图为准）

## 三、对象目录（UI）与磁盘库交叉对账

### 3.1 七分类 × 十三大类映射

| UI 分类 | 条目数 | 磁盘来源 | 磁盘件数 | 对账 |
|---------|-------:|----------|---------:|------|
| 家居家具 | 120 | Moebel（家居标签子集） | ⊆159 | 与「办公家具」并集 = **170 ≈ Moebel 159 + 办公附件 13 = 172（−2）** |
| 办公家具 | 146 | Moebel（办公标签子集）+ Buerozubehoer | ⊆172 | 两类交集 96（双标签件） |
| 卫生间 | 12 | Sanitaer | 12 | **✓ 精确** |
| 店面設計 | 106 | Shop | 101 | +5（显示计件/合并差异） |
| 外部規劃 | 96 | Gebaeude + Stadtmobiliar | 78+17=95 | +1 |
| 道路規劃 | 72 | Verkehrseinrichtungen + Fahrzeuge | 64+8=72 | **✓ 精确** |
| 其他 | 42 | Personen+Treppen+Baeume+Pflanzen+Sportstaetten | 28+5+5+3+1=42 | **✓ 精确** |

### 3.2 对账要点

- **翻译层（修正）**：**UI 显示名直接来自名称表的中文条目**（494/494 件全含中文名，如 `Armchair LC2.m3d → 「扶手椅，C2」`，与 UI 列表逐字一致）；磁盘文件名 = 德语源名。抽样对照（逐项吻合）：`Bett1_breit↔宽床 1`、`ZIGZAG Chair↔Z型椅`、`RED AND BLUE Chair↔红蓝色椅子`、`Armchair LC2 Hide↔扶手椅，LC2皮制`、`Drucker↔打印机`、`FlipChart↔白板`、`Papierkorb↔字纸篓`、`TFT_Bildschirm_mit_Tastatur↔电脑屏幕+键盘`（办公附件 13 件 1:1 全对上）、人名音译 1:1（`Nicoletta↔妮寇丽塔`、`Sarah↔莎菈`、`Tata↔塔塔`、`Alice↔艾莉丝`）。
- **家居/办公的重叠**：96 件同时出现在两类（桌、柜、架等通用件双标签）；「家居家具有、办公没有」24 件 = 沙发/经典设计/床；「办公有、家居没有」50 件 = 书桌/抽屉桌/绘图板/P 系列桌 + 办公附件 13。
- **目录里能看到什么**：**13 大类全部可见**（见 3.1 映射）；UI 分类 = 面向使用场景的重分组，不是磁盘的子集裁剪。
- **什么要走导入通道**：**内置库一律不需要**。`[导入]` 专用于第三方/自定义件（选文件 → 类别名称 → 入库「用户」区；先例 `Cad_furniture` = 一周内新增自定义件）。即：**能看到 = 内置 13 类；要导入 = 非内置的自家/下载件**。

### 3.3 UI 七分类全量条目

→ 见 `DIALux对象目录条目清单_20261007.md`（7 类共 594 条，含重叠，行序为 UI 排序）

## 四、搜索框测试（决定选件策略）

**测试上下文**：办公家具分类（列表已加载）。方法：UIA ValuePattern 设值 + 回读确认 + 条目枚举。

| 检索词 | 命中 | 结论 |
|--------|-----:|------|
| 桌 | **17** | ✓ 分类内中文子串过滤成立（`160x60 桌`→`200x100 会议桌` 等） |
| 马桶 | 0 | ✗ 跨分类不搜（马桶在卫生间类内才有） |
| standard | 0 | ✗ 不认英文/内部名 |
| Tisch | 0 | ✗ 不认德文原名 |

**机理**：即时过滤**当前分类**的列表（虚拟化列表下 = 已加载区间内过滤），非全局、非多语言。
**用法**：先左栏切类 → 再搜中文关键词；记不住中文名时用 CSV 反查（文件/尺寸 → 中文名）。

## 五、选件路径建议

1. **查表法（主路径）**：CSV 全字段查件（如「2 米高的柜有哪些」「1.4×1.4 的桌」）→ 拿到中文名 → 回 UI 分类内搜索或直接人工选。
2. **分类内搜索**：记得中文名的场景最快；注意必须先切对分类。
3. **导入通道**：第三方/自定义件专用（命名自定义类别）。
4. **尺寸数据的附加用途**：布置前净空核算（柜类 2.0–2.2 m 高注意吊顶；工作台 1.5×0.75 标准件可直接进布置图）。

## 附录 · 文件清册

| 产物 | 位置 |
|------|------|
| 全量 CSV（494 行） | `试用记录_20261003\\DIALux家具库清单_20261007.csv` |
| UI 七类条目清单 | `试用记录_20261003\\DIALux对象目录条目清单_20261007.md` |
| 解析数据（JSON） | `D:\\tmp\\m3d_dims.json`（完整字段含多语言名） |
| UI 扫掠数据（JSON） | `D:\\tmp\\ui_categories.json` |
| 截图证据 | `照明优化\\_dwg_analysis\\20261007_*`（Y_搜索_桌 / Z1_导入视图 / Z7_收尾等） |
| 脚本（副本） | `试用记录_20261003\\05g_scripts\\` 目录（5 件，随本次交付） |

---
*生成：2026-10-07 · 试用记录 05g · 只读清点*
'''

open(os.path.join(DIR, '05g_家具库清单_20261007.md'), 'w', encoding='utf-8').write(HEAD)
print('05g saved:', len(HEAD), 'chars')
