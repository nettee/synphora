# Agent化架构改进计划

## 概述

将现有硬编码prompt系统改造为智能Agent架构，让LLM动态生成确认消息并调用工具执行任务，保持现有SSE协议不变。

## 当前实现范围 vs 长期规划

### 🎯 第一期实现（当前）

**核心目标：**
- 替换硬编码的确认消息，改为LLM动态生成
- 将文章评价功能改造为工具调用
- 保持现有SSE协议和前端完全不变
- 实现基础的Agent工作流

**技术范围：**
- 单一文章评价工具
- 简单的LLM决策机制
- 基础事件委托系统
- 错误降级到现有模式

### 🚀 长期规划（暂不实现）

**扩展功能：**
- 多工具并发调用和编排
- 复杂的工具链调用（工具A的输出作为工具B的输入）
- 动态工具发现和注册机制
- 多轮对话和上下文记忆
- 工具执行结果的智能总结和推荐

**高级特性：**
- 工具性能监控和自适应优化
- 基于用户反馈的工具调用策略学习
- 支持第三方工具插件系统
- 分布式工具执行环境

---

## 技术架构设计

### 整体流程

```
用户请求 → Agent编排 → LLM确认消息 → LLM工具决策 → 工具执行(SSE) → 完成
```

### 核心组件

#### 1. Agent编排器（当前实现）
- **位置**: `agent.py` 中的新函数
- **职责**: 
  - 接收用户请求
  - 协调LLM生成确认消息
  - 决策工具调用
  - 统一事件分发

#### 2. 流式工具基类（当前实现）
- **位置**: `tool.py` 扩展
- **职责**:
  - 定义统一的工具接口
  - 支持SSE事件回调
  - 处理异步执行和错误

#### 3. 事件委托机制（当前实现）
- **机制**: 回调函数注入
- **目标**: 让工具能向Agent发送SSE事件
- **保证**: 事件时序和类型正确性

### 关键技术点

#### 回调机制设计
```python
# 工具接收回调函数
async def tool_execute(content: str, event_callback: Callable):
    # 工具内部调用回调发送事件
    await event_callback(ArtifactContentStartEvent.new(...))
    
# Agent提供回调实现
async def agent_event_handler(event: SseEvent):
    yield event  # 转发到Agent的生成器
```

#### 事件委托流程
1. Agent创建event_callback函数
2. 将回调注入到工具实例
3. 工具执行时调用回调发送SSE事件
4. Agent收集并转发所有事件

---

## 实施步骤

### Phase 1: 基础工具系统 (2-3小时)

#### 1.1 扩展工具基类
**文件**: `backend/src/synphora/tool.py`

**任务**:
- 创建 `AsyncStreamingTool` 基类
- 定义 `event_callback` 接口
- 实现 `yield_event` 辅助方法

**关键点**:
- 支持异步执行
- 标准化事件发送接口
- 基础错误处理

#### 1.2 实现文章评价工具
**任务**:
- 继承 `AsyncStreamingTool`
- 实现 `evaluate_article` 方法  
- 集成现有评价prompt逻辑
- 通过回调发送ARTIFACT_*事件序列

**事件序列**:
1. `ARTIFACT_CONTENT_START`
2. 多次 `ARTIFACT_CONTENT_CHUNK`
3. `ARTIFACT_CONTENT_COMPLETE`
4. `ARTIFACT_LIST_UPDATED`

### Phase 2: Agent工作流 (2-3小时)

#### 2.1 创建Agent函数
**文件**: `backend/src/synphora/agent.py`

**任务**:
- 基于现有 `workflow.py` 模式
- 实现两阶段处理：确认消息 + 工具调用
- 集成LLM决策逻辑

**流程设计**:
```python
async def agent_generate_response(request):
    # 1. 发送 RUN_STARTED
    yield RunStartedEvent.new()
    
    # 2. LLM生成确认消息
    confirmation = await llm.ainvoke("生成确认消息...")
    yield TextMessageEvent.new(content=confirmation)
    
    # 3. LLM决策工具调用
    tool_decision = await llm_with_tools.ainvoke(...)
    
    # 4. 执行工具并委托事件
    if tool_decision.tool_calls:
        async for event in execute_tool_with_callback(...):
            yield event
    
    # 5. 发送 RUN_FINISHED
    yield RunFinishedEvent.new()
```

#### 2.2 实现事件委托
**任务**:
- 创建工具执行函数，支持事件回调
- 实现异步生成器的事件委托
- 处理工具执行异常

### Phase 3: 系统集成 (1-2小时)

#### 3.1 修改现有接口
**文件**: `backend/src/synphora/agent.py`

**任务**:
- 修改 `generate_agent_response` 函数
- 添加新旧模式切换逻辑
- 保持现有函数签名不变

**集成策略**:
```python
async def generate_agent_response(request):
    # 配置开关控制使用模式
    if USE_AGENT_MODE:
        async for event in agent_generate_response(request):
            yield event
    else:
        # 原有逻辑保持不变
        async for event in original_logic(request):
            yield event
```

#### 3.2 错误处理和降级
**任务**:
- 实现工具调用失败时的降级机制
- 添加超时控制
- 完善异常捕获和日志
