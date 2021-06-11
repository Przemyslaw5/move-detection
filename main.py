from flask import Flask, render_template, Response, request
import os
from camera import Camera
from move_detector import MoveDetector
from framer import Framer
import threading
import cv2
import json
from flask import jsonify
import subprocess

app = Flask(__name__)

def restart_config():
    with open('config.json') as json_file:
        data = json.load(json_file)
    MoveDetector.set_width(MoveDetector, int(data['width']))
    MoveDetector.set_height(MoveDetector, int(data['height']))
    MoveDetector.set_email_sending(MoveDetector, bool(data['email_sending']))
    MoveDetector.set_recording_time(MoveDetector, int(data['recording_time']))
    MoveDetector.set_min_area(MoveDetector, int(data['min_area']))
    Camera()
    MoveDetector()
    
restart_config()

def generate_frames(framer: Framer):
    while True:
        frame = framer.get_frame()
        _, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/videos')
def videos():
    videos = []
    for file in os.listdir("./static/videos"):
        if file.endswith(".mp4"):
            videos.append(file)
    return render_template('videos/index.html', videos=videos)

@app.route('/')
@app.route('/live')
def live():
    with open('config.json') as json_file:
        data = json.load(json_file)
    return render_template('live/index.html', width=data["width"], height=data["height"])

@app.route('/detection')
def detection():
    with open('config.json') as json_file:
        data = json.load(json_file)
    return render_template('detection/index.html', width=data["width"], height=data["height"])

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(Camera()), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/move_detection')
def move_detection():
    return Response(generate_frames(MoveDetector()), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/config')
def config():
    return render_template('config/index.html')

@app.route('/jsondata', methods=['GET', 'POST'])
def jsondata():
    if request.method == 'POST':
        data = request.get_json()
        with open("config.json", "r+") as jsonFile:
            config = json.load(jsonFile)
            for key in data:
                config[key] = data[key]
            jsonFile.seek(0)
            json.dump(data, jsonFile)
            jsonFile.truncate()
            restart_config()
            return ""
    else:
        with open('config.json') as json_file:
            data = json.load(json_file)
        return jsonify(data)
    
@app.route('/send/<filename>')
def send(filename):
    subprocess.Popen(['python3', 'send_email.py', '-f', 'static/videos/' + filename])
    return ""
        