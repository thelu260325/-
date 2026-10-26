# Assignment 3：论文评述与Python复现

- [下载完整交付包ZIP](Assignment_3_Package.zip?raw=true)
- [下载报告PDF](report.pdf?raw=true)
- [下载三份未签名声明](Plagiarism_Declarations_Unsigned.pdf?raw=true)
- [查看Python入口](reproduce.py)
- [查看可编辑LaTeX报告](report.tex)

本包基于用户提供的作业说明与指定论文完成。报告采用真实IEEEtran会议模板，双栏、10pt、模板默认页边距；参考文献第1项为官方模板链接。正文约1,810词（按PDF提取统计，包含标题、图表部分文字，不含参考文献），共4页。

## 提交材料

- `report.pdf`：英文技术评述报告。
- `report.tex`：可编辑LaTeX源文件；用Overleaf或本地TeX修改。
- Python源码：`channel.py`、`beamforming.py`、`multiuser.py`、`reproduce.py`、`make_report_figures.py`、`test_model.py`。
- `Plagiarism_Declarations_Unsigned.pdf`：三份空白声明，供三名成员分别确认、填写和签署。未代签或作出个人真实性认证。声明源自同课程Assignment1附件；Assignment3未另附专用表格，请按老师接受的格式提交。

作者姓名沿用你们PPT中的Wei Shuwen、Li Su、Lu Zipeng；提交前核对作者顺序与单位。请按实际工作和课程对AI辅助的要求审核全文与声明。提交平台Moodle；原题截止2026年11月7日。本包未代交Moodle。

## 复现达到的范围

已运行并生成原论文Fig.2–6对应的五类实验：SNR空间分布、信噪比扫描、多用户数量、CSI不确定性、反射阶数。`results/curve_data.csv`含303项求解记录，`results/position_stress.npz`含1000次Eve位置试验。所有曲线来自计算，读图参考点单独存放。

这是**明确假设条件下，对论文目标函数与主要机制的独立复现**，不是作者原始仿真的精确重放。原因是论文缺少灯具坐标、反射率、符号周期、用户分布、归一化等信息；老师已提供的全部资料也没有这些补充参数。完整设置见`channel_assumptions.md`和`results/configuration.json`。

我们使用独立分式优化求解器求解论文目标，没有冒充逐行实现其Algorithm1。报告验证了该独立分解论证的一个反例，并说明了dB步长和多用户选择定义的歧义。全局优化的数学构造与数值计算精度是两个层面；7个鲁棒求解记录保留了optimal_inaccurate标记，不能称为严格数值证书。

在本设置下，20dB、p=infinity、四阶反射的最优值为2.579129bit/s/Hz，接近原图近似2.58；ZF、鲁棒和直达路径基线并非全部一致。鲁棒曲线采用球形误差集最坏情形，而原文提到位置平均，两者不可直接等同。

1000次位置试验使用额外假设的0.25m半径，只有65.9%的样本满足所选0.05信道误差界。不能将0.05解释为5厘米或5%。网格检查1m与0.5m在Bob处的DC增益向量差约0.472%，不代表所有位置及时间抽头都已收敛。

## 运行方式

建议Python3.12及独立虚拟环境。普通安装保留TLS验证。

```bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python test_model.py
python reproduce.py
python make_report_figures.py
```

本次完整仿真约41秒，实际时间取决于硬件。`python reproduce.py --skip-multiuser`只用于调试，会省略多用户图；完整提交应使用不带此选项的命令。原始数组、参数与求解状态均保存到`results/`。

编译报告（在项目根目录，有TeX Live的环境）：

```bash
TEXINPUTS=./template//: pdflatex -interaction=nonstopmode -halt-on-error report.tex
TEXINPUTS=./template//: pdflatex -interaction=nonstopmode -halt-on-error report.tex
```

使用Overleaf时可将`template/IEEEtran.cls`复制到`report.tex`旁，并上传`results/figures/`。保持官方模板的字体、栏宽和页边距，不添加geometry或手动缩放正文。模板来源与校验记录见`template/TEMPLATE_PROVENANCE.md`。

## 数据及引用

`benchmark_points.csv`中的100个点是原图的近似读数，附读数误差，不是作者原始数据，也不是程序输出。`plot_audit.md`说明读图限制；`technical_audit.md`给出数学检查细节。源论文PDF、其截图和原始图像未打包或发布。

现有报告已经区分复现、读图、假设、最坏情形与位置平均。提交前请三位成员实际运行、理解并核对这些内容，保留必要的复现实验记录。
