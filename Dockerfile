# 使用官方Python基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制当前目录内容到容器的/app目录
COPY . /app

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt  

# 暴露端口
EXPOSE 8080

# 运行命令
CMD ["python", "app.py"]