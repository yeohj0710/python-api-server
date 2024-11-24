from flask import Flask, Response, jsonify, make_response, request
from weather import get_weather_and_forecast, dfs_xy_conv
import aiohttp

app = Flask(__name__)


@app.route("/", methods=["GET"])
def home():
    return Response(
        '{"message": "Root endpoint에서 인사드려요! 반가워요!"}',
        mimetype="application/json; charset=utf-8",
    )


@app.route("/hello", methods=["GET"])
def hello():
    return Response(
        '{"message": "안녕하세요! \'Hello\' endpoint가 정상적으로 작동하고 있어요."}',
        mimetype="application/json; charset=utf-8",
    )


async def reverse_geocode(latitude, longitude):
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {
        "lat": latitude,
        "lon": longitude,
        "format": "json",
        "accept-language": "ko",
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            data = await response.json()
            address = data.get("address", {})

            state = address.get("state", "")
            city = address.get("city", "")
            county = address.get("county", "")
            town = address.get("town", "")
            village = address.get("village", "")

            location_parts = [state, city or county or town or village]
            location = " ".join(filter(None, location_parts))
            return location


@app.route("/weather", methods=["GET"])
async def weather():
    try:
        latitude = request.args.get("latitude", default=None, type=float)
        longitude = request.args.get("longitude", default=None, type=float)
        if latitude is None or longitude is None:
            # 기본값: 서울특별시 좌표
            latitude = 37.5665
            longitude = 126.9780
        grid = dfs_xy_conv(latitude, longitude)
        address = await reverse_geocode(latitude, longitude)
        result = await get_weather_and_forecast(grid["x"], grid["y"], address)
        return Response(result, mimetype="text/plain; charset=utf-8")
    except Exception as e:
        return Response(
            f"Error fetching weather data: {str(e)}",
            status=500,
            mimetype="text/plain; charset=utf-8",
        )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
