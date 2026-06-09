"""Unified model routing for multiple providers."""

from __future__ import annotations

import json
import re
from typing import Dict, List


class ModelRouter:
    def __init__(
        self,
        provider,
        api_key,
        base_url,
        model_name,
        temperature,
        max_tokens,
    ):
        self.provider = provider
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        if self.provider == "Mock 演示模式":
            return self._mock_generate(system_prompt, user_prompt)

        if not self.api_key:
            raise ValueError("当前模型需要 API Key。请在侧边栏填写 API Key，或切换到 Mock 演示模式。")

        if self.provider in ["智谱 BigModel API", "OpenRouter 兼容 API", "自定义 OpenAI-Compatible API"]:
            return self._openai_compatible_generate(system_prompt, user_prompt)

        if self.provider == "Gemini API":
            return self._gemini_generate(system_prompt, user_prompt)

        raise ValueError(f"暂不支持的模型提供方：{self.provider}")

    def _openai_compatible_generate(self, system_prompt: str, user_prompt: str) -> str:
        try:
            from openai import OpenAI

            client_kwargs = {"api_key": self.api_key}
            if self.base_url:
                client_kwargs["base_url"] = self.base_url

            client = OpenAI(**client_kwargs)
            response = client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            raise RuntimeError(f"模型调用失败：{exc}") from exc

    def _gemini_generate(self, system_prompt: str, user_prompt: str) -> str:
        try:
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(
                self.model_name,
                system_instruction=system_prompt,
            )
            response = model.generate_content(
                user_prompt,
                generation_config={
                    "temperature": self.temperature,
                    "max_output_tokens": self.max_tokens,
                },
            )
            return response.text or ""
        except Exception as exc:
            raise RuntimeError(f"Gemini 调用失败：{exc}") from exc

    def _mock_generate(self, system_prompt: str, user_prompt: str) -> str:
        course = self._extract_course(user_prompt)
        grading_mode = self._extract_mode(system_prompt)
        dimensions = self._extract_dimensions(system_prompt)
        homework = self._extract_homework(user_prompt)

        base_score = self._estimate_score(homework)
        dimension_scores = []
        allocated_scores = [round(item["max_score"] * base_score / 100) for item in dimensions]
        delta = base_score - sum(allocated_scores)
        cursor = 0
        while delta != 0 and dimensions:
            index = cursor % len(dimensions)
            candidate = allocated_scores[index] + (1 if delta > 0 else -1)
            if 0 <= candidate <= dimensions[index]["max_score"]:
                allocated_scores[index] = candidate
                delta += -1 if delta > 0 else 1
            cursor += 1
            if cursor > 1000:
                break

        for index, item in enumerate(dimensions):
            max_score = item["max_score"]
            score = allocated_scores[index]
            dimension_scores.append(
                {
                    "dimension": item["dimension"],
                    "score": score,
                    "comment": f"该维度表现{'较好' if score >= max_score * 0.8 else '仍有提升空间'}，建议结合评分标准进一步完善。",
                }
            )

        too_short = len(homework.strip()) < 80

        result = {
            "course": course,
            "grading_mode": grading_mode,
            "summary": (
                "这是一份 Mock 演示批改结果。作业整体能回应任务要求，但还可以在证据展开、结构组织和表达细节上继续加强。"
                if not too_short
                else "这是一份 Mock 演示批改结果。当前作业内容偏短，难以充分体现完整思路，需要补充过程、依据和细节。"
            ),
            "quality_control": {
                "serious_error_count": 0,
                "major_error_count": 1 if too_short else 0,
                "hard_cap": 79 if too_short else 100,
                "cap_reason": "作业内容过短，信息不足。" if too_short else "未发现触发硬性限分的错误。",
                "detected_errors": (
                    [
                        {
                            "error": "作业内容过短",
                            "evidence": "当前文本不足以充分展示完整思路。",
                            "severity": "主要",
                        }
                    ]
                    if too_short
                    else []
                ),
            },
            "dimension_scores": dimension_scores,
            "strengths": [
                "能够围绕作业主题展开基本表达。",
                "已有一定的结构意识，内容不是完全零散堆叠。",
                "部分观点或步骤具有继续深化的基础。",
            ],
            "problems": [
                {
                    "problem": "论述或解题过程还不够充分。",
                    "evidence": "作业中存在结论较多、解释较少的现象。",
                    "suggestion": "为关键观点补充原因、步骤、例子或计算过程。",
                    "severity": "中",
                },
                {
                    "problem": "结构层次可以更清晰。",
                    "evidence": "部分内容之间的衔接和分段提示不够明显。",
                    "suggestion": "按“观点/步骤-依据-结论”的顺序重新组织段落。",
                    "severity": "中",
                },
                {
                    "problem": "细节表达仍可打磨。",
                    "evidence": "个别表述较笼统，缺少具体对象或判断依据。",
                    "suggestion": "把笼统词语替换为可观察、可验证的具体描述。",
                    "severity": "低",
                },
            ],
            "detailed_feedback": {
                "content": "内容基本覆盖主题，但仍需要补充更多关键细节和支撑材料。",
                "structure": "整体结构可辨认，建议进一步强化开头、主体和结论之间的层次。",
                "language": "表达基本清楚，部分句子可以更准确、更简洁。",
                "logic": "主要逻辑链条成立，但中间推理或说明还可以更完整。",
                "format": "格式基本可读，建议统一段落、符号和书写规范。",
            },
            "teacher_comment": "你已经完成了作业的基本要求，也能看出你在认真组织内容。下一步请把关键依据和过程写得更充分，让读者更容易理解你的思考路径。",
            "revision_plan": [
                "先对照评分维度检查是否每一项都有对应内容。",
                "为最重要的两个观点或步骤补充证据、例子或推导过程。",
                "最后通读全文，调整段落顺序并修改不够准确的表达。",
            ],
            "prompt_engineering_notes": {
                "used_role": "经验丰富、认真负责、评价客观的教师。",
                "used_rubric": "根据课程选择结构化评分维度，并要求每个维度给出分数和评价。",
                "output_constraint": "要求输出固定 JSON 字段，便于页面可视化、下载和容错解析。",
            },
        }
        return json.dumps(result, ensure_ascii=False, indent=2)

    def _extract_course(self, user_prompt: str) -> str:
        match = re.search(r"课程名称：(.+)", user_prompt)
        return match.group(1).strip() if match else "通用课程"

    def _extract_mode(self, system_prompt: str) -> str:
        match = re.search(r"批改模式：(.+)", system_prompt)
        return match.group(1).strip() if match else "详细批改"

    def _extract_homework(self, user_prompt: str) -> str:
        match = re.search(r'学生作业内容：\s*"""(.*?)"""', user_prompt, re.S)
        return match.group(1).strip() if match else user_prompt

    def _extract_dimensions(self, system_prompt: str) -> List[Dict[str, int]]:
        dimensions = []
        for line in system_prompt.splitlines():
            match = re.match(r"-\s*(.+?)：(\d+)\s*分", line.strip())
            if match:
                dimensions.append({"dimension": match.group(1), "max_score": int(match.group(2))})
        if not dimensions:
            dimensions = [{"dimension": "内容完整性", "max_score": 25}, {"dimension": "逻辑结构", "max_score": 20}, {"dimension": "表达清晰度", "max_score": 20}, {"dimension": "重点突出程度", "max_score": 15}, {"dimension": "创新性", "max_score": 10}, {"dimension": "规范性", "max_score": 10}]
        return dimensions

    def _estimate_score(self, homework: str) -> int:
        length = len(homework.strip())
        if length < 40:
            return 55
        if length < 120:
            return 68
        if length < 300:
            return 78
        return 84
