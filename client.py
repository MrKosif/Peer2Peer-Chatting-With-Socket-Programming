import socket
import pickle
from _thread import *
import threading

ClientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ClientSocket.connect(('192.168.1.2', 5556))

udp_socket = 5566
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(("", udp_socket))

HEADER_LENGTH = 10
global busy
busy = False

print('Waiting for connection')

##################  OBJECT RECEIVE AND SENDING ##################
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
        start_menu()
    print()
    register_credentials = {"command": "REGISTER", "username": username, "password": password, "port": udp_socket}
    client_socket.send(format_message(register_credentials))
    print(client_socket.recv(1024).decode("utf-8"))
    start_menu(client_socket)


##################  LOGIN  ##################
def login_user(client_socket):
    print("##### Login ##### ")
    username = input("Username: ")
    password = input("Password: ")
    print("---------------------------")
    register_credentials = {"command": "LOGIN", "username": username, "password": password}
    client_socket.send(format_message(register_credentials))
    user_data = (client_socket.recv(1024)).decode("utf-8")

    if user_data == "CONFIRMED":
        print("User successfully logined!")
        logined_menu(username, client_socket)

    elif user_data == "DECLINED":
        print("Incorrect username of password")
        start_menu(client_socket)


def logined_menu(username, client_socket):
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
                break

            elif choice== "2":
                pass
            else:
                print("Please enter a valid input!")






###############  SEARCH  #######################
def handle_search(username, client_socket):
    # addd someting like hey this is the user you searched do you want to send a request

    search_request = {"command": "SEARCH", "username": username}
    client_socket.send(format_message(search_request))
    user_data = receive_object(client_socket)
    print(user_data)
    IP = user_data[0]
    PORT = user_data[1]
    server_socket.sendto(str.encode("CHAT REQUEST"), (IP, PORT)) 
    answer = server_socket.recvfrom(1024)
    print(answer[0])
    print("chatting is starting")
    ## Call the chatting function if answer is OK if its REJECT than return
    # SEND YOUR USERNAME TOOOOO

################  LISTENING PART  #################
def handle_request(command, ip, port):
    global busy
    if busy == True:
        server_socket.sendto(str.encode("BUSY"),(ip, port)) 
        return

    if command == "CHAT REQUEST":
        busy = True
        chat_request(ip, port)
        busy = False
        return

    elif command == "OK":
        print("chatting is starting")
        return
        ### Start chatting from here

    elif command == "REJECT":
        print(f"User {ip} rejected the request!")
        return

    elif command == "BUSY":
        print(f"User {ip} is chatting with someone else!")
        return


def listen_socket():
    global busy
    busy = False
    while True:
        msg = server_socket.recvfrom(1024)
        command = msg[0].decode("utf-8")
        ip = msg[1][0]
        port = msg[1][1]
        start_new_thread(handle_request, (command, ip, port))
        #job = threading.Thread(target=handle_request, args=(command, ip, port))


###################### CHATT PARTT #########################
def chat_request(ip, port):
    print()
    print(f"user {ip} want to chat with you.")
    print("Whould you like to accept?")
    print("yes / no")
    answer = input(">> ")
    if answer == "yes":
        server_socket.sendto(str.encode("OK"),(ip, port)) 
        print("Chatting is starting...")
        # chat()
    elif answer == "no":
        server_socket.sendto(str.encode("REJECT"),(ip, port)) 
        return
    else:
        print("Please enter a valid input!")


##################  START MENU  ##################
def start_menu(client_socket):
    print()
    print("welcome to the chat system!")
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


li = threading.Thread(target=listen_socket)
men = threading.Thread(target=start_menu, args=(ClientSocket,))
li.start()
men.start()
li.join()
men.join()
ClientSocket.close()