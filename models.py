from pydantic import BaseModel
from typing import Optional, Dict, Any

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"

class UnifiedChatResponse(BaseModel):
    response: str
    trace_id: str
    success: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None
    analysis: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class ResumeAnalysisResponse(BaseModel):
    success: bool
    text_content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    analysis: Optional[Dict[str, Any]] = None
    error: Optional[str] = None