from ursina import *
import time

press_start_time = None
long_press_threshold = 0.5   # seconds
holding = False


def update():
    global press_start_time, holding

    # if button is pressed and not already tracking
    if mouse.left and press_start_time is None:
        press_start_time = time.time()
        holding = False

    # if button is being held
    if mouse.left and press_start_time is not None:
        if not holding and (time.time() - press_start_time) >= long_press_threshold:
            print("Long Press Detected at:", mouse.position)
            holding = True
        elif holding:
            print("Holding at:", mouse.position)

    # if button is released -> reset
    if not mouse.left and press_start_time is not None:
        press_start_time = None
        holding = False


if __name__ == "__main__":
    app = Ursina()
    app.run()
