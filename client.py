import socket
import pickle

ClientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ClientSocket.connect(('192.168.1.2', 5556))

HEADER_LENGTH = 10

print('Waiting for connection')
#try:
#    ClientSocket.connect((host, port))
#except socket.error as e:
#    print(str(e))
#Response = ClientSocket.recv(1024)

def format_message(data):
    pickled_data = pickle.dumps(data)
    return bytes(f'{len(pickled_data):<{HEADER_LENGTH}}', 'utf-8') + pickled_data


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
            pass
            #login_user(client_socket)
        else:
            print("Please enter a valid input!")

#while True:
#    Input = input('Say Something: ')
#    ClientSocket.send(str.encode(Input))
#    Response = ClientSocket.recv(1024)
#    print(Response.decode('utf-8'))
start_menu(ClientSocket)

ClientSocket.close()