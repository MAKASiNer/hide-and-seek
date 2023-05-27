import time
import logging
import multiprocessing as mp

from .common import ServerSocket
from .models import ServerContext, MemberData
from .actions import Action, ActionID
from ..controller import ControllerBase


class ServerApp(ControllerBase):
    
    def __init__(self) -> None:
        super().__init__()
        self.context = ServerContext()

    def bind_action(self, action_id, **static_vars):
        return self.bind_target(action_id, **static_vars)
    
    def default_action(self, **static_vars):
        return self.bind_action(None, **static_vars)
    
    def run_action(self, action):
        default = self.bindings.get(None)
        return self.bindings.get(action.action_id, default).__call__(action=action, context=self.context)

    def serverloop(self, address, pipe):
        logger = mp.log_to_stderr(logging.INFO)

        server = ServerSocket(address)
        logger.info('started listening')

        pipe.send(None)
        while True:
            # прослушка пайпа
            # while pipe.poll():
            #     obj = pipe.recv()

            # прослушка сокета
            try:
                (_action_id, data), sender  = server.read_json()
                action = Action(ActionID(_action_id), data, sender)

                _json = self.run_action(action)
                server.send_json(_json, sender)

                if action.sender not in self.context.lobby.party:
                    self.context.lobby.party[action.sender] = MemberData()
                self.context.lobby.party[action.sender].lastcall = time.time()

                #logger.info('%s:%s <%s> - %s', sender[0], sender[1], action.action_id, type(data))

            except Exception as err:
                logging.error(err, exc_info=True)

            # кикаеn тех кто не колил слишком долго
            kicklist = []
            for member, data in self.context.lobby.party.items():
                if time.time() - data.lastcall > 3.0:
                    kicklist.append(member)

            while kicklist:
                self.context.kick(kicklist.pop())
