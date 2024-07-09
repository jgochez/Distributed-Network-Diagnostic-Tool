import socket
import time


################# UDP FUNCTIONS #######################################################
def udp_client():
    # Server address and port
    server_address = input("Enter IP Address (recommended: '127.0.0.1'): ") or '127.0.0.1'
    server_port = int(input("Enter port number (recommended: 12345): ") or "12345")

    # Create a Datagram Socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        while True:
            # Send Data
            message = input("Write message: ") or "Testing for UDP connection"
            print(f"Sending: {message}...")
            sock.sendto(message.encode(), (server_address, server_port))

            # Receive Data
            response, server = sock.recvfrom(1024)
            print(f"Received: {response.decode()} from {server}...")

            # Check if user wants to continue or leave
            client_input = input("\nPress (enter) to stay in server, type '0' to leave: ")
            if client_input == "0":
                break

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        # Close the Socket
        sock.close()
        print("Socket closed.")


def udp_server():
    # Create a Datagram Socket:
    # socket(): Create a UDP socket using AF_INET for IPv4 and SOCK_DGRAM for UDP
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Bind the Socket:
    # bind(): Bind the socket to a specific IP address and port
    server_address = input("Enter IP Address (recommended: '127.0.0.1'): ") or '127.0.0.1'
    server_port = int(input("Enter port number (recommended: 12345): ") or "12345")
    server_sock.bind((server_address, server_port))

    print("Remember, to exit server press: ^c")
    print("Server is now listening for incoming connections...")

    try:
        while True:
            # Receive and Respond to Data:
            # recvfrom(): Receive data from clients, capturing the client's address
            message, client_address = server_sock.recvfrom(1024)
            print(f"Received message: {message.decode()} from {client_address}")

            # sendto(): Send a response back to the client's address
            response = "Message received by UDP Server!"
            server_sock.sendto(response.encode(), client_address)

    except KeyboardInterrupt:
        print("UDP Server is shutting down")

    finally:
        # Close the Socket:
        # close(): Close the socket when the server is shutting down
        server_sock.close()
        print("Server socket closed")


def check_udp_port(ip_address: str, port: int, timeout: int = 3) -> (bool, str):
    """
    Checks the status of a specific UDP port on a given IP address.

    Args:
    ip_address (str): The IP address of the target server.
    port (int): The UDP port number to check.
    timeout (int): The timeout duration in seconds for the socket operation. Default is 3 seconds.

    Returns:
    tuple: A tuple containing a boolean and a string.
           The boolean is True if the port is open (or if the status is uncertain), False if the port is definitely closed.
           The string provides a description of the port status.

    Description:
    This function attempts to send a UDP packet to the specified port on the given IP address.
    Since UDP is a connectionless protocol, the function can't definitively determine if the port is open.
    It can only confirm if the port is closed, typically indicated by an ICMP 'Destination Unreachable' response.
    """

    try:
        # Create a socket object using the AF_INET address family (IPv4) and SOCK_DGRAM socket type (UDP).
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # Set a timeout for the socket to avoid waiting indefinitely.
            s.settimeout(timeout)

            # Send a dummy packet to the specified IP address and port.
            # As UDP is connectionless, this does not establish a connection but merely sends the packet.
            s.sendto(b'', (ip_address, port))

            try:
                # Try to receive data from the socket.
                # If an ICMP 'Destination Unreachable' message is received, the port is considered closed.
                s.recvfrom(1024)
                return False, f"Port {port} on {ip_address} is closed."

            except socket.timeout:
                # If a timeout occurs, it's uncertain whether the port is open or closed, as no response is received.
                return True, f"Port {port} on {ip_address} is open or no response received."

    except Exception as e:
        # Catch any other exceptions and return a general failure message along with the exception raised.
        return False, f"Failed to check UDP port {port} on {ip_address} due to an error: {e}"


################# TCP FUNCTIONS #######################################################
def tcp_client():
    # Get Server Address and Port from User
    server_address = input("Enter IP Address (recommended: '127.0.0.1'): ") or '127.0.0.1'
    server_port = int(input("Enter port number (recommended: 12345): ") or "12345")

    while True:
        try:
            # Create a Socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                # Establish a Connection
                sock.connect((server_address, server_port))

                # Send Data
                message = input("Write message: ") or "Testing for TCP connection"
                print(f"Sending: {message}...")
                sock.sendall(message.encode())

                # Receive Data
                response = sock.recv(1024)
                print(f"Received: {response.decode()}...")

        except Exception as e:
            print(f"An error occurred: {e}")
            break

        # Check if user wants to continue or leave
        client_input = input("\nPress (enter) to stay in server, type '0' to leave: ")
        if client_input == "0":
            break

    print("Connection closed.")


