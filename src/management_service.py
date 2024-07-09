import socket
import json
import time
import threading
from monitoring_service import start_non_blocking_tcp_server


class ManagementService:
    def __init__(self, server_ip, server_port, max_retries=3):
        self.server_ip = server_ip
        self.server_port = server_port
        self.client_socket = None
        self.max_retries = max_retries

    def write_to_json_file(self, services, filename):
        try:
            # Attempt to open and read the file
            with open(filename, 'r') as file:
                data_to_read = json.load(file)
        except FileNotFoundError:
            # If the file doesn't exist, start with an empty dictionary
            data_to_read = []

        service_id = services['service_id']
        if services["action"] == "add_task":
            service_details = {"task": services["task"], "frequency": services["frequency"],
                               "configuration": services["configuration"], "status": "Running"}
            data_to_append = {service_id: service_details}
            data_to_read.append(data_to_append)
        else:
            for my_dict in data_to_read:
                if service_id in my_dict:
                    if services["action"] == "pause_task":
                        my_dict[service_id]["status"] = "Paused"
                    elif services["action"] == "resume_task":
                        my_dict[service_id]["status"] = "Resumed"
                    elif services["action"] == "stop_task":
                        my_dict[service_id]["status"] = "Stopped"

        # Write updated data back to the file
        with open(filename, 'w') as file:
            json.dump(data_to_read, file, indent=4)

    def server_monitoring_service(self):
        """Set the IP and port for the server to start in the background"""
        print("-" * 50)
        # Only server running on that ip and port
        server_thread = threading.Thread(target=start_non_blocking_tcp_server,
                                         args=(self.server_ip, self.server_port), daemon=True)
        server_thread.start()

    def client_socket_and_connect(self):
        """Attempts to establish a new connection to the server with exponential backoff."""
        attempt = 0
        while attempt < self.max_retries:
            try:
                if self.client_socket:
                    self.client_socket.close()

                # Create socket
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                # Socket configurations for performance and reliability
                self.client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                # Connect to server
                self.client_socket.connect((self.server_ip, self.server_port))
                print(f"Client connected to [{self.server_ip}] : {self.server_port}\n")

                return True

            # Handle reconnection
            except socket.error as e:
                wait = 2 ** attempt  # Exponential backoff
                print(f"Connection attempt {attempt + 1} failed: {e}. Retrying in {wait} seconds...")
                time.sleep(wait)
                attempt += 1
        print("Failed to reconnect after several attempts. Exiting.")
        return False

    def client_sendall_and_response(self, message_data):
        """Sends a request to the server and waits for a response, with reconnection attempts."""
        print("-" * 50)
        try:
            self.client_socket.sendall(json.dumps(message_data).encode('utf-8'))
            response = self.client_socket.recv(1024).decode()
            return response
        except (BrokenPipeError, ConnectionResetError, socket.error) as e:
            print(f"Connection lost: {e}. Attempting to reconnect...")
            if self.client_socket_and_connect():  # Attempt to reconnect
                self.client_socket.sendall(json.dumps(message_data).encode('utf-8'))  # Retry sending after reconnecting
            else:
                print("Unable to reconnect and send the message. Please try again later.")

    def client_management_service(self):
        """Handles the UI and user commands."""
        while True:
            print("=" * 50)
            print("Distributed Network Monitoring Service System")
            print("=" * 50)
            print("A. Add Task")
            print("B. Pause Task")
            print("C. Resume Task")
            print("D. Stop Task")
            print("E. Render Task")
            print("F. Render Status")
            print("Q. Quit")
            print("=" * 50)
            print("\nPrompt loading..")
            print("WARNING: Diagnostics may appear spontaneously.\n")
            print("-" * 50)
            time.sleep(5)
            choice = input("Enter your choice: ").upper()
            if choice == 'Q':
                print("Exiting program.")
                break
            elif choice in ['A', 'B', 'C', 'D', 'E', 'F']:
                self.execute_command(choice)
            else:
                print("Invalid option. Please try again.")

    def execute_command(self, choice):
        """Handles actions based on user choice."""
        if choice == 'A':
            # Add task
            message_data = {
                'action': 'add_task',
                'service_id': input("Enter service ID: "),
                'task': input("Enter service task: ").lower(),
                'frequency': int(input("Enter frequency in seconds: ")),
                'configuration': 'pending'
            }
            configuration = []
            while True:
                config = input("Enter config ('Q' to stop): ")
                if config == 'Q' or config == 'q':
                    break
                else:
                    configuration.append(config)
            message_data['configuration'] = configuration

            # Register services in file
            self.write_to_json_file(message_data, "config_file.json")
            # Send request
            self.client_sendall_and_response(message_data)
        elif choice == 'B':
            # Pause task
            message_data = {
                'action': 'pause_task',
                'service_id': input("Enter service ID: "),
            }
            self.write_to_json_file(message_data, "config_file.json")
            self.client_sendall_and_response(message_data)
        elif choice == 'C':
            # Resume task
            message_data = {
                'action': 'resume_task',
                'service_id': input("Enter service ID: ")
            }
            self.write_to_json_file(message_data, "config_file.json")
            self.client_sendall_and_response(message_data)
        elif choice == 'D':
            # Stop task
            message_data = {
                'action': 'stop_task',
                'service_id': input("Enter service ID: ")
            }
            self.write_to_json_file(message_data, "config_file.json")
            self.client_sendall_and_response(message_data)
        elif choice == 'E':
            # Render task output
            input_file = input("Enter file name: ")
            filename = f"{input_file}.json"
            with open(filename, "r") as file:
                result = json.load(file)
                for stream in result:
                    print(stream)
        elif choice == 'F':
            # Render task status
            service_id = input("Enter service ID: ")
            filename = "config_file.json"
            with open(filename, "r") as file:
                data_to_read = json.load(file)
                for my_dict in data_to_read:
                    if service_id in my_dict:
                        print(f"Service ID: {service_id} | Service: {my_dict[service_id]['task']} | Status: "
                              f"{my_dict[service_id]['status']}")

    def run_management_service(self):
        """Main method to run the client application."""
        self.server_monitoring_service()  # create the monitoring service
        if self.client_socket_and_connect():  # connect to monitoring service
            try:
                self.client_management_service()  # run management service (self.client_sendall_and_response())
            finally:
                if self.client_socket:
                    self.client_socket.close()  # close management service
                    print("Connection closed.")


if __name__ == "__main__":
    server_ip = "127.0.0.1"
    server_port = 9999
    ms_object = ManagementService(server_ip, server_port)
    ms_object.run_management_service()
