import socket
import threading
import videosocket

class Server:
    def __init__(self, host='', port=50000):
        self.server = socket.socket()
        self.server.bind((host, port))
        self.host = host
        self.port = port
        self.buffer_size = 2048
        self.clients = dict()

    def accept_conn(self):
        while True:
            client, client_addr = self.server.accept()
            print("Client with address: %s:%s has connected" %(client_addr))
            threading.Thread(target=self.handle_client, args=(client,)).start()

    def handle_client(self, client):
        username = client.recv(self.buffer_size).decode("utf-8")
        vsock = videosocket.videosocket(client)
        self.clients[username] = (client, vsock)
        is_video = False
        receiver_username = None

        while True:
            if is_video:
                frame = vsock.vreceive()
                for u, c in self.clients.items():
                    if u == receiver_username:
                        c[1].vsend(frame)
            else:
                msg = client.recv(self.buffer_size)
                if msg == bytes("QUIT", "utf-8"):
                    client.close()
                    del self.clients[username]
                    self.broadcast(None, bytes("Client %s left the conversation" %(username), "utf-8"))
                elif msg == bytes("VIDEO_CALL_START", "utf-8"):
                    receiver_username = client.recv(self.buffer_size).decode("utf-8")
                    is_video = True
                else:
                    self.broadcast(username, msg)

    def broadcast(self, sender, msg):
        for u, c in self.clients.items():
            if sender:
                c[0].send(bytes("%s: %s" %(sender, msg), "utf-8"))
            else:
                c[0].send(bytes("%s" %(msg), "utf-8"))

if __name__ == "__main__":
    s = Server()
    s.server.listen(10)
    print("Server is ON. Waiting for clients to connect!!!")
    accept_thread = threading.Thread(target=s.accept_conn)
    accept_thread.start()
    accept_thread.join()
    s.server.close()
