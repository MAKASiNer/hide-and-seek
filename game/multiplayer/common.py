import time
import json
import socket
import multiprocessing as mp

from .actions import ActionID
from .models import Game


Address = tuple[str, int]


def my_ip():
    return socket.gethostbyname(socket.gethostname())


class ServerSocket:

    def __init__(self, addr: Address = ('localhost', 12000)):
        self.address = addr
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(tuple(addr))

    def read(self, pkglen=2048):
        return self.socket.recvfrom(pkglen)

    def send(self, msg: bytes, addr: Address):
        return self.socket.sendto(msg, addr)
    
    def read_json(self):
        msg, _addr = self.read()
        return json.loads(msg), _addr

    def send_json(self, _json, addr: Address):
        msg = json.dumps(_json).encode('utf-8')
        return self.send(msg, addr)
    

class ClientSocket:

    def __init__(self) -> None:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
    def send(self, msg: bytes, addr: Address, timeout=3.0):
        self.socket.settimeout(timeout)
        self.socket.sendto(msg, addr)
        try:
            return self.socket.recvfrom(2048)
        except socket.timeout:
            raise TimeoutError('')
        
    def send_json(self, _json, addr: Address, timeout=3.0):
        msg = json.dumps(_json).encode('utf-8')
        _msg, _addr = self.send(msg, addr, timeout)
        return json.loads(_msg), _addr


class MultiplayClient:

    serverloop = None

    def __init__(self) -> None:
        self.client = ClientSocket()
        self.host = None

    @property
    def ip(self):
        return my_ip()

    def call(self, action_id: ActionID = ActionID.CALL, data=None):
        if self.host:
            return self.client.send_json((action_id, data), self.host)

    def callback(self, action_id: ActionID = ActionID.CALL, data=None):
        res = self.call(action_id, data)
        if res[0] is not None and res[0] != 'ERROR':
            return res[0][1], res[1]
        return None, res[1]

    def connect(self, host, timeout=3.0, delay=0.01):
        self.host = host
        t = time.time()
        while t + timeout >= time.time():
            try:
                self.ping()
            except:
                time.sleep(delay)
                continue
            else:
                return True
        return False

    def disconnect(self):
        self.host = None

    def ping(self):
        start = time.time()
        try:
            self.call(ActionID.PING)
            end = time.time()
            return end - start
        except TimeoutError:
            return None

    def set_ready(self, is_ready):
        return self.call(ActionID.SET_READY, is_ready)[0]

    def get_ready(self):
        return self.callback(ActionID.GET_READY)[0]

    def leave_from_lobby(self):
        return self.call(ActionID.LEAVE_FROM_LOBBY)[0]

    def in_game(self):
        return self.call(ActionID.IN_GAME)[0] == 'Y'

    def check_game(self):
        return self.callback(ActionID.CHECK_GAME)[0]

    def load_map(self):
        if not (res := self.callback(ActionID.LOAD_GAME_MAP)[0]):
            return None
        return Game.decrypt_maze_map(*res)

    def set_position(self, x, y):
        return self.callback(ActionID.SET_POSITION,(x, y))[0]

    def get_position(self):
        return self.callback(ActionID.GET_POSITION)[0]

    def get_role(self):
        return self.callback(ActionID.GET_ROLE)[0]

    def attack(self):
        return self.call(ActionID.ATTACK)[0]

    def get_winner(self):
        return self.callback(ActionID.GET_WINNER)[0]

    def get_game_timer(self):
        return self.callback(ActionID.GET_GAME_TIMER)[0]

class MultiplayHost(MultiplayClient):
    
    def __init__(self) -> None:
        super().__init__()
        self.process = None
        self.pipe = None

    def start(self, host):
        self.pipe, child_pipe = mp.Pipe(duplex=True)
        self.process = mp.Process(target=self.__class__.serverloop, args=[host, child_pipe])
        self.process.daemon = True
        self.process.start()
        return self.connect(host)

    def stop(self):
        self.process.terminate()
        self.process = None
        self.pipe = None

    def show_context(self):
        return self.call(ActionID.SHOW_CONTEXT)[0]
    
    def set_lobby_status(self, status):
        return self.call(ActionID.SET_LOBBY_STATUS, status)[0]
    
    def start_game(self):
        return self.call(ActionID.START_GAME)[0] == 'OK'
    
    def dump_map(self, map):
        return self.call(ActionID.DUMP_GAME_MAP, Game.encrypt_maze_map(map))[0]

    def set_game_lenght(self, secs):
        return self.call(ActionID.SET_GAME_LENGHT, secs)[0]