import eventlet
import numpy as np
from flask import Flask
from keras.models import load_model
import base64
from io import BytesIO
from PIL import Image
import cv2
import socketio

sio = socketio.Server()

app = Flask(__name__)
speed_limit = 100

def image_pre(img):
    img = img[60:135, :, :]
    img = cv2.cvtColor(img, cv2.COLOR_RGB2YUV)
    img = cv2.GaussianBlur(img, (3, 3), 0)
    img = cv2.resize(img, (200, 66))
    img = img / 255
    return img

@sio.on("connect")

def connect(sid, environ):
    print("Connected")
    send_control(0, 0)

def send_control(steering_angle, throttle):
    sio.emit("steer", data={
        "steering_angle": str(steering_angle),
        "throttle": str(throttle)
    })

@sio.on("telemetry")

def telemetry(sid, data):
    speed = float(data["speed"])
    image = Image.open(BytesIO(base64.b64decode(data["image"])))
    image = np.asarray(image)
    image = image_pre(image)
    image = np.array([image])
    steering_angle = float(model.predict(image))

    if speed > speed_limit:
        throttle = 0.0
    else:
        throttle = 1.0 - speed / speed_limit
        
    print("{} {} {}".format(steering_angle, throttle, speed))
    send_control(steering_angle, throttle)

if __name__ == "__main__":
    model = load_model("model/model.h5")
    app = socketio.Middleware(sio, app)
    eventlet.wsgi.server(eventlet.listen(("", 4567)), app)
