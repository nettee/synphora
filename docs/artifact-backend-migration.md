# Artifact 后端管理迁移计划

## 概述

当前 Synphora 应用的 artifact 列表由前端维护，每次调用 LLM 时通过请求传递。为了更好地管理数据一致性、支持后端生成 artifact 以及为未来的持久化做准备，我们计划将 artifact 管理迁移到后端。

## 架构设计

### 数据流
```
用户上传 → 前端乐观更新 → 后端API → 更新服务器状态
后端生成 → 后端创建 → SSE推送 → 前端实时更新  
用户删除 → 前端确认 → 后端API → 删除服务器状态
```

### 技术方案
- **存储**: 后端内存存储（未来可扩展为数据库）
- **同步**: SSE 事件驱动的实时更新
- **体验**: 用户上传乐观更新，删除同步确认

## 分阶段实施计划

## 阶段1: 后端存储层实现 (15分钟)

### 目标
实现后端 artifact 数据结构和内存存储

### 实施步骤

#### 1.1 扩展数据模型 (5分钟)

```python
from typing import Dict, List, Optional
from enum import Enum

class ArtifactType(str, Enum):
    ORIGINAL = "original"
    COMMENT = "comment"

class ArtifactData(BaseModel):
    id: str
    role: str  # "user" | "assistant" 
    type: ArtifactType
    title: str
    description: Optional[str] = None
    content: str
    created_at: str
    updated_at: str
```

#### 1.2 实现存储管理器 (10分钟)

```python
class ArtifactManager:
  pass
```

### 验证方法
- 运行 Python REPL 测试基本 CRUD 操作
- 确保数据结构与前端类型定义兼容

---

## 阶段2: 后端 API 接口实现 (20分钟)

### 目标
实现 artifact 的 CRUD API 接口

### 实施步骤

#### 2.1 更新 server.py 添加 API 接口 (15分钟)

CRUD

#### 2.2 更新 agent.py 使用管理器 (5分钟)
**文件**: `backend/src/synphora/agent.py`

```python
from synphora.artifact_manager import artifact_manager

# 修改 AgentRequest，移除 artifacts 字段
class AgentRequest(BaseModel):
    message: str
    # artifacts: list[ArtifactData]  # 删除这行

async def generate_agent_response(request: AgentRequest) -> AsyncGenerator[SseEvent, None]:
    # ... 其他代码保持不变
    
    # 从管理器获取最新 artifacts
    artifacts = artifact_manager.list_artifacts()
    
    # 格式化 artifacts 用于 LLM
    def format_artifact(artifact: ArtifactData) -> str:
        return f"""<file>
          <name>{artifact.title}</name>
          <content>{artifact.content}</content>
        </file>"""
    
    # ... 使用 artifacts 的代码保持不变
```

### 验证方法
- 使用 curl 测试所有 API 接口
- 验证创建、获取、删除操作的正确性

## 阶段3: SSE 事件扩展 (10分钟)

### 目标
扩展 SSE 事件系统支持 artifact 创建通知

### 实施步骤

#### 3.1 扩展 SSE 事件类型 (5分钟)
**文件**: `backend/src/synphora/sse.py`

```python
class ArtifactCreatedEvent(SseEvent):
    def __init__(self, artifact: ArtifactData):
        super().__init__("ARTIFACT_CREATED", {
            "artifact": artifact.dict()
        })
    
    @classmethod
    def new(cls, artifact: ArtifactData) -> "ArtifactCreatedEvent":
        return cls(artifact)
```

#### 3.2 在 agent 中生成 artifact 时发送事件 (5分钟)
**文件**: `backend/src/synphora/agent.py`

```python
from synphora.sse import ArtifactCreatedEvent

async def generate_agent_response(request: AgentRequest) -> AsyncGenerator[SseEvent, None]:
    # ... 现有代码
    
    # 如果需要生成新的 artifact (例如分析结果)
    if should_create_artifact(request.message):
        new_artifact = artifact_manager.create_artifact(
            title="分析结果",
            content=analysis_result,
            artifact_type=ArtifactType.COMMENT,
            role="assistant"
        )
        yield ArtifactCreatedEvent.new(new_artifact)
    
    # ... 其他代码
```

### 验证方法
- 触发 LLM 生成 artifact 的场景
- 验证前端能接收到 ARTIFACT_CREATED 事件

---

## 阶段4: 前端适配改造 (25分钟)

### 目标
修改前端代码接入后端 API，移除本地 artifact 状态管理

### 实施步骤

#### 4.1 添加 API 调用函数 (10分钟)
**文件**: `frontend/lib/api.ts` (新建)

