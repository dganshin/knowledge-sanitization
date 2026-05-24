# Knowledge Sanitization Setup Progress

## 目标

在 AutoDL 上为 `knowledge-sanitization` 项目完成可复用的运行准备，尽量把耗时工作放在 CPU 计费阶段，减少 GPU 计费阶段的浪费时间。

最终目标分 2 部分：

1. 在 CPU 模式完成环境准备、目录规划、脚本预检查、模型下载准备
2. 在 GPU 模式补齐 `torch/peft/bitsandbytes/accelerate` 并运行 `run_sanitization.sh`

## 项目结论

这个仓库不是产品项目，而是论文 `Knowledge Sanitization of Large Language Models` 的实验代码。

核心流程：

1. `finetune.py`
   - 用 `LlamaForCausalLM` + LoRA 做训练
2. `task.py`
   - 在 3 类测试集上做评测
3. `run_sanitization.sh`
   - 把训练和评测串起来

仓库要求的基础模型不是任意模型，而是：

- `LLaMA 7B`
- Hugging Face 格式
- 目录预期类似 `.../llama-hf/7B`

不能直接把 `meta-llama/llama` GitHub 仓库当作 `base_model` 使用，因为当前代码是按 Hugging Face `from_pretrained()` 目录格式加载模型的。

## 当前目录规划

建议使用数据盘：

- 项目目录: `/root/autodl-tmp/projects/knowledge-sanitization`
- 模型目录: `/root/autodl-tmp/models/llama-hf/7B`
- pip 缓存: `/root/autodl-tmp/.cache/pip`
- Hugging Face 缓存: `/root/autodl-tmp/.cache/huggingface`
- checkpoints: `/root/autodl-tmp/checkpoints`
- outputs: `/root/autodl-tmp/outputs`

## 当前进度

### 已完成

1. 已创建并使用 CPU 环境：
   - conda env: `ks310`
   - Python: `3.10`

2. 已确认并清理代理问题：
   - `mihomo` 已可启动
   - 监听端口：
     - HTTP: `127.0.0.1:7890`
     - SOCKS: `127.0.0.1:7891`

3. 已完成基础非 GPU 依赖安装：
   - `datasets==2.17.1`
   - `fire==0.5.0`
   - `scikit-learn==1.7.2`
   - `sentencepiece==0.2.1`
   - `tqdm==4.65.0`
   - `transformers==4.28.0`
   - `huggingface_hub`

4. 已完成基础 import 检查：
   - `datasets`
   - `fire`
   - `transformers`
   - `sentencepiece`
   - `tqdm`
   - `huggingface_hub`
   - `sklearn`

5. 已完成目录准备：
   - `/root/autodl-tmp/.cache/pip`
   - `/root/autodl-tmp/.cache/huggingface`
   - `/root/autodl-tmp/models/llama-hf/7B`
   - `/root/autodl-tmp/checkpoints`
   - `/root/autodl-tmp/outputs`

6. 已完成代码静态检查：

```zsh
python -m py_compile finetune.py task.py generate.py utils/prompter.py
```

7. 已做过磁盘清理：
   - 删除了部分系统盘 `pip` 缓存
   - 删除了一个较大的 Qwen HF 模型缓存
   - 当前系统盘和数据盘空间已比之前更合理

### 尚未完成

1. 还没有下载项目真正需要的基础模型
   - 目标应为 Hugging Face 格式的 `LLaMA 7B`
   - 当前 `/root/autodl-tmp/models/llama-hf/7B` 还是空目录

2. Hugging Face 登录还未成功
   - `huggingface-cli login` 交互式登录失败
   - 需要改用 token 方式登录

3. 还没有安装 GPU 相关依赖
   - `torch`
   - `peft`
   - `bitsandbytes`
   - `accelerate`

4. 还没有修改 `run_sanitization.sh`

## 已确认的脚本问题

### 1. 模型路径未填写

`run_sanitization.sh` 里还是占位符：

```bash
base_model='{your-llama-path}/llama-hf/7B'
```

后续应改为类似：

```bash
base_model='/root/autodl-tmp/models/llama-hf/7B'
```

### 2. 训练文件后缀写错

脚本中当前是：

```bash
train_sanitize="${python_dir}/data/triviaqa_${num}/train_5-forget-answers_85-percent-retain.json"
```

但仓库实际文件是：

```text
train_5-forget-answers_85-percent-retain.jsonl
```

所以后续必须改成 `.jsonl`。

### 3. 默认 batch 太大

当前脚本默认：

```bash
--batch_size 128
--micro_batch_size 128
--num_epochs 20
```

这对于普通单卡 smoke test 不现实，后续应先改成小规模测试值，比如：

```bash
--batch_size 8
--micro_batch_size 1
--num_epochs 1
```

## CPU 模式还可以做的事

### 必做

1. 生成 Hugging Face token
2. 完成 Hugging Face 登录
3. 下载目标基础模型到数据盘
4. 修改 `run_sanitization.sh`

### 可选

