from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Hello from the root endpoint!"})


@app.route("/hello", methods=["GET"])
def hello():
    return jsonify({"message": "Hello!"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
