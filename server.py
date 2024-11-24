from flask import Flask, Response, jsonify, make_response
import asyncio
from weather import get_weather_and_forecast

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


@app.route("/weather", methods=["GET"])
async def weather():
    try:
        result = await get_weather_and_forecast()
        return Response(result, mimetype="text/plain; charset=utf-8")
    except Exception as e:
        return Response(
            f"Error fetching weather data: {str(e)}",
            status=500,
            mimetype="text/plain; charset=utf-8",
        )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
