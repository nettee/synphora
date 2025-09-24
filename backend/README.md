## 代码格式化

使用便捷脚本：
```bash
./ruff.sh check    # 检查代码质量
./ruff.sh format   # 格式化代码
./ruff.sh fix      # 自动修复问题
./ruff.sh all      # 执行所有操作
```

或者直接使用 uv 命令：
```bash
uv run ruff check src/          # 检查
uv run ruff format src/         # 格式化
uv run ruff check --fix src/    # 修复
```

## 服务启动

目前是简单的 HTTP SSE 服务

启动服务：
```
uv run server
```

健康检查：
```
curl -X GET "http://127.0.0.1:8000/health"
```

发送请求：
```
curl -X POST "http://127.0.0.1:8000/agent" \
-H "Content-Type: application/json" \
-d '{"text": "Hello, how are you?", "model": "openai/gpt-4o", "webSearch": false}'
```

## 数据存储

后端使用基于文件的存储系统，数据在服务重启后会持久化保存。

### 存储配置

通过环境变量 `SYNPHORA_STORAGE_PATH` 配置存储路径：
```bash
# 使用默认路径（tests/data/store）
uv run server

# 使用自定义路径
SYNPHORA_STORAGE_PATH=/path/to/storage uv run server
```

### 存储结构

```
storage_path/
├── metadata.json              # 所有 artifacts 的元数据
├── {artifact_id_1}.txt       # artifact 内容文件
├── {artifact_id_2}.txt       # artifact 内容文件
└── ...
```

**metadata.json 格式：**
```json
{
  "artifact_id": {
    "id": "artifact_id",
    "role": "user|assistant", 
    "type": "original|comment",
    "title": "artifact 标题",
    "description": "artifact 描述（可选）",
    "created_at": "2025-09-22T11:15:12.184144",
    "updated_at": "2025-09-22T11:15:12.184144"
  }
}
```

### Artifact API

创建 artifact：
```bash
curl -X POST "http://127.0.0.1:8000/artifacts" \
-H "Content-Type: application/json" \
-d '{"title": "测试文档", "content": "这是测试内容", "description": "可选描述"}'
```

获取所有 artifacts：
```bash
curl -X GET "http://127.0.0.1:8000/artifacts"
```

获取特定 artifact：
```bash
curl -X GET "http://127.0.0.1:8000/artifacts/{artifact_id}"
```

删除 artifact：
```bash
curl -X DELETE "http://127.0.0.1:8000/artifacts/{artifact_id}"
```

上传文件作为 artifact：
```bash
curl -X POST "http://127.0.0.1:8000/artifacts/upload" \
-F "file=@/path/to/file.txt"
```