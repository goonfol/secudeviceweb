import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(True)

GPIO.setup(9, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

while True:
    motion = GPIO.input(9)
    if motion:
        print("Detected")
    else:
        socketio.sleep(1)
