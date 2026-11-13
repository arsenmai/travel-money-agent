"""
Веб-интерфейс к агенту.
    pip install streamlit
    streamlit run app.py
"""

import json
import time
import streamlit as st
from agent_loop import run_agent

st.set_page_config(page_title="Travel Money Agent", page_icon="✈️")

# ---------- НОВОЕ: простой пароль на вход ----------
# Публичный сайт = каждый посетитель тратит твой баланс Claude.
# Пароль берём из переменной окружения APP_PASSWORD:
#   - на Streamlit Cloud — из раздела Secrets (корневые секреты становятся переменными окружения)
#   - локально — можно добавить строку APP_PASSWORD=... в .env, или не добавлять, и пароля не будет
import os

APP_PASSWORD = os.environ.get("APP_PASSWORD")

if APP_PASSWORD and not st.session_state.get("authed"):
    st.title("✈️ Travel Money Agent")
    pw = st.text_input("Пароль", type="password")
    if st.button("Войти"):
        if pw == APP_PASSWORD:
            st.session_state.authed = True
            st.rerun()
        else:
            st.error("Неверный пароль")
    st.stop()  # дальше страница не рисуется, пока не введён пароль

# Плюшка 1: история запросов, которая живёт между перезапусками скрипта
if "history" not in st.session_state:
    st.session_state.history = []

TOOL_ICONS = {"get_exchange_rate": "💱", "get_weather": "🌦️", "calculate": "🧮"}

st.title("✈️ Travel Money Agent")
st.caption("Курсы валют, погода и расчёты — агент сам решает, какие инструменты вызвать.")
st.caption("Данные: [Rates By Exchange Rate API](https://www.exchangerate-api.com) · [Weather by Open-Meteo](https://open-meteo.com)")

# Примеры задач кнопками — удобно на демо
examples = [
    "Сколько тенге я получу за 250 фунтов?",
    "Я лечу из Лондона в Алматы и меняю 300 фунтов. Сколько получу и какая разница температур?",
    "Где сейчас теплее: в Токио или в Нью-Йорке? И сколько иен стоят 50 долларов?",
]
cols = st.columns(len(examples))
for col, ex in zip(cols, examples):
    if col.button(ex[:28] + "…", use_container_width=True):
        st.session_state.task = ex

task = st.text_area("Задача для агента", key="task", height=100)

if st.button("Запустить агента", type="primary") and task.strip():
    steps = []  # сюда собираем все вызовы инструментов
    start = time.time()

    with st.status("Агент работает…", expanded=True) as status:

        def show_step(step, name, args, result):
            steps.append(name)
            icon = TOOL_ICONS.get(name, "🔧")
            st.write(f"{icon} **Шаг {step}** · `{name}({json.dumps(args, ensure_ascii=False)})` → `{result}`")

        answer = run_agent(task, on_step=show_step)
        status.update(label="Готово — нажми, чтобы увидеть шаги агента", state="complete", expanded=False)

    elapsed = time.time() - start

    # Плюшка 2: метрики работы агента — хорошо смотрятся на демо
    m1, m2, m3 = st.columns(3)
    m1.metric("Вызовов инструментов", len(steps))
    m2.metric("Разных инструментов", len(set(steps)))
    m3.metric("Время", f"{elapsed:.1f} с")

    st.markdown("### Ответ")
    st.markdown(answer)

    st.session_state.history.insert(0, {"task": task, "answer": answer, "tools": len(steps)})

# История в боковой панели
with st.sidebar:
    st.header("🕘 История")
    if not st.session_state.history:
        st.caption("Пока пусто — запусти агента.")
    for item in st.session_state.history:
        with st.expander(item["task"][:40] + ("…" if len(item["task"]) > 40 else "")):
            st.caption(f"Инструментов вызвано: {item['tools']}")
            st.markdown(item["answer"])
    if st.session_state.history and st.button("Очистить историю"):
        st.session_state.history = []
        st.rerun()