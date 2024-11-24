import aiohttp
from datetime import datetime
from dotenv import load_dotenv
import os
import pytz

load_dotenv()

BASE_URL = os.getenv("BASE_URL")
API_KEY = os.getenv("API_KEY")

KST = pytz.timezone("Asia/Seoul")


def dfs_xy_conv(lat, lon):
    RE = 6371.00877  # 지구 반경(km)
    GRID = 5.0  # 격자 간격(km)
    SLAT1 = 30.0  # 투영 위도1(degree)
    SLAT2 = 60.0  # 투영 위도2(degree)
    OLON = 126.0  # 기준점 경도(degree)
    OLAT = 38.0  # 기준점 위도(degree)
    XO = 43  # 기준점 X좌표(GRID)
    YO = 136  # 기준점 Y좌표(GRID)

    import math

    DEGRAD = math.pi / 180.0

    re = RE / GRID
    slat1 = SLAT1 * DEGRAD
    slat2 = SLAT2 * DEGRAD
    olon = OLON * DEGRAD
    olat = OLAT * DEGRAD

    sn = math.tan(math.pi * 0.25 + slat2 * 0.5) / math.tan(math.pi * 0.25 + slat1 * 0.5)
    sn = math.log(math.cos(slat1) / math.cos(slat2)) / math.log(sn)
    sf = math.tan(math.pi * 0.25 + slat1 * 0.5)
    sf = pow(sf, sn) * math.cos(slat1) / sn
    ro = math.tan(math.pi * 0.25 + olat * 0.5)
    ro = re * sf / pow(ro, sn)
    rs = {}
    ra = math.tan(math.pi * 0.25 + lat * DEGRAD * 0.5)
    ra = re * sf / pow(ra, sn)
    theta = lon * DEGRAD - olon
    if theta > math.pi:
        theta -= 2.0 * math.pi
    if theta < -math.pi:
        theta += 2.0 * math.pi
    theta *= sn
    rs["x"] = int(ra * math.sin(theta) + XO + 0.5)
    rs["y"] = int(ro - ra * math.cos(theta) + YO + 0.5)
    return rs


from datetime import datetime, timedelta


async def get_weather_and_forecast(GRID_X, GRID_Y, location_name):
    now = datetime.now(KST)
    base_date = now.strftime("%Y%m%d")
    base_time = now.strftime("%H%M")

    base_times = ["2300", "2000", "1700", "1400", "1100", "0800", "0500", "0200"]
    for bt in base_times:
        if int(bt) <= int(base_time):
            base_time = bt
            break
    else:
        base_time = "2300"
        base_date = (now - timedelta(days=1)).strftime("%Y%m%d")

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
                    return (
                        f"❌ 현재 {location_name}의 날씨 데이터를 가져올 수 없습니다."
                    )

                end_time = now + timedelta(hours=24)

                rain_times = []
                snow_times = []
                temperatures = []

                for item in items:
                    fcst_date = item["fcstDate"]
                    fcst_time = item["fcstTime"]
                    category = item["category"]
                    value = item["fcstValue"]

                    fcst_datetime = datetime.strptime(
                        fcst_date + fcst_time, "%Y%m%d%H%M"
                    )
                    fcst_datetime = KST.localize(fcst_datetime)

                    if now <= fcst_datetime <= end_time:
                        if category == "PTY":
                            if value == "1":
                                rain_times.append(fcst_datetime)
                            elif value == "3":
                                snow_times.append(fcst_datetime)

                        if category == "TMP":
                            temperature = float(value)
                            temperatures.append((fcst_datetime, temperature))

                temp_values = [temp for _, temp in temperatures]
                max_temp = max(temp_values) if temp_values else None
                min_temp = min(temp_values) if temp_values else None

                def format_time_ranges(datetimes):
                    if not datetimes:
                        return []
                    times = [dt.hour for dt in datetimes]
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

                start_time_str = now.strftime("%m/%d %H시")
                end_time_str = end_time.strftime("%m/%d %H시")

                if rain_periods and snow_periods:
                    result.append(
                        f"🌧️❄️ {location_name}의 {start_time_str}부터 {end_time_str}까지 24시간 이내 비와 눈이 예상됩니다. "
                    )
                    result.append(f"⏰ 비가 오는 시간대: {', '.join(rain_periods)}. ")
                    result.append(f"⏰ 눈이 오는 시간대: {', '.join(snow_periods)}. ")
                    result.append("☂️ 우산을 꼭 챙기세요! ")
                elif rain_periods:
                    result.append(
                        f"🌧️ {location_name}의 {start_time_str}부터 {end_time_str}까지 24시간 이내 비가 예상됩니다. "
                    )
                    result.append(f"⏰ 비가 오는 시간대: {', '.join(rain_periods)}. ")
                    result.append("☂️ 우산을 꼭 챙기세요! ")
                elif snow_periods:
                    result.append(
                        f"❄️ {location_name}의 {start_time_str}부터 {end_time_str}까지 24시간 이내 눈이 예상됩니다. "
                    )
                    result.append(f"⏰ 눈이 오는 시간대: {', '.join(snow_periods)}. ")
                    result.append("☂️ 우산을 꼭 챙기세요! ")
                else:
                    result.append(
                        f"☀️ {location_name}의 {start_time_str}부터 {end_time_str}까지 24시간 이내 비나 눈이 오지 않을 예정입니다. "
                    )
                    result.append("🌈 맑은 날씨를 즐기세요! ")

                if min_temp is not None and max_temp is not None:
                    max_temp_emoji = (
                        "🔥"
                        if max_temp >= 30
                        else "☀️" if max_temp >= 25 else "🌤️" if max_temp >= 10 else "❄️"
                    )
                    min_temp_emoji = (
                        "🔥"
                        if min_temp >= 30
                        else "☀️" if min_temp >= 25 else "🌤️" if min_temp >= 10 else "❄️"
                    )
                    result.append(
                        f"🌡️ 예상되는 최저 기온은 {min_temp_emoji} {min_temp:.1f}도, 최고 기온은 {max_temp_emoji} {max_temp:.1f}도예요. "
                    )
                else:
                    result.append("🌡️ 기온 데이터를 가져올 수 없습니다. ")

                return "".join(result)

    except Exception as e:
        return f"❌ {location_name}의 날씨 정보를 가져오는 중 오류가 발생했습니다: {e} "
