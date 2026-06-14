# -*- coding: utf-8 -*-
import os
import sys

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agents.agent import build_agent
from coze_coding_utils.runtime_ctx.context import new_context
from langchain_core.messages import HumanMessage


def main():
    print("=" * 60)
    print("Weekly Report Auto Generation Agent")
    print("=" * 60)
    print()
    print("Welcome! Please input your weekly work items.")
    print("(Enter one item per line, press Enter twice to finish)")
    print()
    
    work_items = []
    while True:
        line = input("> ").strip()
        if line == "":
            break
        work_items.append(line)
    
    if not work_items:
        print("No work items entered. Exiting.")
        return
    
    print()
    print("-" * 60)
    name = input("Your name: ").strip() or "User"
    week_date = input("Week date range (e.g. 2024-01-08 to 2024-01-12): ").strip() or "This week"
    next_plan = input("Next week plan (optional, press Enter to skip): ").strip()
    
    work_text = "\n".join(work_items)
    user_input = "Please help me organize my weekly work and generate a report:\n" + work_text
    user_input += "\n\nName is " + name + ", date range is " + week_date + "."
    if next_plan:
        user_input += " Next week plan: " + next_plan + "."
    
    print()
    print("=" * 60)
    print("Generating report, please wait...")
    print("=" * 60)
    print()
    
    try:
        ctx = new_context(method="main")
        agent = build_agent(ctx)
        messages = [HumanMessage(content=user_input)]
        
        response = agent.invoke({"messages": messages})
        
        print()
        print("=" * 60)
        print("Report Generated Successfully!")
        print("=" * 60)
        
        ai_messages = [m for m in response.get("messages", []) 
                      if hasattr(m, "type") and m.type == "ai"]
        if ai_messages:
            print(ai_messages[-1].content)
        
        print()
        print("=" * 60)
        print("Done!")
        
    except Exception as e:
        print("Error: " + str(e))
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
