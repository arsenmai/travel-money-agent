from dotenv import load_dotenv
load_dotenv()

import json
import anthropic

client = anthropic.Anthropic()
MODEL = "claude-sonnet-5-5"


def get_text(response):
    """Собрать весь текст из ответа (пропуская thinking и tool_use блоки)."""
    return "".join(b.text for b in response.content if b.type == "text")


# ---------- 1. Функции-инструменты ----------

def get_exchange_rate(from_currency: str, to_currency: str) -> str:
    fake_rates = {("GBP", "KZT"): 680.0, ("USD", "KZT"): 515.0, ("GBP", "USD"): 1.32}
    rate = fake_rates.get((from_currency.upper(), to_currency.upper()))
    if rate is None:
        return f"Нет данных для {from_currency}->{to_currency}"
    return str(rate)


def calculate(expression: str) -> str:
    allowed = set("0123456789+-*/(). ")
    if not set(expression) <= allowed:
        return "ERROR: недопустимые символы"
    try:
        return str(eval(expression, {"__builtins__": {}}))
    except Exception as e:
        return f"ERROR: {e}"


# Словарь: имя инструмента -> Python-функция
TOOL_FUNCS = {
    "get_exchange_rate": get_exchange_rate,
    "calculate": calculate,
}


# ---------- 2. Описания инструментов для модели ----------

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
            "properties": {
                "expression": {"type": "string", "description": "Арифметическое выражение"},
            },
            "required": ["expression"],
        },
    },
]

# Просим модель всегда считать через инструмент, а не в уме
SYSTEM = "Для любых вычислений всегда используй инструмент calculate, не считай в уме."

messages = [{"role": "user", "content": "Сколько тенге я получу за 250 фунтов?"}]


# ---------- 3. Первый запрос ----------

response = client.messages.create(
    model=MODEL, max_tokens=1000, system=SYSTEM, tools=tools, messages=messages
)

print("stop_reason:", response.stop_reason)
for block in response.content:
    print("БЛОК:", block.type)
print("=" * 40)


# ---------- 4. Выполняем запрошенные инструменты (ОДИН круг) ----------

if response.stop_reason == "tool_use":
    messages.append({"role": "assistant", "content": response.content})

    tool_results = []
    for block in response.content:
        if block.type == "tool_use":
            print(f"Модель просит вызвать {block.name} с {json.dumps(block.input, ensure_ascii=False)}")
            result = TOOL_FUNCS[block.name](**block.input)
            print("Результат функции:", result)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": result,
            })

    messages.append({"role": "user", "content": tool_results})

    # ---------- 5. Второй запрос ----------
    final = client.messages.create(
        model=MODEL, max_tokens=1000, system=SYSTEM, tools=tools, messages=messages
    )
    print("=" * 40)
    print("stop_reason второго ответа:", final.stop_reason)

    if final.stop_reason == "tool_use":
        # Модели нужен ЕЩЁ один инструмент, но наш код делает только один круг
        for block in final.content:
            if block.type == "tool_use":
                print(f"Модель хочет ещё: {block.name}({json.dumps(block.input, ensure_ascii=False)})")
        print("...но мы его не выполняем — цикла нет. Чиним в уроке 3.")
    else:
        print(get_text(final))
else:
    print(get_text(response))