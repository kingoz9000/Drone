```mermaid
ClassDiagram
  class StunClient{
      stun.socket obj
      int client_id
      str peer_addr
      tuple[str, int] sending_addr
      tuple[str, int] STUN_SERVER_ADDR
      int HOLE_PUNCH_TRIES
      bool hole_punched
      bool running
      bool relay
      bool turn_mode
      register()
      request_peer()
      hole_punch()
      _run_in_thread(func, args*)
      listen()
      main()
    }

      class RelayStunClient{
          obj drone_command_socket
          tuple[str, int] drone_command_addr
          obj drone_video_socket
          bool state
          bool response
          float stats_refresh_rate

          send_command_to_drone(command, take_response=False)
          send_data_to_operator(data, prefix=0)
          state_socket_handler()
      }

      class ControlStunClient{
          queue[str] response
          list[str] log
          dict[str]: drone_stats
          obj stats_lock
          int packet_loss
          list[int] seq_number
          str file_name
          list[tuple] reorder_buffer
          int min_buffer_size
          int last_seq_num

          send_command_to_relay(command, print_command=False, take_response=False)
          get_peer_addr()
          get_drone_stats()
          trigger_turn_mode()
          disconnect_from_stun_server()
          handle_flags(data)
      }
    }


      
  package "joystick" <<Module>> {
    class ButtonMap {
        JoystickHandler joystick_handler
        int deadzone
        int weight
        int for_backward
        int left_right
        int up_down
        int yaw
        List[String] commands
        List[String] get_joystick_values()
    }

    class JoystickHandler {
        Any joystick
        Dict[int, bool] buttons
        __init__(debug: bool = False)
        bool connect_joystick()
        void start_reading()
        void on_joybutton_press(joystick, button)
        void on_joybutton_release(joystick, button)
        Tuple get_values(dt=0)
        static Thread run_in_thread(func, *args)
    }
  }


  package "GUI" <<Module>> {
    class DroneCommunication {
      tuple[str, int] COMMAND_ADDR
        obj COMMAND_SOCKET
        tuple[str, int] STATE_IP
        obj STATE_SOCKET
        int STATE_REFRESH_RATE
        dict[str] stats
        obj stats_lock
        __init__(command_addr, command_returnport)
        send_command(command, print_command, take_response) str|None
        get_direct_drone_stats() dict
        wifi_state_socket_handler() 
    }

    class DroneVideoFeed {
        str VIDEO_ADDRESS
        int frame_grab_timeout
        Queue[obj] frames_queue
        __init__(video_addr)
        frame_grab() 
        get_frame() array|None
        run_in_thread(func, *args) Thread
    }

    class UI {

    }

  }

  package "Webserver" <<Module>> {
    class WebServer {
    }

    note left of WebServer
      Its own process.
      Runs on the strato server.
    end note

    class WebserverSender {
	    List[String] FFMPEG_CMD
	    String WEBSERVER_IP
	    int WEBSERVER_PORT
	    Socket webserver_socket
	    Queue[Frame] frame_queue
	    Popen ffmpeg_process
	    ffmpeg_writer()
    }
  }

  class App {

  }

  class Relay {


  }

  App --|> ControlStunClient: uses
  App --|> ButtonMap: uses
  App --|> DroneCommunication : uses
  App --|> DroneVideoFeed : uses
  App --|> WebserverSender : uses
  App --|> UI : uses

  Relay --|> RelayStunClient: uses
  ButtonMap --|> JoystickHandler : uses

  ControlStunClient --|> StunClient : inherits
  RelayStunClient --|> StunClient : inherits

```
