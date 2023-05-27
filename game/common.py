import pyray

from .controller import GameController, logger
from .multiplayer import MultiplayClient, MultiplayHost



class GameApp(GameController):

    def __init__(self, screen_w, screen_h) -> None:
        super().__init__()
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.font = None
        self.host_addr = None
        self.__host_or_client = None

    def init_window(self):
        pyray.init_window(self.screen_w, self.screen_h, "Game")
        pyray.set_target_fps(60)

    def init_font(self):
        codepoints = [32 + i for i  in range(95)] + [0x400 + i for i in range(255)]
        self.font = pyray.load_font_ex('fonts/font.ttf', 32, codepoints, len(codepoints))
        pyray.gui_set_font(self.font)

    @property
    def host(self) -> MultiplayHost:
        if isinstance(self.__host_or_client, MultiplayHost):
            return self.__host_or_client
        return None
    
    @property
    def client(self) -> MultiplayClient:
        if isinstance(self.__host_or_client, MultiplayClient):
            return self.__host_or_client
        return None

    def loop(self):
        while not pyray.window_should_close():
            pyray.begin_drawing()
            pyray.clear_background(pyray.WHITE)

            try:
                self.run_scene()
            except Exception as err:
                self.prev_scene()
                logger.error(err, exc_info=True)

            pyray.end_drawing()
        pyray.close_window()


    def create_host(self, address=None, port=12000):
        self.__host_or_client = MultiplayHost()
        
        if not address:
            self.host_addr = (self.__host_or_client.ip, port)
        else:
            self.host_addr = (address, port)

        if not self.host.start(self.host_addr):
            self.remove_host()
            return False
        else:
            return True
    
    def remove_host(self):
        if self.host:
            self.host.stop()
            self.host_addr = None
            self.__host_or_client = None

    def create_client(self, host_addr):
        self.__host_or_client = MultiplayClient()
        self.host_addr = host_addr
        if not self.client.connect(self.host_addr):
            self.remove_client()
            return False
        return True

    def remove_client(self):
        if self.client:
            self.host_addr = None
            self.__host_or_client = None

    def screen_senter(self):
        return self.screen_w // 2, self.screen_h // 2