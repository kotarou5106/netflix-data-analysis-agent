# Netflix Data Analysis Agent

## Project Overview / 项目概述

Netflix Data Analysis Agent 是一个面向 Netflix 用户行为数据的本地数据分析 Agent 项目。它从自然语言问题出发，完成意图识别、任务规划、工具选择、数据查询、统计分析、知识库检索、报告生成和结果校验。

本项目不是简单的 Text-to-SQL。SQL 查询只是工具链中的一部分，Agent 还会结合业务知识库、固定统计分析函数、报告规范和校验逻辑，生成带有证据和限制说明的分析报告。

## Why Not Just Text-to-SQL / 为什么不是简单 Text-to-SQL

本项目的目标是构建一个完整但轻量的分析型 Agent 流程，而不是只把用户问题翻译成 SQL：

- Planner / 规划器：识别用户意图并生成结构化分析计划。
- Tool Router / 工具路由：根据意图和计划选择需要执行的工具。
- RAG Knowledge Retrieval / RAG 业务知识检索：检索指标定义、流失分析口径和报告规范。
- SQL Tool / SQL 工具：通过 DuckDB 安全查询本地 CSV 数据。
- Python Analysis Tool / Python 统计分析工具：执行固定统计分析函数。
- Report Writer / 报告生成器：基于工具结果生成结构化 Markdown 报告。
- Verifier / 校验器：检查报告章节和因果性表述。
- Evaluation Runner / 本地评测器：使用测试集评估意图、工具选择和报告完整性。

## Architecture / 架构

```text
User Query
-> Planner
-> Tool Router
-> Executor
-> RAG Tool / SQL Tool / Python Analysis Tool
-> Report Writer
-> Verifier
-> Final Report
```

## LangGraph Workflow / LangGraph 工作流

V2 使用 LangGraph `StateGraph` 表达 Agent 节点流转，流程为 `planner -> tool_router -> executor -> report_writer -> verifier -> END`。每个 LangGraph node 都只是包装已有模块函数，不改变 V1 的业务逻辑。

为了保持本地运行的稳定性，`run_agent(user_query: str)` 的外部调用方式保持不变；如果当前环境没有安装 LangGraph，系统会优雅 fallback 到原来的手写 pipeline。

## LLM Planner with Fallback / 带回退机制的大模型规划器

V3 支持可选 LLM Planner。LLM 只负责根据用户问题生成结构化 JSON 计划，字段包括 `intent` 和 `plan`，每个 plan step 必须包含 `step_id`、`tool`、`description` 和 `depends_on`。

系统会对 LLM 输出进行 schema 校验，并限制合法 intent 和 tool 名称。如果没有配置 `OPENAI_API_KEY`、LLM 不可用、JSON 解析失败、字段缺失或工具名不合法，Planner 会自动回退到规则 Planner，保证 CLI 和评测流程仍可运行。

LLM 不直接执行 SQL，也不直接调用工具；SQL 查询、工具执行和报告校验仍由现有安全模块负责。

## Implemented Features / 已实现功能

- Intent Detection / 意图识别
- Structured Planning / 结构化规划
- RAG Knowledge Retrieval / RAG 知识检索
- Safe SQL Tool / 安全 SQL 工具
- Python Analysis Tool / Python 统计分析工具
- Report Writer / 报告生成
- Verifier / 结果校验
- Evaluation Runner / 本地评测器

## Safety Design / 安全设计

- SQL Tool 只允许执行 `SELECT` 和 `WITH` 查询。
- 明确禁止 `DROP` / `DELETE` / `UPDATE` / `INSERT` / `ALTER` / `CREATE` / `TRUNCATE`。
- 可选 LLM Planner 只生成结构化计划，不直接生成或执行 SQL。
- SQL 查询使用固定模板和字段检查，避免任意 SQL 执行。
- Verifier 会检查强因果表达，避免把相关性直接写成因果性。
- 报告要求包含 Evidence / 证据 和 Limitations / 限制说明。

## How to Run / 如何运行

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m pytest -q
python3 -m src.app "分析不同订阅类型的流失率，并给出运营建议"
python3 -m src.evaluation.eval_runner --limit 2
```

## Example Output / 示例输出

CLI 会输出一份 Markdown 分析报告。报告包含用户问题、识别出的意图、分析计划、使用工具、证据、关键发现、业务建议和限制说明。

示例摘要：

```text
# Analysis Report / 分析报告

## User Question / 用户问题
分析不同订阅类型的流失率，并给出运营建议

## Intent / 意图
churn_analysis

## Evidence / 证据
- RAG 检索到流失分析指南和指标定义
- SQL 展示 subscription_type、user_count、churn_rate 等结果
- Python analysis 展示分组统计结果

## Key Findings / 关键发现
- 不同订阅类型的观察性流失率存在差异，较高的组可被视为高风险群体。

## Limitations / 限制说明
- 当前分析是观察性分析，不能直接证明因果关系。
```

## Evaluation / 评测

本项目包含本地 Evaluation Runner，用于评估主链路在固定测试集上的表现。当前指标包括：

- `intent_accuracy`
- `avg_tool_selection_score`
- `avg_section_completeness_score`

运行默认评测：

```bash
python3 -m src.evaluation.eval_runner
```

只跑前 N 条 case：

```bash
python3 -m src.evaluation.eval_runner --limit 2
```

运行全部 case：

```bash
python3 -m src.evaluation.eval_runner --all
```

## Current Limitations / 当前限制

- 当前 LLM Planner 是可选能力；未配置 `OPENAI_API_KEY` 时会使用规则 Planner。
- RAG 仍是轻量关键词检索，没有使用生产级向量数据库。
- SQL 主要使用固定模板，不支持复杂自由分析问题。
- Python Analysis Tool 只包含少量固定统计函数。
- 评测集规模较小，主要用于本地回归验证。
- 这不是生产级系统，仍需要更多数据校验、权限控制、错误处理和评测覆盖。

## Future Work / 后续扩展

- LLM Planner
- LangGraph
- Embedding RAG
- BM25 + Vector Hybrid Retrieval
- Rerank
- MCP Server
- Streamlit UI
- More Evaluation Cases

## Resume Description / 简历描述

构建了一个基于 Netflix 用户行为数据的本地数据分析 Agent，覆盖意图识别、结构化任务规划、工具路由、业务知识库检索、安全 SQL 查询、Python 统计分析、Markdown 报告生成、结果校验和本地评测流程。项目强调分析证据和限制说明，通过 Verifier 约束相关性与因果性的表述，并使用 Evaluation Runner 对意图识别、工具选择和报告完整性进行回归评估。
