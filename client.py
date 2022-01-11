import socket
import pickle
from _thread import *
import threading
import time
import datetime

# TCP Socket Connection to the registry server
ClientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ClientSocket.connect(('192.168.1.2', 5556))

# Setting up the UDP socket for comminication.
udp_socket = 4447
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind(("", udp_socket))

# Header length for begging of the pickled 
# datas to receive the right amount of data.
HEADER_LENGTH = 10
global busy
busy = False
online = False

# This variables are configured when a peer sends chat request.
my_username = ""
friends_username = ""

job = threading.Thread()
print('Waiting for connection')
##################  RECEIVE SEND LOG ##################
# This function is for storing messages on log files.
# It also contains date and time variables for proper logging.
def add_to_log(info, username=my_username):
    time = str(datetime.datetime.now()).split(" ")[1].split(".")[0]
    date = str(datetime.datetime.now()).split(" ")[0]
    with open(f"{my_username}_user_log.txt", "a+") as file:
        file.write(f"{date} {time} {username}: {info}\n")

# This function is for pickling objects and created for ease of use.
def format_message(data):
    pickled_data = pickle.dumps(data)
    return bytes(f'{len(pickled_data):<{HEADER_LENGTH}}', 'utf-8') + pickled_data

# This function is for receiving objects from server. And contains load oeperations.
def receive_object(client_socket):
    message_header = client_socket.recv(HEADER_LENGTH)
    if not len(message_header):
        return False

    client_data = client_socket.recv(int(message_header.strip()))
    unpickled_data = pickle.loads(client_data)
    return unpickled_data
################################################

##################  REGISTER  ##################
# Register user is used for registering client to registry system.
def register_user(client_socket):
    print("##### Registration ##### ")
    username = input("Username: ")
    password = input("Password: ")
    if username == "" or password == "":
        print("Please Enter valid inputs!")
        return
    # Here we sent command along with the required 
    # datas and used format message to pickle the data
    register_credentials = {"command": "REGISTER", "username": username, "password": password, "port": udp_socket}
    client_socket.send(format_message(register_credentials))
    data = client_socket.recv(1024).decode("utf-8")
    print("---------------------------")
    add_to_log("REGISTER", username)
    print(data)
    add_to_log(data, username)
    return
#############################################

##################  LOGIN  ##################
# This function is for login to registry system.
def login_user(client_socket):
    print("##### Login ##### ")
    username = input("Username: ")
    password = input("Password: ")
    print("---------------------------")
    # dictionary format of the dictionary data.
    register_credentials = {"command": "LOGIN", "username": username, "password": password}
    client_socket.send(format_message(register_credentials))
    user_data = (client_socket.recv(1024)).decode("utf-8")
    add_to_log("LOGIN", username)
    add_to_log(user_data, username)

    if user_data == "CONFIRMED":
        # If registry sends CONFIRMED message then login menu function executes.
        print("User successfully logined!")
        # Online is used for HELLO signals
        global online
        online = True
        # After user logined it starts to sending HELLO messages.
        signal = threading.Thread(target=send_signal, args=(client_socket, username))
        signal.start()
        logined_menu(username, client_socket)

    elif user_data == "DECLINED":
        # Sends user to the start menu if declines.
        print("Incorrect username of password")
        return

def logined_menu(username, client_socket):
    # This menu pops up when user logined to the system.
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
                break

            elif choice == "2":
                # Sends LOGOUT command to the registry and making 
                # itself offline to stop sending HELLO messages.
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
################################################

###############  SEARCH  #######################
def handle_search(username, client_socket):
    # Sends registry SEARCH command along with the requested username.
    search_request = {"command": "SEARCH", "username": username}
    client_socket.send(format_message(search_request))
    add_to_log("SEARCH", username)
    user_data = receive_object(client_socket)
    add_to_log(user_data[0], username)
    if user_data[0] == "NOT FOUND":
        # If not found informs the user.
        print("User is not found!")
        print()
        return
    # friends username is set here and used later on the chatting system.
    global friends_username
    friends_username = username
    IP = user_data[0]
    PORT = user_data[1]
    print()
    while True:
        # This parts purpose is asking the user if it wants to chat with searched peer.
        print("User found!")
        print("---------------------------")
        print(f"{friends_username} | {IP} | {PORT}")
        print("---------------------------")
        print("Whould you like to send chatting request? (yes/no)")
        while True:
            ans = input(">> ")
            if ans == "yes":
                # Sending CHAT REQUEST command along with username.
                server_socket.sendto(str.encode("CHAT REQUEST|" + my_username), (IP, PORT))
                add_to_log("CHAT REQUEST", username)
                return
            elif ans == "no":
                return
            else:
                print("Please provide valid input!")
