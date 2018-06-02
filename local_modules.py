import RPi.GPIO as GPIO
import time
import Adafruit_DHT
import sys
from gpiozero import LED, Buzzer, MotionSensor

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

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


def get_temp_hum(temp_hum_pin=temp_hum_pin):
    sensor = Adafruit_DHT.DHT22
    humidity, temperature = Adafruit_DHT.read_retry(sensor, temp_hum_pin)
    if humidity is not None and temperature is not None:
        return (temperature, humidity)
    else:
        return (0,0)


def set_alarm(timeout=5, n=5):
    bz = Buzzer(buzzer_pin)
    # bz.on()
    # time.sleep(timeout)
    # bz.off()
    bz.beep(on_time=0.5, off_time=0.5, n=n, background=False)
    bz.off()


def set_led_blink(led_pin=led_pin, n=5):
    led = LED(led_pin)
    led.blink(on_time=0.5, off_time=0.5, n=n, background=False)
    led.off()


# get_temp_hum()