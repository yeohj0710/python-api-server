import aiohttp
from datetime import datetime
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

                if not items:
                    return "❌ 현재 날씨 데이터를 가져올 수 없습니다. 🌅 오늘 날씨는 오전 6시에 발표되며, 오전 7시에 알림이 발송됩니다. "

                hourly_forecast = {}
                rain_times = []
                snow_times = []
                temperatures = []

                for item in items:
                    fcst_time = item["fcstTime"]
                    category = item["category"]
                    value = item["fcstValue"]

                    if fcst_time not in hourly_forecast:
                        hourly_forecast[fcst_time] = {}

                    if category == "PTY":
                        hourly_forecast[fcst_time]["rain"] = value
                        if value == "1":
                            rain_times.append(int(fcst_time[:2]))
                        elif value == "3":
                            snow_times.append(int(fcst_time[:2]))

                    if category == "TMP":
                        temperature = float(value)
                        hourly_forecast[fcst_time]["temperature"] = temperature
                        temperatures.append(temperature)

                max_temp = max(temperatures) if temperatures else None
                min_temp = min(temperatures) if temperatures else None

                def format_time_ranges(times):
                    if not times:
                        return []

                    times = sorted(set(times))
                    intervals = []
                    start = times[0]

                    for i in range(1, len(times)):
                        if times[i] != times[i - 1] + 1:
                            intervals.append((start, times[i - 1]))
                            start = times[i]

                    intervals.append((start, times[-1]))
                    return [
                        (
                            f"{start:02}~{end + 1:02}시"
                            if start != end
                            else f"{start:02}~{start + 1:02}시"
                        )
                        for start, end in intervals
                    ]

                rain_periods = format_time_ranges(rain_times)
                snow_periods = format_time_ranges(snow_times)

                result = []

                if rain_periods and snow_periods:
                    result.append("🌧️❄️ 오늘은 비와 눈이 예상됩니다. ")
                    result.append(f"⏰ 비가 오는 시간대: {', '.join(rain_periods)}. ")
                    result.append(f"⏰ 눈이 오는 시간대: {', '.join(snow_periods)}. ")
                    result.append("☂️ 우산을 꼭 챙기세요! ")
                elif rain_periods:
                    result.append("🌧️ 오늘은 비가 예상됩니다. ")
                    result.append(f"⏰ 비가 오는 시간대: {', '.join(rain_periods)}. ")
                    result.append("☂️ 우산을 꼭 챙기세요! ")
                elif snow_periods:
                    result.append("❄️ 오늘은 눈이 예상됩니다. ")
                    result.append(f"⏰ 눈이 오는 시간대: {', '.join(snow_periods)}. ")
                    result.append("☂️ 우산을 꼭 챙기세요! ")
                else:
                    result.append("☀️ 오늘은 비나 눈이 오지 않을 예정입니다. ")
                    result.append("🌈 맑은 날씨를 즐기세요! ")

                if min_temp is not None and max_temp is not None:
                    max_temp_emoji = (
                        "🔥"
                        if max_temp >= 30
                        else "☀️" if max_temp >= 25 else "🌤️" if max_temp >= 15 else "❄️"
                    )
                    result.append(
                        f"🌡️ 오늘의 ❄️ 최저 기온은 {min_temp:.1f}도, {max_temp_emoji} 최고 기온은 {max_temp:.1f}도예요. "
                    )
                else:
                    result.append("🌡️ 기온 데이터를 가져올 수 없습니다. ")

                return "".join(result)

    except Exception as e:
        return f"❌ 날씨 정보를 가져오는 중 오류가 발생했습니다: {e} "
