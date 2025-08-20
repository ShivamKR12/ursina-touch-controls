from ursina import *

swipe_start = None
swipe_threshold = 0.05  # normalized units (since mouse.position is -1..1)


def input(key):
    global swipe_start

    if key == 'left mouse down':
        swipe_start = mouse.position

    if key == 'left mouse up' and swipe_start is not None:
        swipe_end = mouse.position
        delta = swipe_end - swipe_start

        if abs(delta.x) > abs(delta.y):
            if delta.x > swipe_threshold:
                print("Swipe Right")
            elif delta.x < -swipe_threshold:
                print("Swipe Left")
        else:
            if delta.y > swipe_threshold:
                print("Swipe Up")
            elif delta.y < -swipe_threshold:
                print("Swipe Down")

        swipe_start = None


if __name__ == "__main__":
    app = Ursina()
    app.run()
