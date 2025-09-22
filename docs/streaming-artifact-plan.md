# 流式Artifact实现方案

## 需求背景

当前"评价文章"功能在chatbot中流式输出完整内容。用户希望实现：
- Chatbot中只返回确认消息："我将为你生成文章评价"
- 评价的详细内容在Artifact中流式生成
- 提升用户体验的分离式内容展示

## 技术架构概览

### 当前架构
- **通信方式：** Server-Sent Events (SSE)
- **数据流：** 后端 → SSE事件 → 前端实时显示
- **存储模式：** 后端Artifact Manager管理所有artifact数据
- **前端获取：** 通过REST API拉取artifact列表和详情

### 目标架构
- **双轨道输出：** 聊天确认 + Artifact流式内容

## 实现方案

### 核心设计思路

1. **事件分类处理**
   - TEXT_MESSAGE事件 → Chatbot显示确认消息
   - 新增ARTIFACT_CONTENT_*事件 → Artifact区域流式更新

3. **用户体验优化**
   - 立即反馈：确认消息快速显示
   - 自动聚焦：Artifact面板自动展开
   - 无缝切换：流式内容到最终数据的平滑过渡

### 事件流程设计

#### 新增SSE事件类型
- `ARTIFACT_CONTENT_START` - 创建新的Artifact容器
- `ARTIFACT_CONTENT_CHUNK` - Artifact内容片段
- `ARTIFACT_CONTENT_COMPLETE` - 流式完成

#### 完整事件序列
1. RUN_STARTED - 开始处理
2. TEXT_MESSAGE - 发送确认消息到聊天界面
3. ARTIFACT_CONTENT_START - 开始流式填充
4. ARTIFACT_CONTENT_CHUNK (多次) - 流式发送内容片段
5. ARTIFACT_CONTENT_COMPLETE - 流式完成
6. ARTIFACT_CREATED - 用这个事件触发前端更新Artifact列表
7. RUN_FINISHED - 处理结束

## 实现进度

### 阶段1：后端事件系统扩展（已实现）
- 扩展SSE事件类型定义
- 修改Agent逻辑实现事件分离
- 确保Artifact存储的完整性

### 阶段2：前端适配（待实现）
- 适配新的SSE事件类型
- 实现 Artifact 流式内容的显示

### 阶段3：用户体验优化（待实现）
- 添加流式状态指示器
- 实现自动面板展开和焦点管理
- 完善错误处理和恢复机制