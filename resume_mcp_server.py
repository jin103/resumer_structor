"""
MCP服务器：简历解析MCP服务
提供PDF简历解析功能供大模型调用
"""
import asyncio
import json
from typing import Any, Sequence
from mcp import Tool
from mcp.server import Server
from mcp.types import TextContent, PromptMessage, Resource, ResourceTemplate
from resume_parser import resume_parser

# 创建MCP服务器
server = Server("resume-parser")

@server.tool()
async def parse_resume_pdf(file_path: str) -> str:
    """
    解析PDF简历文件并返回文本内容

    Args:
        file_path: PDF文件路径

    Returns:
        解析后的文本内容
    """
    try:
        result = resume_parser.parse_resume_pdf(file_path)

        if result["success"]:
            return json.dumps({
                "status": "success",
                "text_content": result["text_content"],
                "metadata": result["metadata"]
            }, ensure_ascii=False, indent=2)
        else:
            return json.dumps({
                "status": "error",
                "error": result["error"]
            }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e)
        }, ensure_ascii=False, indent=2)

@server.tool()
async def extract_resume_info(text_content: str) -> str:
    """
    从简历文本中提取基本信息和两点提炼

    Args:
        text_content: 简历文本内容

    Returns:
        提取的基本信息和提炼内容
    """
    try:
        # 这里可以调用大模型来分析简历内容
        # 暂时返回结构化的提示信息
        return json.dumps({
            "status": "success",
            "basic_info": {
                "name": "待提取",
                "phone": "待提取",
                "email": "待提取",
                "education": "待提取",
                "experience": "待提取"
            },
            "refinements": [
                "核心优势：待分析",
                "职业建议：待分析"
            ],
            "raw_text": text_content[:500] + "..." if len(text_content) > 500 else text_content
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e)
        }, ensure_ascii=False, indent=2)

async def main():
    """启动MCP服务器"""
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())