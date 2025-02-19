from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
import cv2
import numpy as np
import os

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

UPLOAD_FOLDER = "static/uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Threshold warna limbah
LOWER_HSV = np.array([10, 50, 50])  # Warna air normal
UPPER_HSV = np.array([35, 255, 255])  # Warna limbah

# Halaman dashboard
@app.route("/")
def index():
    return render_template("index.html")

# Endpoint untuk menerima gambar dari ESP32-CAM
@app.route("/upload", methods=["POST"])
def upload_file():
    file = request.files["file"]
    filepath = os.path.join(UPLOAD_FOLDER, "latest.jpg")
    file.save(filepath)

    # Analisis warna
    hasil = analyze_image(filepath)

    # Kirim update ke dashboard
    socketio.emit("update_status", hasil)
    
    return jsonify(hasil)

# Analisis warna air
def analyze_image(image_path):
    image = cv2.imread(image_path)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    mask = cv2.inRange(hsv, LOWER_HSV, UPPER_HSV)
    percentage = (cv2.countNonZero(mask) / (image.shape[0] * image.shape[1])) * 100

    status = "Aman" if percentage < 20 else "Pencemaran Terdeteksi"

    return {"status": status, "warna_tidak_normal": percentage}

# Endpoint untuk menerima data sensor gas dari ESP32
@app.route("/sensor", methods=["POST"])
def sensor_data():
    data = request.json
    socketio.emit("sensor_update", data)  # Kirim data ke dashboard
    return jsonify({"message": "Data diterima"}), 200

# Jalankan Flask
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
