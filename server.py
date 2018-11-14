import socket
import threading
import videosocket
from config import *

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
        username = client.recv(self.buffer_size).decode(ENCODING)
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
                print(username + "-----" + msg.decode(ENCODING))
                if msg == bytes("QUIT", ENCODING):
                    client.close()
                    del self.clients[username]
                    self.broadcast(None, bytes("Client %s left the conversation" %(username), ENCODING))
                elif msg == bytes("VIDEO_CALL_INITIATE", ENCODING):
                    client.send(msg)
                elif msg == bytes("VIDEO_CALL_START", ENCODING):
                    # this client has initiated a video call
                    online_users = self.get_online_users(username)
                    client.send(online_users)

                    # receive the username client selected to chat with
                    receiver_username = client.recv(self.buffer_size).decode(ENCODING)
                    if receiver_username == "VIDEO_CALL_ABORT":
                        continue
                    print("%s requested a video call to: %s" %(username, receiver_username))

                    # send video call request to receiving target
                    success = self.get_receiver_confirmation(client, username, receiver_username)

                    if success:
                        print("Successfully started")
                        is_video = True
                        # send acceptance message to initiator
                        client.send(bytes("VIDEO_CALL_START", ENCODING))
                        print("start msg sent")
                elif msg == bytes("VIDEO_CALL_REJECTED", ENCODING) or msg == bytes("VIDEO_CALL_ACCEPT", ENCODING):
                    print("Confirmation received from %s" %(username))
                    target_name = client.recv(self.buffer_size).decode(ENCODING)
                    print("Sending %s to %s" %(msg.decode(ENCODING), target_name))
                    self.send_to_one(target_name, msg, False)
                else:
                    # normal msg, broadcast to all
                    self.broadcast(username, msg.decode(ENCODING))

    def get_receiver_confirmation(self, client, source, target):
        '''
        Gets confirmation of whether target is willing to accept a video call
        '''
        print("Getting confirmation from %s for %s" %(target, source))
        msg = bytes("VIDEO_CALL_REQUEST$%s" %(source), ENCODING)
        self.send_to_one(target, msg, False)

        confirmation = client.recv(self.buffer_size).decode(ENCODING)
        print(confirmation)
        if confirmation == "VIDEO_CALL_ACCEPT":
            return True
        elif confirmation == "VIDEO_CALL_ABORT":
            return False

    def get_online_users(self, initiator_username):
        '''
        Send all online users separated by $ to initiator
        '''
        users = ""
        for u in self.clients.keys():
        # if u != initiator_username:
            users = users + u + "$"
        msg = bytes(users, ENCODING)
        return msg

    def broadcast(self, sender, msg):
        for u, c in self.clients.items():
            if sender:
                c[0].send(bytes("%s: %s" %(sender, msg), ENCODING))
            else:
                c[0].send(bytes("%s" %(msg), ENCODING))

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
