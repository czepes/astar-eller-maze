"""Module with Maze building, solving and drawing functions"""

from __future__ import annotations
import math
import queue

import random
from typing import Literal, NewType

import numpy as np
from PIL import Image, ImageColor


class EllerMazeCell:
    def __init__(
        self,
        row: int,
        col: int,
        mark: int = 0,
        walls: Walls = {
            'top': False,
            'right': False,
            'bottom': False,
            'left': False,
        },
    ):
        self.mark = mark
        self.row = row
        self.col = col
        self.walls = walls


Walls = NewType('Walls', dict[Literal[
    'top',
    'right',
    'bottom',
    'left',
], bool])

CellSet = NewType('CellSet', set[EllerMazeCell])

CellSets = NewType('CellSets', dict[int, CellSet])

MazeRow = NewType('MazeRow', list[EllerMazeCell])

ListMaze = NewType('ListMaze', list[list[dict[Literal[
    'top',
    'right',
    'bottom',
    'left',
], bool]]])

GraphMaze = NewType('GraphMaze', dict[tuple[int, int], set[tuple[int, int]]])


class EllerMaze:
    MIN_SIZE = 3
    MAX_SIZE = 100

    def __init__(self, width: int, height: int):
        self.height = min(max(height, self.MIN_SIZE), self.MAX_SIZE)
        self.width = min(max(width, self.MIN_SIZE), self.MAX_SIZE)

        self.list_maze: ListMaze = []
        self.sets: CellSets = {}

        self.maze: list[list[EllerMazeCell]] = []

        self.build_maze()

    # Maze building

    def build_maze(self):
        row: MazeRow = []

        self.sets.clear()
        self.list_maze.clear()

        for i in range(self.height):
            row = self.next_row(
                row,
                'first' if i == 0 else 'last' if i == self.height - 1 else 'mid',
            )

        return self.list_maze

    def new_set(self, cell: EllerMazeCell):
        mark = 1

        while mark in self.sets.keys() and len(self.sets[mark]) > 0:
            mark += 1

        cell.mark = mark

        if mark not in self.sets.keys():
            self.sets[mark] = set()

        self.sets[mark].add(cell)

    def add_to_set(
        self,
        mark: int,
        cell: EllerMazeCell,
    ):
        union_set = self.sets[mark].union(self.sets[cell.mark])

        self.sets[cell.mark].clear()

        for cell in union_set:
            cell.mark = mark

        self.sets[mark] = union_set

    def create_row(self, row: MazeRow):
        for i in range(self.width):
            cell = EllerMazeCell(0, i, i + 1, {
                'top': True,
                'right': i == self.width - 1,
                'bottom': False,
                'left': i == 0,
            })

            self.new_set(cell)

            row.append(cell)

        return row

    def update_row(self, row: MazeRow):
        for i in range(self.width):
            cell = row[i]
            cell_set = self.sets[cell.mark]

            cell.row += 1

            # Add wall at the top
            cell.walls['top'] = cell.walls['bottom']

            # Remove walls between cells
            cell.walls['right'] = i == self.width - 1
            cell.walls['left'] = i == 0

            # Move cell to unique set if bottom wall
            # Remove bottom wall
            if cell.walls['bottom']:
                cell_set.remove(cell)
                self.new_set(cell)
                cell.walls['bottom'] = False

        return row

    def finish_row(self, row: MazeRow):
        skip_wall = False
        for i in range(self.width - 1):
            cell = row[i]
            next_cell = row[i + 1]

            cell_set = self.sets[cell.mark]

            # Place bottom walls
            cell.walls['bottom'] = True
            next_cell.walls['bottom'] = True

            # Remove walls between cells of different sets
            if not skip_wall and next_cell not in cell_set:
                cell.walls['right'] = False
                next_cell.walls['left'] = False
                self.add_to_set(cell.mark, next_cell)
                skip_wall = True

            skip_wall = False

        return row

    def add_right_walls(self, row: MazeRow):
        for i in range(len(row) - 1):
            cell = row[i]
            next_cell = row[i + 1]

            cell_set = self.sets[cell.mark]

            # Divide cells of same set
            if next_cell in cell_set:
                cell.walls['right'] = True
                next_cell.walls['left'] = True
                continue

            # Randomly add walls from the right
            if random.randint(0, 99) >= 50:
                cell.walls['right'] = True
                next_cell.walls['left'] = True
                continue

            self.add_to_set(cell.mark, next_cell)

    def add_bottom_walls(self, row: MazeRow):
        bottom_path_on_set = False

        for i in range(len(row) - 1):
            cell = row[i]
            next_cell = row[i + 1]

            cell_set = self.sets[cell.mark]

            # Make sure that there is at least one path to the bottom of each set
            if len(cell_set) == 1 or (
                next_cell not in cell_set
                and not bottom_path_on_set
            ):
                cell.walls['bottom'] = False
                bottom_path_on_set = False
                continue

            # Randomly add walls at the bottom
            if random.randint(0, 99) >= 50:
                cell.walls['bottom'] = True
                continue

            if cell.walls['bottom']:
                bottom_path_on_set = True

    def next_row(
        self,
        row: MazeRow,
        phase: Literal['first', 'last', 'mid'] = 'mid'
    ) -> dict[EllerMazeCell]:
        if phase == 'first':
            row = self.create_row(row)

        if phase == 'mid' or phase == 'last':
            row = self.update_row(row)

        self.add_right_walls(row)
        self.add_bottom_walls(row)

        if phase == 'last':
            row = self.finish_row(row)

        self.list_maze.append([dict(cell.walls) for cell in row])
        self.maze.append([EllerMazeCell(
            cell.row,
            cell.col,
            cell.mark,
            dict(cell.walls)
        ) for cell in row])

        return row

    def as_graph(self):
        graph: GraphMaze = {}
        maze = self.list_maze
        for i in range(self.height):
            for j in range(self.width):
                cell = maze[i][j]
                neighbors = set()

                passable = []

                for direction, blocked in cell.items():
                    if blocked:
                        continue
                    passable.append(direction)

                for direction in passable:
                    y, x = i, j
                    match direction:
                        case 'top':
                            y -= 1
                        case 'right':
                            x += 1
                        case 'bottom':
                            y += 1
                        case 'left':
                            x -= 1
                    neighbors.add((y, x))

                graph[(i, j)] = neighbors

        return graph


