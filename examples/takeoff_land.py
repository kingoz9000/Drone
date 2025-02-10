from djitellopy import Tello
import time

def main():
    # Initialize the Tello drone
    tello = Tello()
    
    try:
        # Connect to the drone
        tello.connect()
        print(f"Battery Level: {tello.get_battery()}%")
        
        # Command the drone to take off
        print("Taking off...")
        tello.takeoff()
        
        # Short delay to ensure stability
        time.sleep(2)
        
        # Command the drone to land
        print("Landing...")
        tello.land()
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Ensure the connection is closed
        tello.end()

if __name__ == "__main__":
    main()

