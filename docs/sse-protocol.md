# 前后端通信协议

本文档定义了前端 (`chatbot-demo.tsx`) 和后端 (`agent.py`) 之间通过 Server-Sent Events (SSE) 进行通信的协议。

## 概述

当用户发送消息后，前端会向后端的 `/agent` 端点发起一个 POST 请求。后端会以 `text/event-stream` 的形式返回一个 SSE 流。这个流包含了一系列事件，用于实时更新前端的用户界面。

一个典型的通信流程如下：
1.  通信开始，后端发送 `RUN_STARTED` 事件。
2.  后端流式发送一个或多个 `TEXT_MESSAGE` 事件，每个事件包含一部分文本内容。属于同一条完整消息的所有文本块共享同一个 `message_id`。
3.  通信结束，后端发送 `RUN_FINISHED` 事件。

## 事件详解

所有事件的数据负载（`data` 字段）都是一个 JSON 对象，其中包含一个 `type` 字段来标识事件类型。

### RUN_STARTED

-   **描述**: 表示后端代理已开始处理请求并生成响应。
-   **方向**: 后端 -> 前端
-   **JSON 负载**:
    ```json
    {
      "type": "RUN_STARTED"
    }
    ```
-   **前端行为**:
    -   重置当前消息状态，准备接收新的助手消息。
    -   可以显示一个加载指示器。

### TEXT_MESSAGE

-   **描述**: 包含助手生成的文本内容的一部分。一个完整的回复可能被分割成多个 `TEXT_MESSAGE` 事件进行流式传输。
-   **方向**: 后端 -> 前端
-   **JSON 负载**:
    ```json
    {
      "type": "TEXT_MESSAGE",
      "data": {
        "message_id": "<string>",
        "content": "<string>"
      }
    }
    ```
    -   `message_id`: 字符串类型，唯一标识当前正在流式传输的这条消息。
    -   `content`: 字符串类型，本次事件传输的文本片段。
-   **前端行为**:
    -   当收到具有新 `message_id` 的第一个 `TEXT_MESSAGE` 事件时，在聊天界面中创建一个新的助手消息。
    -   当收到具有相同 `message_id` 的后续 `TEXT_MESSAGE` 事件时，将其 `content` 附加到现有消息的末尾，实现打字机效果。

### RUN_FINISHED

-   **描述**: 表示后端代理已完成本次请求的所有处理和响应生成。
-   **方向**: 后端 -> 前端
-   **JSON 负载**:
    ```json
    {
      "type": "RUN_FINISHED"
    }
    ```
-   **前端行为**:
    -   将聊天状态设置为空闲（`ready`）。
    -   隐藏加载指示器。
    -   允许用户输入新的消息。

## 新增事件类型

### ARTIFACT_CONTENT_START

-   **描述**: 表示开始创建并流式填充一个新的 Artifact。
-   **方向**: 后端 -> 前端
-   **JSON 负载**:
    ```json
    {
      "type": "ARTIFACT_CONTENT_START",
      "data": {
        "artifact_id": "<string>",
        "title": "<string>",
        "description": "<string, optional>"
      }
    }
    ```
    -   `artifact_id`: 字符串类型，唯一标识这个 Artifact。
    -   `title`: 字符串类型，Artifact 的标题。
    -   `description`: 字符串类型，可选，Artifact 的描述。
-   **前端行为**:
    -   创建一个新的流式 Artifact 对象，设置 `isStreaming: true`。
    -   自动展开 Artifact 面板并选中该 Artifact。
    -   显示加载动画和 "正在生成中..." 状态提示。

### ARTIFACT_CONTENT_CHUNK

-   **描述**: 包含 Artifact 内容的一个片段，用于流式更新内容。
-   **方向**: 后端 -> 前端
-   **JSON 负载**:
    ```json
    {
      "type": "ARTIFACT_CONTENT_CHUNK",
      "data": {
        "artifact_id": "<string>",
        "content": "<string>"
      }
    }
    ```
    -   `artifact_id`: 字符串类型，对应的 Artifact ID。
    -   `content`: 字符串类型，本次传输的内容片段。
-   **前端行为**:
    -   将 `content` 追加到对应 Artifact 的现有内容末尾。
    -   实时渲染更新后的内容，实现流式显示效果。

### ARTIFACT_CONTENT_COMPLETE

-   **描述**: 表示指定 Artifact 的流式内容传输已完成。
-   **方向**: 后端 -> 前端
-   **JSON 负载**:
    ```json
    {
      "type": "ARTIFACT_CONTENT_COMPLETE",
      "data": {
        "artifact_id": "<string>"
      }
    }
    ```
    -   `artifact_id`: 字符串类型，已完成的 Artifact ID。
-   **前端行为**:
    -   将对应 Artifact 的 `isStreaming` 状态设置为 `false`。
    -   移除加载动画和状态提示。
    -   保持内容显示，等待后续的 `ARTIFACT_LIST_UPDATED` 事件。

### ARTIFACT_LIST_UPDATED

-   **描述**: 表示后端的 Artifact 列表已更新，前端应重新获取数据。
-   **方向**: 后端 -> 前端
-   **JSON 负载**:
    ```json
    {
      "type": "ARTIFACT_LIST_UPDATED",
      "data": {}
    }
    ```
-   **前端行为**:
    -   触发重新获取 Artifact 列表的 API 调用。
    -   更新本地缓存，确保数据一致性。

## 典型流程详解

### 流式 Artifact 完整流程

当用户请求生成文章评价时，完整的事件序列如下：

1. **RUN_STARTED** - 开始处理用户请求
   ```json
   { "type": "RUN_STARTED" }
   ```

2. **TEXT_MESSAGE** - 发送确认消息到聊天界面
   ```json
   {
     "type": "TEXT_MESSAGE",
     "data": {
       "message_id": "msg_123",
       "content": "我将为你生成文章评价"
     }
   }
   ```

3. **ARTIFACT_CONTENT_START** - 开始流式填充 Artifact
   ```json
   {
     "type": "ARTIFACT_CONTENT_START", 
     "data": {
       "artifact_id": "artifact_456",
       "title": "文章评价报告",
       "description": "基于内容质量、结构和表达的综合评价"
     }
   }
   ```

4. **ARTIFACT_CONTENT_CHUNK** (多次) - 流式发送内容片段
   ```json
   {
     "type": "ARTIFACT_CONTENT_CHUNK",
     "data": {
       "artifact_id": "artifact_456", 
       "content": "## 内容评价\n\n这篇文章的核心观点..."
     }
   }
   ```

5. **ARTIFACT_CONTENT_COMPLETE** - 流式完成
   ```json
   {
     "type": "ARTIFACT_CONTENT_COMPLETE",
     "data": {
       "artifact_id": "artifact_456"
     }
   }
   ```

6. **ARTIFACT_LIST_UPDATED** - 触发前端更新 Artifact 列表
   ```json
   {
     "type": "ARTIFACT_LIST_UPDATED",
     "data": {}
   }
   ```

7. **RUN_FINISHED** - 处理结束
   ```json
   { "type": "RUN_FINISHED" }
   ```

### 前端状态变化

**聊天界面**:
- 显示确认消息："我将为你生成文章评价"
- 不显示实际的评价内容

**Artifact 面板**:
- 自动展开并显示新创建的 Artifact
- 实时显示流式生成的内容
- 显示加载状态直到完成
- 完成后转为静态显示模式

这种设计实现了**双轨道输出**：聊天确认 + Artifact 流式内容，提升了用户体验。
