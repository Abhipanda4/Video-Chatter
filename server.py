import socket
import threading
import videosocket
import matplotlib.pyplot as plt

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
        username = client.recv(self.buffer_size).decode("utf-16")
        vsock = videosocket.VideoSocket(client)
        self.clients[username] = (client, vsock)
        is_video = False
        receiver_username = None

        while True:
            if is_video:
                frame_bytes = vsock.vreceive()
                self.send_to_one(receiver_username, frame_bytes)
            else:
                msg = client.recv(self.buffer_size)
                if msg == bytes("QUIT", "utf-16"):
                    client.close()
                    del self.clients[username]
                    self.broadcast(None, bytes("Client %s left the conversation" %(username), "utf-16"))
                elif msg == bytes("VIDEO_CALL_START", "utf-16"):
                    print("Video call initiated by %s" %(username))
                    # send all online users to the initiator of video call
                    self.send_online_users(username)
                    # receive the username client selected
                    receiver_username = client.recv(self.buffer_size).decode("utf-16")
                    if receiver_username == "ALL_OUT":
                        continue
                    is_video = True

                    # send acceptance message to initiator
                    self.send_to_one(username, bytes("VIDEO_CALL_START", "utf-16"), is_video=False)
                else:
                    # normal msg, broadcast to all
                    self.broadcast(username, msg.decode("utf-16"))

    def send_online_users(self, initiator_username):
        '''
        Send all online users separated by $ to initiator
        '''
        users = ""
        for u in self.clients.keys():
            if u != initiator_username:
                users = users + u + "$"
        msg = bytes(users, "utf-16")
        self.send_to_one(initiator_username, msg, False)

    def broadcast(self, sender, msg):
        for u, c in self.clients.items():
            if sender:
                c[0].send(bytes("%s: %s" %(sender, msg), "utf-16"))
            else:
                c[0].send(bytes("%s" %(msg), "utf-16"))

    def send_to_one(self, target, msg, is_video=True):
        c = self.clients[target]
        if is_video:
            c[1].vsend(msg)
        else:
            c[0].send(msg)

if __name__ == "__main__":
    s = Server()
    s.server.listen(10)
    print("Server is ON. Waiting for clients to connect!!!")
    accept_thread = threading.Thread(target=s.accept_conn)
    accept_thread.start()
    accept_thread.join()
    s.server.close()
