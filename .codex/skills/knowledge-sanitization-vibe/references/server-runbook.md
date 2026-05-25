# Server Runbook

## 默认服务器进入步骤

```bash
cd /root/autodl-tmp/projects/knowledge-sanitization
git pull --rebase origin master
conda activate ks310
```

## 长任务前

优先:

```bash
tmux new -s ks_run
```

备选:

```bash
screen -S ks_run
```

## 首轮 smoke test

```bash
LOAD_IN_8BIT=false BATCH_SIZE=8 MICRO_BATCH_SIZE=1 NUM_EPOCHS=1 bash run_sanitization.sh
```

## 若只想看 GPU

```bash
watch -n 1 nvidia-smi
```

## Git 拉取失败时

先确认代理和 Git 代理:

```bash
zsh /root/start_mihomo.sh
export http_proxy=http://127.0.0.1:7890
export https_proxy=http://127.0.0.1:7890
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
unset all_proxy
unset ALL_PROXY
git config --global http.proxy http://127.0.0.1:7890
git config --global https.proxy http://127.0.0.1:7890
GIT_CURL_VERBOSE=1 git ls-remote origin
```
