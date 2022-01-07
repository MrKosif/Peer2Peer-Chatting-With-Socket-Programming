import socket
import os
from _thread import *
import pickle

ServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ServerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
ServerSocket.bind(("", 5556))

#host = ""
#port = 5555
ThreadCount = 0
HEADER_LENGTH = 10
login_credentials = {}
client_addresses = {}
socket_addresses = {}
#try:
#    ServerSocket.bind((host, port))
#except socket.error as e:
#    print(str(e))

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

def register_client(user_data, client_socket):
    print("geldim")
    username = user_data["username"]
    if username not in login_credentials:
        login_credentials[username] = user_data["password"]
        client_socket.sendall("User successfully created!")
        print("Hesap başarıyla oluşturuldu!")
        client_addresses[username] = socket_addresses[client_socket]
        client_socket.sendall(str.encode("Hesap başarıyla oluşturuldu!"))

    elif username in login_credentials:
        client_socket.sendall("This username already in use!")


def threaded_client(connection):
    #connection.send(str.encode('Welcome to the Servern'))
    while True:
        data = receive_object(connection)
        print(data)
        if not data:
            continue

        if data["command"] == "REGISTER":
            register_client(data, connection)

    connection.close()


while True:
    client_socket, address = ServerSocket.accept()
    socket_addresses[client_socket] = address
    print('Connected to: ' + address[0] + ':' + str(address[1]))
    start_new_thread(threaded_client, (client_socket, ))
    ThreadCount += 1
    print('Thread Number: ' + str(ThreadCount))
ServerSocket.close()