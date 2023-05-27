import numpy as np
from random import shuffle
from abc import ABC, abstractmethod


# нахождение минимального островного дерева методом Крускала
def kruskal(n, graph):
    # корень множества
    def find(parent, i):
        if parent[i] == i:
            return i
        return find(parent, parent[i])

    # объединение двух множеств
    def union(parent, rank, x, y):
        x_root, y_root = find(parent, x), find(parent, y)

        # если ранг корня одного множества меньше, то он становится производным другого множества
        if rank[x_root] < rank[y_root]:
            parent[x_root] = y_root
        elif rank[x_root] > rank[y_root]:
            parent[y_root] = x_root
        else:
            # если же ранги равны, то одно множество становится подмножеством другого
            parent[y_root] = x_root
            # и его ранг увеличивается на 1
            rank[x_root] += 1

    # mst
    result = [[0] * n for _ in range(n)]

    # связи отсортированные по их весу
    edges = sorted([
        (graph[i][j], i, j)
        for i in range(n)
        for j in range(i + 1, n)
        if graph[i][j] != 0
    ])

    parent, rank = [i for i in range(n)], [0 for _ in range(n)]
    num_edges, i = 0, 0

    # ребер меньше кол-ва вершин более чем на 1
    while num_edges < n - 1:
        # берем следующее по весу ребро и увеличиваем счетчик ребер
        w, u, v = edges[i]
        i += 1

        # находим корни множеств
        x, y = find(parent, u), find(parent, v)

        # объединяем множества и добавляем ребро в mst если корни отличаются
        if x != y:
            num_edges += 1
            result[u][v] = w
            result[v][u] = w
            union(parent, rank, x, y)

    return result


# абстрактный класс
class Maze(ABC):

    data: np.ndarray
    w: int
    h: int

    def __init__(self, w, h) -> None:
        # лабиринт должен быть нечетного размера
        self.w = max(0, w - 1 + w % 2)
        self.h = max(0, h - 1 + h % 2)
        self.data = None

    # этот метод сораняет лабиринт в файл
    def save(self, file):
        with open(file, 'wb') as file:
            np.save(file, [self.h, self.w])
            np.save(file, self.data)

    # этот метод загружает лабиринт из файла
    @classmethod
    def load(cls, file):
        inst = cls(0, 0)
        with open(file, 'rb') as fp:
            inst.h, inst.w = np.load(fp)
            inst.data = np.load(fp)
        return inst

    def to_str(self, solution, wall, road, bread_crumbs):
        canvas = self.to_map()

        for y, row in enumerate(canvas):
            for x, cell in enumerate(row):
                if cell:
                    canvas[y][x] = wall
                else:
                    canvas[y][x] = road

        if solution:
            for x, y in solution:
                canvas[y][x] = bread_crumbs

        return '\n'.join(map(''.join, canvas))

    # этот метод должен трансформировать лабиринт в таблицу (двумерный массив)
    @abstractmethod
    def to_map(self) -> list[list[bool]]: ...

    # этот метод должен пересоздавать лабиринт
    @abstractmethod
    def build(self) -> None: ...

    # этот метод должен возвращать решение для лабиринта
    @abstractmethod
    def solve(self) -> list[tuple[int, int]]: ...

    # этот метод должен возвращать коодинаты начала лабиринта
    @abstractmethod
    def start(self) -> tuple[int, int]: ...

    # этот метод должен возвращать координаты конца лабиринта
    @abstractmethod
    def finish(self) -> tuple[int, int]: ...


class MazeDFS(Maze):
    def to_map(self) -> list[list[bool]]:
        return self.data.tolist()

    def build(self) -> None:
        def f(x, y):
            self.data[y][x] = False
            directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
            shuffle(directions)

            # в случайном порядке проверяем соседа сверху, снизу, слева, справа
            for dx, dy in directions:
                _x = x + dx * 2
                _y = y + dy * 2
                # если сосед существет и он стена
                if 0 < _x < self.w and 0 < _y < self.h and self.data[_y][_x]:
                    #  переходим на него
                    self.data[y + dy][x + dx] = False
                    f(_x, _y)

        self.data = np.ones((self.h, self.w), dtype=bool)
        return f(self.start()[0], self.start()[1])

    def solve(self) -> list[tuple[int, int]]:
        def f(x, y, path):
            path.append((x, y))

            if path[-1] == self.finish():
                return path

            # проверяем соседа сверху, снизу, слева, справа
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                _x = x + dx
                _y = y + dy
                # переходим на соседа если он существует, он не стена и его еще не посещали
                if 0 < _x < self.w and 0 < _y < self.h and not self.data[_y][_x] and (_x, _y) not in path:
                    new_path = f(_x, _y, path.copy())
                    # если дошли до финиша, завершаем поиск
                    if new_path:
                        return new_path

        return f(self.start()[0], self.start()[1], [])

    def start(self) -> tuple[int, int]:
        return 1, 1

    def finish(self) -> tuple[int, int]:
        return self.w - 2, self.h - 2


