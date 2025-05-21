# ursina-touch-controls

A drop‑in touch joystick and button input module for the Ursina game engine.

## Overview

This package provides on-screen joysticks and buttons for games developed with the Ursina engine, making it easy to support touch controls on mobile and desktop platforms. It features:
- Virtual joysticks for movement and camera/aiming.
- Virtual buttons for customizable actions (jump, shoot, etc).
- Unified input handling so your code works seamlessly with both keyboard/mouse and touch.
- Easy integration and flexible customization.

## Features

- **VirtualJoystick**: On-screen draggable joystick for analog input (movement or camera).
- **VirtualButton**: On-screen button mapped to any logical game action.
- **InputManager & InputHandler**: Helper classes to manage multiple entities, callbacks, and unified input across platforms.
- **Custom sensitivity and dead-zone settings**.
- **Callback support for button presses and releases**.
- **Fully compatible with Ursina’s Entity system**.

## Installation

Download or copy the contents of this repository into your Ursina project folder. Make sure all files (e.g., `input_manager.py`, `touch_control.py`) are accessible from your main game script.

> **Requires:** [Ursina Engine](https://www.ursinaengine.org/) installed.

```bash
pip install ursina
```

## Usage

### Example using `InputManager` (recommended for most projects)

```python
from ursina import *
from input_manager import InputManager

app = Ursina()

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

# Register button press callbacks
input_manager_instance.register_button_press_callback('gamepad a', on_button_a_press)
input_manager_instance.register_button_press_callback('gamepad b', on_button_b_press)

def update():
    input_manager_instance.update()
    debug_text.text = (
        f"LStick: {input_manager_instance.joystick_left.value if input_manager_instance.joystick_left else 'N/A'}\n"
        f"RStick: {input_manager_instance.joystick_right.value if input_manager_instance.joystick_right else 'N/A'}\n"
        f"Pos: {player.position}, Rot: {player.rotation}"
    )

Sky()
app.run()
```

### Example using `InputHandler` from `touch_control.py` (alternative API)
```python
from ursina import *
from touch_control import InputHandler

app = Ursina()
handler = InputHandler(use_touch=True)
player = Entity(model='cube', color=color.orange, scale=1.2)

def update():
    handler.update()
    # Use handler.get_movement_vector() and handler.get_look_vector() for control

app.run()
```

## Customization

- Adjust joystick position, sensitivity, and dead zone via constructor arguments.
- Add or remove virtual buttons as needed.
- Bind custom actions to button presses or releases.

## License

[MIT](LICENSE) (if you want to specify one—otherwise, please add a LICENSE file!)

## Credits

Created by [ShivamKR12](https://github.com/ShivamKR12).  
Inspired by the Ursina community.
