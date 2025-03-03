import pyglet

class JoystickHandler:
    def __init__(self):
        """Initialize Pyglet and detect the joystick."""
        self.joystick: pyglet.input | None = None
        self.connect_joystick()

        # Create a Pyglet window (required for event loop)
        self.window = pyglet.window.Window(visible=False)  # Invisible window

        # Schedule update loop
        pyglet.clock.schedule_interval(self.update, 0.1)  # Update every 100ms

        # Run Pyglet event loop
        pyglet.app.run()

    def connect_joystick(self):
        """Find and connect to the first available joystick."""
        devices = pyglet.input.get_joysticks()
        if not devices:
            print("No joystick detected!")
            return
        
        self.joystick = devices[0]
        self.joystick.open()
        print(f"Connected to: {self.joystick.device.name}")

        # Attach event handlers for joystick input
        self.joystick.on_joyaxis_motion = self.on_joyaxis_motion
        self.joystick.on_joybutton_press = self.on_joybutton_press
        self.joystick.on_joybutton_release = self.on_joybutton_release

    def on_joyaxis_motion(self, joystick, axis, value):
        """Handle joystick axis movement (X, Y, and Throttle)."""
        print(f"Axis {axis}: {value:.2f}")

    def on_joybutton_press(self, joystick, button):
        """Handle button press."""
        print(f"Button {button} pressed")

    def on_joybutton_release(self, joystick, button):
        """Handle button release."""
        print(f"Button {button} released")

    def update(self, dt):
        """Update loop (called every 100ms)."""
        if self.joystick:
            x_axis = self.joystick.x  # Left/Right
            y_axis = self.joystick.y  # Forward/Backward

            print(f"X: {x_axis:.2f}, Y: {y_axis:.2f}")

if __name__ == "__main__":
    JoystickHandler()