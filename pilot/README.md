# 字体样张核验

本目录保存 81 字、54 个重点字对的首版核验材料及样张生成工具。此阶段用于检查固定字体、图像条件和标签；没有进行模型训练，也未划分训练、验证或测试集。

## 从哪里查看

- [交互核验页面](./samples/v1/index.html)：清晰总览、字对对照、全部字符的位移检查，支持原尺寸和放大显示。
- [清晰字表总览](./samples/v1/overview_clear.png)、[sigma=1 字表总览](./samples/v1/overview_sigma1.png)。
- [样张核验记录](./样张核验记录.md)：自动检查结果、视觉检查范围及仍需区分的结论。
- [参数与版本](./samples/v1/config.json)、[自动核验详情](./samples/v1/audit.json)、[逐图清单](./samples/v1/manifest.jsonl)。

页面直接在浏览器打开，无需联网或启动服务。字对页面中的人工标记保存在当前浏览器；使用“导出”按钮保存核验记录，跨浏览器不会自动同步。自动检查结果与人工标记是两种不同证据。

## 本次渲染规则

以 `characters.json` 为标签来源，使用同一个思源黑体 SC Regular 文件，不使用字体回退。所有字符在四倍画布上采用共同字号与共同基线；共同定位基于全部 81 字相对于同一基线的包围盒并集，不逐字紧框裁剪或单独拉伸。

1. 输出为 64×64、8 位灰度、白底黑字。
2. 在 256×256 尺度绘制，共同字号为 192 px，即输出尺度 48 px。若字表改变导致联合包围盒超出 192×192，则脚本统一减小字号并要求另用输出目录。
3. 使用固定 Lanczos 下采样；之后应用 `sigma=0、0.5、1.0` 的 Pillow GaussianBlur。模糊前四周补 16 px 白边，处理后裁回原画布。
4. 检查位置为居中，以及横纵均为 ±3 px 的四个角向组合：每字 3×5=15 张，共 1,215 张。这只覆盖核验位置，不代表正式 ±3 px、0.25 px 步长的完整采样。
5. PNG 只包含汉字图像；标签、边框和注释只出现在总览页和对照页。放大图使用近邻复制像素，没有重新渲染字符或补造细节。

81 字、54 对仍是人工候选关系。共享构件不代表像素完全相同；自动检查通过也不等于所有字对都易混淆或方法已经有效。

## 文件与来源

| 文件 | 用途 |
|---|---|
| 核验字表.md、characters.json | 用户提供的核验字表，生成器只读 |
| prepare_font.py | 下载官方字体及许可证；已有资源会核对哈希后复用 |
| fonts/ | 字体、许可证及固定来源元数据 |
| render_samples.py | 生成单字图、自动核验、对照图及离线页面 |
| gallery_template.html | 离线核验页面模板 |
| samples/v1/ | 本次输出；包含全部 PNG 和生成记录 |
| requirements.txt | 此次实际使用的 Python 包版本 |

字体来自 [Adobe 官方 Source Han Sans 仓库](https://github.com/adobe-fonts/source-han-sans)，固定源提交与 SHA-256 见 [fonts/source.json](./fonts/source.json)，许可证随文件保存在 [fonts/LICENSE.txt](./fonts/LICENSE.txt)。字体版本由下载文件的 name 表读取，而非仅凭文件名推断。

有关 API 含义见 [Pillow 字体基线与包围盒](https://pillow.readthedocs.io/en/stable/reference/ImageFont.html#PIL.ImageFont.FreeTypeFont.getbbox)和 [GaussianBlur 参数](https://pillow.readthedocs.io/en/stable/reference/ImageFilter.html#PIL.ImageFilter.GaussianBlur)；本次实际软件版本记录在 config.json。

## 复现

在 `pilot` 目录内运行。首次准备可使用 Python 3.13 建立独立虚拟环境，再安装 `requirements.txt`。本机 `.venv` 使用已安装的 Pillow，并在项目环境内安装 fonttools；包版本已记录，未修改系统 Python 包。

```powershell
# 已配置好的本机环境
.\.venv\Scripts\python.exe prepare_font.py
.\.venv\Scripts\python.exe render_samples.py
```

首次下载字体需要网络；已有字体和许可证的哈希正确时，生成样张可离线完成。用新环境复现时先安装依赖：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe prepare_font.py
.\.venv\Scripts\python.exe render_samples.py
```

重新生成会覆盖生成器管理的图片、页面和 JSON 记录，不修改输入字表及独立的核验记录文档。若字表、字体、尺寸、位置、模糊级别、字号或基线改变，使用新输出目录，例如 `render_samples.py --output samples/v2`。正式数据划分与训练需要另行实施，不能把这里的核验图片直接称作独立测试集。