############################################################

###################### CHATT PARTT #########################
def chatting(ip, port):
    global my_username
    while True:
        message = input()
        # This part is explained in the raport shortly its using for clean chatting in terminal.
        print ('\033[1A' + my_username + ": " + message + '\033[K')
        if message == "exit":
            # Informing the other peer that his friend disconnected from chat.
            server_socket.sendto(str.encode(f"User {my_username} disconnected from chat!"), (ip, port))
            add_to_log(f"User {my_username} disconnected from chat!", my_username)
            return
        # Sending the message using UDP.
        server_socket.sendto(str.encode(message), (ip, port))
        add_to_log("CHAT REQUEST", my_username)


def chat_request(ip, port):
    # This function pops when a peer sends a chatting request.
    print(f"User {friends_username} want to chat with you.")
    print("Whould you like to accept? (yes/no)")
    print("Pres Enter to answer!")
    print("---------------------------")
    while True:
        answer = input(">> ")
        if answer == "yes":
            # If answer yes it sends OK
            server_socket.sendto(str.encode("OK"),(ip, port)) 
            add_to_log("OK", my_username)
            print("Chatting is starting...")
            print()
            chatting(ip, port)
            return
        elif answer == "no":
            # If no it sends REJECT
            server_socket.sendto(str.encode("REJECT"),(ip, port)) 
            add_to_log("REJECT", my_username)
            return
        else:
            print("Please enter a valid input!")
###################################################

################  LISTENING PART  #################
def handle_request(command, ip, port):
    global friends_username
    if command[:12] == "CHAT REQUEST": #getting chat request signal form the command 
        friends_username = command.split("|")[1]
        add_to_log("CHAT REQUEST", friends_username) #adding chat request signal inforamtion in to log file 
        global busy
        if busy == True:
            server_socket.sendto(str.encode("BUSY"),(ip, port))  #sending a busy signal to the server.py
            return
        
        busy = True
        chat_request(ip, port) 
        busy = False
        return

    add_to_log(command, friends_username) #adding chat information inside log 
    if command == "OK":
        print("Pres Enter to start chatting")  #getting confirmation from the user to start a chat
        busy = True
        chatting(ip, port) # sending ip and port adress of the user 
        busy = False
        return

    elif command == "REJECT": # reject signal if the user reject of a chat request 
        print(f"User {ip} rejected the request!")
        return

    elif command == "BUSY": # if user us already chatting with someone else this signal is sent
        print(f"User {ip} is chatting with someone else!")
        return

    else:
        print(f"{friends_username}: {command}") # printing the other side users username in terminal


def listen_socket():
    global busy
    busy = False
    while True:
        msg = server_socket.recvfrom(1024)
        command = msg[0].decode("utf-8")
        ip = msg[1][0] #ip address of user
        port = msg[1][1] #port address of user
        #start_new_thread(handle_request, (command, ip, port))
        global job
        job = threading.Thread(target=handle_request, args=(command, ip, port)) 
        #starting a thread for the requests
        job.start()
##################################################

##################  START MENU  ##################
def start_menu(client_socket):
    #main menu while loop 
    while True:
        print()
        print("---------------------------")
        print("Welcome to the chat system!")
        print("---------------------------")
        print("1- Register to System")
        print("2- Login to System")
        print("---------------------------")

        while True:
            choice = input(">> ") #getting input from user
            print()
            if choice == "1":
                register_user(client_socket) # option 1 is for the registering user
                break

            elif choice== "2":
                login_user(client_socket) # option 2 is for the login user
                break

            else:
                print("Please enter a valid input!")
#######################################################

###############  SERVER COMMuNICATION  ################
def send_signal(client_socket, username):
    global online
    while True:
        if online == True:
            while True:
                client_socket.send(format_message({"command": "HELLO", "username": username})) #sending Hello signal to the server
                #add_to_log("HELLO", my_username)
                time.sleep(6) #6 second waiting time for the hello signal
                break
        else:
            return
#######################################################

def main():
    li = threading.Thread(target=listen_socket) #defining threads for the listen socket
    men = threading.Thread(target=start_menu, args=(ClientSocket,)) #defining threads for the start menu
    li.start() #starting threads
    men.start() #starting threads
    li.join()
    men.join()
    ClientSocket.close() #finisihing socket process

main()