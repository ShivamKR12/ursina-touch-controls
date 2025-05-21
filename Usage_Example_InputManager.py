from ursina import *
from input_manager import InputManager

app = Ursina()

# Example entity to control
player = Entity(model='cube', color=color.orange, scale=1.2)
Text.default_resolution = 1080 * Text.size
debug_text = Text(x=-.5, y=.4, origin=(0,0), color=color.black)

# Create InputManager and bind to player entity, enable onscreen controls
input_manager_instance = InputManager(entities=[player], enable_onscreen_controls=True, sensitivity=1.0, dead_zone=0.05)

# Define button press callbacks
def on_button_a_press(key):
    if key == 'gamepad a':
        player.animate_y(player.y + .5, duration=.2, curve=curve.out_bounce)

def on_button_b_press(key):
    if key == 'gamepad b':
        player.position += player.forward.normalized() * 1

def on_button_x_press(key):
    if key == 'gamepad x':
        player.color = color.random_color()

def on_button_y_press(key):
    if key == 'gamepad y':
        factor = 2 if player.scale_x < 1.5 else 0.5
        player.animate_scale(player.scale * factor, duration=.2)

# Register button press callbacks
input_manager_instance.register_button_press_callback('gamepad a', on_button_a_press)
input_manager_instance.register_button_press_callback('gamepad b', on_button_b_press)
input_manager_instance.register_button_press_callback('gamepad x', on_button_x_press)
input_manager_instance.register_button_press_callback('gamepad y', on_button_y_press)

def update():
    input_manager_instance.update()
    debug_text.text = (
        f"LStick: {input_manager_instance.joystick_left.value if input_manager_instance.joystick_left else 'N/A'}\n"
        f"RStick: {input_manager_instance.joystick_right.value if input_manager_instance.joystick_right else 'N/A'}\n"
        f"Pos: {player.position}, Rot: {player.rotation}"
    )

Sky()
app.run()
