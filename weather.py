import aiohttp
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import pytz

load_dotenv()

BASE_URL = os.getenv("BASE_URL")
API_KEY = os.getenv("API_KEY")

GRID_X = 61
GRID_Y = 126

KST = pytz.timezone("Asia/Seoul")


async def get_weather_and_forecast():
    now = datetime.now(KST)

    if now.hour < 6:
        return "\n".join(
            [
                "⏰ 현재는 오늘 날씨 데이터가 발표되지 않았습니다.",
                "🌅 오늘의 첫 발표는 오전 6시에 이루어지며, 오전 7시에 알림이 발송됩니다.",
            ]
        )

    if now.hour >= 6:
        base_date = now.strftime("%Y%m%d")
        base_time = "0500"
    else:
        base_date = now.strftime("%Y%m%d")
        base_time = "2300"

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

                if not items:
                    return "\n".join(
                        [
                            "❌ 현재 날씨 데이터를 가져올 수 없습니다.",
                            "🌅 오늘 날씨는 오전 6시에 발표되며, 오전 7시에 알림이 발송됩니다.",
                        ]
                    )

                hourly_forecast = {}
                rain_times = []
                temperatures = []

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
                        temperature = float(value)
                        hourly_forecast[fcst_time]["temperature"] = temperature
                        temperatures.append(temperature)

                max_temp = max(temperatures) if temperatures else "N/A"
                min_temp = min(temperatures) if temperatures else "N/A"

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
                    rain_periods = ", ".join(
                        f"{start}~{end}시" if start != end else f"{start}시"
                        for start, end in rain_intervals
                    )
                    result.append(f"🌧️ 오늘은 비가 예상됩니다.")
                    result.append(f"⏰ 비가 오는 시간대: {rain_periods}.")
                    result.append("☂️ 우산을 꼭 챙기세요!")
                else:
                    result.append("☀️ 오늘은 비가 오지 않을 예정입니다.")
                    result.append("🌈 맑은 날씨를 즐기세요!")

                result.append(
                    f"🌡️ 오늘의 ❄️ 최저 기온은 {min_temp}도, 최고 기온은 {max_temp}도예요."
                )

                return "\n".join(result)

    except Exception as e:
        return f"❌ 날씨 정보를 가져오는 중 오류가 발생했습니다: {e}"
