"""Prompt templates and course rubrics for the grading assistant."""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Dict, List, Optional


class PromptFactory:
    """Build course-aware prompts with explicit prompt engineering structure."""

    DEFAULT_RUBRICS: Dict[str, List[dict]] = {
        "语文": [
            {"dimension": "主题理解", "max_score": 25},
            {"dimension": "内容完整性", "max_score": 20},
            {"dimension": "结构层次", "max_score": 15},
            {"dimension": "语言表达", "max_score": 20},
            {"dimension": "情感与思考", "max_score": 10},
            {"dimension": "错别字与病句", "max_score": 10},
        ],
        "数学": [
            {"dimension": "解题思路", "max_score": 25},
            {"dimension": "关键步骤", "max_score": 25},
            {"dimension": "逻辑严密性", "max_score": 20},
            {"dimension": "计算准确性", "max_score": 20},
            {"dimension": "书写规范", "max_score": 10},
        ],
        "英语": [
            {"dimension": "内容切题程度", "max_score": 20},
            {"dimension": "语法准确性", "max_score": 25},
            {"dimension": "词汇使用", "max_score": 20},
            {"dimension": "句式表达", "max_score": 15},
            {"dimension": "篇章结构", "max_score": 10},
            {"dimension": "拼写与标点", "max_score": 10},
        ],
        "计算机": [
            {"dimension": "概念理解", "max_score": 20},
            {"dimension": "算法或代码逻辑", "max_score": 25},
            {"dimension": "实现完整性", "max_score": 20},
            {"dimension": "错误分析能力", "max_score": 15},
            {"dimension": "表达规范性", "max_score": 10},
            {"dimension": "可改进方向", "max_score": 10},
        ],
        "通用课程": [
            {"dimension": "内容完整性", "max_score": 25},
            {"dimension": "逻辑结构", "max_score": 20},
            {"dimension": "表达清晰度", "max_score": 20},
            {"dimension": "重点突出程度", "max_score": 15},
            {"dimension": "创新性", "max_score": 10},
            {"dimension": "规范性", "max_score": 10},
        ],
    }

    OUTPUT_SCHEMA = {
        "course": "课程名称",
        "grading_mode": "批改模式",
        "summary": "总体评价",
        "quality_control": {
            "serious_error_count": 0,
            "major_error_count": 0,
            "hard_cap": 100,
            "cap_reason": "无硬性限分",
            "detected_errors": [
                {
                    "error": "严重错误描述",
                    "evidence": "学生作业中的原文或现象",
                    "severity": "严重/主要/一般",
                }
            ],
        },
        "dimension_scores": [
            {
                "dimension": "评分维度名称",
                "score": 16,
                "comment": "该维度评价",
            }
        ],
        "strengths": ["优点1", "优点2", "优点3"],
        "problems": [
            {
                "problem": "问题描述",
                "evidence": "作业中的对应原文、现象或位置",
                "suggestion": "具体修改建议",
                "severity": "高/中/低",
            }
        ],
        "detailed_feedback": {
            "content": "内容方面评价",
            "structure": "结构方面评价",
            "language": "语言表达评价",
            "logic": "逻辑方面评价",
            "format": "格式规范评价",
        },
        "teacher_comment": "一段适合发给学生的教师评语",
        "revision_plan": ["第一步修改建议", "第二步修改建议", "第三步修改建议"],
        "prompt_engineering_notes": {
            "used_role": "本次提示词中的角色设定",
            "used_rubric": "本次使用的评分标准说明",
            "output_constraint": "本次使用的输出约束",
        },
    }

    def __init__(
        self,
        rubric_overrides: Optional[Dict[str, List[dict]]] = None,
    ) -> None:
        self.rubric_overrides = rubric_overrides or {}

    def get_course_rubric(self, course_name: str) -> dict:
        """Return the structured rubric for a course."""
        dimensions = self.rubric_overrides.get(
            course_name,
            self.DEFAULT_RUBRICS.get(course_name, self.DEFAULT_RUBRICS["通用课程"]),
        )
        return {
            "course": course_name,
            "dimensions": deepcopy(dimensions),
        }

    def build_system_prompt(self, course_name: str, grading_mode: str, strict_json: bool) -> str:
        rubric = self.get_course_rubric(course_name)
        rubric_text = self._format_rubric(rubric["dimensions"])
        mode_instruction = self._mode_instruction(grading_mode)
        output_schema = json.dumps(self.OUTPUT_SCHEMA, ensure_ascii=False, indent=2)
        json_constraint = (
            "你必须只输出一个合法 JSON 对象，不要输出 Markdown、代码块标记、前后解释或多余文本。"
            if strict_json
            else "请优先输出合法 JSON；如需补充说明，也必须保证 JSON 对象完整且可被解析。"
        )

        return f"""# 角色
你是一名经验丰富、认真负责、评价客观的教师。你熟悉提示词工程中的结构化输出、评分标准分解和可解释反馈方法。你的任务不是简单给分，而是基于课程特点对学生作业进行专业批改，并给出可操作的修改建议。

# 上下文
- 课程名称：{rubric["course"]}
- 批改模式：{grading_mode}
- 评分标准：总分 100 分，具体维度如下：
{rubric_text}

# 批改模式要求
{mode_instruction}

# 批改任务
请完成以下任务：
1. 先进行事实、概念、题意和关键过程核查，列出严重错误与主要错误。
2. 根据下方“硬性限分规则”确定 hard_cap；没有触发限分时填 100。
3. 判断作业是否切题。
4. 按课程维度评分，并给出每个维度的简要评价。
5. 找出主要优点。
6. 找出主要问题。
7. 对问题给出具体证据，证据可以是原文、现象或位置描述。
8. 给出可执行的修改建议。
9. 生成适合教师反馈场景的教师评语。
10. 生成学生可执行的修改计划。

# 硬性限分规则
- “严重错误”指作者、作品、核心概念、关键事实、题意、主要公式、关键步骤、程序核心逻辑等基础性错误，会直接破坏作业成立的前提。
- “主要错误”指明显影响理解、论证、过程或结论，但未完全破坏作业基础的错误。
- 出现 1 处严重错误：hard_cap 不得高于 69。
- 出现 2 处及以上严重错误：hard_cap 不得高于 59。
- 核心任务基本未完成、严重跑题、关键结论整体错误或大量内容建立在错误前提上：hard_cap 不得高于 49。
- 出现 2 处及以上主要错误但没有严重错误：hard_cap 不得高于 79。
- hard_cap 是最终总分上限，不是建议分数。必须在 quality_control 中明确给出错误数量、证据和限分原因。
- 语文读后感特别规则：混淆作品作者、关键人物、核心情节或重要意象属于严重错误；用“可能是不同版本”等无依据说法回避核实，至少属于主要错误。
- 数学特别规则：关键公式、主要推导或最终结论错误属于严重错误。
- 英语特别规则：严重跑题或大量语法错误导致基本含义难以理解，属于严重错误。
- 计算机特别规则：核心概念、算法主逻辑或关键代码行为错误，属于严重错误。

# 约束条件
- 不编造学生作业中不存在的内容。
- 评价要客观、具体、可解释。
- 问题必须尽量给出对应原文或现象。
- 修改建议必须可执行，避免空泛表达。
- 每个维度分数必须在 0 到该维度满分之间。
- 只评价并输出每个维度的分数，不要计算或输出总分与等级；总分和等级由程序统一计算。
- quality_control 必须填写，不得省略；hard_cap 只能依据作业中的实际错误确定。
- 如果作业内容过短，需要明确指出。
- 如果作业跑题，需要降低内容相关维度得分。
- 采用严格、审慎的评分尺度，不因礼貌、鼓励学生或避免否定而抬高分数；鼓励式批改只改变反馈语气，不改变评分标准。
- 每一项得分都必须由作业中的实际证据支撑。证据不足、内容笼统、仅完成基本要求时，不得给高分。
- 每个维度按其满分比例严格评分：达到该维度满分 90% 以上，必须有充分证据证明表现优秀且几乎没有明显缺陷。
- 达到维度满分 80%-89% 表示表现较好但仍有明确不足；70%-79% 表示完成主要要求但提升空间明显。
- 达到维度满分 60%-69% 表示仅达到基本要求；存在明显缺失、过程不足或错误时，该维度应低于满分的 60%。
- 不要把“没有明显错误”等同于优秀；缺少深度、细节、证据或完整过程也必须扣分。
- 评分时先寻找缺失项和问题并据此扣分，再确认优点，禁止默认从高分起评。
- {json_constraint}

# 输出格式
请严格贴合以下 JSON 结构，字段名不要改写：
{output_schema}
"""

    def build_user_prompt(
        self,
        course_name: str,
        homework_text: str,
    ) -> str:
        rubric = self.get_course_rubric(course_name)
        return f"""请批改以下学生作业。

课程名称：{rubric["course"]}

学生作业内容：
\"\"\"
{homework_text.strip()}
\"\"\"
"""

    def _format_rubric(self, dimensions: List[dict]) -> str:
        return "\n".join(
            f"- {item['dimension']}：{item['max_score']} 分" for item in dimensions
        )

    def _mode_instruction(self, grading_mode: str) -> str:
        if grading_mode == "快速批改":
            return "- 输出简洁，适合快速判断作业质量；重点给出各维度分数、主要问题和简短建议。"
        if grading_mode == "鼓励式批改":
            return "- 语气更温和，保留问题指出，但强调鼓励和成长，适合直接给学生阅读。"
        return "- 输出完整，对每个评分维度都给出评价，适合教师正式批改。"
