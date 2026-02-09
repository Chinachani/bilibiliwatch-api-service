# bilibiliwatch-api-service

这是为 AstrBot 插件 `astrbot_plugin_bilibiliwatch` 配套的独立 API 服务，提供 B 站视频信息解析、下载任务与扫码登录接口。

## 版权与来源
本项目基于开源项目 **Suxiaoqinx/bilibili** 进行整理与适配，原项目使用 **MIT License**。原作者信息已保留在 `LICENSE` 中。

## 功能概览
- 视频信息解析：`/api/video/info`
- 质量列表：`/api/video/quality`、`/api/video/quality/json`
- 下载任务：`/api/video/download`、`/api/download/status/{id}`、`/api/download/file/{id}`
- 合并音视频：`/api/download/merge/{id}`
- 任务列表与取消：`/api/tasks`、`/api/tasks/json`、`/api/tasks/cancel/{id}`
- 删除任务：`/api/tasks/remove/{id}`
- 文件列表与删除：`/api/files`、`/api/files/{filename}`
- 下载指定文件：`/api/files/{filename}`
- 扫码登录：`/api/login/qr`、`/api/login/qr/image`、`/api/login/status`

## 运行
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn fastapi_app:app --host 0.0.0.0 --port 8000
```

## 回调推送（可选）
下载完成后可主动通知机器人插件（HTTP 回调）。

环境变量：
- `CALLBACK_URL`：回调地址，例如 `http://机器人IP:8787/bili/callback`
- `CALLBACK_TOKEN`：回调令牌（与插件配置 `callback_token` 一致）
- `CALLBACK_TIMEOUT_SEC`：回调超时（秒，默认 5）
- `CALLBACK_RETRIES`：回调重试次数（默认 2）

示例：
```bash
export CALLBACK_URL="http://127.0.0.1:8787/bili/callback"
export CALLBACK_TOKEN="your_token"
uvicorn fastapi_app:app --host 0.0.0.0 --port 8000
```

也可以通过接口动态配置（需登录 token）：
- `GET  /api/callback/config?token=...`
- `POST /api/callback/config?token=...&callback_url=...&callback_token=...`

## 登录 token 与配置持久化
首次运行会生成登录 token，并保存在 `config.json`，每次启动日志都会打印当前 token。
你也可以通过环境变量指定：
- `LOGIN_TOKEN`：强制设置登录 token
- `CONFIG_FILE`：指定配置文件路径（默认 `config.json`）

## Docker 运行
```bash
sudo docker build -t bilibiliwatch-api-service .
sudo docker run -d --name bilibiliwatch-api-service -p 8000:8000 bilibiliwatch-api-service
```

## 说明
- 启动后日志会输出登录 token（用于 `/api/login/*`）。
- 扫码成功后会生成 `cookies.txt`。
- 下载文件默认存储在 `downloads/` 目录。

## 简单示例
```bash
# 1) 获取视频信息
curl "http://127.0.0.1:8000/api/video/info?url=https://www.bilibili.com/video/BVxxxx"

# 2) 发起下载
curl "http://127.0.0.1:8000/api/video/download?url=https://www.bilibili.com/video/BVxxxx"

# 3) 查询进度
curl "http://127.0.0.1:8000/api/download/status/<task_id>"

# 4) 获取文件
curl -O "http://127.0.0.1:8000/api/download/file/<task_id>"
```
