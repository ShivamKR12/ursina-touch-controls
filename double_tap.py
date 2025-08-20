from ursina import *
import time

last_click_time = 0
double_tap_threshold = 0.3  # seconds


def input(key):
    global last_click_time

    if key == 'left mouse down':
        now = time.time()
        if now - last_click_time <= double_tap_threshold:
            print("Double Tap at:", mouse.position)
        last_click_time = now


if __name__ == "__main__":
    app = Ursina()
    app.run()
