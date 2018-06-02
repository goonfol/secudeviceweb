#!/usr/bin/env python
from threading import Lock
from flask import Flask, render_template, session, request
from flask_socketio import SocketIO, emit
import time

import RPi.GPIO as GPIO
from gpiozero import LED, Buzzer, MotionSensor
import Adafruit_DHT

# local modules
import local_modules

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(True)

buzzer_pin = 21

motion_pin = 13
gas_smoke_pin = 3
flame_pin = 26
vibration_pin = 19
magnetic_pin = 2
temp_hum_pin = 16

siren_btn_pin = 4
attend_btn_pin = 17

led_pin = 6


GPIO.setup(buzzer_pin, GPIO.OUT)
GPIO.setup(motion_pin, GPIO.IN)
GPIO.setup(temp_hum_pin, GPIO.IN)
GPIO.setup(flame_pin, GPIO.IN)
GPIO.setup(gas_smoke_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(vibration_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(magnetic_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)


sensor = Adafruit_DHT.DHT22

async_mode = "threading"

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()



def flame_sensor_bgt():
    while True:
        f = GPIO.input(flame_pin)
        if f == 1:
            print ("detected")
            current_time = time.ctime()
            socketio.emit('flame_response', {'flame': f, 'time': current_time}, namespace='/test')
            time.sleep(10)
        else:
            socketio.sleep(0.1)
            socketio.emit('flame_response', {'flame': 0, 'time': current_time}, namespace='/test')


def temp_hum_sensor_bgt():
    while True:
        humidity, temperature = Adafruit_DHT.read_retry(sensor, temp_hum_pin)
        if humidity is not None and temperature is not None:
            current_time = time.ctime()
            socketio.emit('temp_hum_response', {'temp': round(temperature, 4), 'hum': round(humidity, 4), 'time': current_time}, namespace='/test')
            time.sleep(5)
        else:
            socketio.sleep(3)


def motion_sensor_bgt():
    while True:
        motion = GPIO.input(motion_pin)
        if motion:
            current_time = time.ctime()
            socketio.emit('motion_response', {'detected': motion}, namespace='/test')
            time.sleep(15)
        else:
            socketio.sleep(0.3)
            socketio.emit('motion_response', {'detected': 0}, namespace='/test')

def vibration_sensor_bgt():
    while True:
        vibration = GPIO.input(vibration_pin)
        if vibration:
            current_time = time.ctime()
            socketio.emit('vibration_response', {'detected': vibration}, namespace='/test')
            time.sleep(15)
        else:
            socketio.sleep(0.3)
            socketio.emit('vibration_response', {'detected': 0}, namespace='/test')



# routes
@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)



# socket calls
@socketio.on('my_ping', namespace='/test')
def ping_pong():
    emit('my_pong')



@socketio.on('connect', namespace='/test')
def flame_sensor_job():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(target=flame_sensor_bgt)
            thread = socketio.start_background_task(target=temp_hum_sensor_bgt)
            thread = socketio.start_background_task(target=motion_sensor_bgt)
            thread = socketio.start_background_task(target=vibration_sensor_bgt)
            
        emit('flame_response', {'flame': 0, 'time': 0})
        emit('temp_hum_response', {'temp': 0.0, 'hum': 0.0, 'time': 0}, namespace='/test')
        emit('motion_response', {'detected': 0}, namespace='/test')
        emit('vibration_response', {'detected': 0}, namespace='/test')



@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected', request.sid)




# run flask socket server
if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0')
