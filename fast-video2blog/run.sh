#!/bin/bash

# 获取脚本所在的目录，这样无论从哪里运行，都能找到 main.py
# SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
# SCRIPT_DIR = "/Users/qiqizhou/video2txt/"
# echo "脚本所在目录：$SCRIPT_DIR"

# --- Conda 环境激活 ---
# 尝试找到 conda 的 activate 脚本
# 通常在 conda 安装目录的 bin/activate 或者 etc/profile.d/conda.sh
# 用户可能需要根据自己的 conda 安装路径调整
CONDA_BASE="/opt/miniconda3"

# if [ -z "$CONDA_BASE" ]; then
#     echo "错误：无法找到 Conda 安装目录。请确保 Conda 已正确安装并配置在 PATH 中。" >&2
#     # 尝试备用路径 (Mambaforge/Miniforge 常见路径)
#     if [ -f "$HOME/miniforge3/etc/profile.d/conda.sh" ]; then
#         CONDA_BASE="$HOME/miniforge3"
#     elif [ -f "$HOME/mambaforge/etc/profile.d/conda.sh" ]; then
#         CONDA_BASE="$HOME/mambaforge"
#     elif [ -f "$HOME/opt/anaconda3/etc/profile.d/conda.sh" ]; then
#         CONDA_BASE="$HOME/opt/anaconda3"
#     elif [ -f "/opt/homebrew/Caskroom/miniconda/base/etc/profile.d/conda.sh" ]; then # Homebrew M1/M2
#         CONDA_BASE="/opt/homebrew/Caskroom/miniconda/base"
#     elif [ -f "/usr/local/Caskroom/miniconda/base/etc/profile.d/conda.sh" ]; then # Homebrew Intel
#         CONDA_BASE="/usr/local/Caskroom/miniconda/base"
#     else
#         echo "备用 Conda 路径也未找到。请手动配置 CONDA_BASE 变量。" >&2
#         exit 1
#     fi
# fi

# 激活 conda 环境
# shellcheck source=/dev/null
source "${CONDA_BASE}/etc/profile.d/conda.sh"
# add /opt/homebrew/bin/ to PATH
export PATH="/opt/homebrew/bin/:$PATH"

if ! conda activate speech; then
    echo "错误：无法激活 Conda 环境 'speech'。请确保该环境存在。" >&2
    exit 1
fi 

echo "Conda 环境 'speech' 已激活。"

# 切换到应用目录
# cd "$SCRIPT_DIR"

# 运行 Python 应用
echo "正在启动视频转文字工具..."
python /Users/qiqizhou/video2txt/main.py

# （可选）停用 conda 环境，但这在脚本结束时通常会自动处理
# conda deactivate

echo "应用程序已关闭。"