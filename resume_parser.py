"""
MCP服务：简历PDF解析服务
使用pdfplumber解析PDF简历文件
"""
import pdfplumber
import tempfile
import os
from typing import Dict, Any
from pathlib import Path
from docx import Document

class ResumeParserService:
    """简历解析服务"""

    SUPPORTED_EXTENSIONS = [".pdf", ".docx"]

    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()

    def parse_resume(self, file_path: str) -> Dict[str, Any]:
        """根据文件类型解析简历"""
        ext = Path(file_path).suffix.lower()
        if ext == ".pdf":
            return self.parse_resume_pdf(file_path)
        if ext == ".docx":
            return self.parse_resume_docx(file_path)

        return {
            "success": False,
            "text_content": "",
            "metadata": {},
            "error": f"不支持的文件类型：{ext}。仅支持 PDF 和 Word (.docx) 文件。"
        }

    def parse_resume_pdf(self, file_path: str) -> Dict[str, Any]:
        """
        解析PDF简历文件

        Args:
            file_path: PDF文件路径

        Returns:
            包含解析结果的字典
        """
        try:
            with pdfplumber.open(file_path) as pdf:
                text_content = ""
                metadata = {
                    "total_pages": len(pdf.pages),
                    "file_name": os.path.basename(file_path),
                    "file_size": os.path.getsize(file_path)
                }

                # 提取所有页面的文本
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content += page_text + "\n\n"

                # 清理文本
                text_content = self._clean_text(text_content)

                return {
                    "success": True,
                    "text_content": text_content,
                    "metadata": metadata,
                    "error": None
                }

        except Exception as e:
            return {
                "success": False,
                "text_content": "",
                "metadata": {},
                "error": str(e)
            }

    def parse_resume_docx(self, file_path: str) -> Dict[str, Any]:
        """解析Word (.docx) 简历文件"""
        try:
            document = Document(file_path)
            paragraphs = [p.text for p in document.paragraphs if p.text and p.text.strip()]
            text_content = "\n\n".join(paragraphs)
            metadata = {
                "total_paragraphs": len(paragraphs),
                "file_name": os.path.basename(file_path),
                "file_size": os.path.getsize(file_path)
            }

            text_content = self._clean_text(text_content)

            return {
                "success": True,
                "text_content": text_content,
                "metadata": metadata,
                "error": None
            }

        except Exception as e:
            return {
                "success": False,
                "text_content": "",
                "metadata": {},
                "error": str(e)
            }

    def _clean_text(self, text: str) -> str:
        """清理和格式化提取的文本"""
        if not text:
            return ""

        # 移除多余的空白字符
        text = ' '.join(text.split())

        # 移除多余的换行符
        text = '\n'.join(line.strip() for line in text.split('\n') if line.strip())

        return text

    def save_uploaded_file(self, file_content: bytes, filename: str) -> str:
        """保存上传的文件到临时目录"""
        file_path = os.path.join(self.temp_dir, filename)

        with open(file_path, 'wb') as f:
            f.write(file_content)

        return file_path

    def cleanup_temp_file(self, file_path: str):
        """清理临时文件"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"清理临时文件失败: {e}")

# 创建全局服务实例
resume_parser = ResumeParserService()