"""
Чат с агентом, который помнит контекст разговора.
    streamlit run chat_app.py
"""

import json
import os

import streamlit as st
from agent_loop import run_agent

st.set_page_config(page_title="Travel Money Chat", page_icon="💬")

# ---------- Пароль (как в app.py) ----------
APP_PASSWORD = os.environ.get("APP_PASSWORD")
if APP_PASSWORD and not st.session_state.get("authed"):
    st.title("💬 Travel Money Chat")
    pw = st.text_input("Пароль", type="password")
    if st.button("Войти"):
        if pw == APP_PASSWORD:
            st.session_state.authed = True
            st.rerun()
        else:
            st.error("Неверный пароль")
    st.stop()

# Сколько последних реплик отправлять модели. Каждая реплика = токены = деньги,
# поэтому длинную историю обрезаем.
MAX_HISTORY_MESSAGES = 12

TOOL_ICONS = {"get_exchange_rate": "💱", "get_weather": "🌦️", "calculate": "🧮", "days_until": "📅"}

# ---------- Состояние ----------
# chat — то, что показываем на экране (включая шаги агента)
if "chat" not in st.session_state:
    st.session_state.chat = []

st.title("💬 Travel Money Chat")
st.caption("Агент помнит разговор: можно уточнять — «а в Стамбуле?», «а если 500 фунтов?»")

with st.sidebar:
    st.header("Диалог")
    st.caption(f"Реплик в истории: {len(st.session_state.chat)}")
    if st.button("🧹 Новый диалог"):
        st.session_state.chat = []
        st.rerun()

# ---------- Показываем историю ----------
# Важно: Streamlit перезапускает скрипт при каждом сообщении,
# поэтому весь чат каждый раз рисуется заново из session_state.
for msg in st.session_state.chat:
    with st.chat_message(msg["role"]):
        if msg.get("steps"):
            with st.expander(f"🔧 Шаги агента: {len(msg['steps'])}"):
                for s in msg["steps"]:
                    st.write(s)
        st.markdown(msg["content"])

# ---------- Новое сообщение ----------
if prompt := st.chat_input("Спроси про курсы, погоду или посчитай что-нибудь…"):
    # 1. Показываем вопрос пользователя
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Готовим историю для модели: только текст реплик, без шагов и иконок
    history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.chat]
    history = history[-MAX_HISTORY_MESSAGES:]

    # 3. Запускаем агента и показываем шаги вживую
    with st.chat_message("assistant"):
        steps = []
        with st.status("Агент думает…", expanded=True) as status:

            def show_step(step, name, args, result):
                line = f"{TOOL_ICONS.get(name, '🔧')} **{step}** · `{name}({json.dumps(args, ensure_ascii=False)})` → `{result}`"
                steps.append(line)
                st.write(line)

            try:
                answer = run_agent(prompt, on_step=show_step, history=history)
                status.update(label=f"Готово · шагов: {len(steps)}", state="complete", expanded=False)
            except Exception as e:
                answer = f"⚠️ Ошибка: {e}"
                status.update(label="Ошибка", state="error")
        st.markdown(answer)

    # 4. Сохраняем обе реплики в историю
    st.session_state.chat.append({"role": "user", "content": prompt})
    st.session_state.chat.append({"role": "assistant", "content": answer, "steps": steps})