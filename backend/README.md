```
uv run uvicorn src.synphora.server:app --reload
```

```
curl -X GET "http://127.0.0.1:8000/health"
```

```
curl -X POST "http://127.0.0.1:8000/agent" \
-H "Content-Type: application/json" \
-d '{"message": "Hello, how are you?"}'
```