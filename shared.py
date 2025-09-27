# shared.py
import json
import struct


# Simple length-prefixed JSON message protocol
# send_message(sock, obj) and recv_message(sock) wrappers


def send_message(sock, obj):
    # Custom JSON encoder for PowerUp objects
    class GameEncoder(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, PowerUp):
                return {'__powerup__': True, 'name': o.name}
            if isinstance(o, RandomEvent):
                return {'__random_event__': True, 'name': o.name}
            return json.JSONEncoder.default(self, o)

    data = json.dumps(obj, cls=GameEncoder).encode('utf-8')
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

    # Custom JSON decoder for PowerUp and RandomEvent objects
    def game_decoder(dct):
        if '__powerup__' in dct:
            return dct['name']
        if '__random_event__' in dct:
            return dct['name']
        return dct

    return json.loads(data.decode('utf-8'), object_hook=game_decoder)


def recvall(sock, n):
    data = b''
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            return None
        data += chunk
    return data

    data = json.dumps(obj, cls=PowerUpEncoder).encode('utf-8')
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

    # Custom JSON decoder for PowerUp objects
    def powerup_decoder(dct):
        if '__powerup__' in dct:
            # In a real scenario, you'd map 'name' back to a PowerUp instance
            # For now, we just return the name, as the client doesn't need the full object yet
            return dct['name']
        return dct

    return json.loads(data.decode('utf-8'), object_hook=powerup_decoder)


def recvall(sock, n):
    data = b''
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            return None
        data += chunk
    return data