class MazeMST(Maze):
    def mn(self):
        ''' Вернет количество узлов в лабиринте по вертикали и горизонтали '''
        return self.w // 2, self.h // 2

    def node_inx(self, x, y):
        ''' Переводит координаты узла в его порядковый номер в матрице смежности '''
        w = self.w // 2
        return x + y * w

    def node_xy(self, idx):
        ''' Переводит порядковый номер узла в матрице смежности в его координаты '''
        w = self.w // 2
        return idx % w, idx // w

    def to_map(self) -> list[list[bool]]:
        m, n = self.mn()
        s = m * n

        # перенос из формата матрицы смежности в формат таблицы
        data = np.ones((self.h, self.w), dtype=bool)

        # берем каждый i-ый узел
        for i in range(s):
            x, y = self.node_xy(i)

            # ищем его соседий сверху, снизу, справа и слева
            for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                _x, _y = x + dx, y + dy

                # если сосед существует
                if 0 <= _x < m and 0 <= _y < n:
                    j = self.node_inx(_x, _y)

                    # и с ним есть связь
                    if self.data[i][j] or self.data[j][i]:
                        ox = 1 + x * 2
                        oy = 1 + y * 2
                        # проводим коридор
                        data[oy][ox] = False
                        data[oy + dy][ox + dx] = False

        return data.tolist()

    def build(self) -> None:
        m, n = self.mn()
        s = m * n

        # матрицы смежности
        mtx = np.zeros((s, s))

        # проходимя по каждому узлу
        for i in range(s):
            x, y = self.node_xy(i)

            # берем его соседа сверху, снизу, слева и справа
            for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                _x, _y = x + dx, y + dy

                # и если сосед существует
                if 0 <= _x < m and 0 <= _y < n:
                    j = self.node_inx(_x, _y)

                    # проводим связь к нему со случайным весом
                    if mtx[i][j] == 0 or mtx[j][i] == 0:
                        mtx[i][j] = np.random.randint(1, 100)

        # ищем MTS методом Крускала
        self.data = kruskal(s, mtx)

    def solve(self) -> list[tuple[int, int]]:
        m, n = self.mn()

        def f(x, y, path):
            path.append((x, y))

            if path[-1] == self.finish():
                return path

            i = self.node_inx(x, y)

            # ищем все узлы, связанные с i-ым
            for j in [j for j, w in enumerate(self.data[i]) if w != 0 and i != j]:
                _x, _y = self.node_xy(j)

                # преходим к j-ому узлу еще не были на нем
                if 0 <= _x < m and 0 <= _y < n and (_x, _y) not in path:
                    new_path = f(_x, _y, path.copy())

                    # если дошли до финиша, то завершаем поиск
                    if new_path:
                        return new_path

        # рекурсивный проход по mst
        solution = f(self.start()[0], self.start()[1], [])

        # перевод координат узлов в координаты клеток таблицы
        fixed_solution = [(1 + x * 2, 1 + y * 2) for x, y in solution]

        # добавление координат коридоров (кол-во точек увеличится до 2N - 1)
        solution.clear()
        for i in range(1, len(fixed_solution)):
            # имеет точку №1 и №2
            x0, y0 = fixed_solution[i - 1]
            x1, y1 = fixed_solution[i]
            # точку №3 нужно поставить ровно между ними
            dx = (x1 - x0) // 2
            dy = (y1 - y0) // 2
            solution += [(x0, y0), (x0 + dx, y0 + dy)]
        solution.append(fixed_solution[-1])

        return solution

    def start(self) -> tuple[int, int]:
        return 0, 0

    def finish(self) -> tuple[int, int]:
        return self.mn()[0] - 1,  self.mn()[1] - 1


# maze = MazeDFS(30, 30)
# maze.build()
# print(maze.to_str(maze.solve(), '██', '  ', '. '))

# print()

# maze = MazeMST(30, 30)
# maze.build()
# print(maze.to_str(maze.solve(), '██', '  ', '. '))
