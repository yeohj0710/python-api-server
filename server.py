from flask import Flask, Response, jsonify
import asyncio
from weather import get_weather_and_forecast

app = Flask(__name__)


@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Hello from the root endpoint!"})


@app.route("/hello", methods=["GET"])
def hello():
    return jsonify({"message": "Hello!"})


@app.route("/weather", methods=["GET"])
async def weather():
    try:
        # weather.py의 비동기 함수 호출
        result = await get_weather_and_forecast()
        return Response(result, mimetype="text/plain")
    except Exception as e:
        return Response(
            f"Error fetching weather data: {str(e)}", status=500, mimetype="text/plain"
        )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
