
from __future__ import annotations
from pathlib import Path

import random
from typing import Literal, NewType

import numpy as np
from PIL import Image


class EllerMazeCell:
    def __init__(
        self,
        row: int,
        col: int,
        mark: int = 0,
        walls: Walls = {
            'right': False,
            'bottom': False,
        },
    ):
        self.mark = mark
        self.row = row
        self.col = col
        self.walls = walls


Walls = NewType('Walls', dict[Literal[
    'right',
    'bottom',
], bool])

CellSet = NewType('CellSet', set[EllerMazeCell])

CellSets = NewType('CellSets', dict[int, CellSet])

MazeRow = NewType('MazeRow', list[EllerMazeCell])

ListMaze = NewType('ListMaze', list[list[dict[Literal[
    'right',
    'bottom',
], bool]]])


class EllerMaze:
    MIN_SIZE = 3
    MAX_SIZE = 20

    def __init__(self, height: int, width: int):
        self.height = min(max(height, self.MIN_SIZE), self.MAX_SIZE)
        self.width = min(max(width, self.MIN_SIZE), self.MAX_SIZE)

        self.list_maze: ListMaze = []
        self.sets: CellSets = {}

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
                'right': i == self.width - 1,
                'bottom': False,
            })

            self.new_set(cell)

            row.append(cell)

        return row

    def update_row(self, row: MazeRow):
        for i in range(self.width):
            cell = row[i]
            cell_set = self.sets[cell.mark]

            # Remove walls between cells
            cell.walls['right'] = i == self.width - 1

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
                continue

            # Randomly add walls from the right
            if random.randint(0, 99) >= 50:
                cell.walls['right'] = True
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

        self.list_maze.append([{
            'right': cell.walls['right'],
            'bottom': cell.walls['bottom'],
        } for cell in row])

        return row


# Maze output functions

def draw_maze(
    list_maze: ListMaze,
    scale: int = 50,
    filepath: str or Path = './maze.png'
):
    if (height := len(list_maze)) <= 0 \
            or (width := len(list_maze[0])) <= 0:
        return

    image_width = width * scale + 1
    image_height = height * scale + 1
    image_maze = np.full((image_height, image_width, 3), 255, dtype=np.uint8)

    # Maze Walls
    image_maze[0, :image_width] = [0, 0, 0]
    image_maze[image_height - 1, :image_width] = [0, 0, 0]
    image_maze[:image_height, 0] = [0, 0, 0]
    image_maze[:image_height, image_width - 1] = [0, 0, 0]

    # Cell walls
    for i in range(1, image_height - 1, scale):
        for j in range(1, image_width - 1, scale):
            cell = list_maze[(i - 1) // scale][(j - 1) // scale]

            if cell['right']:
                image_maze[i - 1: i + scale, j + scale - 1] = [0, 0, 0]

            if cell['bottom']:
                image_maze[i + scale - 1, j - 1: j + scale] = [0, 0, 0]

    Image.fromarray(image_maze).save(filepath)


def stringify_maze(list_maze: list[list[dict]]):
    str_maze = ''

    height = len(list_maze)

    for i in range(height):
        str_row = stringify_row(
            list_maze[i],
            i == 0,
            i == height - 1
        )
        str_maze += str_row + '\n'

    return str_maze


def stringify_row(
    row: dict[Literal['right', 'bottom', 'mark']: bool],
    first: bool = False,
    last: bool = False
):
    str_row = ''
    width = len(row)

    if first:
        str_row = ' ' + ('_____' * width)[:-1] + '\n'

    str_row += '|'
    for cell in row:
        str_row += '  '
        str_row += ' '
        str_row += '  |' if cell['right'] else '   '
    str_row += '\n'

    str_row += '|'
    for cell in row:
        str_row += '   '
        str_row += '  |' if cell['right'] else '   '
    str_row += '\n'

    str_row += '|'
    for cell in row:
        str_row += '__' if cell['bottom'] else '  '
        str_row += '_' if cell['bottom'] else ' '
        str_row += '__|' if cell['right'] and cell['bottom'] else \
            '___' if last else \
            '__ ' if cell['bottom'] else  \
            '  |' if cell['right'] else '   '

    return str_row


def main():
    maze = EllerMaze(10, 15)
    draw_maze(maze.list_maze)


if __name__ == '__main__':
    main()
