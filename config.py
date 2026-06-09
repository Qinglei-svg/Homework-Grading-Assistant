"""Application configuration helpers."""

import os
from typing import Any

import streamlit as st
from dotenv import load_dotenv


load_dotenv()


APP_NAME = "教师作业批改助手"
APP_SUBTITLE = "基于提示词工程的多课程智能批改 Agent"

PROVIDER_OPTIONS = [
    "智谱 BigModel API",
    "OpenRouter 兼容 API",
    "Gemini API",
    "自定义 OpenAI-Compatible API",
    "Mock 演示模式",
]

PROVIDER_DEFAULTS = {
    "智谱 BigModel API": {
        "api_key_env": "ZHIPU_API_KEY",
        "base_url_env": "ZHIPU_BASE_URL",
        "model_env": "ZHIPU_MODEL",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "model_name": "glm-4-flash",
    },
    "OpenRouter 兼容 API": {
        "api_key_env": "OPENROUTER_API_KEY",
        "base_url_env": "OPENROUTER_BASE_URL",
        "model_env": "OPENROUTER_MODEL",
        "base_url": "https://openrouter.ai/api/v1",
        "model_name": "openrouter/auto",
    },
    "Gemini API": {
        "api_key_env": "GEMINI_API_KEY",
        "base_url_env": "",
        "model_env": "GEMINI_MODEL",
        "base_url": "",
        "model_name": "gemini-1.5-flash",
    },
    "自定义 OpenAI-Compatible API": {
        "api_key_env": "CUSTOM_API_KEY",
        "base_url_env": "CUSTOM_BASE_URL",
        "model_env": "CUSTOM_MODEL",
        "base_url": "https://api.openai.com/v1",
        "model_name": "gpt-4o-mini",
    },
    "Mock 演示模式": {
        "api_key_env": "",
        "base_url_env": "",
        "model_env": "",
        "base_url": "",
        "model_name": "mock-grading-model",
    },
}


def get_secret_or_env(name: str, default: str = "") -> str:
    """Read a value from Streamlit secrets first, then environment variables."""
    if not name:
        return default

    try:
        value: Any = st.secrets.get(name, "")
        if value:
            return str(value)
    except Exception:
        pass

    return os.getenv(name, default)


def get_provider_defaults(provider: str) -> dict:
    defaults = PROVIDER_DEFAULTS.get(provider, PROVIDER_DEFAULTS["智谱 BigModel API"])
    return {
        "api_key": get_secret_or_env(defaults["api_key_env"], ""),
        "base_url": get_secret_or_env(defaults["base_url_env"], defaults["base_url"]),
        "model_name": get_secret_or_env(defaults["model_env"], defaults["model_name"]),
    }
