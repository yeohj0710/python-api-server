import aiohttp
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

BASE_URL = os.getenv("BASE_URL")
API_KEY = os.getenv("API_KEY")

GRID_X = 61
GRID_Y = 126


async def get_weather_and_forecast():
    now = datetime.now()

    if now.hour < 6:
        return "\n".join(
            [
                "⏰ 현재 시각은 오전 6시 이전입니다.",
                "🌅 오늘의 날씨 정보는 오전 6시 이후에 제공됩니다.",
            ]
        )

    base_date = now.strftime("%Y%m%d")
    base_time = "0500"

    params = {
        "serviceKey": API_KEY,
        "pageNo": 1,
        "numOfRows": 1000,
        "dataType": "JSON",
        "base_date": base_date,
        "base_time": base_time,
        "nx": GRID_X,
        "ny": GRID_Y,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(BASE_URL, params=params) as response:
                weather_data = await response.json()

                items = (
                    weather_data.get("response", {})
                    .get("body", {})
                    .get("items", {})
                    .get("item", [])
                )

                hourly_forecast = {}
                rain_times = []

                for item in items:
                    fcst_time = item["fcstTime"]
                    category = item["category"]
                    value = item["fcstValue"]

                    if fcst_time not in hourly_forecast:
                        hourly_forecast[fcst_time] = {}

                    if category == "PTY":
                        hourly_forecast[fcst_time]["rain"] = value
                        if value != "0":
                            rain_times.append(int(fcst_time[:2]))

                    if category == "TMP":
                        hourly_forecast[fcst_time]["temperature"] = value

                rain_intervals = []
                if rain_times:
                    start = rain_times[0]
                    for i in range(1, len(rain_times)):
                        if rain_times[i] != rain_times[i - 1] + 1:
                            rain_intervals.append((start, rain_times[i - 1]))
                            start = rain_times[i]
                    rain_intervals.append((start, rain_times[-1]))

                result = []

                if rain_intervals:
                    result.append("🌧️ 오늘은 비가 예상됩니다.")
                    rain_periods = ", ".join(
                        f"{start}~{end}시" for start, end in rain_intervals
                    )
                    result.append(f"⏰ 비가 오는 시간대: {rain_periods}")
                    result.append("☂️ 우산을 꼭 챙기세요!")
                else:
                    result.append("☀️ 오늘은 비가 오지 않을 예정입니다.")
                    result.append("🌈 맑은 날씨를 즐기세요!")

                result.append("\n📅 시간별 날씨 예보:")

                if hourly_forecast:
                    for time, data in sorted(hourly_forecast.items()):
                        temp = data.get("temperature", "N/A")
                        rain_status = data.get("rain", "0")
                        weather_map = {"0": "맑음", "1": "비", "2": "비/눈", "3": "눈"}
                        weather = weather_map.get(rain_status, "알 수 없음")
                        result.append(f"{time[:2]}시: 온도 {temp}°C, 날씨 {weather}")
                else:
                    result.append("시간별 예보 데이터를 가져올 수 없습니다.")

                return "\n".join(result)

    except Exception as e:
        return f"❌ 날씨 정보를 가져오는 중 오류가 발생했습니다: {e}"
