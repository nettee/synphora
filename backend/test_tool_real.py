#!/usr/bin/env python3
"""
真实工具测试 - 使用真实LLM
"""
import asyncio
import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from synphora.tool import ArticleEvaluationTool
from synphora.sse import SseEvent


async def test_real_tool():
    """测试真实工具执行"""
    
    # 创建工具实例
    tool = ArticleEvaluationTool()
    
    # 测试文章uv 
    article = """
# 重新思考产品经理的价值

在AI大潮涌起的今天，产品经理这个职业正面临前所未有的挑战。
许多人开始质疑：当AI可以分析数据、生成需求文档、甚至设计产品原型时，
产品经理还有什么独特价值？

## 从协调者到价值创造者

传统的产品经理更多是一个协调者角色——在技术、设计、运营之间传递信息，
确保项目按时交付。但这种模式正在被AI工具快速替代。

真正的产品经理应该是价值创造者：
- **洞察用户本质需求**：不是用户说什么要什么，而是理解他们真正想解决的问题
- **构建产品愿景**：将抽象的商业目标转化为具体的产品体验
- **平衡多方利益**：在用户价值、商业价值、技术可行性之间找到最优解

## 不可替代的人文判断

AI擅长处理数据和逻辑，但产品决策往往需要人文判断：
- 什么功能会让用户感到温暖而不是冰冷？
- 如何在商业利益和用户体验之间取得平衡？
- 面对争议性功能，如何做出符合价值观的选择？

这些问题没有标准答案，需要的是同理心、价值观和人生阅历。

## 结语

AI时代的产品经理，不应该害怕被替代，而应该拥抱变化，
将自己从执行者升级为思考者，从协调者升级为决策者。
技术会进步，但对美好产品的追求永不过时。
    """
    
    print("🚀 开始真实工具测试")
    print("📝 文章标题: 重新思考产品经理的价值")
    print("=" * 60)
    
    # 收集事件
    events = []
    content_chunks = []
    
    print("⏳ 正在执行评价...")
    async for event in tool.execute(article_content=article):
        events.append(event)
        
        if event.type.value == "ARTIFACT_CONTENT_START":
            print(f"🎬 开始生成: {event.data.title}")
            print(f"📝 Artifact ID: {event.data.artifact_id}")
            
        elif event.type.value == "ARTIFACT_CONTENT_CHUNK":
            content_chunks.append(event.data.content)
            # 实时显示内容
            print(event.data.content, end="", flush=True)
            
        elif event.type.value == "ARTIFACT_CONTENT_COMPLETE":
            print(f"\n\n✅ 内容生成完成")
            
        elif event.type.value == "ARTIFACT_LIST_UPDATED":
            print(f"📋 Artifact已保存: {event.data.artifact_id}")
    
    print("\n" + "=" * 60)
    print(f"📊 总共生成 {len(events)} 个事件")
    print(f"📦 内容块数量: {len(content_chunks)}")
    print(f"📝 总内容长度: {len(''.join(content_chunks))} 字符")
    
    # 事件类型统计
    event_counts = {}
    for event in events:
        event_type = event.type.value
        event_counts[event_type] = event_counts.get(event_type, 0) + 1
    
    print("\n📈 事件类型分布:")
    for event_type, count in event_counts.items():
        print(f"  {event_type}: {count}")


async def test_callback_mechanism():
    """测试回调机制"""
    print("\n\n🔄 测试回调机制")
    print("=" * 60)
    
    callback_events = []
    
    async def test_callback(event):
        callback_events.append(event)
        print(f"📞 回调收到: {event.type.value}")
    
    tool = ArticleEvaluationTool(event_callback=test_callback)
    
    short_article = """
# 简短测试文章

这是一篇用于测试回调机制的简短文章。
我们只需要验证工具能否正确触发回调。
    """
    
    execution_events = []
    async for event in tool.execute(article_content=short_article):
        execution_events.append(event)
    
    print(f"\n📊 执行事件: {len(execution_events)}")
    print(f"📞 回调事件: {len(callback_events)}")
    print("✅ 回调机制测试完成")


if __name__ == "__main__":
    print("🧪 真实工具系统测试")
    print("使用真实LLM，观察实际效果")
    print("=" * 70)
    
    asyncio.run(test_real_tool())
    asyncio.run(test_callback_mechanism())
    
    print("\n🎉 测试完成！")