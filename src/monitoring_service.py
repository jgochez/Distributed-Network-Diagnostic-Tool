import socket
import select
import typing
import json
import time
import threading
from monitoring_service_task import *

filename = "thread_file.json"
thread_tracker = {}


def read_from_json_file(filename):
    """
    Read from file for user

    :param filename: Will always be thread_file.json
    :return: data that will be read to user
    """
    try:
        # Attempt to read existing data
        with open(filename, 'r') as file:
            data_to_read = json.load(file)
    except FileNotFoundError:
        # If the file doesn't exist, start with an empty list
        data_to_read = []
    return data_to_read


def write_to_json_file(filename, data_to_write):
    """
    Write updated data back to file for user

    :param filename: Will always be thread_file.json
    :param data_to_write:
    """
    with open(filename, 'w') as file:
        json.dump(data_to_write, file, indent=4)


def start_non_blocking_tcp_server(server_ip: str, server_port: int) -> None:
    """
    Starts a non-blocking TCP server that listens on a specified IP address and port.
    Uses the select module to manage multiple connections efficiently.

    :param server_ip: The IP address the server will listen on.
    :param server_port: The port number the server will listen on.
    """

    # Create server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Configuration of socket
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    server_socket.setblocking(False)
    # Prepare socket for listening
    server_socket.bind((server_ip, server_port))
    server_socket.listen(5)

    print(f"\nMonitoring Service on: [{server_ip}] : {server_port}")

    sockets_list: typing.List[socket.socket] = [server_socket]

    while True:
        read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list, 0)

        for notified_socket in read_sockets:
            if notified_socket == server_socket:
                client_socket, client_address = server_socket.accept()
                sockets_list.append(client_socket)
            else:
                try:
                    message = notified_socket.recv(1024)
                    if message:
                        client_data = json.loads(message.decode())
                        handle_monitoring_services(notified_socket, client_data)
                except Exception as e:
                    print(f"\n\n**ERROR: {notified_socket}: {e}")
                    print(f"**ERROR: Closing connection to socket: {notified_socket}\n\n")
                    if sockets_list:
                        sockets_list.remove(notified_socket)
                    notified_socket.close()

        # clean up
        for notified_socket in exception_sockets:
            print(f"CLEAN UP: Closing connection to socket: {notified_socket}")
            if sockets_list:
                sockets_list.remove(notified_socket)
            notified_socket.close()


def add_task(service_id, task_function, freq, *args):
    """
    Adds task by creating a new thread that will be handled
    using threading events.

    :param service_id: Service id for task to add
    :param task_function: Mapped function to execute task
    :param freq: Frequency in seconds for iteration of task
    :param args: Specific arguments required for task
    :return:
    """
    if service_id not in thread_tracker:
        # .Event() -> Create event
        pause_event = threading.Event()
        pause_event.set()
        stop_event = threading.Event()
        # .Thread() -> Create thread
        thread = threading.Thread(target=persistent_connection, args=(task_function, service_id, freq, pause_event,
                                                                      stop_event, *args))
        # Track thread status
        thread_tracker[service_id] = {'thread': thread, 'pause_event': pause_event, 'stop_event': stop_event}

        # Start thread
        thread.start()
        print(f"\n**Task {service_id} started**\n")

        # Add new thread to JSON file
        obj_to_str = []
        for curr_thread in thread_tracker:
            obj_to_str.append(str(curr_thread))
        write_to_json_file(filename, obj_to_str)
    else:
        print(f"WARNING: Task {service_id} is already running")


def pause_task(service_id):
    """
        Pause task by setting threading events

        :param service_id: Service id for task to pause
        """
    if service_id in thread_tracker and thread_tracker[service_id]['pause_event'].is_set():
        print(f"\n**Task {service_id} pause requested.\n")
        # .set() -> True == Pause
        thread_tracker[service_id]['pause_event'].clear()

        # Edit event status on json file
        obj_to_str = []
        for curr_thread in thread_tracker:
            obj_to_str.append(str(curr_thread))
        write_to_json_file(filename, obj_to_str)
    else:
        print(f"WARNING: Task {service_id} not found or already paused")


def resume_task(service_id):
    """
        Resume task by setting threading events

        :param service_id: Service id for task to resume
        """
    if service_id in thread_tracker and not thread_tracker[service_id]['pause_event'].is_set():
        print(f"\n**Task {service_id} resume requested.\n")
        # .clear() -> False == Resume
        thread_tracker[service_id]['pause_event'].set()

        # Edit event status on json file
        obj_to_str = []
        for curr_thread in thread_tracker:
            obj_to_str.append(str(curr_thread))
        write_to_json_file(filename, obj_to_str)
        write_to_json_file(filename, str(thread_tracker))
    else:
        print(f"WARNING: Task {service_id} not found or not paused")


def stop_task(service_id):
    """
    Stop task by setting threading events

    :param service_id: Service id for task to stop
    """
    if service_id in thread_tracker:
        print(f"\n**Task {service_id} stop and removal requested.\n")

        # Set stop event and pause event and join
        thread_tracker[service_id]['stop_event'].set()
        if not thread_tracker[service_id]['pause_event'].is_set():
            thread_tracker[service_id]['pause_event'].set()
        # .join() -> waits for thread to end
        thread_tracker[service_id]['thread'].join()

        # delete thread and edit json file
        del thread_tracker[service_id]
        data = []
        for curr_thread in thread_tracker:
            data.append(str(curr_thread))
        write_to_json_file(filename, data)
        write_to_json_file(filename, str(thread_tracker))
    else:
        print(f"WARNING: Task {service_id} not found")


def handle_monitoring_services(client_socket, data):
    """
    Handle different types of data and actions.

    :param client_socket: Current client socket we are working with.
    :param data: Dictionary: data = { 'action': str , 'service_id': str , 'task': str , 'frequency': int, 'configuration': []}
    """

    # Map task to task_function
    task_mapping = {                    # sample configurations:
        "ping": ping_task,              # [domain, count] -> [google.com, 1]
        "traceroute": traceroute_task,  # [domain, count] -> [google.com, 1]
        "http": http_task,              # [domain] -> [http://google.com]
        "https": https_task,            # [domain] -> [https://google.com]
        "ntp": ntp_task,                # [domain] -> [pool.ntp.org]
        "dns": dns_task,                # [server, domain, record type] -> [8.8.8.8, www.google.com, A]
        "tcp": tcp_task,                # [domain, port] -> [github.com, 22]
        "udp": udp_task                 # [domain, port] -> [dns.google.com, 53]
    }
    # Extract data from message
    action = data["action"]
    service_id = data["service_id"]

    # Handle request
    if action == "add_task":
        task = data["task"]
        if task in task_mapping:
            freq = data["frequency"]
            config = data["configuration"]
            task_function = task_mapping[task]
            add_task(service_id, task_function, freq, *config)
        else:
            print(f"WARNING: Task [{task}] does not exist.")
    elif action == "pause_task":
        pause_task(service_id)
    elif action == "resume_task":
        resume_task(service_id)
    elif action == "stop_task":
        stop_task(service_id)
    else:
        print(f"WARNING: Action {action} is not supported.")
        return

    # Handle response
    response = {"action": action, "message": f"Action [{action}] for service ID [{service_id}] processed."}
    try:
        response_data = json.dumps(response).encode('utf-8')
        client_socket.sendall(response_data)
    except Exception as e:
        print(f"WARNING: Failed to send response: {e}")
