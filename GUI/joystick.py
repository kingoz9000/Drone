import pyglet


class JoystickHandler:
    def __init__(self):
        """Initialize Pyglet and detect the joystick."""
        self.joystick = None
        self.connect_joystick()

        self.running = False

        if __name__ == "__main__":
            pyglet.clock.schedule_interval(self.get_values, 0.05)  # Update every 50ms
            self.start_reading()

    def start_reading(self):
        # Run Pyglet event loop
        self.running = True
        pyglet.app.run()

    def connect_joystick(self) -> None:
        """Find and connect to the first available joystick."""
        devices = pyglet.input.get_joysticks()
        if not devices:
            print("No joystick detected!")
            return

        self.joystick = devices[0]
        self.joystick.open()
        print(f"Connected to: {self.joystick.device.name}")

        # Attach event handlers for joystick input
        self.joystick.on_joybutton_press = self.on_joybutton_press
        self.joystick.on_joybutton_release = self.on_joybutton_release

        # Define button dictionary
        self.buttons: dict = {}

    def on_joybutton_press(self, joystick, button) -> None:
        """Handle button press."""
        self.buttons[button + 1] = True

    def on_joybutton_release(self, joystick, button) -> None:
        """Handle button release."""
        self.buttons[button + 1] = False

    def get_values(self, dt=0) -> tuple:
        """Update loop (called every 100ms)."""
        if dt != 0:
            print(self.joystick.x, self.joystick.y, self.joystick.z, self.buttons)

        return (self.joystick.x, self.joystick.y, self.joystick.z, self.buttons)


if __name__ == "__main__":
    JoystickHandler()

