"""Core grading workflow."""

from __future__ import annotations

from json_utils import parse_model_json


class GradingEngine:
    def __init__(self, model_router, prompt_factory):
        self.model_router = model_router
        self.prompt_factory = prompt_factory

    def grade(
        self,
        course_name,
        grading_mode,
        homework_text,
        strict_json,
    ):
        system_prompt = self.prompt_factory.build_system_prompt(
            course_name=course_name,
            grading_mode=grading_mode,
            strict_json=strict_json,
        )
        user_prompt = self.prompt_factory.build_user_prompt(
            course_name=course_name,
            homework_text=homework_text,
        )
        raw_output = self.model_router.generate(system_prompt, user_prompt)
        parsed_result = parse_model_json(raw_output)
        parsed_result = self._calculate_scores(course_name, parsed_result)

        return {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "raw_output": raw_output,
            "parsed_result": parsed_result,
        }

    def _calculate_scores(self, course_name, parsed_result):
        """Use configured weights as the source of truth for final scoring."""
        if not parsed_result.get("parse_success", False):
            return parsed_result

        expected_dimensions = self.prompt_factory.get_course_rubric(course_name)["dimensions"]
        model_dimensions = parsed_result.get("dimension_scores", [])
        if not isinstance(model_dimensions, list):
            model_dimensions = []

        model_by_name = {
            str(item.get("dimension", "")).strip(): item
            for item in model_dimensions
            if isinstance(item, dict) and str(item.get("dimension", "")).strip()
        }
        normalized_dimensions = []
        total_score = 0.0

        for index, expected in enumerate(expected_dimensions):
            dimension_name = expected["dimension"]
            max_score = max(0.0, float(expected["max_score"]))
            model_item = model_by_name.get(dimension_name)

            if model_item is None and index < len(model_dimensions):
                fallback = model_dimensions[index]
                model_item = fallback if isinstance(fallback, dict) else {}
            model_item = model_item or {}

            try:
                score = float(model_item.get("score", 0))
            except (TypeError, ValueError):
                score = 0.0

            score = min(max(score, 0.0), max_score)
            total_score += score
            normalized_dimensions.append(
                {
                    "dimension": dimension_name,
                    "max_score": self._clean_number(max_score),
                    "score": self._clean_number(score),
                    "comment": model_item.get("comment", "模型未返回该维度评价。"),
                }
            )

        total_score = min(max(total_score, 0.0), 100.0)
        pre_cap_score = total_score
        quality_control = parsed_result.get("quality_control", {})
        if not isinstance(quality_control, dict):
            quality_control = {}
        hard_cap = self._resolve_hard_cap(quality_control)
        cap_applied = total_score > hard_cap
        if cap_applied:
            normalized_dimensions = self._scale_dimensions_to_cap(
                normalized_dimensions,
                hard_cap,
            )
            total_score = sum(float(item["score"]) for item in normalized_dimensions)

        parsed_result.pop("score", None)
        parsed_result.pop("level", None)
        parsed_result["dimension_scores"] = normalized_dimensions
        parsed_result["score"] = self._clean_number(total_score)
        parsed_result["level"] = self._score_level(total_score)
        parsed_result["quality_control"] = quality_control
        parsed_result["score_adjustment"] = {
            "pre_cap_score": self._clean_number(pre_cap_score),
            "hard_cap": self._clean_number(hard_cap),
            "cap_applied": cap_applied,
            "reason": quality_control.get("cap_reason", "无硬性限分"),
        }
        return parsed_result

    def _scale_dimensions_to_cap(self, dimensions, hard_cap):
        current_total = sum(float(item["score"]) for item in dimensions)
        if current_total <= 0 or current_total <= hard_cap:
            return dimensions

        scale = hard_cap / current_total
        scaled = []
        running_total = 0.0
        for index, item in enumerate(dimensions):
            if index == len(dimensions) - 1:
                score = max(0.0, hard_cap - running_total)
            else:
                score = round(float(item["score"]) * scale, 1)
                running_total += score
            scaled.append({**item, "score": self._clean_number(score)})
        return scaled

    @staticmethod
    def _parse_hard_cap(value):
        try:
            return min(max(float(value), 0.0), 100.0)
        except (TypeError, ValueError):
            return 100.0

    def _resolve_hard_cap(self, quality_control):
        declared_cap = self._parse_hard_cap(quality_control.get("hard_cap", 100))
        try:
            serious_count = max(0, int(quality_control.get("serious_error_count", 0)))
        except (TypeError, ValueError):
            serious_count = 0
        try:
            major_count = max(0, int(quality_control.get("major_error_count", 0)))
        except (TypeError, ValueError):
            major_count = 0

        rule_cap = 100.0
        if serious_count >= 2:
            rule_cap = 59.0
        elif serious_count == 1:
            rule_cap = 69.0
        elif major_count >= 2:
            rule_cap = 79.0
        return min(declared_cap, rule_cap)

    @staticmethod
    def _clean_number(value):
        return int(value) if float(value).is_integer() else round(value, 1)

    @staticmethod
    def _score_level(score):
        if score >= 90:
            return "优秀"
        if score >= 80:
            return "良好"
        if score >= 70:
            return "中等"
        if score >= 60:
            return "及格"
        return "需改进"
