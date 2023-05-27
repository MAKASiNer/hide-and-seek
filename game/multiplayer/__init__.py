from . import views
from .common import MultiplayClient, MultiplayHost
from .actions import ActionID, Action
from .multiplayer import server, server_loop_wrap


MultiplayHost.serverloop = server_loop_wrap