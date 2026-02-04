# 第一阶段：构建依赖
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

# 环境变量设置
ENV UV_COMPILE_BYTECODE=1 
ENV UV_LINK_MODE=copy

WORKDIR /app

# 安装 git (必须，因为依赖中有 git 仓库)
RUN apt-get update && apt-get install -y git

# 复制依赖定义文件
COPY pyproject.toml uv.lock ./

# 同步依赖
# --frozen: 严格遵守 uv.lock，不更新 lock 文件
# --no-dev: 不安装开发依赖
# --no-install-project: 不安装当前项目本身
RUN uv sync --frozen --no-dev --no-install-project

# 第二阶段：生成最终镜像
FROM python:3.12-slim-bookworm

WORKDIR /xiaomi_plugin_power

# 从 builder 阶段复制构建好的虚拟环境
# 注意：我们将 .venv 复制到 /app/.venv (或者直接复制到项目目录下，这里为了清晰放在 /env)
COPY --from=builder /app/.venv /env

# 将虚拟环境的 bin 目录添加到 PATH
# 这样执行 python 或 pip 时会自动使用虚拟环境中的版本
ENV PATH="/env/bin:$PATH"

# 复制项目代码
COPY . /xiaomi_plugin_power

CMD ["python", "main.py"]