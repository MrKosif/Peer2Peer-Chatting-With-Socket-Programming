import socket
import pickle

ClientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ClientSocket.connect(('192.168.1.2', 5556))

HEADER_LENGTH = 10

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
    register_credentials = {"command": "REGISTER", "username": username, "password": password}
    client_socket.send(format_message(register_credentials))
    print(client_socket.recv(1024).decode("utf-8"))
    start_menu(client_socket)

def handle_search(username, client_socket):
    print("2. beklenti")
    search_request = {"command": "SEARCH", "username": username}
    client_socket.send(format_message(search_request))
    user_data = receive_object(client_socket)
    print(user_data)
    # MAKES CONNECTION WITH ANOTHER PEER
    #IP = user_data["data"][0]
    #PORT = user_data[1]
    #friend_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #friend_socket.connect((IP, PORT))
    #friend_socket.setblocking(True)


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
        print()

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


start_menu(ClientSocket)

ClientSocket.close()