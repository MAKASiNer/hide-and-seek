from .server import ServerApp


server = ServerApp()

# это нужно чтобы обойти передачу экземпляра класса через args
def server_loop_wrap(*args, **kwargs):
    return server.serverloop(*args, **kwargs)
