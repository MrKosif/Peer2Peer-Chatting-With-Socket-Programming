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
        #search_menu(client_socket)

    elif user_data == "DECLINED":
        print("Incorrect username of password")
        start_menu(client_socket)


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

        elif choice== "2":
            login_user(client_socket)
        else:
            print("Please enter a valid input!")


start_menu(ClientSocket)

ClientSocket.close()