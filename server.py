import socket
import os
from _thread import *
import pickle

ServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ServerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
ServerSocket.bind(("", 5556))

ThreadCount = 0
HEADER_LENGTH = 10
login_credentials = {}
client_addresses = {}
socket_addresses = {}
online_users = []

print('Waitiing for a Connection..')
ServerSocket.listen(5)


def format_message(data):
    pickled_data = pickle.dumps(data)
    return bytes(f'{len(pickled_data):<{HEADER_LENGTH}}', 'utf-8') + pickled_data


def receive_object(client_socket):
    message_header = client_socket.recv(HEADER_LENGTH)
    if not len(message_header):
        return False

    client_data = client_socket.recv(int(message_header.strip()))
    unpickled_data = pickle.loads(client_data)
    return unpickled_data

#################### REGISTER #####################
def register_client(user_data, client_socket):
    username = user_data["username"]
    if username not in login_credentials:
        login_credentials[username] = user_data["password"]
        socket_addresses[client_socket].append(user_data["port"])
        client_addresses[username] = socket_addresses[client_socket]
        client_socket.sendall(str.encode("User successfully created!"))

    elif username in login_credentials:
        client_socket.sendall(str.encode("This username already in use!"))


####################  LOGIN  #####################
def login_client(user_data, client_socket):
    username = user_data["username"]
    password = user_data["password"]
    if username in login_credentials:
        if password == login_credentials[username]:
            online_users.append(username)
            client_socket.sendall(str.encode("CONFIRMED"))
            return

    client_socket.sendall(str.encode("DECLINED"))


#################### SEARCH #####################
def search_users(user_data, client_socket):
    print("Birinci adım")
    # This only checks the user list but it should also check if the user online or not
    for username in client_addresses:
        if username == user_data["username"]:
            #packet = {"command": "FOUND", "username": username}
            client_socket.send(format_message(client_addresses[username]))
            return

    client_socket.sendall(format_message(["NOT FOUND"]))


def threaded_client(connection):
    #connection.send(str.encode('Welcome to the Servern'))
    while True:
        data = receive_object(connection)
        print(data)
        if not data or data==False:
            break

        elif data["command"] == "REGISTER":
            register_client(data, connection)

        elif data["command"] == "LOGIN":
            login_client(data, connection)

        elif data["command"] == "SEARCH":
            search_users(data, connection)

    connection.close()


while True:
    client_socket, address = ServerSocket.accept()
    socket_addresses[client_socket] = [address[0]]
    print('Connected to: ' + address[0] + ':' + str(address[1]))
    start_new_thread(threaded_client, (client_socket, ))
    ThreadCount += 1
    print('Thread Number: ' + str(ThreadCount))
ServerSocket.close()