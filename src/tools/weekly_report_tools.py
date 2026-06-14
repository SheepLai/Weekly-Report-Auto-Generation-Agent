"""
周报智能体工具模块

提供工作内容整理、周报格式化、飞书文档创建等功能
"""
from langchain.tools import tool
from typing import List, Dict, Any
from coze_coding_utils.log.write_log import request_context
from coze_coding_utils.runtime_ctx.context import new_context
import logging

logger = logging.getLogger(__name__)


@tool
def format_work_items(work_items: str) -> str:
    """
    整理和分类用户输入的工作事项。

    Args:
        work_items: 用户输入的原始工作事项，可以是多行文本，每个事项用换行分隔

    Returns:
        格式化后的工作事项列表，包含分类信息
    """
    ctx = request_context.get() or new_context(method="format_work_items")
    logger.info(f"[format_work_items] Processing work items, length: {len(work_items)}")

    if not work_items or not work_items.strip():
        return "请提供工作事项内容"

    items = [item.strip() for item in work_items.strip().split('\n') if item.strip()]

    categories = {
        "日常事务": [],
        "项目任务": [],
        "沟通协作": [],
        "学习成长": [],
        "其他": []
    }

    keywords_map = {
        "日常事务": ["日常", "维护", "处理", "回复", "邮件", "审批", "整理", "统计", "打卡", "例会", "会议"],
        "项目任务": ["项目", "开发", "需求", "设计", "测试", "上线", "部署", "bug", "优化", "重构", "代码", "任务"],
        "沟通协作": ["沟通", "协作", "讨论", "对齐", "同步", "评审", "汇报", "反馈", "交接", "培训"],
        "学习成长": ["学习", "培训", "阅读", "研究", "总结", "分享", "课程", "考证", "提升"]
    }

    for item in items:
        categorized = False
        for category, keywords in keywords_map.items():
            if any(kw in item for kw in keywords):
                categories[category].append(item)
                categorized = True
                break
        if not categorized:
            categories["其他"].append(item)

    result = "## 📋 工作事项整理\n\n"
    for category, items_list in categories.items():
        if items_list:
            result += f"\n### {category}\n"
            for idx, item in enumerate(items_list, 1):
                result += f"{idx}. {item}\n"

    return result


@tool
def generate_markdown_report(
    user_name: str,
    week_date: str,
    work_summary: str,
    next_week_plan: str = ""
) -> str:
    """
    生成结构化的Markdown格式周报。

    Args:
        user_name: 姓名
        week_date: 周报日期范围（如：2024年1月1日-1月7日）
        work_summary: 本周工作内容摘要（由format_work_items生成）
        next_week_plan: 下周工作计划（可选）

    Returns:
        格式化后的Markdown周报
    """
    ctx = request_context.get() or new_context(method="generate_markdown_report")
    logger.info(f"[generate_markdown_report] Generating report for {user_name}, week: {week_date}")

    report = f"""# 📊 周报

**姓名**: {user_name}
**周期**: {week_date}
**生成时间**: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}

---

## 📌 本周工作概览

{work_summary}

"""

    if next_week_plan:
        report += f"""---

## 🎯 下周工作计划

{next_week_plan}

"""

    report += """---

## 📈 本周总结

请在此处填写本周的工作反思、收获与不足。

### 亮点
-

### 待改进
-

### 建议与想法
-

"""

    return report


@tool
def create_feishu_weekly_table(table_name: str = "周报记录表") -> str:
    """
    在飞书创建周报多维表格，用于存储周报数据。

    Args:
        table_name: 多维表格名称，默认"周报记录表"

    Returns:
        创建结果，包含app_token和table_id
    """
    from storage.feishu_bitable import FeishuBitable

    ctx = request_context.get() or new_context(method="create_feishu_weekly_table")
    logger.info(f"[create_feishu_weekly_table] Creating table: {table_name}")

    try:
        client = FeishuBitable()

        # 创建多维表格
        result = client.create_base(name=table_name)

        if result.get("code") != 0:
            return f"创建失败: {result.get('msg')}"

        app_token = result["data"]["app"]["app_token"]

        # 定义表头字段
        fields = [
            {"field_name": "姓名", "type": 1},  # 文本
            {"field_name": "周报周期", "type": 1},  # 文本
            {"field_name": "工作类别", "type": 4},  # 多选
            {"field_name": "工作内容", "type": 1},  # 文本
            {"field_name": "产出/结果", "type": 1},  # 文本
            {"field_name": "创建时间", "type": 5},  # 日期
        ]

        # 创建数据表
        table_result = client.create_table(
            app_token=app_token,
            table_name="周报明细",
            fields=fields
        )

        if table_result.get("code") != 0:
            return f"创建数据表失败: {table_result.get('msg')}"

        table_id = table_result["data"]["table_id"]["table_id"]

        return f"""✅ 周报多维表格创建成功！

**表格名称**: {table_name}
**App Token**: {app_token}
**Table ID**: {table_id}

请保存以上信息，后续添加周报记录时需要使用。"""

    except Exception as e:
        logger.error(f"[create_feishu_weekly_table] Error: {e}")
        return f"创建失败: {str(e)}"


@tool
def save_weekly_to_feishu(
    app_token: str,
    table_id: str,
    user_name: str,
    week_date: str,
    work_items: List[Dict[str, str]]
) -> str:
    """
    将周报数据保存到飞书多维表格。

    Args:
        app_token: 飞书多维表格的App Token
        table_id: 数据表的Table ID
        user_name: 姓名
        week_date: 周报周期
        work_items: 工作事项列表，每项包含 category(类别) 和 content(内容)

    Returns:
        保存结果
    """
    from storage.feishu_bitable import FeishuBitable

    ctx = request_context.get() or new_context(method="save_weekly_to_feishu")
    logger.info(f"[save_weekly_to_feishu] Saving weekly report for {user_name}")

    try:
        client = FeishuBitable()

        # 构造记录
        records = []
        for item in work_items:
            record = {
                "fields": {
                    "姓名": user_name,
                    "周报周期": week_date,
                    "工作类别": item.get("category", "其他"),
                    "工作内容": item.get("content", ""),
                    "产出/结果": item.get("result", ""),
                }
            }
            records.append(record)

        # 批量添加记录
        result = client.add_records(
            app_token=app_token,
            table_id=table_id,
            records=records
        )

        if result.get("code") != 0:
            return f"保存失败: {result.get('msg')}"

        return f"✅ 成功保存 {len(records)} 条周报记录到飞书！"

    except Exception as e:
        logger.error(f"[save_weekly_to_feishu] Error: {e}")
        return f"保存失败: {str(e)}"
