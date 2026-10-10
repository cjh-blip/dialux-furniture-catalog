# DIALux 家具目录（元数据清单）

> DIALux evo 14 家具与对象目录的**元数据**清点：**494 条家具条目** ＋ **594 条 UI 目录条目**，
> 含分类、文件名、尺寸（米）、来源标记与多语言名称。
>
> **本仓库不含任何模型文件（`.m3d` / `.gdms`）、贴图或几何数据。** 只有名字、尺寸、文件名这类可核对的事实。

## 为什么有这个

做照明/室内仿真时要**按尺寸挑家具**（比如「找一张 1.4 × 0.8 的桌」或「0.45 m 进深的柜」），
但 DIALux 不提供可导出的目录清单，只能在界面里一个个翻；换机器或换版本就重新来过。
这次把目录整体清了一遍，清成**可查询的表**——按尺寸筛、按名称查、按分类统计都能做。

## 文件

| 文件 | 内容 |
|---|---|
| `DIALux家具库清单_20261007.csv` | **494 行**，全部字段见下节；可直接 `pandas.read_csv()` 或 `grep` |
| `05g_家具库清单_20261007.md` | 13 类分类主清单（人读版，含各类计数） |
| `DIALux对象目录条目清单_20261007.md` | UI 七分类 **594 条**（只有分类 + 中文名，没有尺寸） |
| `scripts/` | 清点脚本与中间数据：`m3d_extract.py`（从模型文件读包围盒）、`gen_05g.py`（生成清单）、`fix_names.py` 等 |

## CSV 字段

`category, subcategory, file, dim_x_m, dim_y_m, dim_z_m, dim_source, name_main, names_all, size_bytes`

| 字段 | 含义 |
|---|---|
| `category` / `subcategory` | 目录分类，如 `Moebel` / `Moebel\Tische`（家具 / 家具-桌） |
| `file` | 模型文件名，如 `140x80_standard.m3d` |
| `dim_x_m` `dim_y_m` `dim_z_m` | 包围盒尺寸，**单位米** |
| `dim_source` | `parsed` = 从模型文件包围盒读出；`filename` = 仅从文件名推断（**这类的尺寸不可信，字段可能为空**） |
| `name_main` | 主显示名（首条 + 中文） |
| `names_all` | 该条目在 DIALux 里的**全部多语言名称**，竖线分隔（`Baum01 \| Strom01 \| træ01 \| Tree01 \| …`） |
| `size_bytes` | 模型文件字节数 |

> ⚠️ 尺寸是**包围盒**，不是净使用面积；一件带支腿/带竖板的条目会把高度算进去。

## 怎么用

```python
import pandas as pd
df = pd.read_csv("DIALux家具库清单_20261007.csv")
# 找长 1.3~1.5 m、进深 0.6~0.9 m 的桌
df[(df.category == "Moebel") & df.dim_x_m.between(1.3, 1.5) & df.dim_y_m.between(0.6, 0.9)]
# 只看尺寸可靠的
df[df.dim_source == "parsed"]
```

## 复现

`scripts/m3d_extract.py` 遍历 DIALux 安装目录下的模型文件读包围盒，`scripts/gen_05g.py` 汇总成清单。
DIALux 安装路径按本机实际位置改（脚本里是可配项）。

## 数据来源与声明

- **来源**：本机安装的 **DIALux evo 14** 的目录与模型文件（2026-10-07 清点）。
- **只保留事实性元数据**：名称、尺寸、文件名、字节数。**不含模型、贴图、几何或任何可重建其形状的数据。**
- **DIALux 是 Dialux GmbH 的产品**，相关商标与产品名归其所有者；此处仅作技术参考，与官方无关联。
- 若权利人认为有任何内容需要调整，开 issue 即可，会立即处理。

## License

仓库内**脚本与文档**：MIT（见 `LICENSE`）。元数据部分按上一节的声明处理。
