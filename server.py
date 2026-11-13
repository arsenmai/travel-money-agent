"""
БЭКЕНД: FastAPI-сервер вокруг агента.

Установка:
    pip install fastapi uvicorn

Запуск (из папки hackathon-practice, с активированным venv):
    uvicorn server:app --reload

Потом открой:
    http://localhost:8000          — фронтенд (static/index.html)
    http://localhost:8000/docs     — автодокументация API, можно слать запросы из браузера
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from agent_loop import run_agent, tools as AGENT_TOOLS

app = FastAPI(title="Travel Money Agent API")


# ---------- API-контракт: что принимаем и что отдаём ----------

class AskRequest(BaseModel):
    # Field проверяет входные данные: пустую задачу или роман на 5000 символов не пропустим
    task: str = Field(..., min_length=1, max_length=1000)


class Step(BaseModel):
    step: int
    tool: str
    args: dict
    result: str


class AskResponse(BaseModel):
    answer: str
    steps: list[Step]


# ---------- Эндпоинты ----------

@app.get("/health")
def health():
    """Простая проверка, что сервер жив."""
    return {"status": "ok"}


class ToolInfo(BaseModel):
    name: str
    description: str


@app.get("/tools", response_model=list[ToolInfo])
def list_tools():
    """НОВОЕ: какие инструменты есть у агента. Берём прямо из описаний tools в agent_loop.py,
    поэтому новый инструмент появится здесь сам — без правок в server.py."""
    return [{"name": t["name"], "description": t["description"]} for t in AGENT_TOOLS]


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    """Главный эндпоинт: принимает задачу, запускает агента, возвращает ответ и шаги."""
    steps = []

    def collect(step, name, args, result):
        steps.append({"step": step, "tool": name, "args": args, "result": str(result)})

    try:
        answer = run_agent(req.task, on_step=collect)
    except Exception as e:
        # Наружу отдаём понятную ошибку, а не падаем с трейсбеком
        raise HTTPException(status_code=500, detail=f"Агент упал: {type(e).__name__}: {e}")

    return {"answer": answer, "steps": steps}


@app.get("/")
def index():
    """Отдаём фронтенд. Он лежит в static/index.html."""
    return FileResponse("static/index.html")