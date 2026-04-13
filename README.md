# 小YO - AI聊天助手

这是一个基于LangChain框架，使用硅基流动的DeepSeek-R1-Distill-Qwen-7B模型，具有记忆功能的FastAPI接口。

## ✨ 特色功能

- 🤖 **AI角色**: 小YO - 一个有趣、友善的聊天助手
- 💬 **流式输出**: 实时流式显示AI回复，提升用户体验
- 🧠 **记忆上下文**: 自动保持对话历史，支持多轮对话
- 📱 **响应式设计**: 支持手机和电脑访问
- 🎨 **现代化UI**: 渐变背景、动画效果、emoji表情
- ⚡ **实时状态**: 显示服务器连接状态
- 🗑️ **对话管理**: 一键清空对话记录

## 安装依赖

```bash
pip install langchain langchain-openai fastapi uvicorn python-dotenv langchain-community langchain-experimental starlette pdfplumber python-docx
```

## 配置

1. 在`.env`文件中设置您的硅基流动API密钥：

```
SILICONFLOW_API_KEY=your_actual_api_key_here
```

2. 如需更改监听端口，可设置：

```
PORT=8005
```

## 快速启动

### Windows用户
双击运行 `start.bat` 文件

### 命令行启动
```bash
python main.py
```

应用将在 http://localhost:8001 启动。

## 访问方式

### 1. 前端聊天界面
- **完整版**: http://localhost:8001/chat (包含流式输出)
- **简化版**: http://localhost:8001/simple (用于测试)
- **测试页面**: http://localhost:8001/test (验证服务器)

前端界面特性：
- 🗣️ 实时聊天界面
- 💬 多轮对话支持
- 🧠 自动记忆上下文
- 📱 响应式设计
- 🎨 现代化UI
- ⚡ 实时状态显示
- 🗑️ 一键清空对话

### 2. API接口
- **健康检查**: `http://localhost:8001/`
- **流式聊天API**: `POST http://localhost:8001/stream_chat` (推荐)
- **普通聊天API**: `POST http://localhost:8001/chat`

## API使用

### 流式聊天 (推荐使用)

```bash
curl -X POST "http://localhost:8001/stream_chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "你好，小YO"}'
```

响应格式：Server-Sent Events 流
```
data: {"type": "trace_id", "data": "uuid"}
data: {"type": "chunk", "data": "你"}
data: {"type": "chunk", "data": "好"}
...
data: {"type": "done", "data": "完整回复"}
```

### 普通聊天

```bash
curl -X POST "http://localhost:8001/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "你好"}'
```

响应格式：
```json
{
  "response": "AI的回复内容",
  "trace_id": "唯一的跟踪ID"
}
```

### 统一聊天与简历接口

`POST http://localhost:8001/chat` 支持两种请求：

- 普通聊天：JSON 请求
```bash
curl -X POST "http://localhost:8001/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "你好"}'
```

- 上传简历并解析：表单请求
```bash
curl -X POST "http://localhost:8001/chat" \
     -F "file=@resume.pdf"
```

响应格式：
```json
{
  "response": "AI的回复内容或简历分析摘要",
  "trace_id": "唯一的跟踪ID",
  "success": true,
  "metadata": { ... },
  "analysis": {
    "basic_info": { ... },
    "refinements": [ ... ]
  },
  "error": null
}
```

### 健康检查

```bash
curl http://localhost:8001/
```

## 项目结构

- `main.py`: FastAPI应用入口，包含中间件和路由
- `chat_service.py`: 聊天服务类，处理LLM调用和记忆
- `config.py`: 配置管理
- `logger.py`: 日志记录功能
- `models.py`: Pydantic模型定义
- `.env`: 环境变量配置

## 日志

日志文件保存在`app.log`中，包含trace_id、时间戳、用户消息和AI回复。