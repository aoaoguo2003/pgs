# 企鹅个体识别（Penguin Individual Re-Identification）

[English](README.md) | **中文**

给定一张**洪堡企鹅（Humboldt penguin）**照片，识别它是**哪一只**具体的企鹅（个体身份，非物种）。最终目标：游客拍一张照片，即可查出对应企鹅个体，以及它的名字、特征、习性。本项目所有个体均为同一种群的洪堡企鹅。

项目正从**分类 baseline** 演进为 **embedding 检索 + RAG** 系统——把每张照片转成向量，在向量数据库中匹配，再用 LLM 生成有事实依据（grounded）的企鹅介绍。检索内核已跑通，但一次**数据泄露审计**（[§5](#5-数据泄露审计与跨场次评估)）发现：原来的头号数字被**训练/测试之间共享的同场次连拍**抬高了——诚实的**跨场次** top-1 只有 **~0.49**（同场次 ~0.96）。缩小这个差距（靠度量学习 + 更多样的照片），连同档案/RAG 层与对话式界面，是当前的工作。

---

## 目录
- [1. 数据集](#1-数据集)
- [2. 已完成的实验](#2-已完成的实验)
- [3. 实验数据记录图](#3-实验数据记录图)
- [4. 关键结论](#4-关键结论)
- [5. 数据泄露审计与跨场次评估](#5-数据泄露审计与跨场次评估)
- [6. 旗舰方案：Embedding 检索 + RAG](#6-旗舰方案embedding-检索--rag)
- [7. 目录结构](#7-目录结构)
- [8. 复现方式](#8-复现方式)

---

## 1. 数据集

- 原始数据 `penguins_data/`：共 **82 只**企鹅，每只照片数从 1 到 291 张不等，**长尾严重不均衡**。
- 按「照片数 ≥ 16 张」筛选出 **44 只**作为可训练个体（`penguin_image_count_summary.csv` 中 `selected=True`），其余 37 只（≤15 张）样本太少，暂不参与训练。
- 已按个体切分为 train / val / test：`penguins_dataset_split/`。
- 肚子裁剪版本数据（由肚子检测器裁出）：`penguins_dataset_split_belly_by_yoloV8/`。

> 即便在筛选后的 44 类内部，样本量仍从 291（Medici）到约 16，最大/最小差约 18 倍，是后续所有难点的根源。见 [图 05](#3-实验数据记录图)。

## 2. 已完成的实验

| 实验 | 输入 | 模型 | 训练轮次 | best val acc | **test acc** |
|---|---|---|---|---|---|
| **exp1 baseline** | 全身照 | ResNet18（迁移学习） | 29（早停，上限30） | 0.907 | **0.950** |
| **exp2 belly** | 肚子裁剪图 | ResNet18（迁移学习） | 39（早停，上限50） | 0.867 | 0.866 |
| **belly detector** | 全身照 | YOLOv8s 检测 | 98 | mAP@50 ≈ 0.98 | mAP@50-95 ≈ 0.60 |
| **exp3 向量检索** | 全身照 | ResNet18 特征 + FAISS（免训练） | — | — | **0.959**（原型）/ 0.947（1-NN）/ 0.978（top-5） |

> ⚠️ **泄露提醒：** 上表 exp1（0.950）与 exp3（0.959）的准确率用的是**随机划分**。后续审计发现同场次连拍会泄露进测试集、抬高这些数字；诚实的**跨场次** top-1 只有 **~0.44–0.49**。详见 [§5](#5-数据泄露审计与跨场次评估)。

三者共用流程：
- `torchvision.datasets.ImageFolder` 加载
- 迁移学习（ImageNet 预训练 ResNet18）
- 类别不均衡处理：`WeightedRandomSampler` + 类别加权 `CrossEntropyLoss`
- 按验证集准确率保存最优 checkpoint，最后在 test 上评估并导出预测 CSV

**exp1（全身照）**——test accuracy **0.950**，best val 0.907（第 21 轮）。每类表现见 [图 04](#3-实验数据记录图)：样本多的个体（Cooper n=20、Ron_burgundy n=29、Medici n=44）几乎全对；出错集中在 test 只有 3~5 张样本的小类。

**exp2（肚子裁剪）**——test accuracy **0.866**，明显**低于**全身照的 0.950。其 val loss 始终高于 exp1（[图 01](#3-实验数据记录图) 右），泛化更差。

**肚子检测器（YOLOv8s）**——训练 98 轮，验证 **mAP@50 ≈ 0.98、mAP@50-95 ≈ 0.60**，precision/recall 约 0.95（[图 03](#3-实验数据记录图)）。权重：`runs/detect/runs/belly_detector/exp1/weights/best.pt`。检测本身够好，但裁剪会**丢弃脸/胸带/体型等身份信息**，且检测误差会传播给下游分类器——这解释了实验二为何更差。

**exp3（向量检索——旗舰方案的 CNN 路线）**——复用 exp1 的 ResNet18 作为**冻结的 512 维特征提取器**（去掉分类头），把 train+val 全部图片注册进 **FAISS** 向量库，对 test 照片用最近邻 / 类原型检索识别。**不做新训练。** 结果：原型（类均值）top-1 **0.959**、1-NN top-1 0.947、top-5 0.978——即检索式识别**追平/略超** softmax 分类器（0.950），同时得到一个可注册的向量库（新个体直接入库、无需重训）。代码：`embedding_id/`（`embedder.py`、`build_and_eval.py`、`identify.py`），这就是 `identify_penguin` 工具的可用内核。

## 3. 实验数据记录图

所有图由 `plot_experiments.py` 从各 run 的日志重新生成，输出到 `figures/`。

**图 01 — 分类器训练曲线（全身 vs 肚子）**
![训练曲线](figures/01_classifier_training_curves.png)

**图 02 — 最终 44 类 test 准确率对比**
![准确率对比](figures/02_test_accuracy_comparison.png)

**图 03 — 肚子检测器（YOLOv8s）验证指标**
![检测器指标](figures/03_belly_detector_map.png)

**图 04 — 实验一每类 test 准确率（按准确率排序，含每类支持样本数 n）**
![每类准确率](figures/04_exp1_per_class_accuracy.png)

**图 05 — 数据集每个个体的照片数分布（蓝=入选可训练，灰=样本太少被弃）**
![数据分布](figures/05_dataset_distribution.png)

## 4. 关键结论

1. **全身照 > 肚子裁剪（0.950 vs 0.866）。** 身份信号不只在肚子——脸部花纹、胸前黑带、体型比例都是线索。裁得太狠会丢信息，检测误差还会传播噪声。
2. **训练/采集标准 = 全身正面照。** 不再强求肚子清晰完整。
3. **只用正面。** 企鹅背部大面积均匀深色，个体间几乎无差别，正反混训会拉高类内方差、引入跨类混淆。线上系统对「非正面」照片应提示重拍，而不是硬给身份。
4. **瓶颈是数据，不是模型。** 错误几乎全部落在样本 ≤5 张的小类上；样本多的个体已接近满分。提升上限的关键是**补数据 + 更强的少样本/度量学习方法**，而非单纯换更大的 backbone。一次去泄露的评估（[§5](#5-数据泄露审计与跨场次评估)）把这一点坐实了：跨场次准确率远低于随机划分的数字。

## 5. 数据泄露审计与跨场次评估

数据集里有很大一部分是**连拍序列**——同一台相机、同一时刻、连续帧号（如 `DSC_2743…2749`）。由于 `a.py` 对每只企鹅的照片**随机划分**，同一组连拍的近重复帧可能同时落入训练集和测试集；模型于是被拿"其实已经见过的照片"来考，准确率因此虚高。

**审计**（`analysis/leakage_audit.py`）——用与模型无关的信号（感知哈希、像素相关、EXIF 拍摄时间、文件名帧号）：
- **13.8%** 的测试图在 train+val 底库里有近重复；
- **97.8%** 与底库里的照片来自同一**拍摄场次**；
- 在有 EXIF 的照片中，约 29% 与最近的训练图拍摄间隔 ≤1 秒。

**诚实重评。** 我们改为**按整个场次划分**（任何一组连拍不跨训练/测试），并**从零重训**，同时设一个**随机划分对照组**：同样 35 只、同样 1743 张、每只张数完全一致——这样任何差距都只能归因于划分方式，而非数据变少。按场次划分的测试集近重复为 **0%**，对照组为 **10%**。

| 指标 | 随机划分（泄露） | 按场次划分（诚实） | 差距 |
|---|---|---|---|
| softmax 分类 top-1 | 0.943 | **0.433** | +0.510 |
| 检索 原型 top-1 | 0.950 | **0.490** | +0.460 |
| 检索 1-NN top-1 | 0.931 | 0.441 | +0.490 |
| 检索 top-5 | 0.958 | **0.594** | +0.364 |

对照组**复现了 ~0.95 的头号数字**，所以掉分能干净地归因于划分方式。两条路一起塌——区分能力其实来自一个"见过所有场次"的特征提取器。**诚实的跨场次 top-1 约 0.44–0.49（top-5 约 0.59）：** 原来的 0.95/0.959 主要衡量的是*同场次*识别，高估了*跨场次*（换一天/换光线）的真实泛化。

**开放集阈值**（`embedding_id/tune_openset.py`）——识别器还必须会说"我不认识这只"（约 81 只种群里只登记了 44 只）。用留一法模拟未知个体，已知 vs 未知的可分性为 **AUC 0.991**；置信阈值从 **0.55 提到 0.80**（放行 91.9% 已登记、拒绝 96.6% 未登记），于是未登记企鹅会被拒识而不是被张冠李戴。

**含义。** 真正的挑战是**跨场次泛化**（而非同场次准确率），且它受限于数据：44 只已登记个体中有 10 只只有一到两个拍摄场次。这引出接下来两个抓手：**ArcFace 度量学习**（特征直接为余弦检索度量而建）与**为每只个体补拍多场次照片**。

脚本：`analysis/leakage_audit.py`、`analysis/build_session_splits.py`、`analysis/eval_session_retrain.py`、`analysis/session_disjoint_eval.py`、`embedding_id/tune_openset.py`。

## 6. 旗舰方案：Embedding 检索 + RAG

核心方向：把分类器升级为**多模态检索 + 检索增强生成（RAG）**应用。

### 流水线
```
游客照片
   │
   ▼
[检测 + 正面过滤]  ── 非正面 / 非企鹅 ──▶ “请重拍”
   │
   ▼
[图像 embedding 模型]  （ArcFace 训练的 backbone，或 CLIP / DINOv2）
   │  照片 → 向量
   ▼
[向量数据库：企鹅底库]  （FAISS / Qdrant / Milvus / pgvector）
   │  ANN 检索 top-k 已注册向量
   ▼
[匹配 + 开放集阈值]  ── 距离过大 ──▶ “未知个体”
   │  身份 = Cooper
   ▼
[知识检索 — RAG]
   ├─ Cooper 的结构化档案（名字、年龄、性别、脚环颜色、性格、习性、饲养员备注）
   └─ 企鹅通用知识片段（物种生物学、种群、保育）
   │
   ▼
[LLM 基于检索文档生成]  → 名字、特征、习性、回答游客问题
```

### RAG 的两种角色（同时使用）
1. **档案 grounded 生成**——识别出身份后，取该个体的档案文档，让 LLM 生成自然语言介绍。grounding 能防止模型**对一只真实、有名字的动物编造事实**——这是这里用 RAG 的一个具体、站得住脚的理由。
2. **开放域问答**——一个知识库（企鹅生物学、种群、饲养、保育）切块 + 向量化；游客自由提问时检索相关片段 → 有引用来源的 grounded 回答。

### 可选的 Agent 层
一个 LLM agent 编排工具：`identify_penguin(image)`、`get_profile(name)`、`search_knowledge(query)`——由模型决定调用哪个。这在一个系统里同时展示 **AI agent + 多模态检索 + RAG**。

### 产品形态：可对话的洪堡企鹅专家
面向用户的外壳是一个聊天窗口。用户扫码 / 打开 App 进入时，机器人主动打招呼：

> 🐧 你好！我是这里的**洪堡企鹅专家**。拍一张企鹅的**正面全身照**发给我，我就能告诉你它是哪一只，以及它的名字、生日、性格和小故事～ 关于企鹅的任何问题也都可以问我！

- **人设** = agent 的 system prompt（亲切、简洁，像热情的饲养员）。
- **照片 → 身份**：收到企鹅照片触发 `identify_penguin`，再用 `get_profile` 介绍这一只。
- **问题 → 知识**：通用企鹅问题触发 `search_knowledge`。
- **会话记忆**：把本次识别出的企鹅存进会话状态，后续追问（"它几岁？"）无需重新上传照片。
- **不确定时优雅处理**：置信度低 / 非正面照时，请用户重拍清晰正面照，而不是硬猜。
- **事实 grounding**：关于某只企鹅的事实只来自 `get_profile`，字段缺失就如实说没有，绝不编造——这是防幻觉的核心保证。

### 建议技术栈
- **图像 embedding**：当前用 exp1 的 ResNet18 作冻结特征提取器（exp3）；计划训练 ArcFace backbone，并与开箱即用的 **DINOv2 / CLIP** 做对照。
- **向量数据库**：FAISS（简单/本地）→ **Qdrant**（更有生产感）做 demo。
- **文本 embedding**：开源 `bge` / `e5`，用于知识库。
- **LLM**：**本地部署的开源模型**（如 Qwen / Llama），可选在企鹅资料上做 **LoRA 微调**——自建部署而非付费 API——做 grounded 生成 + 引用。
- **服务**：FastAPI 后端 + Streamlit/Gradio demo 前端。
- **评测**：检索命中率（top-k）、回答 **忠实度/grounded 程度**、开放集拒识精度。

### 技术范围
本方案综合了细粒度计算机视觉、**度量学习**、**向量数据库**、**多模态 RAG**、**带防幻觉护栏的 grounded LLM 生成**与 **RAG 评测**，并应用于真实数据集。

### 当前状态与下一步
**已完成**——CNN 检索路线（exp3）：一个可用的 **FAISS 向量数据库**，支持**增量注册**（新企鹅存入特征即可登记，无需重训）与**开放集拒识**（阈值经留一法调到 **0.80**，AUC 0.991；照片模糊/未登记 → 拒识而非张冠李戴）。一次**数据泄露审计**（[§5](#5-数据泄露审计与跨场次评估)）确立了诚实的基线：同场次 top-1 ~0.96，但**跨场次仅 ~0.49**。分类器路线仅保留作基线；**检索是今后的识别方式**。

**下一步**
1. **缩小跨场次差距（优先）**——**ArcFace** 度量学习重训（特征直接为余弦检索度量而建，并在按场次划分上评估）+ 为只拍过一两个场次的个体**补拍多场次照片**。（免训练的测试时增强 TTA 实测无增益，因为模型训练时已用了水平翻转增强。）
2. **建立整洁的企鹅档案库**——每只一份结构化记录（姓名、出生日期、性格、特征、习性、脚环颜色），用于给 `get_profile` 做事实支撑。
3. **搭建 agent 主循环**——用 LLM 的 function-calling / tool-use 编排 `identify_penguin` / `get_profile` / `search_knowledge`，并带会话记忆。
4. **对话式洪堡企鹅专家界面**——聊天窗口，含上文的欢迎语与会话记忆。

## 7. 目录结构

```text
pgs/
├─ README.md / README.zh-CN.md       # 中英双语文档
├─ plot_experiments.py               # 由日志重新生成 figures/
├─ figures/                          # 实验记录图（PNG）
├─ penguin_image_count_summary.csv   # 82 只个体照片数与是否入选
├─ make_doc.py                       # 生成《企鹅照片收集清单》.docx
│
├─ a.py                              # 按个体划分 train/val/test
├─ train_experiment1.py              # 分类训练脚本（exp1/exp2，及 §5 的重训）
├─ eval_checkpoint.py                # checkpoint 评估
├─ crop_penguin_belly_yolo.py        # 用 YOLO 裁肚子
├─ prepare_belly_yolo_dataset.py     # 准备肚子检测数据集
├─ train_belly_detector.py           # 训练肚子检测器
├─ annotate_belly.py                 # 肚子标注工具
│
├─ embedding_id/                     # 检索内核：特征提取、向量库、识别、开放集调阈
├─ analysis/                         # 数据泄露审计与跨场次评估（§5）
│
├─ penguins_data/                    # 原始数据
├─ penguins_dataset_split/           # 全身照 train/val/test（exp1）
├─ penguins_dataset_split_belly_by_yoloV8/  # 肚子裁剪 train/val/test（exp2）
│
└─ runs/
   ├─ exp1_baseline/                 # 全身照分类结果
   ├─ exp2_belly_resnet18/           # 肚子裁剪分类结果
   ├─ exp1b_session_disjoint/        # §5 诚实的跨场次重训
   ├─ exp1b_random_control/          # §5 随机划分对照组
   └─ detect/…/belly_detector/exp1/  # 肚子检测器结果
```

## 8. 复现方式

安装依赖（RTX 4060 用 CUDA 版 PyTorch）：
```powershell
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
pip install numpy pillow ultralytics matplotlib python-docx
```

训练分类器：
```powershell
# 实验一：全身照
python train_experiment1.py --data-dir penguins_dataset_split --epochs 30 --batch-size 32
# 实验二：肚子裁剪
python train_experiment1.py --data-dir penguins_dataset_split_belly_by_yoloV8 --epochs 50 --batch-size 32
```

数据泄露审计与诚实的跨场次评估（§5）：
```powershell
# 量化当前划分里的连拍/场次泄露
python analysis/leakage_audit.py
# 构建按场次划分 + 随机对照划分，然后重训并对比
python analysis/build_session_splits.py
python train_experiment1.py --data-dir penguins_dataset_split_session_disjoint --output-dir runs/exp1b_session_disjoint
python train_experiment1.py --data-dir penguins_dataset_split_session_random  --output-dir runs/exp1b_random_control
python analysis/eval_session_retrain.py
# 调开放集拒识阈值（留一法）
python embedding_id/tune_openset.py
```

重新生成实验图 / 照片清单：
```powershell
python plot_experiments.py
python make_doc.py
```
