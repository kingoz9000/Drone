```mermaid
classDiagram

StunClient <|-- RelayStunClient : Inherits
StunClient <|-- ControlStunClient : Inherits

namespace stun{
    class StunClient {
        socket socket
        int client_id
        tuple[str, int] peer_addr
        tuple[str, int] sending_addr
        tuple[str, int] STUN_SERVER_ADDR
        int HOLE_PUNCH_TRIES
        bool hole_punched
        bool running
        bool relay
        bool turn_mode
        None register()
        None request_peer()
        None hole_punch()
        threading.Thread _run_in_thread()
        None handle_server_messages()
        None handle_hole_punch_message()
    }

    class RelayStunClient{
        socket drone_command_socket
        tuple[str, int] drone_command_addr
        socket drone_video_socket
        str state
        bytes response
        float stats_refresh_rate
        None send_command_to_drone()
        None send_data_to_operator()
        None state_socket_handler()
        None bandwidth_tester()
        None listen()
        None main()
    }

    class ControlStunClient{
        queue[str] response
        list[str] log
        dict drone_stats
        obj stats_lock
        int packet_loss
        list[int] seq_number
        str file_name
        list[tuple] reorder_buffer
        int min_buffer_size
        int last_seq_num
        None send_command_to_relay()
        tuple[str,int] get_peer_addr()
        dict get_drone_stats()
        None trigger_turn_mode()
        None disconnect_from_stun_server()
        None send_videofeed()
        None respond()
        None state()
        None bandwidth_test()
        None listen()
        None main()
    }
}
ButtonMap --o JoystickHandler : Uses
namespace joystick {
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
        __init__()
        bool connect_joystick()
        None start_reading()
        None on_joybutton_press()
        None on_joybutton_release()
        Tuple get_values()
        static Thread run_in_thread()
    }
}
namespace GUI{
    class DroneCommunication {
        tuple[str, int] COMMAND_ADDR
        obj COMMAND_SOCKET
        tuple[str, int] STATE_IP
        obj STATE_SOCKET
        int STATE_REFRESH_RATE
        dict[str] stats
        obj stats_lock
        __init__()
        str|None send_command()
        dict get_direct_drone_stats()
        None wifi_state_socket_handler()
    }
    class DroneVideoFeed {
        str VIDEO_ADDRESS
        int frame_grab_timeout
        Queue[obj] frames_queue
        __init__()
        None frame_grab()
        array|None get_frame()
        Thread run_in_thread()
    }
    class UserInterface {
        instance
        __init__()
        None init_ui_components()
        None update_battery_circle()
    }
}
note for WebserverApp "Its own process. Runs on the strato server."
namespace Webserver {
    class WebserverSender {
        List[String] FFMPEG_CMD
        String WEBSERVER_IP
        int WEBSERVER_PORT
        Socket webserver_socket
        Queue[Frame] frame_queue
        Popen ffmpeg_process
        ffmpeg_writer()
    }
    class WebserverApp{
        str index()
        None start_ffmpeg()
        None cleanup()
        None signal_handeler()
        Flask app
        signal signal
    }
}

App --o ControlStunClient: Uses
App --o ButtonMap: Uses
App --o DroneCommunication : Uses
App --o DroneVideoFeed : Uses
App --o WebserverSender : Uses
App --o UserInterface : Uses
class App{
    __init__()
    None init_drone_com()
    None fetch_and_update_drone_stats()
    None update_graph()
    None update_drone_stats()
    tuple get_peer_address()
    None startup_drone()
    None update_video_frame()
    None update_canvas()
    None control_drone()
    None get_ping()
    None trigger_turnmode()
    None check_connection()
    None cleanup()
    threading.Thread run_in_thread()
    dict ARGS
    CTk root
    UserInterface ui
    WebserverSender webserver_sender
    ControlStunClient stun_handler
    tuple peer_addr
    tuple drone_video_addr
    function send_command
    tuple drone_comm_addr
    DroneCommunication drone_communication
    DroneVideoFeed video_stream
    list ping_data
    int packet_loss
}
Relay --o RelayStunClient : Uses
class Relay {
    __init__()
    None main()
    RelayStunClient client
    int seq_num
}
```
