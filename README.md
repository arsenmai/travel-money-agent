# ✈️ Travel Money Agent

AI-агент, который отвечает на вопросы путешественника: живые курсы валют, текущая погода в любом городе мира и расчёты. Модель сама решает, какие инструменты вызвать и в каком порядке, в том числе несколько параллельно.

## Как это устроено

```
Браузер (static/index.html)
   │  POST /ask {"task": "..."}
   ▼
FastAPI (server.py)
   │
   ▼
Цикл агента (agent_loop.py) ──► Claude API (tool calling)
   │
   ├──► get_exchange_rate ──► ExchangeRate-API
   ├──► get_weather       ──► Open-Meteo
   └──► calculate
```

- **agent_loop.py** — цикл агента: запрос к модели → выполнение запрошенных инструментов → результаты обратно модели, пока она не даст финальный ответ.
- **real_tools.py** — инструменты на реальных API, с таймаутами, обработкой ошибок и кэшем.
- **server.py** — REST API на FastAPI: `POST /ask`, `GET /tools`, `GET /health`.
- **static/index.html** — фронтенд на чистых HTML/CSS/JS.
- **app.py** — альтернативный интерфейс на Streamlit.

## Запуск

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Создай файл `.env`:

```
ANTHROPIC_API_KEY=your-key-here
```

Затем:

```bash
uvicorn server:app --reload     # сайт: http://localhost:8000, API-документация: /docs
# или
streamlit run app.py            # интерфейс на Streamlit
```

## Данные

[Rates By Exchange Rate API](https://www.exchangerate-api.com) · [Weather by Open-Meteo](https://open-meteo.com)
