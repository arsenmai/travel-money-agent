from dotenv import load_dotenv
load_dotenv()

import json
import anthropic

client = anthropic.Anthropic()
MODEL = "claude-sonnet-5-5"


def get_text(response):
    return "".join(b.text for b in response.content if b.type == "text")


# ---------- Инструменты (те же, что в tools_demo.py) ----------

def get_exchange_rate(from_currency: str, to_currency: str) -> str:
    fake_rates = {("GBP", "KZT"): 680.0, ("USD", "KZT"): 515.0, ("GBP", "USD"): 1.32}
    f, t = from_currency.upper(), to_currency.upper()

    if f == t:
        return "1.0"

    # 1) Прямая пара
    rate = fake_rates.get((f, t))

    # 2) НОВОЕ: обратная пара — если знаем GBP->KZT, то KZT->GBP = 1 / курс
    if rate is None:
        reverse = fake_rates.get((t, f))
        if reverse is not None:
            rate = round(1 / reverse, 6)

    if rate is None:
        return f"Нет данных для {f}->{t}"
    return str(rate)


def calculate(expression: str) -> str:
    allowed = set("0123456789+-*/(). ")
    if not set(expression) <= allowed:
        return "ERROR: недопустимые символы"
    try:
        return str(eval(expression, {"__builtins__": {}}))
    except Exception as e:
        return f"ERROR: {e}"


# НОВОЕ (упражнение 2), часть 1: сама функция
def get_weather(city: str) -> str:
    fake_weather = {
        "london": {"temp_c": 6, "condition": "дождь"},
        "almaty": {"temp_c": -3, "condition": "снег"},
        "astana": {"temp_c": -12, "condition": "ясно"},
        "istanbul": {"temp_c": 14, "condition": "облачно"},
    }
    data = fake_weather.get(city.lower())
    if data is None:
        return f"Нет данных о погоде для {city}"
    return json.dumps(data, ensure_ascii=False)  # инструмент может вернуть JSON-строку


# ---------- Переключатель: фейковые или реальные данные ----------
# True  -> живые курсы (open.er-api.com) и погода (Open-Meteo) из real_tools.py
# False -> фейковые функции выше (работают без интернета — запасной план на демо)
USE_REAL_DATA = True

if USE_REAL_DATA:
    from real_tools import get_exchange_rate, get_weather  # перекрывают фейковые


# НОВОЕ, часть 3: добавили get_weather в словарь
TOOL_FUNCS = {
    "get_exchange_rate": get_exchange_rate,
    "calculate": calculate,
    "get_weather": get_weather,
}

tools = [
    {
        "name": "get_exchange_rate",
        "description": "Получить текущий курс обмена между двумя валютами.",
        "input_schema": {
            "type": "object",
            "properties": {
                "from_currency": {"type": "string", "description": "Код валюты, например GBP"},
                "to_currency": {"type": "string", "description": "Код валюты, например KZT"},
            },
            "required": ["from_currency", "to_currency"],
        },
    },
    {
        "name": "calculate",
        "description": "Посчитать арифметическое выражение, например '250 * 680'.",
        "input_schema": {
            "type": "object",
            "properties": {"expression": {"type": "string"}},
            "required": ["expression"],
        },
    },
    # НОВОЕ, часть 2: описание get_weather для модели
    {
        "name": "get_weather",
        "description": "Получить текущую погоду в любом городе мира: температура и ощущаемая температура в °C, описание, ветер, местное время.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "Название города на английском, например London"},
            },
            "required": ["city"],
        },
    },
]

SYSTEM = "Для любых вычислений всегда используй инструмент calculate, не считай в уме."


# ---------- ЦИКЛ АГЕНТА ----------

def run_agent(task: str, max_steps: int = 10, on_step=None) -> str:
    """on_step — необязательная функция, которую вызываем после каждого инструмента
    (её передаёт интерфейс, чтобы показывать шаги агента вживую)."""
    messages = [{"role": "user", "content": task}]

    for step in range(1, max_steps + 1):
        response = client.messages.create(
            model=MODEL, max_tokens=1000, system=SYSTEM, tools=tools, messages=messages
        )
        messages.append({"role": "assistant", "content": response.content})

        # Модель закончила — возвращаем текст
        if response.stop_reason != "tool_use":
            return get_text(response)

        # Модель просит инструменты — выполняем ВСЕ, что она попросила
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                func = TOOL_FUNCS.get(block.name)
                if func is None:
                    result = f"ERROR: нет инструмента {block.name}"
                else:
                    result = func(**block.input)
                print(f"[шаг {step}] {block.name}({json.dumps(block.input, ensure_ascii=False)}) -> {result}")
                if on_step is not None:
                    on_step(step, block.name, block.input, result)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

        messages.append({"role": "user", "content": tool_results})
        # ...и идём на следующий круг

    return "Достигнут лимит шагов — агент не успел закончить."


if __name__ == "__main__":
    answer = run_agent(
        "Я лечу из Лондона в Алматы и меняю 300 фунтов на тенге. "
        "Сколько получу и какая разница температур между городами?"
    )
    print("=" * 40)
    print(answer)