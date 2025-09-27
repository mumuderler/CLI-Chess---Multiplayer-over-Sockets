# shared.py
import json
import struct


# Simple length-prefixed JSON message protocol
# send_message(sock, obj) and recv_message(sock) wrappers


def send_message(sock, obj):
data = json.dumps(obj).encode('utf-8')
length = struct.pack('!I', len(data))
sock.sendall(length + data)




def recv_message(sock):
# read 4 bytes length
buf = recvall(sock, 4)
if not buf:
return None
length = struct.unpack('!I', buf)[0]
data = recvall(sock, length)
if not data:
return None
return json.loads(data.decode('utf-8'))




def recvall(sock, n):
data = b''
while len(data) < n:
chunk = sock.recv(n - len(data))
if not chunk:
return None
data += chunk
return data