def tcp_server():
    # Create a Socket:
    # socket(): Create a TCP/IP socket using AF_INET for IPv4 and SOCK_STREAM for TCP
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Bind the Socket:
    # bind(): Bind the socket to a specific IP address and port
    server_address = input("Enter IP Address (recommended: '127.0.0.1'): ") or '127.0.0.1'
    server_port = int(input("Enter port number (recommended: 12345): ") or "12345")
    server_sock.bind((server_address, server_port))

    # Listen for Incoming Connections:
    # listen(): Put the socket into server mode and Listen for incoming connections
    server_sock.listen(5)  # Argument is the backlog of connections allowed

    print("Remember, to exit server press: ^c")
    print("Server is now listening for incoming connections...")

    try:
        while True:
            # Accept Connections:
            # accept(): Accept a new connection
            client_sock, client_address = server_sock.accept()
            print(f"Connection from {client_address}")

            try:
                # Send and Receive Data:
                # recv(): Receive data from the client
                message = client_sock.recv(1024)
                print(f"Received message: {message.decode()}")

                # sendall(): Send a response back to the client
                response = "Message received by TCP Server!"
                client_sock.sendall(response.encode())

            finally:
                # Close Client Connection:
                # close() (on the client socket): Close the client connection
                client_sock.close()
                print(f"Connection with {client_address} closed")

    except KeyboardInterrupt:
        print("Server is shutting down")

    finally:
        # Close Server Socket:
        # close() (on the server socket): Close the server socket
        server_sock.close()
        print("Server socket closed")


def check_tcp_port(ip_address: str, port: int) -> (bool, str):
    """
    Checks the status of a specific TCP port on a given IP address.

    Args:
    ip_address (str): The IP address of the target server.
    port (int): The TCP port number to check.

    Returns:
    tuple: A tuple containing a boolean and a string.
           The boolean is True if the port is open, False otherwise.
           The string provides a description of the port status.

    Description:
    This function attempts to establish a TCP connection to the specified port on the given IP address.
    If the connection is successful, it means the port is open; otherwise, the port is considered closed or unreachable.
    """

    try:
        # Create a socket object using the AF_INET address family (IPv4) and SOCK_STREAM socket type (TCP).
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # Set a timeout for the socket to avoid waiting indefinitely. Here, 3 seconds is used as a reasonable timeout duration.
            s.settimeout(3)

            # Attempt to connect to the specified IP address and port.
            # If the connection is successful, the port is open.
            s.connect((ip_address, port))
            return True, f"Port {port} on {ip_address} is open."

    except socket.timeout:
        # If a timeout occurs, it means the connection attempt took too long, implying the port might be filtered or the server is slow to respond.
        return False, f"Port {port} on {ip_address} timed out."

    except socket.error:
        # If a socket error occurs, it generally means the port is closed or not reachable.
        return False, f"Port {port} on {ip_address} is closed or not reachable."

    except Exception as e:
        # Catch any other exceptions and return a general failure message along with the exception raised.
        return False, f"Failed to check port {port} on {ip_address} due to an error: {e}"


################# ECHO FUNCTIONS #######################################################
def echo_server():
    """
    A simple echo server that listens for connections and echoes back any received data.

    The server listens on a specified IP address and port. When a client connects and sends data,
    the server simply sends the same data back to the client (echoes it). The server runs
    indefinitely until interrupted manually.

    The server uses TCP/IP for reliable data transmission.
    """

    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = input("Enter IP Address (recommended: '127.0.0.1'): ") or '127.0.0.1'
    server_port = int(input("Enter port number (recommended: 12345): ") or "12345")
    server_sock.bind((server_address, server_port))
    server_sock.listen(1)
    print("Echo Server is listening...")

    try:
        while True:
            client_sock, addr = server_sock.accept()
            print(f"Connection from {addr}")
            data = client_sock.recv(1024)
            if data:
                client_sock.sendall(data)
            client_sock.close()
    except KeyboardInterrupt:
        print("Shutting down Echo Server.")
    finally:
        server_sock.close()


def echo_client():
    """
    A simple echo client for sending messages to an echo server and receiving responses.

    The client connects to an echo server specified by IP address and port. The user is prompted
    to enter a message, which is sent to the server. The client then waits for a response and
    checks if the received message is the same as the sent message. If they match, it prints a
    success message; otherwise, it indicates a mismatch.

    The client can send multiple messages in a loop, and the user can choose to continue or exit
    after each message. The client uses TCP/IP for reliable data transmission.

    """

    ip_address = input("Enter IP address (recommended: localhost): ") or "localhost"
    port = int(input("Enter port number (recommended: 12345): ") or "12345")

    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((ip_address, port))
                message = input("Write Message for Diagnostics: ") or "Testing for ECHO connection"
                print("-------------------------------------")
                sock.sendall(message.encode())
                received = sock.recv(1024).decode()
                if received == message:
                    for _ in range(3):
                        print("echo...\n")
                        time.sleep(1)
                    print("wait, hold up..\n")
                    time.sleep(3)
                    print("Just kidding.\n")
                    time.sleep(1)
                    for _ in range(3):
                        print("echo...\n")
                        time.sleep(1)
                    print(f"Message received by server: {message}")
                    print("-------------------------------------")
                    print("Echo server connection was a success.")
                else:
                    print("Echo server response mismatch.")

        except Exception as e:
            print(f"Error connecting to echo server: {e}")
            break

        # Check if user wants to continue or leave
        client_input = input("\nPress (enter) to continue, type '0' to leave: ")
        if client_input == "0":
            break

    print("Client connection closed.")