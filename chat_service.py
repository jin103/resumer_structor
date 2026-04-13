from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from config import Config
from logger import logger
from resume_parser import resume_parser
import json
import re

SYSTEM_PROMPT = """你是小YO，一个友善的AI聊天助手。请遵循以下规则：

核心原则：
- 回答要简洁明了，直接回应用户的问题
- 保持友好和有帮助的态度
- 不要过度解释或添加无关信息
- 适度使用emoji，但不要过多

回答风格：
- 直接回答问题要点
- 避免冗长的开场白或客套话
- 保持对话的连贯性
- 如果不确定就诚实说明

记住：你是小YO，专注于提供有价值的对话体验。"""

RESUME_ANALYSIS_PROMPT = """你是一个专业的简历分析助手。请根据提供的简历文本内容，提取以下信息：

1. 基本信息：
   - 姓名
   - 联系方式（电话、邮箱）
   - 学历背景
   - 工作经验年限
   - 当前职位

2. 两点提炼：
   - 核心优势：总结候选人的主要优势和技能
   - 职业建议：基于简历内容给出职业发展建议

请用JSON格式返回结果，格式如下：
{
  "basic_info": {
    "name": "姓名",
    "phone": "电话号码",
    "email": "邮箱地址",
    "education": "学历背景",
    "experience": "工作经验",
    "current_position": "当前职位"
  },
  "refinements": [
    "核心优势：...",
    "职业建议：..."
  ]
}

如果信息不完整，请在相应字段中标注"未提及"或"信息不足"。"""

