# 教师作业批改助手

产品体验链接：待部署后填写

## 1. 项目简介

教师作业批改助手是一款面向教师、助教和学生的 AI 作业批改工具。它通过提示词工程将不同课程的批改标准结构化，并调用大模型生成专业、清晰、可解释的批改结果。系统支持作业文本输入、文档上传、课程选择、模型切换、JSON 结构化输出、批改报告导出和提示词调试展示，帮助教师提高批改效率，帮助学生明确修改方向。

本项目使用 Python + Streamlit 开发，默认支持智谱 BigModel API，同时保留 OpenRouter、Gemini、自定义 OpenAI-Compatible API 和 Mock 演示模式。

## 2. 产品亮点

* 课程化评分标准：内置语文、数学、英语、计算机和通用课程。
* 教师权重设置：各学科提供默认权重，教师可按教学目标调整，权重合计保持 100 分。
* 程序统一算分：模型只返回各维度得分和反馈，总分与等级由程序计算。
* 严重错误限分：模型先核查事实、概念和关键过程，程序根据严重错误数量执行最高分限制。
* 提示词模板产品化：将角色、上下文、任务、约束和输出格式封装成稳定模板。
* 模型可切换：默认智谱 BigModel API，也支持 OpenRouter、Gemini 和自定义兼容 API。
* 严格 JSON 输出：要求模型输出固定结构，便于结果展示、下载和二次开发。
* JSON 容错解析：模型输出不规范时，尝试提取 JSON 对象，失败也能展示原始输出。
* 可视化批改结果：总分、等级、维度得分、优点、问题、建议、评语和修改计划清晰展示。
* 报告导出：支持下载 Markdown 批改报告和 JSON 批改结果。
* Mock 演示模式：没有 API Key 也能完整跑通，适合课程展示和录屏。

## 3. 为什么说这是提示词工程产品

本项目不是简单地把作业文本发送给大模型，而是把提示词工程转化为可使用、可展示、可复用的产品流程：

* 角色设定：让模型扮演经验丰富、认真负责、评价客观的教师。
* 课程上下文：根据不同课程自动切换评分维度和批改重点。
* 任务分解：将批改任务拆成切题判断、维度评分、优点识别、问题定位、证据说明、修改建议、教师评语和学生修改计划。
* 输出约束：要求模型输出固定 JSON 字段，降低结果不可控性。
* 质量控制：要求问题尽量给出原文、现象或位置，减少空泛评价。
* 硬性评分闸门：核心事实或概念错误会触发 69、59 或 49 分上限，程序同步调整维度分数，避免优点抵消基础性错误。
* 容错机制：通过 JSON 解析和原始输出展示，提升真实模型调用场景下的稳定性。
* 调试展示：页面可以展开 System Prompt 和 User Prompt，清楚展示提示词工程过程。

## 4. 功能列表

* 粘贴作业文本。
* 上传 txt、md、docx、pdf 文档。
* 使用内置示例作业快速演示。
* 选择课程和批改模式。
* 修改当前学科各评分维度的权重。
* 选择模型提供方、Base URL、模型名称、temperature 和 max_tokens。
* 严格 JSON 输出开关。
* 提示词调试展示开关。
* 批改结果可视化。
* Markdown 报告下载。
* JSON 结果下载。

## 5. 技术栈

* 前端与应用框架：Streamlit
* 后端语言：Python
* 默认模型 API：智谱 BigModel API
* 模型调用封装：OpenAI-compatible SDK 风格
* 文档解析：python-docx、pypdf
* 数据展示：pandas + Streamlit dataframe
* 环境变量管理：python-dotenv

## 6. 项目结构

```text
teacher_grading_assistant/
├── app.py
├── config.py
├── model_router.py
├── prompt_factory.py
├── grading_engine.py
├── file_reader.py
├── report_generator.py
├── json_utils.py
├── sample_homework/
│   ├── chinese_sample.txt
│   ├── math_sample.txt
│   ├── english_sample.txt
│   └── computer_sample.txt
├── .env.example
├── requirements.txt
└── README.md
```

## 7. 本地运行方法

进入项目目录：

```bash
cd teacher_grading_assistant
```

安装依赖：

```bash
pip install -r requirements.txt
```

启动应用：

```bash
streamlit run app.py
```

如果暂时没有 API Key，可以在侧边栏选择“Mock 演示模式”，直接体验完整批改流程。

## 8. API Key 配置方法

