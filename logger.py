import logging
import uuid
from datetime import datetime
from config import Config

# 配置日志
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def log_chat_interaction(trace_id: str, user_message: str, ai_response: str, error: str = None):
    """记录聊天交互日志"""
    timestamp = datetime.now().isoformat()
    if error:
        logger.error(f"TraceID: {trace_id} | Time: {timestamp} | Error: {error}")
    else:
        logger.info(f"TraceID: {trace_id} | Time: {timestamp} | User: {user_message} | AI: {ai_response}")

def generate_trace_id() -> str:
    """生成唯一的trace_id"""
    return str(uuid.uuid4())