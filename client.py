import socket
from threading import Thread
import tkinter as tk

import videosocket
from videofeed import VideoFeed

class Client:
    def __init__(self):
        self.socket = socket.socket()
        self.buffer_size = 2048
        self.videofeed = VideoFeed("client_cam", 1)
        self.vsock = videosocket.VideoSocket(self.socket)
        self.is_video_call = False

    def receive(self):
        while True:
            if self.is_video_call:
                frame = self.videofeed.get_frame()
                self.vsock.vsend(frame)
                # rcvd_frame = self.vsock.vreceive()
                # self.videofeed.set_frame(rcvd_frame)
            else:
                msg = self.socket.recv(self.buffer_size)
                if msg == bytes("VIDEO_CALL_START", "utf-16"):
                    self.is_video_call = True
                else:
                    self.update_gui(msg, False)

    def send(self, msg=None):
        if msg is None:
            msg = msg_box.get()
            msg_box.delete(0, tk.END)
            self.socket.send(bytes(msg, "utf-16"))
        else:
            self.socket.send(msg)

    def initiate_video_call(self):
        self.send(bytes("VIDEO_CALL_START", "utf-16"))
        self.online_users_window()

    def update_gui(self, msg, is_sent=False):
        display_listbox.insert("end", msg.decode("utf-16"))

    def online_users_window(self):
        usernames = self.socket.recv(self.buffer_size).decode("utf-16")
        names = usernames.split("$")[:-1]
        print(names)

        num_online = len(names)
        root = tk.Tk()
        root.geometry("300x%s" %(str((2 + num_online) * 100)))
        if num_online == 0:
            l = tk.Label(root, text="No users online, try again later!!", padx=20, pady=10)
            l.pack()
        else:
            l = tk.Label(root, text="Select user that you want to call", padx=20, pady=10)
            l.pack()

        for n in names:
            b = tk.Button(root, text=n, command=lambda: self.send_target_name(root, n))
            b.pack()

        qb = tk.Button(root, text="Quit", command=lambda: self.send_target_name(root, None))
        qb.pack()
        root.mainloop()

    def send_target_name(self, root, target_name):
        if target_name:
            self.send(bytes(target_name, "utf-16"))
        else:
            self.send(bytes("ALL_OUT", "utf-16"))
        root.destroy()



client = Client()
white = "#fff"

msg_box = None
display_listbox = None

def cleanup(root):
    root.destroy()
    client.send(bytes("QUIT", "utf-16"))


def design_top(root, master):
    fr1 = tk.Frame(master, bg=white, width=150, height=40, padx=10)
    fr1.pack(side=tk.LEFT)
    fr1.pack_propagate(0)

    btn1 = tk.Button(fr1, text="Video Call", height=40, command=client.initiate_video_call)
    btn1.pack(fill=tk.BOTH)

    fr2 = tk.Frame(master, bg=white, width=150, height=40, padx=10)
    fr2.pack(side=tk.LEFT)
    fr2.pack_propagate(0)

    btn2 = tk.Button(fr2, text="Quit", height=40, command=lambda: cleanup(root))
    btn2.pack(fill=tk.BOTH)


def design_middle(master):
    fr = tk.Frame(master, bg=white, padx=20, pady=20)
    fr.pack(expand=1, fill=tk.BOTH)

    scrollbar = tk.Scrollbar(fr)
    global display_listbox
    display_listbox = tk.Listbox(fr, bg="#d1d1d1", yscrollcommand=scrollbar.set)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    display_listbox.pack(expand=1, fill=tk.BOTH)

def design_bottom(master):
    hold_frame = tk.Frame(master, pady=20, bg=white)
    hold_frame.pack(fill=tk.BOTH)

    send_msg_box = tk.Entry(hold_frame)
    send_msg_box.pack(expand=True, side=tk.LEFT, fill=tk.BOTH)

    send_btn = tk.Button(hold_frame, text="SEND", width=10, command=client.send)
    send_btn.pack(side=tk.LEFT)

    return send_msg_box

def create_window():
    root = tk.Tk()
    root.geometry("800x600")
    root.protocol('WM_DELETE_WINDOW', lambda: cleanup(root))

    top_frame = tk.Frame(root, width=800, height=100, bg=white, padx=15, pady=15)
    display_frame = tk.Frame(root, width=800, height=600, bg=white,padx=15, pady=15)
    send_frame = tk.Frame(root, width=800, height=100, bg=white, padx=15, pady=15)

    top_frame.pack_propagate(0)
    top_frame.pack()
    display_frame.pack_propagate(0)
    display_frame.pack()
    send_frame.pack_propagate(0)
    send_frame.pack()

    design_top(root, top_frame)
    design_middle(display_frame)
    global msg_box
    msg_box = design_bottom(send_frame)

    return root

def IP_window():
    root = tk.Tk()
    root.geometry("200x200")
    l1 = tk.Label(root, text="Enter server IP", padx=20, pady=20)
    l1.pack()
    e = tk.Entry(root)
    e.pack()
    return root, e

server_IP = None
def get_IP(root, e):
    global server_IP
    server_IP = e.get()
    root.destroy()

if __name__ == "__main__":
    connected = False
    username = None
    while not connected:
        dialog, e = IP_window()
        b1 = tk.Button(dialog, text="Submit", command=lambda: get_IP(dialog, e))
        b1.pack()
        dialog.mainloop()

        if server_IP == "":
            server_IP = "127.0.0.1"
        server_port = 50000
        try:
            client.socket.connect((server_IP, server_port))
            username = input("Enter username: ")
            client.send(bytes(username, "utf-16"))
            connected = True
        except:
            print("Could not connect to server with IP: %s!! Try Again." %(server_IP))


    receive_thread = Thread(target=client.receive)
    receive_thread.start()

    window = create_window()
    window.mainloop()
