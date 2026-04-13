import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    # 硅基流动API配置
    SILICONFLOW_BASE_URL = "https://api.siliconflow.cn/v1"
    SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY")
    MODEL_NAME = "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"
    TEMPERATURE = 0.3  # 降低温度参数，让回答更保守

    # FastAPI配置
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8001"))

    # 日志配置
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "app.log")

# 验证配置
if not Config.SILICONFLOW_API_KEY:
    raise ValueError("请在.env文件中设置SILICONFLOW_API_KEY")
