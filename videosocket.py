import socket

class VideoSocket:
    def __init__(self , sock=None):
        if sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.sock = sock

    def connect(self,host,port):
        self.sock.connect((host,port))

    def vsend(self, framestring):
        length = len(framestring)
        lengthstr = str(length).zfill(8)

        lensent = 0
        # send length of the image first
        while lensent < 18 :
            msg = bytes(lengthstr[lensent:], "utf-16")
            sent = self.sock.send(msg)
            if sent == 0:
                raise RuntimeError("Socket connection broken")
            lensent += sent

        # send actual data
        totalsent = 0
        while totalsent < length :
            sent = self.sock.send(framestring[totalsent:])
            if sent == 0:
                raise RuntimeError("Socket connection broken")
            totalsent += sent

    def vreceive(self):
        # first length of the image is received
        lenArray = []
        lenrec = 0
        while lenrec < 18:
            chunk = self.sock.recv(18 - lenrec)
            if chunk == '':
                raise RuntimeError("Socket connection broken")
            lenArray.append(chunk.decode("utf-16"))
            lenrec += len(chunk)
        lengthstr = ''.join(lenArray)
        length = int(lengthstr)

        # now we know length of image array
        # receive the image
        totrec = 0
        imgArray = []
        while totrec < length :
            chunk = self.sock.recv(length - totrec)
            if chunk == '':
                raise RuntimeError("Socket connection broken")
            imgArray.append(chunk)
            totrec += len(chunk)
        return b''.join(imgArray)
