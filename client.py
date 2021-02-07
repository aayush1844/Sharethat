import os
import queue
import time
import readchar
import sys
import threading
import random
import socket
import subprocess
import socket_interact
import shell_interact
from config import *


user_name = None
messages = queue.Queue()
cmd_entered = ">>> "


def main():
    global user_name
    conn = socket_interact.get_client_socket()
    user_name = register_client(conn)
    listen_server_thread = threading.Thread(target = listen_server, args = (conn, ), daemon = True)
    listen_server_thread.start()
    cmd_output_thread = threading.Thread(target = cmd_output, args = (), daemon = True)
    cmd_output_thread.start()
    global cmd_entered
    char_input = ""
    while True:
        print(f"\r{' ' * len(cmd_entered)}", end = "")
        if char_input == "\x7f":
            if len(cmd_entered) > 4:
                cmd_entered = cmd_entered[ : -1]
        else:
            cmd_entered = cmd_entered + char_input
        if cmd_entered.isprintable():
            print(f"\r{cmd_entered}", end = "")
        else:
            try:
                print(f"\r{cmd_entered}", end = "")
                cmd = cmd_entered.strip().split()
                cmd = cmd[1 : ]
                typ = cmd[0]
                if typ == "connect" and len(cmd) == 2:
                    join_other_room(conn, int(cmd[1]))
                elif typ == "disconnect" and len(cmd) == 1:
                    disconnect_room(conn)
                elif typ == "quit" and len(cmd) == 1:
                    quit_app(conn)
                    conn.close()
                    os._exit(0)
                elif typ == "info" and len(cmd) == 1:
                    get_info(conn, user_name)
                elif typ == "sm" and len(cmd) > 1:
                    send_message(conn, " ".join(cmd[1 : ]))
                elif typ == "sf" and len(cmd) == 2:
                    send_file(conn, int(cmd[1]))
            except:
                messages.put("Unknown command entered.")
            cmd_entered = ">>> "
            print(f"\r\n{cmd_entered}", end = "")
        char_input = readchar.readkey()
    

def register_client(conn):
    """
    - Registers a client with a unique user-name
    - Returns a unique user-name
    """
    user_name = input(">>> Enter a user-name: ")
    print(user_name)
    while user_name_taken(conn, user_name):
        user_name = input(f">>> (user-name: {user_name}) is already taken. Enter a different user-name: ")
    print(f"Welcome {user_name}")
    return user_name


def user_name_taken(conn, user_name):
    """
    - Return True if user_name is already registered with server else False
    """
    socket_interact.send_message(conn, 1, user_name)
    p_no, data_sz, file_name_size = socket_interact.receive_header(conn)
    message = socket_interact.receive_message(conn, data_sz)
    if message == "BAD":
        return True
    else:
        print(f"Joined (room: {message}).")
        return False


def cmd_output():
    """
    - Blocks input and prints messages from messages queue
    """
    global messages
    while True:
        message = messages.get()
        print(f"\r{' ' * len(cmd_entered)}\r", end = "")
        print(message)
        print(f"\r{cmd_entered}", end = "")


def listen_server(conn):
    """
    - Listens server for any messages
    - Adds them to messages queue
    """
    while True:
        p_no, data_sz, file_name_size = socket_interact.receive_header(conn)
        message = None
        if file_name_size == 0:
            message = socket_interact.receive_message(conn, data_sz)
        else:
            message = socket_interact.receive_raw_data(conn, data_sz)
        if p_no == "001":
            assert(false)
        elif p_no == "002":
            message = message.split()
            room_no = int(message[1])
            if message[0] == "OK":
                add_log_message(f"Joined (room: {room_no}).")
            else:
                add_log_message(f"(room: {room_no}) doesn't exist.")
        elif p_no == "003":
            if message == "BAD":
                add_log_message(f"You can't disconnect from a room with single user.")
            else:
                prv_room, new_room = map(int, message.split())
                add_log_message(f"Disconnected from (room: {prv_room}).")
                add_log_message(f"Joined (room: {new_room}).")
        elif p_no == "005":
            message = message.split()
            log_message = str()
            log_message = log_message + f"User: {user_name}\n\r"
            log_message = log_message + f"Room number: {message[0]}\n\r"
            log_message = log_message + f"Users in room {message[0]}:\n\r"
            for i in range(1, len(message)):
                log_message = log_message + f"\t{i}) {message[i]}\n\r"
            log_message = log_message + "Files:\n\r"
            files = shell_interact.run_command("ls " + CLIENT_FILES_LOC)
            files = files.split("\n")
            files.pop()
            for i in range(len(files)):
                log_message = log_message + f"\t{i + 1}) {files[i]}\n\r"
            add_log_message(log_message) 
        elif p_no == "006":
            messages.put(message)
        elif p_no == "007":
            file_name = message[ : file_name_size].decode()
            file_binary_data = message[file_name_size : ]
            open(f"{CLIENT_FILES_LOC}/{'_' + file_name}", "wb").write(file_binary_data)
            add_log_message(f"Received {file_name}.")


def add_log_message(message):
    """
    - Adds message to queue
    """
    message = message.strip()
    messages.put(message)


def join_other_room(conn, room_no):
    """
    - Takes user to some other room (Lobby where his friends maybe present :P)
    """
    socket_interact.send_message(conn, 2, str(room_no))


def disconnect_room(conn):
    """
    - Disconnects user from current room (with several users)
    - Moves him to new empty room
    """
    socket_interact.send_message(conn, 3, "")


def quit_app(conn):
    """
    - Erases user from server
    """
    socket_interact.send_message(conn, 4, "")


def get_info(conn, user_name):
    """
    - Asks server for room info
    - Displays files present on system to user
    """
    socket_interact.send_message(conn, 5, "")


def send_message(conn, message):
    """
    - Sends message in room
    """
    message = "[ " + user_name + " ]: " + message
    socket_interact.send_message(conn, 6, message)


def send_file(conn, file_no):
    """
    - Sends file to all users in room
    """
    files = shell_interact.run_command("ls " + CLIENT_FILES_LOC)
    files = files.split("\n")
    files.pop()
    if file_no > len(files):
        add_log_message("File doesn't exist")
    else:
        file_name = files[file_no - 1]
        file_data = open(f"{CLIENT_FILES_LOC}/{file_name}", "rb").read()
        socket_interact.send_message(conn, 7, file_name.encode() + file_data, len(file_name))


if __name__ == "__main__":
    main()
