
from __future__ import annotations

import random
from typing import Literal, NewType


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
        cell_type: Literal['path', 'entrance', 'exit'] = 'path',
    ):
        self.mark = mark
        self.row = row
        self.col = col
        self.walls = walls
        self.cell_type = cell_type


Walls = NewType('Walls', dict[Literal[
    'top',
    'right',
    'bottom',
    'left'
], bool])

CellSet = NewType('CellSet', set[EllerMazeCell])

CellSets = NewType('CellSets', dict[int, CellSet])

MazeRow = NewType('MazeRow', list[EllerMazeCell])

ListMaze = NewType('Maze', list[MazeRow])


class EllerMaze:
    def __init__(self, size: int):
        self.size = min(max(size, 3), 20)
        self.list_maze: ListMaze = []
        self.sets: CellSets = {}

        self.build_maze()

    # Maze building

    def build_maze(self):
        row: MazeRow = []

        self.sets.clear()
        self.list_maze.clear()

        for i in range(self.size):
            row = self.next_row(
                row,
                'first' if i == 0 else 'last' if i == self.size - 1 else 'mid',
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
        size = self.size
        for i in range(size):
            cell = EllerMazeCell(0, i, i + 1, {
                'top': True,
                'right': i == size - 1,
                'bottom': False,
                'left': i == 0,
            })

            self.new_set(cell)

            row.append(cell)

        return row

    def update_row(self, row: MazeRow):
        size = self.size
        for i in range(size):
            cell = row[i]
            cell_set = self.sets[cell.mark]

            # Remove walls between cells
            cell.walls['right'] = i == size - 1
            cell.walls['left'] = i == 0

            # Move cell to unique set if bottom wall
            # Remove bottom wall
            if cell.walls['bottom']:
                cell_set.remove(cell)
                self.new_set(cell)
                cell.walls['bottom'] = False

        return row

    def finish_row(self, row: MazeRow):
        size = self.size
        skip_wall = False
        for i in range(size - 1):
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

        self.list_maze.append([EllerMazeCell(
            cell.row + 1,
            cell.col,
            cell.mark,
            dict(cell.walls),
        ) for cell in row])

        return row

    # Maze output

    def stringify_maze(self):
        stringified = ''

        mark_len = 0

        for row in self.list_maze:
            for cell in row:
                mark_len = max(len(str(cell.mark)), mark_len)

        for i in range(self.size):
            stringified += self.stringify_row(
                self.list_maze[i],
                mark_len,
                i == 0,
                i == self.size - 1
            )

        return stringified

    def stringify_row(
        self,
        row: MazeRow,
        mark_len: int,
        first: bool = False,
        last: bool = False
    ):
        stringified = ''

        if first:
            stringified = ' ' + ('_____' * self.size +
                                 '_' * mark_len * len(row))[:-1] + '\n'

        stringified += '|'
        for cell in row:
            stringified += '  '
            stringified += ' ' * mark_len
            stringified += '  |' if cell.walls['right'] else '   '
        stringified += '\n'

        stringified += '|'
        for cell in row:
            stringified += '  '
            stringified += f'{cell.mark:0{mark_len}}'
            # stringified += ' '
            stringified += '  |' if cell.walls['right'] else '   '
        stringified += '\n'

        stringified += '|'
        for cell in row:
            stringified += '__' if cell.walls['bottom'] else '  '
            stringified += ('_' if cell.walls['bottom'] else ' ') * mark_len
            stringified += '__|' if cell.walls['right'] and cell.walls['bottom'] else \
                '___' if last else \
                '__ ' if cell.walls['bottom'] else  \
                '  |' if cell.walls['right'] else '   '
        stringified += '\n'

        return stringified


def main():
    maze = EllerMaze(10)
    print(maze.stringify_maze())


if __name__ == '__main__':
    main()