class ChatService:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=Config.MODEL_NAME,
            base_url=Config.SILICONFLOW_BASE_URL,
            api_key=Config.SILICONFLOW_API_KEY,
            temperature=Config.TEMPERATURE
        )
        # 会话存储：session_id -> {'messages': [...], 'resume_context': {...}}
        self.sessions = {}

    def _get_session(self, session_id: str):
        """获取或创建会话"""
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                'messages': [SystemMessage(content=SYSTEM_PROMPT)],
                'resume_context': None
            }
        return self.sessions[session_id]

    def set_resume_context(self, session_id: str, resume_analysis: dict):
        """设置简历上下文"""
        session = self._get_session(session_id)
        session['resume_context'] = resume_analysis
        
        # 更新系统提示以包含简历信息
        resume_info = self._format_resume_for_context(resume_analysis)
        enhanced_prompt = SYSTEM_PROMPT + "\n\n" + resume_info
        session['messages'][0] = SystemMessage(content=enhanced_prompt)

    def _format_resume_for_context(self, analysis: dict) -> str:
        """将简历分析结果格式化为上下文字符串"""
        if not analysis or not analysis.get('basic_info'):
            return ""
        
        basic = analysis['basic_info']
        refinements = analysis.get('refinements', [])
        
        context = "用户已上传简历，以下是简历的关键信息：\n"
        context += f"- 姓名：{basic.get('name', '未提及')}\n"
        context += f"- 联系方式：{basic.get('phone', '未提及')} / {basic.get('email', '未提及')}\n"
        context += f"- 学历：{basic.get('education', '未提及')}\n"
        context += f"- 工作经验：{basic.get('experience', '未提及')}\n"
        context += f"- 当前职位：{basic.get('current_position', '未提及')}\n"
        
        if refinements:
            context += "- 核心优势和建议：\n"
            for i, refinement in enumerate(refinements, 1):
                context += f"  {i}. {refinement}\n"
        
        context += "\n请基于以上简历信息回答用户的问题，提供针对性的建议和分析。"
        return context

    def chat(self, message: str, session_id: str = "default") -> str:
        """处理聊天请求"""
        try:
            session = self._get_session(session_id)
            
            # 添加用户消息到历史
            session['messages'].append(HumanMessage(content=message))

            # 调用LLM
            response = self.llm.invoke(session['messages'])

            # 添加AI回复到历史
            session['messages'].append(AIMessage(content=response.content))

            return response.content
        except Exception as e:
            logger.error(f"聊天服务错误: {str(e)}")
            raise e

    def analyze_resume(self, file_content: bytes, filename: str, session_id: str = "default") -> dict:
        """分析简历文件（PDF / Word）"""
        try:
            file_path = resume_parser.save_uploaded_file(file_content, filename)
            parse_result = resume_parser.parse_resume(file_path)
            resume_parser.cleanup_temp_file(file_path)

            if not parse_result["success"]:
                return {
                    "success": False,
                    "error": parse_result["error"],
                    "analysis": None
                }

            analysis_result = self._analyze_resume_content(parse_result["text_content"])
            
            # 设置简历上下文到会话
            self.set_resume_context(session_id, analysis_result)

            return {
                "success": True,
                "text_content": parse_result["text_content"],
                "metadata": parse_result["metadata"],
                "analysis": analysis_result,
                "error": None
            }

        except Exception as e:
            logger.error(f"简历分析错误: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "analysis": None
            }

    def _extract_json_from_text(self, text: str) -> str:
        """从模型返回文本中提取 JSON 字符串。"""
        if not text:
            return ""

        # 尝试提取 markdown 代码块内的 JSON
        matches = re.findall(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text, re.IGNORECASE)
        if matches:
            return matches[-1].strip()

        # 尝试提取第一个完整 JSON 对象
        brace_depth = 0
        start_index = None
        for i, ch in enumerate(text):
            if ch == "{":
                if start_index is None:
                    start_index = i
                brace_depth += 1
            elif ch == "}":
                brace_depth -= 1
                if brace_depth == 0 and start_index is not None:
                    candidate = text[start_index:i + 1].strip()
                    return candidate

        return text.strip()

    def _sanitize_json_text(self, json_text: str) -> str:
        """修复 JSON 字符串内的未转义控制字符。"""
        if not json_text:
            return json_text

        result = []
        in_string = False
        escape = False
        for ch in json_text:
            if in_string:
                if escape:
                    result.append(ch)
                    escape = False
                elif ch == "\\":
                    result.append(ch)
                    escape = True
                elif ch == '"':
                    result.append(ch)
                    in_string = False
                elif ch == '\n':
                    result.append('\\n')
                elif ch == '\r':
                    result.append('\\r')
                elif ch == '\t':
                    result.append('\\t')
                else:
                    result.append(ch)
            else:
                result.append(ch)
                if ch == '"':
                    in_string = True
        return ''.join(result)

    def _analyze_resume_content(self, text_content: str) -> dict:
        """使用大模型分析简历内容"""
        try:
            analysis_messages = [
                SystemMessage(content=RESUME_ANALYSIS_PROMPT + "\n\n请仅返回标准 JSON 对象，禁止添加其他解释、摘要、markdown、\"思考\"内容或代码块。"),
                HumanMessage(content=f"请分析以下简历内容：\n\n{text_content}")
            ]

            response = self.llm.invoke(analysis_messages)
            raw_text = response.content.strip()
            json_text = self._extract_json_from_text(raw_text)
            json_text = self._sanitize_json_text(json_text)

            try:
                analysis_data = json.loads(json_text)
                return analysis_data
            except json.JSONDecodeError:
                logger.error(f"简历分析解析失败，原始返回：{raw_text}")
                return {
                    "basic_info": {
                        "name": "解析失败",
                        "phone": "解析失败",
                        "email": "解析失败",
                        "education": "解析失败",
                        "experience": "解析失败",
                        "current_position": "解析失败"
                    },
                    "refinements": [
                        f"核心优势：{raw_text[:200]}...",
                        "职业建议：建议查看原始简历内容"
                    ],
                    "raw_analysis": raw_text
                }

        except Exception as e:
            logger.error(f"简历内容分析错误: {str(e)}")
            return {
                "basic_info": {
                    "name": "分析失败",
                    "phone": "分析失败",
                    "email": "分析失败",
                    "education": "分析失败",
                    "experience": "分析失败",
                    "current_position": "分析失败"
                },
                "refinements": [
                    f"核心优势：分析过程中出现错误 - {str(e)}",
                    "职业建议：请检查简历文件格式或联系技术支持"
                ]
            }

    def stream_chat(self, message: str, session_id: str = "default"):
        """处理流式聊天请求"""
        try:
            session = self._get_session(session_id)
            
            # 添加用户消息到历史
            session['messages'].append(HumanMessage(content=message))

            # 使用流式响应
            full_response = ""
            for chunk in self.llm.stream(session['messages']):
                if chunk.content:
                    full_response += chunk.content
                    yield chunk.content

            # 添加完整回复到历史
            if full_response:
                session['messages'].append(AIMessage(content=full_response))
        except Exception as e:
            logger.error(f"聊天服务错误: {str(e)}")
            yield f"[错误] 处理您的请求时出错：{str(e)}"