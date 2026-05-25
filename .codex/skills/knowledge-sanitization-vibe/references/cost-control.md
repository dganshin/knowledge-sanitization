# Cost Control

## 网络

进入任何需要联网的服务器步骤前, 先提醒:

```bash
zsh /root/start_mihomo.sh
```

必要时再检查:

```bash
env | grep -i proxy
```

避免因为 clash / mihomo 没开导致:
- `git pull` 失败
- HF 下载失败
- 长实验前才发现网络炸了

## 环境复用

1. 优先复用已有 conda 环境。
2. 不随意新建新环境。
3. 不随意重复安装:
- `torch`
- CUDA 相关大包
- 其它大体积依赖

## 存储原则

默认都放数据盘:

- 模型
- HF cache
- pip cache
- checkpoints
- outputs

系统盘只放必须放系统盘的内容。

## 长实验前的负载原则

先做短 smoke test, 观察:
- 显存占用
- GPU-Util
- 温度

如果明显偏低, 先拉高负载再开始长实验。

优先调:
1. `MICRO_BATCH_SIZE`
2. `BATCH_SIZE`

## 显卡规格档位

先问用户当前开的显卡规格, 再调参。

### 24G 档
- 先保守
- 小步增加 `MICRO_BATCH_SIZE`

### 40G / 48G 档
- 可以更积极提高 `MICRO_BATCH_SIZE`
- 再提高 `BATCH_SIZE`

### 80G 档
- 可以显著提高负载
- 但仍先短测再长跑

## 过夜实验

只有在用户明确说:
- 今晚跑
- 明天再看

才主动建议:
- 跑完保存结果后自动关机

否则不要默认加自动关机命令。

## Git 节奏

重要修改后:
1. 及时提交
2. 及时推送到远程 fork
3. 再提醒服务器 `git pull`

避免上下文切换后本地和服务器分叉。
