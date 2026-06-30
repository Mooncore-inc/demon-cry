# Demon Cry 🔍

Demon Cry — это автономный OSINT-агент, который использует LLM для проведения расследований в открытых источниках. Агент сам строит гипотезы, выбирает инструменты и анализирует данные.

### Установка

# Клонируем репозиторий
```bash
git clone https://github.com/Mooncore-inc/demon-cry.git && cd demon-cry
```
# Создаём виртуальное окружение
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows
```
# Устанавливаем зависимости
```bash
pip install -r requirements.txt
```
# Конфигурация
```bash
cp example_config.json config.json
```

# Запуск
```bash
uvicorn core.__main__:app --host 0.0.0.0 --port 8000
```
# Открываем в браузере
# http://localhost:8000

# API
```bash
curl -X POST http://localhost:8000/investigate \
     -H "Content-Type: application/json" \
     -d '{"target": "Илон маск", "max_iterations": 10}'
```
