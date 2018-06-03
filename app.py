#!/usr/bin/env python
from threading import Lock
from flask import Flask, render_template, session, request
from flask_socketio import SocketIO, emit
import time
import serial
import sys

import RPi.GPIO as GPIO
from gpiozero import LED, Buzzer, MotionSensor
import Adafruit_DHT

# local modules
import local_modules
# from sim_module import gsm


class gsm():
    echo_on = 1

    def __init__(self, serialPort):
        self.serialPort = serialPort

    def sendCommand(self, at_command):
        self.serialPort.write(at_command + '\r')

    def getResponse(self):
        self.serialPort.flushInput()
        self.serialPort.flushOutput()
        if gsm.echo_on == 1:
            response = self.serialPort.readline()  # comment this line if echo off
        response = self.serialPort.readline()
        response = response.rstrip()
        return response

    def getPrompt(self):
        if gsm.echo_on == 1:
            response = self.serialPort.readline()  # comment this line if echo off
        if (self.serialPort.readline(1) == '>'):
            return True
        else:
            return False

    def sendMessage(self, phone_number, message):
        flag = False
        self.sendCommand('AT+CMGS=\"' + phone_number + '\"')
        time.sleep(2)
        # print ('SUCCESS')
        self.serialPort.write(message)
        self.serialPort.write('\x1A')  # send messsage if prompt received
        flag = True

        time.sleep(5)
        return flag

    def readMessage(self):
        flag = False
        message = ''
        self.sendCommand('AT+CMGR=1')
        self.serialPort.flushInput()
        self.serialPort.flushOutput()
        self.serialPort.readline().rstrip()
        while True:
            response = self.serialPort.readline().rstrip()
            if len(response) > 1:
                if response == 'OK':
                    break
                else:
                    message = message + " " + response
                    flag = True

        return flag, message


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
GPIO.setup(siren_btn_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
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



def send_message_on_alarm(phn_number, mgs_text):
    gsm_ser = serial.Serial()
    gsm_ser.port = "/dev/ttyAMA0"
    gsm_ser.baudrate = 9600
    gsm_ser.timeout = 1

    try:
        gsm_ser.open()
        gsm_ser.flushInput()
        gsm_ser.flushOutput()
    except:
        print ('Cannot open serial port')
        sys.exit()

    GSM = gsm(gsm_ser)

    GSM.sendCommand("AT")
    print (GSM.getResponse())

    time.sleep(.1)

    GSM.sendCommand("AT+CMGF=1;&W")
    print (GSM.getResponse())

    time.sleep(.1)

    GSM.sendCommand("AT+CREG?")
    print (GSM.getResponse())

    time.sleep(.1)

    status, msg = GSM.readMessage()
    if status == 0:
        print ('No new messages')
    else:
        print ('New messages arrived: ' + msg)
    
    if (GSM.sendMessage(phn_number, mgs_text)):
        print ('Message sending Success')
    else:
        print ('Message sending Failed')

    time.sleep(.1)
    gsm_ser.close()


def flame_sensor_bgt():
    while True:
        f = GPIO.input(flame_pin)
        # g = GPIO.input(gas_smoke_pin)
        current_time = time.ctime()
        if f == 1:
            socketio.emit('flame_response', {'flame': f, 'time': current_time}, namespace='/test')
            send_message_on_alarm("01821081270", "Fire Alarm Text @ {}".format(current_time))
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


def magnetic_sensor_bgt():
    while True:
        magnetic = GPIO.input(magnetic_pin)
        socketio.emit('magnetic_response', {'state': magnetic}, namespace='/test')
        socketio.sleep(0.1)


def siren_sensor_bgt():
    while True:
        siren = GPIO.input(siren_btn_pin)
        socketio.sleep(0.1)
        socketio.emit('siren_response', {'state': siren}, namespace='/test')



# routes
@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)

@app.route('/about')
def about():
    return render_template('about.html')



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
            thread = socketio.start_background_task(target=magnetic_sensor_bgt)
            thread = socketio.start_background_task(target=siren_sensor_bgt)

            thread = socketio.start_background_task(target=buzzer_bgt)
            thread = socketio.start_background_task(target=led_bgt)
            
        emit('flame_response', {'flame': 0, 'time': 0})
        emit('temp_hum_response', {'temp': 0.0, 'hum': 0.0, 'time': 0}, namespace='/test')
        emit('motion_response', {'detected': 0}, namespace='/test')
        emit('vibration_response', {'detected': 0}, namespace='/test')
        emit('magnetic_response', {'state': 0}, namespace='/test')
        emit('siren_response', {'state': 1}, namespace='/test')



@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected', request.sid)




# run flask socket server
if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0')
