import re
from random import shuffle
from pyray import *
from raylib import ffi

from .game import game, SERVER_TICKRATE
from .maze import MazeMST
from .multiplayer.models import *


def new_map(w, h, remove_rate=60):
    maze = MazeMST(w, h)
    maze.build()
    maze_map = maze.to_map()

    pool = list()
    for j, row in enumerate(maze_map[1:-1], 1):
        for i, wall in enumerate(row[1:-1], 1):
            if not wall:
                continue
                
            count = 0
            for dj in (-1, 0, 1):
                for di in (-1, 0, 1):
                    count += maze_map[j + dj][i + di]
            
            if count > 4:
                pool.append((i, j))

    shuffle(pool)
    l = min(max(0, remove_rate / 100), 1)
    print(l)
    for k in range(int(l * len(pool))):
        i, j = pool[k]
        maze_map[j][i] = False

    return maze_map


@game.bind_scene('home')
def home_scene(context):
    rect = (game.screen_w // 2 - 200, game.screen_h // 2 - 25, 400, 40)
    if gui_button(rect, "Продолжить как хост"):
        game.next_scene('create_session')

    rect = (game.screen_w // 2 - 200, game.screen_h // 2 + 25, 400, 40)
    if gui_button(rect, "Продолжить как клиент"):
        game.next_scene('connect_to_session')


@game.bind_scene('create_session')
def create_session_scene(context):
    context.clear()

    rect = (0, 0, 120, 40)
    if gui_button(rect, 'Назад'):
        game.prev_scene()

    rect = (game.screen_w // 2 - 100, game.screen_h // 2 - 25, 200, 40)
    if gui_button(rect, 'Создать'):
        # if game.create_host('localhost'):
        if game.create_host():
            game.next_scene('lobby')


@game.bind_scene('connect_to_session', buf=b'\x00'*23, edit_mode=False)
def connect_to_session_scene(context):
    context.clear()

    rect = (0, 0, 120, 40)
    if gui_button(rect, 'Назад'):
        game.prev_scene()

    t = 'Адрес хоста:'
    l = measure_text(t, game.font.baseSize)
    rect = (game.screen_w // 2 - 150 - l, game.screen_h // 2 - 25, 300, 40)
    gui_label(rect, t)

    # сам тексбокс
    rect = (game.screen_w // 2 - 150, game.screen_h // 2 - 25, 300, 40)
    buf = connect_to_session_scene.buf
    edit_mode = connect_to_session_scene.edit_mode
    if gui_text_box(rect, buf, len(buf) + 1, edit_mode):
        connect_to_session_scene.edit_mode = False

    # управление фокусом на текстбокс
    if is_mouse_button_pressed(MouseButton.MOUSE_BUTTON_LEFT):
        if check_collision_point_rec(get_mouse_position(), rect):
            connect_to_session_scene.edit_mode = True

    # подтверждения
    rect = (game.screen_w // 2 - 150, game.screen_h // 2 + 25, 300, 40)
    if gui_button(rect, 'Подключится'):
        raw_addres = buf.decode().strip('\x00')
        p = re.compile(r'^(localhost|((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)\.?\b){4}):\d{3,6}$')

        if p.fullmatch(raw_addres):
            ip, _, port = raw_addres.rpartition(':')
            if game.create_client((ip, int(port))):
                game.next_scene('lobby')


@game.bind_scene('lobby', timer=0,
                 w=ffi.new('int *', 10), wem=False,
                 h=ffi.new('int *', 10), hem=False,
                 r=ffi.new('int *', 40), rem=False,
                 l=ffi.new('int *', 180), lem=False)
def lobby_scene(context):
    # ожидание начала игры (а заодно и колим сервер)
    lobby_scene.timer += context['timedelta']
    if lobby_scene.timer >= 1/5:
        lobby_scene.timer = 0

        # обновляем локальную копию если она отличается от хранимой на сервере
        maze_map = game.client.load_map()
        if maze_map and context.get('maze_map') != maze_map:
            context['maze_map'] = maze_map
            gw, gh = len(maze_map[0]), len(maze_map)
            image = gen_image_color(int(gw), int(gh), WHITE)
            for j in range(gh):
                for i in range(gw):
                    if maze_map[j][i]:
                        image_draw_pixel(image, i, j, BLACK)
            context['maze_texture'] = load_texture_from_image(image)

        # идем играть если игра началась и мы в игре
        game_status = game.client.check_game()
        if game_status == GAME_STATUS_GOING:
            # проверка начала игры
            if game.client.in_game():
                game.next_scene('game')
                context['position'] = Vector2(*game.client.get_position())
                return

    # отрисовка текстуры лабиринта
    if context.get('maze_texture') is not None:
        gw, gh = game.screen_w - 280, game.screen_h - 70
        lw, lh = context['maze_texture'].width, context['maze_texture'].height
        scale = min(gw / lw, gh / lh)
        x = 10 + (gw - scale * lw) / 2
        y = 10 + (gh - scale * lh) / 2
        draw_texture_ex(context['maze_texture'], (x, y), 0, scale, WHITE)

    # панель настройки
    if game.host:
        rect = (game.screen_w - 110, 10, 100, 40)
        if gui_spinner(rect, 'Высота:', lobby_scene.w, 10, 50, lobby_scene.wem):
            lobby_scene.wem = False

        if is_mouse_button_pressed(MouseButton.MOUSE_BUTTON_LEFT):
            if check_collision_point_rec(get_mouse_position(), rect):
                lobby_scene.wem = True

        rect = (game.screen_w - 110, 60, 100, 40)
        if gui_spinner(rect, 'Высота:', lobby_scene.h, 10, 50, lobby_scene.hem):
            lobby_scene.hem = False

        if is_mouse_button_pressed(MouseButton.MOUSE_BUTTON_LEFT):
            if check_collision_point_rec(get_mouse_position(), rect):
                lobby_scene.hem = True
        
        rect = (game.screen_w - 110, 110, 100, 40)
        if gui_spinner(rect, 'Тупики %:', lobby_scene.r, 0, 100, lobby_scene.rem):
            lobby_scene.rem = False

        if is_mouse_button_pressed(MouseButton.MOUSE_BUTTON_LEFT):
            if check_collision_point_rec(get_mouse_position(), rect):
                lobby_scene.rem = True

        rect = (game.screen_w - 260, 160, 250, 40)
        if gui_button(rect, 'Пересоздать') or not context.get('maze_map'):
            maze_map = new_map(lobby_scene.w[0], lobby_scene.h[0], 100 - lobby_scene.r[0])
            game.host.dump_map(maze_map)

        rect = (game.screen_w - 110, 220, 100, 40)
        if gui_spinner(rect, 'Время с.:', lobby_scene.l, 60, 999, lobby_scene.lem):
            game.host.set_game_lenght(lobby_scene.l[0])
            lobby_scene.lem = False

        if is_mouse_button_pressed(MouseButton.MOUSE_BUTTON_LEFT):
            if check_collision_point_rec(get_mouse_position(), rect):
                lobby_scene.lem = True

    # чекбокс готовности
    rect = (game.screen_w / 2, game.screen_h - 50, 40, 40)
    a = bool(game.client.get_ready())
    b = gui_check_box(rect, 'Готов', a)
    if a != b:
        game.client.set_ready(b)

    if game.host:
        # кнопка начала игры
        rect = (game.screen_w - 210, game.screen_h - 50, 200, 40)
        if gui_button(rect, 'Начать'):
            if game.host.start_game():
                game.next_scene('game')
                context['position'] = Vector2(*game.client.get_position())

        # кнопка принта контекста сервера
        # from pprint import pprint
        # rect = (game.screen_w - 210, game.screen_h - 100, 200, 40)
        # if gui_button(rect, 'Контекст'):
        #     _json = eval(game.host.show_context())
        #     pprint(_json, indent=2, compact=True)

        rect = (game.screen_w - 250, game.screen_h - 140, 200, 40)
        gui_label(rect, 'Адрес лобби:')
        rect = (game.screen_w - 250, game.screen_h - 100, 200, 40)
        draw_text_ex(game.font, '%s:%s' % game.host_addr, rect[:2], 20, 0, GRAY)
        #gui_label(rect, '%s:%s' % game.host_addr)

    # кнопка выйти/закрыть лобби
    rect = (10, game.screen_h - 50, 300, 40)
    if gui_button(rect, 'Закрыть лобби' if game.host else 'Покинуть лобби'):
        game.client.leave_from_lobby()
        game.remove_host()
        game.prev_scene()


@game.bind_scene('game', timer=0, camera=Camera2D((game.screen_w / 2, game.screen_h / 2), (0, 0), 0, 40))
def game_scene(context):

    def role2cl(role):
        if role == PL_ROLE_HUNTER:
            return RED
        elif role == PL_ROLE_PREY:
            return LIME
        else:
            return LIGHTGRAY
        
    def draw_player(pos, role, me=False):
        draw_circle_v(pos, 0.3, DARKGRAY)
        if me:
            draw_circle_v(pos, 0.25, GOLD)
        draw_circle_v(pos, 0.2, role2cl(role))

    # опрос сервера N раз в секунду
    game_scene.timer += context['timedelta']
    if game_scene.timer >= 1 / SERVER_TICKRATE:
        game_scene.timer = 0
        
        game_status = game.client.check_game()
        # выводим победителей если игра закончилась
        if game_status == GAME_STATUS_FINISHED:
            game.swap_scene('finish_game')
        # обновляем данные если игра идет
        elif game_status == GAME_STATUS_GOING:
            v = context.get('position', Vector2(0, 0))
            context['other'] = game.client.set_position(v.x, v.y)
            context['role'] = game.client.get_role()
            t = game.client.get_game_timer()
            context['timer'] = f'{int(t // 60):0>2}:{int(t % 60):0>2}'
        # иначе отправляемся обратно в лобби
        else:
            game.prev_scene()
            return

    # нажатия клавиш
    dv=Vector2(0, 0)
    if is_key_down(KeyboardKey.KEY_W):
        dv.y -= 1
    if is_key_down(KeyboardKey.KEY_D):
        dv.x += 1
    if is_key_down(KeyboardKey.KEY_S):
        dv.y += 1
    if is_key_down(KeyboardKey.KEY_A):
        dv.x -= 1

    # охотник убивает жертву касанием
    if context.get('role') == 'hunter':
        a = context.get('position', Vector2(0, 0))
        for player in context.get('other', []):     
            if player['role'] != PL_ROLE_PREY:
                continue
            b = player['position']
            if vector_2distance_sqr(a, b) < 0.6 ** 2:
                game.client.attack()

    # перемещение персонажа
    speed = 3.25
    pos=context['position']
    px=pos.x + dv.x * context['timedelta'] * speed
    py=pos.y + dv.y * context['timedelta'] * speed
    # проверка коллизии
    maze_map=context.get('maze_map', [[]])
    mh, mw=len(maze_map), len(maze_map[0])
    if 0 < px  < mw and 0 < py < mh:
        if maze_map[int(py)][int(px)] == False:
            context['position']=Vector2(px, py)
    # камера следует за персонажем
    game_scene.camera.target=context['position']
    # режим камеры
    begin_mode_2d(game_scene.camera)
    # лабиринт
    draw_texture_ex(context['maze_texture'], (0, 0), 0, 1, WHITE)
    # другие игроки
    for player in context.get('other', []):
        pos = player.get('position', Vector2(0, 0))
        role = player.get('role')
        draw_player(pos, role)
    # игрок
    draw_player(context.get('position'), context.get('role'), me=True)
    end_mode_2d()
    # таймер
    t = context.get('timer', '00:00')
    draw_rectangle_v((0, 0), measure_text_ex(game.font, t, game.font.baseSize, 0), LIGHTGRAY)
    draw_text_ex(game.font, t, (0, 0), game.font.baseSize, 0, DARKGRAY)


@game.bind_scene('finish_game', timer=0)
def finish_game_scene(context):
    finish_game_scene.timer += context['timedelta']
    if finish_game_scene.timer >= 1/5:
        finish_game_scene.timer = 0
        context['winner'] = game.client.get_winner()
    
    t =''
    if context.get('winner') == PL_ROLE_HUNTER:
        t = 'Победил охотник'
    elif context.get('winner') == PL_ROLE_PREY:
        t = 'Победили выжившие'
       
    fs = game.font.baseSize * 2
    v = measure_text_ex(game.font, t, fs, 0)
    draw_text_ex(game.font, t, ((game.screen_w - v.x) / 2, (game.screen_h - v.y) / 2), fs, 0, DARKGRAY)

    rect = (game.screen_w / 2 - 205, game.screen_h * 2 / 3, 200, 40)
    if gui_button(rect, 'Выйти'):
        game.reset_scenes()
        game.next_scene('home')
        if game.host:
            game.remove_host()
        return

    rect = (game.screen_w / 2 + 5, game.screen_h * 2 / 3, 200, 40)
    if gui_button(rect, 'Продолжить'):
        game.prev_scene()
        return
