from os.path import abspath
import socket
import os

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 8000


server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((SERVER_HOST, SERVER_PORT))
server_socket.listen(1)
print('Listening on port %s ...' % SERVER_PORT)

while True:
    client_conn, client_addr = server_socket.accept()

    request = client_conn.recv(1024).decode()
    print(request)

    headers = request.split('\n')
    filename = headers[0].split()[1]

    if filename == '/':
        filename = '/index.html'

    dir_path = os.path.dirname(__file__)
    fpath = dir_path + '/htdocs' + filename

    try:
        fin = open(fpath)
        content = fin.read()
        fin.close()

        response = 'HTTP/1.0 200 OK\n\n' + content
    except IOError:
        response = 'HTTP/1.0 404 NOT FOUND\n\nFile Not Found' 
    client_conn.sendall(response.encode())
    client_conn.close()


server_socket.close()