1. 预下载普通 wheel 包到 `/root/autodl-tmp/wheels`
2. 把代理和 `mihomo` 启动写入 shell 初始化脚本

## GPU 模式再做的事

以下内容建议等开卡后再做：

1. 安装 `torch`
2. 安装 `peft==0.3.0`
3. 安装 `bitsandbytes`
4. 安装 `accelerate`
5. 用 `nvidia-smi` 检查 GPU
6. 先跑 `triviaqa_1` 的 smoke test

## Hugging Face Token 获取方式

在 Hugging Face 网站中操作：

1. 登录 Hugging Face
2. 打开 `Settings`
3. 打开 `Access Tokens`
4. 创建一个 `Read` 权限 token

服务器中推荐这样登录：

```zsh
hf auth login --token <YOUR_TOKEN>
hf auth whoami
```

如果 `hf auth whoami` 能显示账号名，才算登录成功。

## 模型下载说明

当前仓库要的是 Hugging Face 格式的 `LLaMA 7B`，不是直接使用 `meta-llama/llama` GitHub 仓库。

模型下载目标目录：

```text
/root/autodl-tmp/models/llama-hf/7B
```

下载命令模板：

```zsh
hf download <repo_id> \
  --local-dir /root/autodl-tmp/models/llama-hf/7B \
  --local-dir-use-symlinks False
```

注意：

- `<repo_id>` 需要替换成你实际拥有权限的 HF 模型仓库
- 如果是受限的 LLaMA 模型，光有 token 不够，还需要该账号已获访问授权

## 当前推荐的下一步

### 新设备接手时先做

```zsh
conda activate ks310
zsh /root/start_mihomo.sh
export http_proxy=http://127.0.0.1:7890
export https_proxy=http://127.0.0.1:7890
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
export all_proxy=socks5://127.0.0.1:7891
export ALL_PROXY=socks5://127.0.0.1:7891
export PIP_CACHE_DIR=/root/autodl-tmp/.cache/pip
export HF_HOME=/root/autodl-tmp/.cache/huggingface
export TRANSFORMERS_CACHE=/root/autodl-tmp/.cache/huggingface/transformers
cd /root/autodl-tmp/projects/knowledge-sanitization
```

### 然后优先做

1. 用 HF token 登录
2. 下载基础模型到 `/root/autodl-tmp/models/llama-hf/7B`
3. 修改 `run_sanitization.sh`
4. 开 GPU 后安装 GPU 依赖
5. 运行 smoke test

## 备注

当前最大的未完成事项不是 Python 基础环境，而是：

1. 基础模型尚未下载
2. GPU 依赖尚未安装
3. 运行脚本尚未改成可执行配置

## 换设备前强调

### 1. 一定使用数据盘里的项目目录

真正工作的目录是：

```text
/root/autodl-tmp/projects/knowledge-sanitization
```

不要再回到旧路径：

```text
/root/projects/knowledge-sanitization
```

### 2. 目前还没有下载基础模型

虽然目录已经建好：

```text
/root/autodl-tmp/models/llama-hf/7B
```

但这里当前还是空的。没有基础模型，后续训练和评测都不能开始。

### 3. 目前还没有安装 GPU 相关依赖

以下内容仍然未安装或未确认：

- `torch`
- `peft`
- `bitsandbytes`
- `accelerate`

这些建议在 GPU 实例里再处理，不要误以为当前环境已经可直接运行训练。

### 4. `run_sanitization.sh` 还没改完

提交前要记住，脚本仍处于“待修改”状态，至少还要改：

1. `base_model`
2. `train_sanitize` 的 `.json` -> `.jsonl`
3. `batch_size`
4. `micro_batch_size`
5. `num_epochs`

### 5. 换设备后先启动代理再联网

推荐顺序：

```zsh
zsh /root/start_mihomo.sh
export http_proxy=http://127.0.0.1:7890
export https_proxy=http://127.0.0.1:7890
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
export all_proxy=socks5://127.0.0.1:7891
export ALL_PROXY=socks5://127.0.0.1:7891
```

否则 `git`、`pip`、`conda`、`hf` 相关命令可能再次出现连接失败。

### 6. 换设备后先进入正确环境

```zsh
conda activate ks310
cd /root/autodl-tmp/projects/knowledge-sanitization
```

### 7. Hugging Face 还没有登录成功

之前的交互式登录没有真正保存 token，所以换设备后应直接使用：

```zsh
hf auth login --token <YOUR_TOKEN>
hf auth whoami
```

只有 `hf auth whoami` 能正常显示账号，才说明可以继续下载模型。

### 8. 数据盘不会随镜像保存

`/root/autodl-tmp` 适合放模型、缓存和项目运行数据，但它不会随保存镜像自动保留。

所以如果后续不是继续使用同一台实例，而是重新开新实例，一定要重新确认这些内容是否还在：

- 项目目录
- 模型目录
- HF 缓存
- wheels 缓存

### 9. 长任务尽量后台执行

后续像模型下载、安装大包、运行训练这类长任务，建议使用 `screen`、`nohup` 或类似方式，避免换设备或断开 SSH 后任务被中断。
