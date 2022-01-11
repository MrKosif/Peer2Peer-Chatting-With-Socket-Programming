import socket
import pickle
from _thread import *
import threading
import time
import datetime

ClientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ClientSocket.connect(('192.168.1.2', 5556))

udp_socket = 4445
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(("", udp_socket))

HEADER_LENGTH = 10
global busy
busy = False
online = False

## second olarak variable gir

my_username = ""
friends_username = ""

job = threading.Thread()

print('Waiting for connection')

##################  OBJECT RECEIVE AND SENDING ##################
def add_to_log(info, username=my_username):
    time = str(datetime.datetime.now()).split(" ")[1].split(".")[0]
    date = str(datetime.datetime.now()).split(" ")[0]
    with open(f"{my_username}_user_log.txt", "a+") as file:
        file.write(f"{date} {time} {username}: {info}\n")

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


##################  REGISTER  ##################
def register_user(client_socket):
    print("##### Registration ##### ")
    username = input("Username: ")
    password = input("Password: ")
    if username == "" or password == "":
        print("Please Enter valid inputs!")
        return
    print()
    register_credentials = {"command": "REGISTER", "username": username, "password": password, "port": udp_socket}
    client_socket.send(format_message(register_credentials))
    data = client_socket.recv(1024).decode("utf-8")
    add_to_log("REGISTER", username)
    print(data)
    add_to_log(data, username)
    return


##################  LOGIN  ##################
def login_user(client_socket):
    print("##### Login ##### ")
    username = input("Username: ")
    password = input("Password: ")
    print("---------------------------")
    register_credentials = {"command": "LOGIN", "username": username, "password": password}
    client_socket.send(format_message(register_credentials))
    user_data = (client_socket.recv(1024)).decode("utf-8")
    add_to_log("LOGIN", username)
    add_to_log(user_data, username)

    if user_data == "CONFIRMED":
        print("User successfully logined!")
        global online
        online = True
        signal = threading.Thread(target=send_signal, args=(client_socket, username))
        signal.start()
        logined_menu(username, client_socket)

    elif user_data == "DECLINED":
        print("Incorrect username of password")
        return

def logined_menu(username, client_socket):
    global my_username
    my_username = username
    while True:
        print()
        print(f"Welcome {username}!")
        print("---------------------------")
        print("1- Search a user")
        print("2- Log out")
        print("---------------------------")

        while True:
            choice = input(">> ")
            if choice == "1":
                print()
                print("##### Search User ##### ")
                search_username = input("Search User: ")
                print("---------------------------") 
                handle_search(search_username, client_socket)
                #while True:
                #    time.sleep(2)
                #    if busy == False:
                #        break
                break

            elif choice == "2":
                global online
                client_socket.send(format_message({"command": "LOGOUT", "username": username}))
                add_to_log("LOGOUT", username)
                online = False
                return

            else:
                while True:
                    time.sleep(2)
                    if busy == False:
                        break
                break


###############  SEARCH  #######################
def handle_search(username, client_socket):
    # addd someting like hey this is the user you searched do you want to send a request
    search_request = {"command": "SEARCH", "username": username}
    client_socket.send(format_message(search_request))
    add_to_log("SEARCH", username)
    user_data = receive_object(client_socket)
    add_to_log(user_data[0], username)
    if user_data[0] == "NOT FOUND":
        print("User is not found!")
        return
    global friends_username
    friends_username = username
    IP = user_data[0]
    PORT = user_data[1]
    print()
    server_socket.sendto(str.encode("CHAT REQUEST|" + my_username), (IP, PORT))
    add_to_log("CHAT REQUEST", username)

    # SEND YOUR USERNAME TOOOOO


###################### CHATT PARTT #########################

def chatting(ip, port):
    global my_username
    while True:
        message = input()
        print ('\033[1A' + my_username + ": " + message + '\033[K')
        if message == "exit":
            server_socket.sendto(str.encode(f"User {my_username} disconnected from chat!"), (ip, port))
            add_to_log(f"User {my_username} disconnected from chat!", my_username)
            return
        server_socket.sendto(str.encode(message), (ip, port))
        add_to_log("CHAT REQUEST", my_username)


def chat_request(ip, port):
    print()
    print(f"User {friends_username} want to chat with you.")
    print("Whould you like to accept?")
    print("yes / no")
    print("Pres Enter to answer!")
    while True:
        answer = input(">> ")
        if answer == "yes":
            server_socket.sendto(str.encode("OK"),(ip, port)) 
            add_to_log("OK", my_username)
            print("Chatting is starting...")
            chatting(ip, port)
            return
        elif answer == "no":
            server_socket.sendto(str.encode("REJECT"),(ip, port)) 
            add_to_log("REJECT", my_username)
            return
        else:
            print("Please enter a valid input!")
        

################  LISTENING PART  #################
def handle_request(command, ip, port):
    global friends_username
    if command[:12] == "CHAT REQUEST":
        friends_username = command.split("|")[1]
        add_to_log("CHAT REQUEST", friends_username)
        global busy
        if busy == True:
            server_socket.sendto(str.encode("BUSY"),(ip, port)) 
            return
        
        busy = True
        chat_request(ip, port)
        busy = False
        return

    add_to_log(command, friends_username)
    if command == "OK":
        print("Pres Enter to start chatting")
        busy = True
        chatting(ip, port)
        busy = False
        return
        ### Start chatting from here

    elif command == "REJECT":
        print(f"User {ip} rejected the request!")
        return

    elif command == "BUSY":
        print(f"User {ip} is chatting with someone else!")
        return

    else:
        print(f"{friends_username}: {command}")


def listen_socket():
    global busy
    busy = False
    while True:
        msg = server_socket.recvfrom(1024)
        command = msg[0].decode("utf-8")
        ip = msg[1][0]
        port = msg[1][1]
        #start_new_thread(handle_request, (command, ip, port))
        global job
        job = threading.Thread(target=handle_request, args=(command, ip, port))
        job.start()


##################  START MENU  ##################
def start_menu(client_socket):
    while True:
        print()
        print("---------------------------")
        print("Welcome to the chat system!")
        print("---------------------------")
        print("1- Register to System")
        print("2- Login to System")
        print("---------------------------")
        print()

        while True:
            choice = input(">> ")
            if choice == "1":
                register_user(client_socket)
                break

            elif choice== "2":
                login_user(client_socket)
                break

            else:
                print("Please enter a valid input!")


def send_signal(client_socket, username):
    global online
    while True:
        if online == True:
            counter = 0
            while True:
                if counter == 6:
                    client_socket.send(format_message({"command": "HELLO", "username": username}))
                    add_to_log("HELLO", my_username)
                    break
                time.sleep(1)
                counter += 1
        else:
            return


li = threading.Thread(target=listen_socket)
men = threading.Thread(target=start_menu, args=(ClientSocket,))
li.start()
men.start()
li.join()
men.join()
ClientSocket.close()