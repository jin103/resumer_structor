from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from models import ChatRequest, UnifiedChatResponse, ResumeAnalysisResponse
from chat_service import ChatService
from logger import log_chat_interaction, generate_trace_id
from config import Config
import uvicorn
import json

# 初始化FastAPI应用
app = FastAPI(title="LangChain DeepSeek API", description="使用LangChain和硅基流动的DeepSeek模型的对话接口")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 初始化聊天服务
chat_service = ChatService()

class TraceMiddleware(BaseHTTPMiddleware):
    """中间件为每个请求添加trace_id"""
    async def dispatch(self, request: Request, call_next):
        trace_id = generate_trace_id()
        request.state.trace_id = trace_id
        response = await call_next(request)
        return response

# 添加中间件
app.add_middleware(TraceMiddleware)

@app.post("/stream_chat")
async def stream_chat(request: ChatRequest, req: Request):
    """流式聊天接口"""
    trace_id = req.state.trace_id
    session_id = getattr(request, 'session_id', 'default')
    
    def event_generator():
        try:
            # 首先发送trace_id
            yield f"data: {json.dumps({'type': 'trace_id', 'data': trace_id})}\n\n"
            
            # 流式发送AI回复
            full_response = ""
            for chunk in chat_service.stream_chat(request.message, session_id):
                full_response += chunk
                yield f"data: {json.dumps({'type': 'chunk', 'data': chunk})}\n\n"
            
            # 发送完成信号
            yield f"data: {json.dumps({'type': 'done', 'data': full_response})}\n\n"
            
            # 记录日志
            log_chat_interaction(trace_id, request.message, full_response)
        except Exception as e:
            error_msg = str(e)
            yield f"data: {json.dumps({'type': 'error', 'data': error_msg})}\n\n"
            log_chat_interaction(trace_id, request.message, "", error=error_msg)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@app.post("/chat", response_model=UnifiedChatResponse)
async def chat(req: Request, file: UploadFile = File(None)):
    trace_id = req.state.trace_id
    try:
        content_type = req.headers.get("content-type", "")
        message = None
        session_id = "default"

        if content_type.startswith("application/json"):
            body = await req.json()
            message = body.get("message", "")
            session_id = body.get("session_id", "default")
        else:
            form = await req.form()
            message = form.get("message", "")
            session_id = form.get("session_id", "default")

        if file:
            filename = file.filename
            if not filename:
                raise HTTPException(status_code=400, detail="上传文件必须包含文件名")
            lower_name = filename.lower()
            if not lower_name.endswith((".pdf", ".docx")):
                raise HTTPException(status_code=400, detail="仅支持 PDF 和 Word (.docx) 格式的文件上传")

            file_bytes = await file.read()
            result = chat_service.analyze_resume(file_bytes, filename, session_id)
            if not result.get("success"):
                raise HTTPException(status_code=500, detail=result.get("error", "简历解析失败"))

            analysis = result.get("analysis")
            response_text = (
                "简历分析完成。"
                f"姓名：{analysis.get('basic_info', {}).get('name', '未提及')}；"
                f"电话：{analysis.get('basic_info', {}).get('phone', '未提及')}；"
                f"邮箱：{analysis.get('basic_info', {}).get('email', '未提及')}。"
                f"核心优势：{analysis.get('refinements', ['未提及'])[0]}"
            )

            log_chat_interaction(trace_id, f"上传简历：{filename}", response_text)
            return UnifiedChatResponse(
                response=response_text,
                trace_id=trace_id,
                success=True,
                metadata=result.get("metadata"),
                analysis=analysis,
                error=None
            )

        if not message:
            raise HTTPException(status_code=400, detail="消息内容或简历文件必须提供")

        ai_response = chat_service.chat(message, session_id)
        log_chat_interaction(trace_id, message, ai_response)
        return UnifiedChatResponse(response=ai_response, trace_id=trace_id)
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        log_chat_interaction(trace_id, message or "", "", error=error_msg)
        raise HTTPException(status_code=500, detail="内部服务器错误")

@app.get("/")
async def root():
    return {"message": "LangChain DeepSeek API is running"}

@app.get("/chat")
async def chat_page():
    """返回聊天页面"""
    from fastapi.responses import FileResponse
    return FileResponse("static/index.html", media_type="text/html")

@app.get("/simple")
async def simple_chat_page():
    """返回简化版聊天页面"""
    from fastapi.responses import FileResponse
    return FileResponse("static/simple_chat.html", media_type="text/html")

@app.get("/test")
async def test_page():
    """返回测试页面"""
    from fastapi.responses import FileResponse
    return FileResponse("static/test.html", media_type="text/html")

if __name__ == "__main__":
    uvicorn.run(app, host=Config.HOST, port=Config.PORT)
