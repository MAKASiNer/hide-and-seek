import time
from .common import ControllerBase


class GameController(ControllerBase):

    def __init__(self) -> None:
        super().__init__()
        self.context = dict()
        self.scenes_stack = list()
        self.tpoint = None

    @property
    def scene(self):
        return self.target
    
    @scene.setter
    def scene(self, _scene):
        self.target = _scene

    # переходит к новой сцене, старую помещает в стек
    def next_scene(self, scene):
        if self.scene:
            self.scenes_stack.append(self.scene)
        self.scene = scene
        return self.scene
    
    # изменяет последню сцену в стеке на переданную
    def swap_scene(self, scene):
        if self.scenes_stack:
            self.prev_scene()
        return self.next_scene(scene)

    # переходит к предыдущей сцене из стека
    def prev_scene(self):
        if self.scenes_stack:
            self.scene = self.scenes_stack.pop()
        else:
            self.scene = None
        return self.scene

    # сбрасывает стек сцен
    def reset_scenes(self):
        self.scenes_stack.clear()


    def bind_scene(self, scene, **static_vars):
        return self.bind_target(scene, **static_vars)
    
    def run_scene(self):
        if self.tpoint is None:
            self.tpoint = time.time()
        self.context['timedelta'] = time.time() - self.tpoint
        self.tpoint = time.time()

        return self.run_bind(context=self.context)