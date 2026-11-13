import anthropic

client = anthropic.Anthropic()  # сам берёт ключ из ANTHROPIC_API_KEY

messages = [{"role": "user", "content": "Объясни в двух предложениях, что такое хакатон."}]
r1 = client.messages.create(model="claude-sonnet-5-5", max_tokens=500, messages=messages)
print(r1.content[0].text, "\n---")

messages.append({"role": "assistant", "content": r1.content[0].text})
messages.append({"role": "user", "content": "А теперь объясни то же самое для пятилетнего."})
r2 = client.messages.create(model="claude-sonnet-5-5", max_tokens=500, messages=messages)
print(r2.content[0].text)
