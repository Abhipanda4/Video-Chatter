import socket
import threading
import videosocket


# DEBUG
import io
from PIL import Image
import numpy as np
import cv2

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

                #### Just trying things, remove it afterwards
                pil_bytes = io.BytesIO(frame_bytes)
                pil_image = Image.open(pil_bytes)
                cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
                cv2.imshow("oh yeah", cv_image)

                self.send_to_one(receiver_username, frame_bytes)

            else:
                msg = client.recv(self.buffer_size)
                if msg == bytes("QUIT", "utf-16"):
                    client.close()
                    del self.clients[username]
                    self.broadcast(None, bytes("Client %s left the conversation" %(username), "utf-16"))
                elif msg == bytes("VIDEO_CALL_START", "utf-16"):
                    # note the receiver username and send a confirmation
                    print("Sending confirmation msg")
                    receiver_username = client.recv(self.buffer_size).decode("utf-16")
                    is_video = True
                    self.send_to_one(username, bytes("VIDEO_CALL_START", "utf-16"), is_video=False)
                else:
                    # normal msg, broadcast to all
                    self.broadcast(username, msg.decode("utf-16"))

    def broadcast(self, sender, msg):
        for u, c in self.clients.items():
            if sender:
                c[0].send(bytes("%s: %s" %(sender, msg), "utf-16"))
            else:
                c[0].send(bytes("%s" %(msg), "utf-16"))

    def send_to_one(self, target, msg, is_video=True):
        for u, c in self.clients.items():
            if u == target:
                if is_video:
                    c[1].vsend(frame)
                else:
                    c[0].send(msg)
                break

if __name__ == "__main__":
    s = Server()
    s.server.listen(10)
    print("Server is ON. Waiting for clients to connect!!!")
    accept_thread = threading.Thread(target=s.accept_conn)
    accept_thread.start()
    accept_thread.join()
    s.server.close()
