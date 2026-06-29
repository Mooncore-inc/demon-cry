# demon-cry

он пока пиз##бол, но это исправим потом

установка:
```bash
pip install -r requirements.txt
```
запуск:
```bash
uvicorn core.__main__:app --host 0.0.0.0 --port 8000
```

тест:
```bash
curl -X POST http://localhost:8000/investigate \
     -H "Content-Type: application/json" \
     -d '{"target": "Илон маск", "max_iterations": 10}'
```