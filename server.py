import socket
import os
from _thread import *
import pickle
import time
import datetime
import threading

ServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #setting TCP connection inside server
#ServerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
ServerSocket.bind(("", 5556))


#dictionarys for the storng data 
ThreadCount = 0
HEADER_LENGTH = 10 #header lenght size
login_credentials = {}
client_addresses = {}
socket_addresses = {}
online_users = {} #Online users information dictionary

print('Waitiing for a Connection..')
ServerSocket.listen(5) #support max 5 people conenction, can be chnage in later

#creating log file necesarry history and date information 
def add_to_log(info):
    time = str(datetime.datetime.now()).split(" ")[1].split(".")[0]
    date = date = str(datetime.datetime.now()).split(" ")[0]
    with open("server_log.txt", "a+") as file:
        file.write(f"{date} {time}: {info}\n") # writing inside of file with date

#formatting messages 
def format_message(data):
    pickled_data = pickle.dumps(data) #paersing pickle data  with utf 8 format
    return bytes(f'{len(pickled_data):<{HEADER_LENGTH}}', 'utf-8') + pickled_data


#getting data from clients 
def receive_object(client_socket):
    message_header = client_socket.recv(HEADER_LENGTH)
    if not len(message_header):
        return False

    client_data = client_socket.recv(int(message_header.strip())) #receiving a message from client
    unpickled_data = pickle.loads(client_data) #unpacking data
    return unpickled_data

#################### REGISTER #####################
def register_client(user_data, client_socket):
    username = user_data["username"]
    if username not in login_credentials:
        login_credentials[username] = user_data["password"] ## setting password to user
        socket_addresses[client_socket].append(user_data["port"]) # appending inside dictonary 
        client_addresses[username] = socket_addresses[client_socket]
        client_socket.sendall(str.encode("User successfully created!"))
        add_to_log("User successfully created!") #sending into log file 

    elif username in login_credentials: #checking if user is aldready exist
        client_socket.sendall(str.encode("This username already in use!")) #sending exist data information to user
        add_to_log("This username already in use!")


####################  LOGIN  #####################
def login_client(user_data, client_socket):
    username = user_data["username"]
    password = user_data["password"]
    if username in login_credentials: #login to user 
        if password == login_credentials[username]: #checking login information of the user
            online_users[username] = 0
            client_socket.sendall(str.encode("CONFIRMED")) #sending info mesage to user
            add_to_log("CONFIRMED") #adding confirmation log message to log file 
            return

    client_socket.sendall(str.encode("DECLINED")) #sending declined message to log file 
    add_to_log("DECLINED")



#################### SEARCH #####################
def search_users(user_data, client_socket):
    # This only checks the user list but it should also check if the user online or not
    for username in client_addresses:
        if username == user_data["username"]: #seraching user with their username
            if username in online_users:
                #packet = {"command": "FOUND", "username": username}
                client_socket.send(format_message(client_addresses[username]))
                add_to_log(client_addresses[username])
                return

    client_socket.sendall(format_message(["NOT FOUND"]))# sending message to client if user not found
    add_to_log("NOT FOUND")#adding inside log dile not found signal


def threaded_client(connection):
    #connection.send(str.encode('Welcome to the Servern'))
    while True:
        data = receive_object(connection)
        try:
            add_to_log(str(data["command"])) # getting signals 
        except:
            pass
        if not data or data==False:
            break

        elif data["command"] == "HELLO": # hello signal for the maintaining the connection
            online_users[data["username"]] = 0

        elif data["command"] == "REGISTER":# register signal for registering a new client
            register_client(data, connection)

        elif data["command"] == "LOGIN":# login signal for loggin a user into system
            login_client(data, connection)

        elif data["command"] == "SEARCH": # search signal for searching a new user to chat
            search_users(data, connection)

        elif data["command"] == "LOGOUT":# logout signal forthe terminating all the process for the current user
            username = data["username"]
            print(online_users)
            del online_users[username]
            print(online_users)
            print(f"{username} is logged out!") #printing logout message into the CLI
            add_to_log(f"{username} is logged out!") #sending logout information to the log file

    connection.close()

def connection_guard():
    # This function is for checking HELLO messages and setting users 
    # offline if they don't send HELLO for 20 seconds.
    # I set up the system like every user has 0 points in the beggining.
    # every second they gain 1 point and every second loop checks if any user
    # reaches 20 points. if it does users condition sets to offline.
    # if user sends HELLO to the system points reset to 0.
    naughty_list = []
    while True:
        print(online_users)
        for username in online_users:
            if online_users[username] == 20: #counting 20 sec for the logging out user
                naughty_list.append(username)
                print(f"{username}'s connection is terminated!")#printing terminated message to the terminal
                add_to_log(f"{username}'s connection is terminated!") #adding terminated information to the log file 
                continue
            online_users[username] += 1
        
        for naughty in naughty_list:
            del online_users[naughty]
        naughty_list = []
        time.sleep(1)

def main():
    guard = threading.Thread(target=connection_guard) #defining thread
    guard.start() #starting athread

    while True:
        client_socket, address = ServerSocket.accept() #accepting socket informations
        socket_addresses[client_socket] = [address[0]]
        print('Connected to: ' + address[0] + ':' + str(address[1])) #viewing the connected users ip addresses 
        add_to_log('Connected to: ' + address[0] + ':' + str(address[1])) #adding the connected users ip addresses into log file
        #start_new_thread(threaded_client, (client_socket, ))
        client = threading.Thread(target=threaded_client, args=((client_socket,)))#starting a thread with threaded_client
        client.start()

main()