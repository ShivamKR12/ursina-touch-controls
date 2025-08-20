from ursina import *

def input(key):
    if key == 'scroll up':
        print("Pinch Out (Zoom In)")
    elif key == 'scroll down':
        print("Pinch In (Zoom Out)")

if __name__ == "__main__":
    app = Ursina()
    app.run()