# Maze output functions


COLORS = {
    'ground': ImageColor.getrgb('white'),
    'wall': ImageColor.getrgb('black'),
    'visited': ImageColor.getrgb('silver'),
    'current': ImageColor.getrgb('deeppink'),
}

MazeImage = NewType('MazeImage', np.ndarray[np.ndarray[
    np.ndarray[np.uint8]
]])


def maze_to_image(list_maze: ListMaze, scale: int = 50):
    height, width = len(list_maze), len(list_maze[0])

    image_width = width * scale + 1
    image_height = height * scale + 1

    maze_image = np.full(
        (image_height, image_width, 3),
        COLORS['ground'][0],
        dtype=np.uint8
    )

    # Maze Walls
    maze_image[0, :image_width] = COLORS['wall']
    maze_image[image_height - 1, :image_width] = COLORS['wall']
    maze_image[:image_height, 0] = COLORS['wall']
    maze_image[:image_height, image_width - 1] = COLORS['wall']

    # Cell walls
    for i in range(1, image_height - 1, scale):
        for j in range(1, image_width - 1, scale):
            y, x = (i - 1) // scale, (j - 1) // scale
            cell = list_maze[y][x]

            if cell['right']:
                maze_image[i - 1: i + scale, j + scale - 1] = COLORS['wall']

            if cell['bottom']:
                maze_image[i + scale - 1, j - 1: j + scale] = COLORS['wall']

    return maze_image


def draw_path(
    maze_image: MazeImage,
    current: tuple[int, int] = (),
    visited: set(tuple[int, int]) = (),
    scale: int = 50,
):
    def adapt_coord(coord): return coord * scale + 1

    def draw_cell(y: int, x: int, color: str):
        y_wall, x_wall = y + scale - 1, x + scale - 1

        maze_image[y: y + scale - 1, x: x + scale - 1] = COLORS[color]

        if (maze_image[y_wall, x] != COLORS['wall']).all():
            maze_image[y_wall, x: x_wall] = COLORS[color]

        if (maze_image[y, x_wall] != COLORS['wall']).all():
            maze_image[y: y_wall, x_wall] = COLORS[color]

    # Current cell
    draw_cell(*map(adapt_coord, current), color='current')

    # Visited cells
    for cell in visited:
        draw_cell(*map(adapt_coord, cell), color='visited')

    return Image.fromarray(maze_image)


def draw_maze(
    list_maze: ListMaze,
    path: list[tuple[int, int]] = None,
    scale: int = 50,
    filename: str = 'maze'
):
    maze_image = maze_to_image(list_maze, scale=scale)

    img = Image.fromarray(maze_image)
    img.save(f'{filename}.png')

    if path:
        frames = []

        for idx, cell in enumerate(path):
            path_img = draw_path(maze_image, cell, path[:idx])
            frames.append(path_img)

        path_img.save('path.png')

        frames[0].save(
            'path.gif',
            save_all=True,
            append_images=frames[1:],
            optimize=True,
            duration=100,
            loop=0
        )

    return img


def stringify_maze(list_maze: list[list[dict]]):
    str_maze = ''

    height = len(list_maze)

    for i in range(height):
        str_maze += stringify_row(
            list_maze[i],
            i == 0,
            i == height - 1
        )

    return str_maze


def stringify_row(
    row: dict[Literal['right', 'bottom', 'mark']: bool],
    first: bool = False,
    last: bool = False
):
    width = len(row)

    top = ' '
    mid = '|'
    bottom = '|'

    if first:
        top += ('____' * width)[:-1]

    for cell in row:
        mid += '   |' if cell['right'] else '    '

    for idx, cell in enumerate(row):
        bottom += '___|' if cell['right'] and cell['bottom'] else \
            '____' if last else \
            '____' if cell['bottom'] and idx < width - 1 and row[idx + 1]['bottom'] else \
            '___ ' if cell['bottom'] else  \
            '   |' if cell['right'] else '    '

    return '\n'.join((top, mid, bottom))


# Maze solving functions

def rate_distance(a: tuple[int, int], b: tuple[int, int]):
    x, y = b[1] - b[1], b[0] - a[0]
    return math.sqrt(x**2 + y**2)


def solve_maze(graph_maze: GraphMaze, entry: tuple[int, int], exit: tuple[int, int]):
    walker = queue.PriorityQueue()
    walker.put((0, entry))

    came_from = {entry: None}
    score_of = {entry: 0}

    current = None

    iterations = []

    while current != exit and not walker.empty():
        priority, current = walker.get()

        for nieghbor in graph_maze[current]:
            new_score = score_of[current] + 1
            priority = rate_distance(nieghbor, exit) + new_score

            if nieghbor not in came_from or new_score < score_of[nieghbor]:
                walker.put((priority, nieghbor))

                score_of[nieghbor] = new_score
                came_from[nieghbor] = current

    path = []
    current = exit

    while current != entry:
        path.append(current)
        current = came_from[current]

    path.append(entry)
    path.reverse()

    return path
