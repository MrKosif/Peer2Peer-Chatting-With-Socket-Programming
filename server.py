import socket
import os
from _thread import *
import pickle
import time
import datetime

ServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ServerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
ServerSocket.bind(("", 5556))

ThreadCount = 0
HEADER_LENGTH = 10
login_credentials = {}
client_addresses = {}
socket_addresses = {}
online_users = {}

print('Waitiing for a Connection..')
ServerSocket.listen(5)

def add_to_log(info):
    time = str(datetime.datetime.now()).split(" ")[1].split(".")[0]
    date = date = str(datetime.datetime.now()).split(" ")[0]
    with open("server_log.txt", "a+") as file:
        file.write(f"{date} {time}: {info}\n")

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
        add_to_log("User successfully created!")

    elif username in login_credentials:
        client_socket.sendall(str.encode("This username already in use!"))
        add_to_log("This username already in use!")


####################  LOGIN  #####################
def login_client(user_data, client_socket):
    username = user_data["username"]
    password = user_data["password"]
    if username in login_credentials:
        if password == login_credentials[username]:
            online_users[username] = 0
            client_socket.sendall(str.encode("CONFIRMED"))
            add_to_log("CONFIRMED")
            return

    client_socket.sendall(str.encode("DECLINED"))
    add_to_log("DECLINED")



#################### SEARCH #####################
def search_users(user_data, client_socket):
    # This only checks the user list but it should also check if the user online or not
    for username in client_addresses:
        if username == user_data["username"]:
            if username in online_users:
                #packet = {"command": "FOUND", "username": username}
                client_socket.send(format_message(client_addresses[username]))
                add_to_log(client_addresses[username])
                return

    client_socket.sendall(format_message(["NOT FOUND"]))
    add_to_log("NOT FOUND")


def threaded_client(connection):
    #connection.send(str.encode('Welcome to the Servern'))
    while True:
        data = receive_object(connection)
        add_to_log(str(data["command"]))
        if not data or data==False:
            break

        elif data["command"] == "HELLO":
            online_users[data["username"]] = 0

        elif data["command"] == "REGISTER":
            register_client(data, connection)

        elif data["command"] == "LOGIN":
            login_client(data, connection)

        elif data["command"] == "SEARCH":
            search_users(data, connection)

        elif data["command"] == "LOGOUT":
            username = data["username"]
            print(online_users)
            del online_users[username]
            print(online_users)
            print(f"{username} is logged out!")
            add_to_log(f"{username} is logged out!")

    connection.close()

def connection_guard():
    naughty_list = []
    while True:
        for username in online_users:
            if online_users[username] == 20:
                naughty_list.append(username)
                print(f"{username}'s connection is terminated!")
                add_to_log(f"{username}'s connection is terminated!")
                continue
            online_users[username] += 1
        
        for naughty in naughty_list:
            del online_users[naughty]
        naughty_list = []
        time.sleep(1)



while True:
    client_socket, address = ServerSocket.accept()
    socket_addresses[client_socket] = [address[0]]
    print('Connected to: ' + address[0] + ':' + str(address[1]))
    add_to_log('Connected to: ' + address[0] + ':' + str(address[1]))
    start_new_thread(threaded_client, (client_socket, ))
    start_new_thread(connection_guard, (()))
    ThreadCount += 1
    print('Thread Number: ' + str(ThreadCount))
ServerSocket.close()