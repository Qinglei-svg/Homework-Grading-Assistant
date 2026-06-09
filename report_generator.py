"""Markdown report generation."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict


def generate_markdown_report(result: Dict[str, Any], metadata: Dict[str, Any]) -> str:
    parsed = result.get("parsed_result", result)
    dimensions = parsed.get("dimension_scores", [])
    strengths = parsed.get("strengths", [])
    problems = parsed.get("problems", [])
    feedback = parsed.get("detailed_feedback", {})
    revision_plan = parsed.get("revision_plan", [])
    notes = parsed.get("prompt_engineering_notes", {})
    adjustment = parsed.get("score_adjustment", {})
    quality_control = parsed.get("quality_control", {})

    generated_at = metadata.get("grading_time") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        "# 教师作业批改报告",
        "",
        "## 一、基本信息",
        f"* 课程：{metadata.get('course', parsed.get('course', ''))}",
        f"* 批改模式：{metadata.get('grading_mode', parsed.get('grading_mode', ''))}",
        f"* 使用模型：{metadata.get('model', '')}",
        f"* 批改时间：{generated_at}",
        "",
        "## 二、总体结果",
        f"* 分数：{parsed.get('score', '')}",
        f"* 等级：{parsed.get('level', '')}",
        f"* 总体评价：{parsed.get('summary', '')}",
        f"* 硬性限分：{'是' if adjustment.get('cap_applied') else '否'}",
        f"* 限分原因：{adjustment.get('reason', '无')}",
        "",
        "## 三、维度得分",
        "| 评分维度 | 满分 | 得分 | 评价 |",
        "| --- | ---: | ---: | --- |",
    ]

    for item in dimensions:
        lines.append(
            f"| {item.get('dimension', '')} | {item.get('max_score', '')} | {item.get('score', '')} | {item.get('comment', '')} |"
        )

    lines.extend(["", "### 严重错误与限分依据"])
    detected_errors = quality_control.get("detected_errors", []) if isinstance(quality_control, dict) else []
    if detected_errors:
        for item in detected_errors:
            lines.append(
                f"* [{item.get('severity', '')}] {item.get('error', '')}；证据：{item.get('evidence', '')}"
            )
    else:
        lines.append("* 未发现触发硬性限分的错误。")

    lines.extend(["", "## 四、主要优点"])
    if strengths:
        lines.extend([f"* {item}" for item in strengths])
    else:
        lines.append("* 暂无")

    lines.extend(
        [
            "",
            "## 五、存在问题与修改建议",
            "| 问题 | 证据 | 建议 | 严重程度 |",
            "| --- | --- | --- | --- |",
        ]
    )
    for item in problems:
        lines.append(
            f"| {item.get('problem', '')} | {item.get('evidence', '')} | {item.get('suggestion', '')} | {item.get('severity', '')} |"
        )

    lines.extend(["", "## 六、详细反馈"])
    if isinstance(feedback, dict):
        for key, value in feedback.items():
            lines.append(f"* {key}：{value}")
    else:
        lines.append(str(feedback))

    lines.extend(
        [
            "",
            "## 七、教师评语",
            parsed.get("teacher_comment", ""),
            "",
            "## 八、学生修改计划",
        ]
    )
    if revision_plan:
        lines.extend([f"{index}. {item}" for index, item in enumerate(revision_plan, 1)])
    else:
        lines.append("暂无")

    lines.extend(
        [
            "",
            "## 九、提示词工程说明",
            "本产品通过角色设定、课程化评分标准、结构化任务分解、固定 JSON 输出约束和容错解析机制，将提示词工程产品化为一个稳定的作业批改流程。",
            "",
            f"* 角色设定：{notes.get('used_role', '让模型扮演经验丰富、评价客观的教师。')}",
            f"* 评分标准：{notes.get('used_rubric', '根据课程切换结构化评分维度。')}",
            f"* 输出约束：{notes.get('output_constraint', '要求模型输出固定 JSON，便于可视化展示和报告导出。')}",
        ]
    )

    return "\n".join(lines)
