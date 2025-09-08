目前是简单的 HTTP SSE 服务

启动服务：
```
uv run uvicorn synphora.server:app --app-dir src --reload
```

健康检查：
```
curl -X GET "http://127.0.0.1:8000/health"
```

发送请求：
```
curl -X POST "http://127.0.0.1:8000/agent" \
-H "Content-Type: application/json" \
-d '{"message": "Hello, how are you?", "model": "openai/gpt-4o", "webSearch": false}'
```