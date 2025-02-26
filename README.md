# WeChat2NPM - 企业微信与 Telegram 集成 Nginx Proxy Manager 工具

WeChat2NPM 是一个用于将 **企业微信** 和 **Telegram** 与 Nginx Proxy Manager (NPM) 集成的工具，允许用户通过企业微信应用或 Telegram Bot 远程控制 NPM 的流状态（开启或关闭代理）。通过简单的配置，用户可以在企业微信或 Telegram 中一键开启或关闭 NPM 的代理服务，方便管理内网穿透。

---

## 功能特性

- **企业微信集成**：通过企业微信应用实现远程控制 NPM 的流状态。
- **Telegram 集成**：通过 Telegram Bot 实现远程控制 NPM 的流状态。
- **Nginx Proxy Manager 支持**：与 NPM 无缝集成，支持通过 API 控制代理状态。
- **Docker 支持**：通过 Docker 容器化部署，简化安装和配置过程。
- **自定义菜单**：支持在企业微信中创建自定义菜单，方便用户操作。
- **日志记录**：支持不同级别的日志记录，便于调试和监控。

---

## 快速开始

### 1. 安装 Docker 和 Docker Compose

确保你已经安装了 Docker 和 Docker Compose。如果尚未安装，请参考以下链接进行安装：

- [Docker 安装指南](https://docs.docker.com/get-docker/)
- [Docker Compose 安装指南](https://docs.docker.com/compose/install/)

### 2. 配置环境变量

在项目根目录下创建一个 `.env` 文件，并填写以下内容：

```yaml
# 企业微信配置
WECHAT_TOKEN=              # 企业微信回调 Token
WECHAT_ENCODING_AES_KEY=   # 企业微信回调 EncodingAESKey
WECHAT_CORP_ID=            # 企业 ID
WECHAT_CORP_SECRET=        # 企业应用 Secret
WECHAT_API_TOKEN=nginx     # 企业微信回调 API Token

# Telegram 配置
TELEGRAM_TOKEN=            # Telegram Bot Token
TELEGRAM_CHAT_ID=          # Telegram Chat ID

# NPM 配置
NPM_URL=http://172.17.0.1:81 # NPM URL
NPM_ITEM_ID=1               # NPM Item ID
NPM_IDENTITY=               # NPM 邮箱地址
NPM_SECRET=                 # NPM 密码

# 其他配置
# CURRENT_THREAD_WAIT_TIME=7200 # NPM Stream 开启时长，单位秒；默认 7200
# LOG_LEVEL=INFO             # 日志级别，默认 INFO
# PIC_URL_OPEN=            # NPM 状态开启响应图片
# PIC_URL_CLOSED=          # NPM 状态关闭响应图片
```

### 3. 启动服务

使用以下命令启动服务：

```bash
wget https://raw.githubusercontent.com/getyufelix/wechat2npm/refs/heads/main/docker-compose.yml

vi docker-compose.yaml # 【可选】

docker compose up -d
```

---

## 企业微信配置

### 1. 创建企业微信应用

1. 登录企业微信管理后台，创建一个新的应用。
2. 获取以下信息并填写到 `.env` 文件中：
   - **企业 ID** (`WECHAT_CORP_ID`)
   - **应用 Secret** (`WECHAT_CORP_SECRET`)
   - **回调 Token** (`WECHAT_TOKEN`)
   - **回调 EncodingAESKey** (`WECHAT_ENCODING_AES_KEY`)

### 2. 配置回调 URL

在企业微信应用设置中，配置回调 URL 为 `https://<你的服务器地址>/api/v1/message/?token=<WECHAT_TOKEN>`。

### 3. 创建自定义菜单

在企业微信中创建自定义菜单，允许用户通过菜单项开启或关闭 NPM 代理。你可以使用以下 Python 脚本创建菜单：

[create\_menu.py](https://raw.githubusercontent.com/getyufelix/wechat2npm/refs/heads/main/create_menu.py)

---

## Telegram 配置

### 1. 创建 Telegram Bot

1. 打开 Telegram，搜索 `@BotFather`。
2. 发送 `/newbot`，按照提示创建你的 Bot。
3. 创建完成后，`BotFather` 会提供一个 Token，将其保存到 `.env` 文件中，作为 `TELEGRAM_TOKEN` 的值。

### 2. 设置 Bot 命令

为了让 Bot 更易用，可以设置自定义命令菜单：

1. 向 `@BotFather` 发送 `/setcommands`。
2. 按照提示发送以下内容：

   ```
   enable - 开启NPM代理
   disable - 关闭NPM代理
   ```

---

## 使用方法

### 通过企业微信控制 NPM

1. 在企业微信中打开配置的应用。
2. 点击自定义菜单中的“Enable”或“Disable”按钮，即可开启或关闭 NPM 的代理服务。

### 通过 Telegram 控制 NPM

1. 在 Telegram 中打开你的 Bot。
2. 发送 `/enable` 开启 NPM 代理。
3. 发送 `/disable` 关闭 NPM 代理。

---

## 注意事项

- **安全性**：确保你的 NPM 管理界面和 API 接口受到保护，避免未经授权的访问。
- **资源管理**：在不使用 NPM 代理时，请务必关闭代理服务，以避免不必要的资源消耗。
- **日志监控**：定期检查日志文件，确保系统运行正常。

---

## 贡献

欢迎提交 Issue 和 Pull Request，帮助我们改进 WeChat2NPM。

---

## 许可证

本项目采用 MIT 许可证。详情请参阅 [LICENSE](LICENSE) 文件。

---

感谢使用 WeChat2NPM！
