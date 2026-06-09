"""Read uploaded homework files."""

from __future__ import annotations

from io import BytesIO


def read_uploaded_file(uploaded_file) -> str:
    if uploaded_file is None:
        return ""

    file_name = uploaded_file.name.lower()

    try:
        if file_name.endswith((".txt", ".md")):
            data = uploaded_file.getvalue()
            for encoding in ["utf-8", "gbk", "gb2312"]:
                try:
                    return data.decode(encoding)
                except UnicodeDecodeError:
                    continue
            return data.decode("utf-8", errors="ignore")

        if file_name.endswith(".docx"):
            from docx import Document

            document = Document(BytesIO(uploaded_file.getvalue()))
            paragraphs = [paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()]
            return "\n".join(paragraphs)

        if file_name.endswith(".pdf"):
            from pypdf import PdfReader

            reader = PdfReader(BytesIO(uploaded_file.getvalue()))
            pages = []
            for page in reader.pages:
                pages.append(page.extract_text() or "")
            text = "\n".join(pages).strip()
            return text or "PDF 已读取，但没有提取到可批改文本。请确认 PDF 是否为可复制文本，或改为粘贴文本。"

        return "暂不支持该文件格式。请上传 txt、md、docx 或 pdf 文件。"
    except Exception as exc:
        return f"文档解析失败：{exc}。请尝试改为粘贴文本。"
