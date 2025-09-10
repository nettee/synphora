# 前后端 SSE 通信协议

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
