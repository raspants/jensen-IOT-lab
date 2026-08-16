from flask import Flask, jsonify, request, render_template
import os
import socket

from db import (
    device_exists,
    get_devices,
    get_measurements,
    get_latest_measurement,
    get_measurements_for_device,
    insert_measurement,
    total_amount_of_measurements,
    get_average_temp,
    get_measurements_last_24h,
)
from validation import validate_measurement
from cache import get_latest_from_cache, set_latest_in_cache

app = Flask(__name__)

APP_VERSION = os.getenv("APP_VERSION", "v1")
POD_NAME = socket.gethostname()


@app.get("/")
def dashboard():
    return render_template("index.html", version=APP_VERSION, pod=POD_NAME)


@app.get("/health")
def health():
    return jsonify({
        "status": "ok",
        "version": APP_VERSION,
        "pod": POD_NAME,
    }), 200


@app.get("/devices")
def devices():
    return jsonify(get_devices()), 200


@app.get("/measurements")
def measurements():
    return jsonify(get_measurements()), 200


@app.get("/devices/<device_id>/latest")
def latest(device_id):

    if not device_exists(device_id):
        return jsonify({"error": "unknown device"}), 404

    measurement = get_latest_measurement(device_id)

    if measurements is None:
        return jsonify({"error": "Measurement not found"}), 404

    return jsonify(measurement), 200


    # TODO M2:
    # Utöka M1-lösningen med cache-aside:
    # 1. Försök läsa från Redis.
    # 2. Vid cache miss: läs från PostgreSQL.
    # 3. Spara databasresultatet i Redis.
    return jsonify({
        "message": "TODO: implementera latest measurement",
        "deviceId": device_id
    }), 501


@app.get("/devices/<device_id>/measurements")
def device_history(device_id):
    if not device_exists(device_id):
        return jsonify({"error": "unknown device"}), 404
    
    measurements = get_measurements_for_device(device_id)
    
    return jsonify(measurements), 200


@app.post("/measurements")
def create_measurement():
    data = request.get_json(silent=True) or {}
    errors = validate_measurement(data)

    if errors:
        print(f"INVALID measurement from {data.get('deviceId', 'unknown')}: {errors}")
        return jsonify({"errors": errors}), 400

    known = device_exists(data.get("deviceId"))

    if not known:
        print(f"INVALID deviceid from {data.get('deviceId')}")
        return jsonify({"error": "Unknown device"}), 400

    insert_measurement(data)

    print(f"Valid measurements received: {data}")
    return jsonify({"status": "created", "measurement": data}), 201 #change status when saving
        
    #
    # TODO M2:
    # Uppdatera latest-cache för sensorn.
    #
    # Under starter-fasen returneras 202 så att simulatorn kan köras
    # även innan studenten implementerat persistensen.
    print(f"VALID measurement received: {data}")
    return jsonify({"status": "accepted", "measurement": data}), 202


@app.get("/count-readings")
def count_readings():
    return jsonify(total_amount_of_measurements()), 200


@app.get("/average-temp")
def average_temp():
    return jsonify(get_average_temp()), 200


@app.get("/last-24")
def last_24hours():
    return jsonify(get_measurements_last_24h()), 200


@app.get("/statistics")
def statistics():
    # ⭐ Utmaning:
    # Returnera antal devices, antal measurements, avg temp etc.
    return jsonify({"message": "Optional challenge"}), 501


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
