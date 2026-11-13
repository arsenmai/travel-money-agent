"""
Реальные инструменты: живые данные из бесплатных API без ключа.

    pip install requests

- Курсы валют: ExchangeRate-API, открытый эндпоинт open.er-api.com
  (без ключа, обновляется раз в сутки, просит ссылку-атрибуцию на exchangerate-api.com).
- Погода: Open-Meteo (без ключа, для некоммерческого использования).
"""

import json
import time

import requests

TIMEOUT = 10  # секунд; без таймаута зависший API подвесит весь агент


# ---------- Курсы валют ----------

# Простой кэш: курсы обновляются раз в сутки, поэтому нет смысла
# дёргать API на каждый вопрос (и открытый эндпоинт ограничивает частые запросы).
_rates_cache = {}  # base -> (время_загрузки, словарь_курсов)
CACHE_SECONDS = 60 * 60


def _load_rates(base: str) -> dict:
    cached = _rates_cache.get(base)
    if cached and time.time() - cached[0] < CACHE_SECONDS:
        return cached[1]

    r = requests.get(f"https://open.er-api.com/v6/latest/{base}", timeout=TIMEOUT)
    r.raise_for_status()
    data = r.json()
    if data.get("result") != "success":
        raise ValueError(f"API вернул ошибку: {data.get('error-type', data)}")

    _rates_cache[base] = (time.time(), data["rates"])
    return data["rates"]


def get_exchange_rate(from_currency: str, to_currency: str) -> str:
    f, t = from_currency.upper(), to_currency.upper()
    try:
        rates = _load_rates(f)
    except Exception as e:
        # Ошибку возвращаем ТЕКСТОМ: модель её прочитает и сможет объяснить пользователю
        return f"ERROR: не удалось получить курс {f}->{t}: {e}"

    if t not in rates:
        return f"Нет данных для {f}->{t}"
    return str(rates[t])


# ---------- Погода ----------

# Open-Meteo отдаёт погоду числовым кодом WMO — переводим в слова
WEATHER_CODES = {
    0: "ясно", 1: "преимущественно ясно", 2: "переменная облачность", 3: "пасмурно",
    45: "туман", 48: "изморозь",
    51: "морось", 53: "морось", 55: "сильная морось",
    61: "небольшой дождь", 63: "дождь", 65: "сильный дождь",
    66: "ледяной дождь", 67: "ледяной дождь",
    71: "небольшой снег", 73: "снег", 75: "сильный снег", 77: "снежная крупа",
    80: "ливень", 81: "ливень", 82: "сильный ливень",
    85: "снегопад", 86: "сильный снегопад",
    95: "гроза", 96: "гроза с градом", 99: "гроза с градом",
}


def get_weather(city: str) -> str:
    try:
        # Шаг 1: город -> координаты (геокодинг)
        geo = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1, "language": "en"},
            timeout=TIMEOUT,
        ).json()
        if not geo.get("results"):
            return f"Город '{city}' не найден"
        place = geo["results"][0]

        # Шаг 2: координаты -> текущая погода
        weather = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "current": "temperature_2m,apparent_temperature,weather_code,wind_speed_10m",
                "timezone": "auto",
            },
            timeout=TIMEOUT,
        ).json()
        cur = weather["current"]
    except Exception as e:
        return f"ERROR: не удалось получить погоду для {city}: {e}"

    return json.dumps({
        "city": place["name"],
        "country": place.get("country"),
        "temp_c": cur["temperature_2m"],
        "feels_like_c": cur["apparent_temperature"],
        "condition": WEATHER_CODES.get(cur["weather_code"], f"код {cur['weather_code']}"),
        "wind_kmh": cur["wind_speed_10m"],
        "local_time": cur["time"],
    }, ensure_ascii=False)


if __name__ == "__main__":
    # Быстрая проверка без модели: python real_tools.py
    print(get_exchange_rate("GBP", "KZT"))
    print(get_exchange_rate("KZT", "GBP"))
    print(get_weather("London"))
    print(get_weather("Almaty"))