from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from config import APP_NAME, APP_SUBTITLE, PROVIDER_OPTIONS, get_provider_defaults
from file_reader import read_uploaded_file
from grading_engine import GradingEngine
from json_utils import to_pretty_json
from model_router import ModelRouter
from prompt_factory import PromptFactory
from report_generator import generate_markdown_report


BASE_DIR = Path(__file__).parent
SAMPLE_DIR = BASE_DIR / "sample_homework"


st.set_page_config(
    page_title=APP_NAME,
    page_icon="📝",
    layout="wide",
)


def main() -> None:
    apply_page_style()
    render_header()

    sidebar_state = render_sidebar()

    st.markdown("### 作业批改工作台")
    left_col, right_col = st.columns([0.58, 0.42], gap="large")

    with left_col:
        course_name = render_course_controls()
        grading_mode = st.radio(
            "批改模式",
            ["快速批改", "详细批改", "鼓励式批改"],
            index=1,
            horizontal=True,
        )
        homework_text = render_homework_input(course_name)

    with right_col:
        dimensions, weights_valid = render_weight_editor(course_name)
        render_prompt_engineering_explainer()

    prompt_factory = PromptFactory(rubric_overrides={course_name: dimensions})

    button_col, _ = st.columns([0.24, 0.76])
    with button_col:
        start_grading = st.button(
            "开始批改",
            type="primary",
            width="stretch",
            disabled=not weights_valid,
        )

    if start_grading:
        if not homework_text.strip():
            st.warning("请先输入或上传需要批改的作业内容。")
            return

        if sidebar_state["provider"] != "Mock 演示模式" and not sidebar_state["api_key"]:
            st.warning("当前模型需要 API Key。请在侧边栏填写 API Key，或切换到 Mock 演示模式。")
            return

        with st.spinner("正在调用批改 Agent，请稍候..."):
            router = ModelRouter(
                provider=sidebar_state["provider"],
                api_key=sidebar_state["api_key"],
                base_url=sidebar_state["base_url"],
                model_name=sidebar_state["model_name"],
                temperature=sidebar_state["temperature"],
                max_tokens=sidebar_state["max_tokens"],
            )
            engine = GradingEngine(router, prompt_factory)
            try:
                result = engine.grade(
                    course_name=course_name,
                    grading_mode=grading_mode,
                    homework_text=homework_text,
                    strict_json=sidebar_state["strict_json"],
                )
            except Exception as exc:
                st.error(str(exc))
                return

        st.session_state["last_result"] = result
        st.session_state["last_metadata"] = {
            "course": prompt_factory.get_course_rubric(course_name)["course"],
            "grading_mode": grading_mode,
            "model": f"{sidebar_state['provider']} / {sidebar_state['model_name']}",
            "grading_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    if st.session_state.get("last_result"):
        render_result(
            st.session_state["last_result"],
            st.session_state["last_metadata"],
            show_prompt=sidebar_state["show_prompt"],
        )


def render_header() -> None:
    st.markdown(
        f"""
        <div class="app-header">
            <h1>{APP_NAME}</h1>
            <p>{APP_SUBTITLE}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> dict:
    with st.sidebar:
        st.markdown("## 产品简介")
        st.write(
            "面向教师、助教和学生的 AI 作业批改工具。系统把课程评分标准、批改任务和输出格式封装成可复用提示词模板。"
        )

        provider = st.selectbox("模型选择", PROVIDER_OPTIONS, index=0)
        defaults = get_provider_defaults(provider)

        api_key = st.text_input(
            "API Key",
            value=defaults["api_key"],
            type="password",
            placeholder="未填写时可切换到 Mock 演示模式",
            key=f"api_key_{provider}",
        )
        base_url = st.text_input(
            "Base URL",
            value=defaults["base_url"],
            key=f"base_url_{provider}",
        )
        model_name = st.text_input(
            "模型名称",
            value=defaults["model_name"],
            key=f"model_name_{provider}",
        )
        temperature = st.slider("temperature", min_value=0.0, max_value=1.5, value=0.3, step=0.1)
        max_tokens = st.number_input("max_tokens", min_value=512, max_value=8192, value=2048, step=256)
        show_prompt = st.checkbox("显示本次使用的提示词", value=True)
        strict_json = st.checkbox("启用严格 JSON 输出", value=True)

    return {
        "provider": provider,
        "api_key": api_key.strip(),
        "base_url": base_url.strip(),
        "model_name": model_name.strip(),
        "temperature": temperature,
        "max_tokens": int(max_tokens),
        "show_prompt": show_prompt,
        "strict_json": strict_json,
    }


def render_course_controls():
    return st.selectbox(
        "课程选择",
        ["语文", "数学", "英语", "计算机", "通用课程"],
        index=0,
    )


def render_homework_input(course_name: str) -> str:
    input_mode = st.radio(
        "作业输入方式",
        ["粘贴文本", "上传文档", "使用示例作业"],
        horizontal=True,
    )

    if input_mode == "粘贴文本":
        return st.text_area(
            "作业内容",
            placeholder="请在这里粘贴学生作业文本...",
            height=260,
        )

    if input_mode == "上传文档":
        uploaded_file = st.file_uploader("上传作业文件", type=["txt", "md", "docx", "pdf"])
        if uploaded_file:
            text = read_uploaded_file(uploaded_file)
            st.text_area("解析后的作业内容", value=text, height=260)
            return text
        return ""

    sample_map = {
        "语文": "chinese_sample.txt",
        "数学": "math_sample.txt",
        "英语": "english_sample.txt",
        "计算机": "computer_sample.txt",
    }
    sample_file = sample_map.get(course_name, "chinese_sample.txt")
    sample_text = read_sample(sample_file)
    st.text_area("示例作业内容", value=sample_text, height=260)
    return sample_text


def render_weight_editor(course_name: str):
    rubric = PromptFactory().get_course_rubric(course_name)
    st.markdown("### 评分权重设置")
    st.caption(f"当前课程：{rubric['course']}")
    default_df = pd.DataFrame(
        {
            "评分维度": [item["dimension"] for item in rubric["dimensions"]],
            "权重（分）": [item["max_score"] for item in rubric["dimensions"]],
        }
    )
    edited_df = st.data_editor(
        default_df,
        key=f"rubric_weights_{course_name}",
        hide_index=True,
        width="stretch",
        disabled=["评分维度"],
        column_config={
            "评分维度": st.column_config.TextColumn("评分维度"),
            "权重（分）": st.column_config.NumberColumn(
                "权重（分）",
                min_value=0,
                max_value=100,
                step=1,
                format="%d",
            ),
        },
    )
    dimensions = [
        {
            "dimension": str(row["评分维度"]),
            "max_score": 0 if pd.isna(row["权重（分）"]) else int(row["权重（分）"]),
        }
        for _, row in edited_df.iterrows()
    ]
    total_weight = sum(item["max_score"] for item in dimensions)
    if total_weight == 100:
        st.success("当前权重合计：100 分")
    else:
        st.error(f"当前权重合计：{total_weight} 分。请调整为 100 分后再开始批改。")
    return dimensions, total_weight == 100


def render_prompt_engineering_explainer() -> None:
    with st.expander("提示词工程说明", expanded=True):
        st.markdown(
            """
            **角色设定**：让模型扮演经验丰富、认真负责、评价客观的教师。

            **课程上下文**：根据语文、数学、英语、计算机或通用课程切换评分标准。

            **教师权重**：保留各学科默认权重，并允许教师调整；权重合计必须为 100 分。

            **任务分解**：将批改拆成切题判断、维度评分、优点、问题、证据、建议、教师评语和修改计划。

            **输出约束**：模型只返回维度评分与反馈，不返回总分和等级。

            **程序算分**：系统按教师设置的权重校验维度分数，并在程序中计算总分和等级。

            **容错机制**：对模型输出进行 JSON 提取解析，失败时保留原始结果，避免页面崩溃。
            """
        )


def render_result(result: dict, metadata: dict, show_prompt: bool) -> None:
    st.divider()
    st.markdown("## 批改结果")

    parsed = result["parsed_result"]
    if not parsed.get("parse_success", False):
        st.error("模型输出未能解析为 JSON，以下展示原始输出。")
        st.text_area("模型原始输出", value=parsed.get("raw_output", result.get("raw_output", "")), height=260)
        render_downloads(result, metadata)
        return

    score = parsed.get("score", "N/A")
    level = parsed.get("level", "N/A")
    card1, card2, card3 = st.columns(3)
    card1.metric("总分", score)
    card2.metric("等级", level)
    card3.metric("课程", parsed.get("course", metadata.get("course", "")))

    st.markdown("### 总体评价")
    st.write(parsed.get("summary", "暂无总体评价"))

    score_adjustment = parsed.get("score_adjustment", {})
    if score_adjustment.get("cap_applied"):
        st.warning(
            f"触发硬性限分：维度原始合计 {score_adjustment.get('pre_cap_score')} 分，"
            f"最终上限 {score_adjustment.get('hard_cap')} 分。"
            f"原因：{score_adjustment.get('reason', '')}"
        )

    quality_control = parsed.get("quality_control", {})
    detected_errors = quality_control.get("detected_errors", []) if isinstance(quality_control, dict) else []
    if detected_errors:
        with st.expander("严重错误与限分依据", expanded=True):
            st.dataframe(pd.DataFrame(detected_errors), hide_index=True, width="stretch")

    st.markdown("### 各维度得分")
    dimension_scores = parsed.get("dimension_scores", [])
    if dimension_scores:
        st.dataframe(pd.DataFrame(dimension_scores), hide_index=True, width="stretch")
    else:
        st.info("暂无维度得分。")

    left_col, right_col = st.columns([0.45, 0.55], gap="large")
    with left_col:
        st.markdown("### 主要优点")
        strengths = parsed.get("strengths", [])
        if strengths:
            for item in strengths:
                st.success(item)
        else:
            st.write("暂无")

    with right_col:
        st.markdown("### 主要问题与修改建议")
        problems = parsed.get("problems", [])
        if problems:
            st.dataframe(pd.DataFrame(problems), hide_index=True, width="stretch")
        else:
            st.info("暂无问题列表。")

    st.markdown("### 详细反馈")
    feedback = parsed.get("detailed_feedback", {})
    if isinstance(feedback, dict):
        feedback_cols = st.columns(5)
        for index, (key, value) in enumerate(feedback.items()):
            with feedback_cols[index % 5]:
                st.markdown(f"**{key}**")
                st.write(value)
    else:
        st.write(feedback)

    st.markdown("### 教师评语")
    st.info(parsed.get("teacher_comment", "暂无教师评语"))

    st.markdown("### 学生修改计划")
    revision_plan = parsed.get("revision_plan", [])
    if revision_plan:
        for index, item in enumerate(revision_plan, 1):
            st.write(f"{index}. {item}")
    else:
        st.write("暂无")

    with st.expander("最终结果 JSON（含程序计算的总分与等级）", expanded=False):
        st.code(to_pretty_json(parsed), language="json")

    with st.expander("模型原始输出（不含程序计算字段）", expanded=False):
        st.code(result.get("raw_output", ""), language="json")

    if show_prompt:
        st.markdown("## 提示词调试展示")
        with st.expander("System Prompt", expanded=False):
            st.code(result["system_prompt"], language="markdown")
        with st.expander("User Prompt", expanded=False):
            st.code(result["user_prompt"], language="markdown")

    render_downloads(result, metadata)


def render_downloads(result: dict, metadata: dict) -> None:
    st.markdown("## 报告下载")
    markdown_report = generate_markdown_report(result, metadata)
    json_text = to_pretty_json(result.get("parsed_result", result))
    file_time = datetime.now().strftime("%Y%m%d_%H%M%S")

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "下载 Markdown 批改报告",
            data=markdown_report,
            file_name=f"grading_report_{file_time}.md",
            mime="text/markdown",
            width="stretch",
        )
    with col2:
        st.download_button(
            "下载 JSON 批改结果",
            data=json_text,
            file_name=f"grading_result_{file_time}.json",
            mime="application/json",
            width="stretch",
        )


def read_sample(file_name: str) -> str:
    path = SAMPLE_DIR / file_name
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return "示例作业文件不存在，请改用粘贴文本。"


def apply_page_style() -> None:
    st.markdown(
        """
        <style>
        .app-header {
            padding: 1.2rem 1.4rem;
            border: 1px solid #e6e8eb;
            border-radius: 8px;
            background: #ffffff;
            margin-bottom: 1.2rem;
        }
        .app-header h1 {
            margin: 0;
            color: #1f2937;
            font-size: 2rem;
            letter-spacing: 0;
        }
        .app-header p {
            margin: 0.35rem 0 0;
            color: #4b5563;
            font-size: 1rem;
        }
        div[data-testid="stMetric"] {
            border: 1px solid #e6e8eb;
            border-radius: 8px;
            padding: 0.9rem 1rem;
            background: #ffffff;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
