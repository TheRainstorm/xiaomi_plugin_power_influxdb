# 第一阶段：构建依赖
FROM python:3.12 as builder
COPY requirements.txt .
RUN pip install --user -r requirements.txt
    # && pip install git+https://github.com/rytilahti/python-miio.git@0aa4df3ab1e47d564c8312016fbcfb3a9fc06c6c

# 第二阶段：生成最终镜像
FROM python:3.11-slim
COPY --from=builder /root/.local /root/.local
COPY . /xiaomi_plugin_power
WORKDIR /xiaomi_plugin_power
CMD ["python", "main.py"]
