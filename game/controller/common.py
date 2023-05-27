import logging
from functools import wraps


logger = logging.getLogger('CONTROLLER')


class ControllerBase:

    def __init__(self) -> None:
        self.bindings = dict()
        self.__target = None

    @property
    def target(self):
        return self.__target

    @target.setter
    def target(self, _target):
        if _target not in self.bindings:
            logger.warning('unbounded target %s', _target)
        self.__target = _target

    def bind_target(self, target, **static_vars):
        def decorator(func):
            @wraps(func)
            def wrap(*args, **kwargs):
                return func(*args, **kwargs)
            for var in static_vars:
                setattr(wrap, var, static_vars[var])
            self.bindings[target] = wrap
            return wrap

        if target in self.bindings:
            logger.warning('rebinding target %s', target)

        return decorator
    
    def add_middleware(self, middleware):
        def decorator(func):
            @wraps(func)
            def wrap(*args, **kwargs):
                result = middleware(*args, **kwargs) 
                if result is not None:
                    return result
                return func(*args, **kwargs)
            return wrap
        return decorator


    def run_bind(self, *args, **kwargs):
        bind = self.bindings.get(self.target)
        if bind is not None:
            return bind(*args, **kwargs)