方式一：复制 `.env.example` 为 `.env`，然后填写自己的 Key。

```bash
cp .env.example .env
```

方式二：在 Streamlit 页面侧边栏直接输入 API Key。

方式三：部署到 Streamlit Community Cloud 时，在项目 Secrets 中配置：

```toml
ZHIPU_API_KEY = "your_zhipu_api_key_here"
ZHIPU_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"
ZHIPU_MODEL = "glm-4-flash"
```

## 9. 智谱 BigModel API 配置说明

默认模型提供方为“智谱 BigModel API”。

默认配置：

```text
ZHIPU_API_KEY=your_zhipu_api_key_here
ZHIPU_BASE_URL=https://open.bigmodel.cn/api/paas/v4
ZHIPU_MODEL=glm-4-flash
```

页面中的模型名称输入框是可编辑的。你可以根据自己的账号权限和课程要求，改为其他可用模型名称。

代码中不会写死 API Key。系统读取顺序为：

1. Streamlit Secrets
2. 环境变量或 `.env`
3. 页面侧边栏输入

## 10. 如何切换其他 API

侧边栏“模型选择”支持：

* 智谱 BigModel API
* OpenRouter 兼容 API
* Gemini API
* 自定义 OpenAI-Compatible API
* Mock 演示模式

OpenRouter 和自定义 API 使用 OpenAI SDK 的兼容写法，只需要填写 API Key、Base URL 和模型名称。

Gemini API 使用 `google-generativeai` 调用，只需要填写 Gemini API Key 和模型名称。

Mock 演示模式不调用任何外部 API，适合无网络、无 Key 或课堂录屏演示。

## 11. Streamlit 部署方法

1. 将项目推送到 GitHub 仓库。
2. 登录 Streamlit Community Cloud。
3. 选择仓库和入口文件 `teacher_grading_assistant/app.py`。
4. 在 Secrets 中填写 API Key，例如：

```toml
ZHIPU_API_KEY = "your_zhipu_api_key_here"
ZHIPU_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"
ZHIPU_MODEL = "glm-4-flash"
```

5. 部署完成后，将生成的链接填写到 README 顶部的“产品体验链接”。

## 12. 操作说明

1. 打开应用后，在侧边栏选择模型。如果没有 API Key，选择 Mock 演示模式。
2. 设置 Base URL、模型名称、temperature 和 max_tokens。
3. 根据需要开启“显示本次使用的提示词”和“启用严格 JSON 输出”。
4. 在主页面选择课程和批改模式。
5. 通过粘贴文本、上传文档或示例作业提供作业内容。
6. 查看并按需修改评分权重，确保权重合计为 100 分。
7. 点击“开始批改”。
8. 查看分数、等级、维度得分、优点、问题、详细反馈、教师评语和修改计划。
9. 展开“原始 JSON”和提示词调试区，展示提示词工程过程。
10. 下载 Markdown 报告或 JSON 结果。

## 13. 视频演示脚本建议

以下脚本适合 2-3 分钟课程作业展示：

1. 介绍产品背景：这是“教师作业批改助手”，目标是把提示词工程应用到真实教学场景中，帮助教师快速批改作业，也帮助学生获得清晰反馈。
2. 展示课程选择：页面支持语文、数学、英语、计算机和通用课程，不同课程会自动切换默认评分标准。
3. 展示教师权重设置：修改某个维度权重，并说明模型只负责维度评价，总分和等级由程序计算。
4. 展示作业输入或上传：可以粘贴作业文本，也可以上传 txt、md、docx、pdf 文件。为了演示，选择内置示例作业。
5. 展示模型选择：侧边栏默认支持智谱 BigModel API，也保留 OpenRouter、Gemini、自定义兼容 API 和 Mock 演示模式。说明 API Key 不会写死在代码中。
6. 点击开始批改：系统会生成课程化提示词，调用模型，并解析 JSON 结果。
7. 展示批改结果：依次展示程序计算的分数和等级、维度得分、主要优点、存在问题、证据和修改建议。
8. 展示提示词调试区：展开 System Prompt 和 User Prompt，说明本产品的核心是提示词工程，包括角色设定、课程上下文、任务分解和 JSON 输出约束。
9. 下载 Markdown 报告：点击下载按钮，说明报告可以用于教师归档或发给学生。
10. 总结产品价值：它把提示词从一次性文本变成可配置、可解释、可导出的教学批改 Agent。

## 14. 产品体验链接占位

产品体验链接：待部署后填写