```typescript
import { ArtifactData } from './types';

const API_BASE = 'http://127.0.0.1:8000';

export class ArtifactAPI {
  static async getArtifacts(): Promise<ArtifactData[]> {
    const response = await fetch(`${API_BASE}/artifacts`);
    if (!response.ok) throw new Error('Failed to fetch artifacts');
    const data = await response.json();
    return data.artifacts;
  }

  static async createArtifact(title: string, content: string): Promise<ArtifactData> {
    const response = await fetch(`${API_BASE}/artifacts`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, content })
    });
    if (!response.ok) throw new Error('Failed to create artifact');
    return response.json();
  }

  static async uploadArtifact(file: File): Promise<ArtifactData> {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_BASE}/artifacts/upload`, {
      method: 'POST',
      body: formData
    });
    if (!response.ok) throw new Error('Failed to upload artifact');
    return response.json();
  }

  static async deleteArtifact(id: string): Promise<void> {
    const response = await fetch(`${API_BASE}/artifacts/${id}`, {
      method: 'DELETE'
    });
    if (!response.ok) throw new Error('Failed to delete artifact');
  }
}
```

#### 4.2 修改 synphora.tsx 移除本地状态 (10分钟)
**文件**: `frontend/app/synphora.tsx`

```typescript
import { ArtifactAPI } from '@/lib/api';

const SynphoraPage = ({ 
  initialArtifactStatus = ArtifactStatus.EXPANDED
}: {
  initialArtifactStatus?: ArtifactStatus;
}) => {
  const [artifacts, setArtifacts] = useState<ArtifactData[]>([]);
  const [loading, setLoading] = useState(true);

  // 从后端加载 artifacts
  useEffect(() => {
    const loadArtifacts = async () => {
      try {
        const data = await ArtifactAPI.getArtifacts();
        setArtifacts(data);
      } catch (error) {
        console.error('Failed to load artifacts:', error);
      } finally {
        setLoading(false);
      }
    };
    loadArtifacts();
  }, []);

  const handleUploadArtifact = async (file: File) => {
    try {
      const newArtifact = await ArtifactAPI.uploadArtifact(file);
      setArtifacts(prev => [...prev, newArtifact]);
    } catch (error) {
      console.error('Upload failed:', error);
    }
  };

  const handleDeleteArtifact = async (id: string) => {
    if (!confirm('确定删除这个文件？')) return;
    
    try {
      await ArtifactAPI.deleteArtifact(id);
      setArtifacts(prev => prev.filter(a => a.id !== id));
    } catch (error) {
      console.error('Delete failed:', error);
    }
  };

  if (loading) {
    return <div>加载中...</div>;
  }

  if (artifacts.length === 0) {
    return <div>暂无文件，请上传文件开始使用</div>;
  }

  // ... 其他代码保持不变
};
```

#### 4.3 修改 chatbot.tsx 处理 SSE 事件 (5分钟)
**文件**: `frontend/components/chatbot.tsx`

```typescript
export const Chatbot = ({
  initialMessages = [],
  artifacts = [],
  onArtifactCreated,
}: {
  initialMessages: ChatMessage[];
  artifacts: ArtifactData[];
  onArtifactCreated?: (artifact: ArtifactData) => void;
}) => {
  // ... 现有代码

  const sendMessage = async (text: string) => {
    // ... 现有代码，移除 artifacts 传递部分
    
    body: JSON.stringify({
      message: text,
      // 移除 artifacts 字段
    }),

    onmessage(msg) {
      try {
        if (msg.data && msg.data.trim() !== "") {
          const eventData = JSON.parse(msg.data);

          switch (eventData.type) {
            // ... 现有 case

            case "ARTIFACT_CREATED":
              const newArtifact = eventData.data.artifact;
              onArtifactCreated?.(newArtifact);
              break;
          }
        }
      } catch (error) {
        console.error("Error parsing SSE data:", error);
      }
    },
  };
```

### 验证方法
- 测试页面加载时从后端获取 artifacts
- 测试用户上传文件功能
- 测试用户删除文件功能
- 测试后端生成 artifact 的实时推送

---

## 阶段5: 集成测试和优化 (10分钟)

### 目标
端到端测试和用户体验优化

### 实施步骤

#### 5.1 端到端测试 (5分钟)
1. 启动后端服务：`uv run server`
2. 启动前端服务：`pnpm dev`
3. 测试场景：
   - 页面加载显示空状态
   - 上传文件后立即显示
   - 删除文件确认流程
   - 发送消息触发 LLM 分析
   - 验证生成的 artifact 实时出现

#### 5.2 体验优化 (5分钟)
- 添加加载状态指示器
- 优化错误提示信息
- 添加上传进度显示
- 完善确认对话框样式

### 验证方法
- 完整流程测试通过
- 网络错误时的降级体验
- 并发操作的正确处理

## 后续扩展计划（本次不实现）

### 短期优化
- 添加 artifact 编辑功能
- 实现批量操作
- 支持文件预览

### 长期规划
- 持久化存储（数据库）
- 用户会话管理
- 协作功能支持
- 版本历史管理

## 进度

- [x] 阶段1: 后端存储层实现 (15分钟)
- [x] 阶段2: 后端 API 接口实现 (20分钟)
- [x] 阶段3: SSE 事件扩展 (10分钟)
- [x] 阶段4: 前端适配改造 (25分钟)
- [x] 阶段5: 集成测试和优化 (10分钟)