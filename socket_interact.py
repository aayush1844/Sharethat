import socket
from config import *


def get_server_socket():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", PORT))
    server.listen(USERS)
    return server


def get_client_socket():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))
    return client


def get_header(p_no, data_sz, file_name_size = 0):
    p_no = str(p_no)
    p_no = (3 - len(p_no)) * "0" + p_no
    data_sz = str(data_sz)
    data_sz = (10 - len(data_sz)) * "0" + data_sz
    file_name_size = (3 - len(str(file_name_size))) * "0" + str(file_name_size)
    header = p_no + "," + data_sz + "," + file_name_size
    header = header.encode()
    return header


def send_message(conn, p_no, data, file_name_size = 0):
    header = get_header(p_no, len(data), file_name_size)
    try:
        data = data.encode()
    except:
        pass
    message = header + data
#    print(f"Header: {header}    |    Data: {data}")
#    print(f"Message: {message}")
#    print(f"Target: {conn}")
    conn.send(message)


def receive_header(conn):
    header = receive_message(conn, HEADER_SIZE)
#    print(f"Header: \"{header}\"")
    p_no, data_sz, file_name_size = header.split(",")
    return p_no, int(data_sz), int(file_name_size)


def receive_message(conn, rem):
    data = bytes()
    while rem > 0:
        buff = conn.recv(min(CHUNK_SIZE, rem))
        data += buff
        rem -= len(buff)
    data = data.decode()
    return data


def receive_raw_data(conn, rem):
    data = bytes()
    while rem > 0:
        buff = conn.recv(min(CHUNK_SIZE, rem))
        data += buff
        rem -= len(buff)
    return data
