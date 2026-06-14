"""
周报自动生成智能体 (WeeklyReportAgent)

帮助用户整理一周的工作内容，自动生成结构化的周报，并可推送到飞书文档归档。
"""
import os
import json
from typing import Annotated, List, Dict, Any
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage, HumanMessage
from coze_coding_utils.runtime_ctx.context import default_headers, new_context

# 尝试从 storage.memory 导入 memory_saver，如果失败则使用 langgraph 的 MemorySaver
try:
    from storage.memory.memory_saver import get_memory_saver
    def get_checkpointer():
        return get_memory_saver()
except ImportError:
    from langgraph.checkpoint.memory import MemorySaver
    def get_checkpointer():
        return MemorySaver()

from tools.weekly_report_tools import (
    format_work_items,
    generate_markdown_report,
    create_feishu_weekly_table,
    save_weekly_to_feishu,
)

LLM_CONFIG = "config/agent_llm_config.json"

# 默认保留最近 20 轮对话 (40 条消息)
MAX_MESSAGES = 40

# 工具列表
TOOLS = [
    format_work_items,
    generate_markdown_report,
    create_feishu_weekly_table,
    save_weekly_to_feishu,
]


def _windowed_messages(old, new) -> list[AnyMessage]:
    """滑动窗口: 只保留最近 MAX_MESSAGES 条消息"""
    combined = add_messages(old, new)
    if len(combined) <= MAX_MESSAGES:
        return combined
    return list(combined)[-MAX_MESSAGES:]


class AgentState(MessagesState):
    messages: Annotated[list[AnyMessage], _windowed_messages]


def build_agent(ctx=None):
    """
    构建周报自动生成智能体

    Args:
        ctx: 请求上下文，用于链路追踪

    Returns:
        配置好的 Agent 实例
    """
    workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
    config_path = os.path.join(workspace_path, LLM_CONFIG)

    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    api_key = os.getenv("COZE_WORKLOAD_IDENTITY_API_KEY")
    base_url = os.getenv("COZE_INTEGRATION_MODEL_BASE_URL")

    llm = ChatOpenAI(
        model=cfg["config"].get("model"),
        api_key=api_key,
        base_url=base_url,
        temperature=cfg["config"].get("temperature", 0.7),
        streaming=True,
        timeout=cfg["config"].get("timeout", 600),
        extra_body={
            "thinking": {
                "type": cfg["config"].get("thinking", "disabled")
            }
        },
        default_headers=default_headers(ctx) if ctx else {},
    )

    return create_agent(
        model=llm,
        system_prompt=cfg.get("sp"),
        tools=TOOLS,
        checkpointer=get_checkpointer(),
        state_schema=AgentState,
    )
