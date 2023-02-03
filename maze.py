"""Module with Maze building, solving and drawing functions"""

from __future__ import annotations
import math
import queue

import random
from typing import Literal, NewType

import numpy as np
from PIL import Image, ImageColor


class EllerMazeCell:
    """
    Cell of EllerMaze.
    """

    def __init__(
        self,
        mark: int,
        walls: Walls,
    ):
        """
        Initialize maze cell.

        Args:
            mark (int): Number of set this cell belongs to.
            walls (Walls, optional): Walls surrounding cell.
        """
        self.mark = mark
        self.top = walls['top']
        self.right = walls['right']
        self.bottom = walls['bottom']
        self.left = walls['left']


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

GraphCell = NewType('RouteCell', tuple[int, int])

GraphMaze = NewType('GraphMaze', dict[GraphCell, set[GraphCell]])

Route = NewType('Route', list[GraphCell])


class EllerMaze:
    """
    Maze built with Eller's algorithm.
    """
    MIN_SIZE = 3
    MAX_SIZE = 100

    def __init__(self, width: int, height: int):
        """
        Initialize and build maze.

        Args:
            width (int): Number of cells in width.
            height (int): Number of cells in height.
        """
        self.height = min(max(height, self.MIN_SIZE), self.MAX_SIZE)
        self.width = min(max(width, self.MIN_SIZE), self.MAX_SIZE)

        self.list_maze: ListMaze = []
        self.sets: CellSets = {}

        self.build_maze()

    # Maze building

    def build_maze(self) -> ListMaze:
        """
        Build maze using Eller's algorithm.

        Returns:
            ListMaze: Maze as list of wall dictionaries.
        """
        row: MazeRow = []

        self.sets.clear()
        self.list_maze.clear()

        for i in range(self.height):
            row = self.build_next_row(
                row,
                'start' if i == 0 else
                'end' if i == self.height - 1 else
                'active',
            )

        return self.list_maze

    def new_set(self, cell: EllerMazeCell):
        """
        Initialize new set of cells.

        Args:
            cell (EllerMazeCell): Maze cell.
        """
        mark = 1

        while mark in self.sets and len(self.sets[mark]) > 0:
            mark += 1

        cell.mark = mark

        if mark not in self.sets.keys():
            self.sets[mark] = set()

        self.sets[mark].add(cell)

    def union_sets(
        self,
        mark: int,
        cell_set: CellSet,
    ):
        """
        Union cell sets. Update cell marks.

        Args:
            mark (int): Number of set that eats other set.
            cell_set (CellSet): Set that will be eaten to other set.
        """
        union_set = self.sets[mark].union(cell_set)

        cell_set.clear()

        for cell in union_set:
            cell.mark = mark

        self.sets[mark] = union_set

    def create_row(self) -> MazeRow:
        """
        Create first row of cells.

        Returns:
            MazeRow: First row of the maze.
        """
        row: MazeRow = []

        for i in range(self.width):
            cell = EllerMazeCell(0, {
                'top': True,
                'right': i == self.width - 1,
                'bottom': False,
                'left': i == 0,
            })

            self.new_set(cell)

            row.append(cell)

        return row

    def update_row(self, row: MazeRow):
        """
        Morph row into new row.

        Args:
            row (MazeRow): Row of cells.
        """
        for i in range(self.width):
            cell = row[i]
            cell_set = self.sets[cell.mark]

            # Add wall at the top
            cell.top = cell.bottom

            # Remove walls between cells
            cell.right = i == self.width - 1
            cell.left = i == 0

            # Move cell to unique set if it has bottom wall and remove it
            if cell.bottom:
                cell_set.remove(cell)
                self.new_set(cell)
                cell.bottom = False

    def finish_row(self, row: MazeRow):
        """
        Morph row of cells into last row of the maze.

        Args:
            row (MazeRow): Row of cells.
        """
        for i in range(self.width - 1):
            cell = row[i]
            next_cell = row[i + 1]

            cell_set = self.sets[cell.mark]

            # Place bottom walls
            cell.bottom = True
            next_cell.bottom = True

            # Remove walls between cells of different sets
            if next_cell not in cell_set:
                cell.right = False
                next_cell.left = False
                self.union_sets(cell.mark, self.sets[next_cell.mark])

    def add_right_walls(self, row: MazeRow):
        """
        Randomly add right walls to row.

        Args:
            row (MazeRow): First of middle row of maze.
        """
        for i in range(len(row) - 1):
            cell = row[i]
            next_cell = row[i + 1]

            cell_set = self.sets[cell.mark]

            # Divide cells of same set
            if next_cell in cell_set:
                cell.right = True
                next_cell.left = True
                continue

            # Randomly add walls from the right
            if random.randint(0, 99) >= 50:
                cell.right = True
                next_cell.left = True
                continue

            self.union_sets(cell.mark, self.sets[next_cell.mark])

    def add_bottom_walls(self, row: MazeRow):
        """
        Randomly add bottom walls to row.

        Args:
            row (MazeRow): First of middle row of maze.
        """
        for cell in row:
            cell_set = self.sets[cell.mark]

            # Randomly add walls at the bottom
            if random.randint(0, 99) >= 50:
                cell.bottom = True

            # Make sure that there is at least one path to the bottom of each set
            if len(cell_set) == 1 or \
                    all(cell.bottom for cell in cell_set):
                cell.bottom = False

    def build_next_row(
        self,
        row: MazeRow,
        phase: Literal['start', 'end', 'active'] = 'active'
    ) -> MazeRow:
        """
        Build next row of the maze on the basis of the previous row.

        Args:
            row (MazeRow): Previous row of cells.
            phase (Literal['start', 'end', 'active'], optional):
                Phase of maze construction. Defaults to 'active'.

        Returns:
            MazeRow: Built row.
        """
        if phase == 'start':
            row = self.create_row()

        if phase in ('active', 'end'):
            self.update_row(row)

        self.add_right_walls(row)
        self.add_bottom_walls(row)

        if phase == 'end':
            self.finish_row(row)

        self.list_maze.append([{
            'top': cell.top,
            'right': cell.right,
            'bottom': cell.bottom,
            'left': cell.left
        } for cell in row])

        return row

    def as_graph(self) -> GraphMaze:
        """
        Convert maze into graph.

        Returns:
            GraphMaze: Graph of the maze.
        """
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
                    coord_y, coord_x = i, j
                    match direction:
                        case 'top':
                            coord_y -= 1
                        case 'right':
                            coord_x += 1
                        case 'bottom':
                            coord_y += 1
                        case 'left':
                            coord_x -= 1
                    neighbors.add((coord_y, coord_x))

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


def maze_to_image(list_maze: ListMaze, scale: int = 50) -> MazeImage:
    """
    Convert maze to the array of pixels.

    Args:
        list_maze (ListMaze): List representation of the maze.
        scale (int, optional): Number of pixels for one cell. Defaults to 50.

    Returns:
        MazeImage: Maze as array of pixels.
    """
    height, width = len(list_maze), len(list_maze[0])

    image_width = width * scale + 1
    image_height = height * scale + 1

    maze_image: MazeImage = np.full(
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
            coord_y, coord_x = (i - 1) // scale, (j - 1) // scale
            cell = list_maze[coord_y][coord_x]

            if cell['right']:
                maze_image[i - 1: i + scale, j + scale - 1] = COLORS['wall']

            if cell['bottom']:
                maze_image[i + scale - 1, j - 1: j + scale] = COLORS['wall']

    return maze_image


def route_to_image(
    maze_image: MazeImage,
    current: GraphCell = (),
    visited: Route = (),
    scale: int = 50,
) -> MazeImage:
    """
    Convert maze solve route into array of pixels.

    Args:
        maze_image (MazeImage): Maze as array of pixels representation.
        current (RouteCell, optional): Current cell of the route. Defaults to ().
        visited (Route, optional): Visited cells of the route. Defaults to ().
        scale (int, optional): Number of pixels for one cell. Defaults to 50.

    Returns:
        MazeImage: Route as array of pixels.
    """
    def adapt_coord(coord):
        return coord * scale + 1

    def draw_cell(coord_y: int, coord_x: int, color: str):
        y_wall, x_wall = coord_y + scale - 1, coord_x + scale - 1

        maze_image[
            coord_y: y_wall,
            coord_x: x_wall
        ] = COLORS[color]

        if (maze_image[y_wall, coord_x] != COLORS['wall']).all():
            maze_image[y_wall, coord_x: x_wall] = COLORS[color]

        if (maze_image[coord_y, x_wall] != COLORS['wall']).all():
            maze_image[coord_y: y_wall, x_wall] = COLORS[color]

    # Current cell
    draw_cell(*map(adapt_coord, current), color='current')

    # Visited cells
    for cell in visited:
        draw_cell(*map(adapt_coord, cell), color='visited')

    return maze_image


def draw_maze(
    list_maze: ListMaze,
    route: Route = None,
    scale: int = 50,
) -> tuple[Image.Image, list[Image.Image]]:
    """
    Draw maze and route.

    Args:
        list_maze (ListMaze): List represenation of the maze.
        route (Route, optional): Maze solved route. Defaults to None.
        scale (int, optional): Number of pixels for one cell. Defaults to 50.

    Returns:
        tuple[Image.Image, list[Image.Image]]:: Maze image, route images
    """
    maze_image = maze_to_image(list_maze, scale=scale)
    img = Image.fromarray(maze_image)

    frames = None

    if route:
        frames: list[Image.Image] = []

        for idx, cell in enumerate(route):
            frames.append(Image.fromarray(
                route_to_image(maze_image, cell, route[:idx])
            ))

    return (img, frames)


def stringify_maze(list_maze: ListMaze) -> str:
    """
    Covert maze to string.

    Args:
        list_maze (ListMaze): List representation of the maze.

    Returns:
        str: Maze as string.
    """
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
    row: dict[Literal['right', 'bottom', 'mark'], bool],
    first: bool = False,
    last: bool = False
) -> str:
    """
    Covert maze row to string.

    Args:
        row (dict[Literal['right', 'bottom', 'mark'], bool]): Maze row.
        first (bool, optional): Row is first. Defaults to False.
        last (bool, optional): Row is last. Defaults to False.

    Returns:
        str: Row as string.
    """
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

def distance(first: GraphCell, second: GraphCell) -> float:
    """
    Heuristic function for estimating the distance between two cells.

    Args:
        first (tuple[int, int]): First cell.
        second (tuple[int, int]): Second cell.

    Returns:
        float: Estimated distance.
    """
    return math.sqrt(
        (second[1] - first[1])**2
        + (second[0] - first[0])**2
    )


def solve_maze(
    graph_maze: GraphMaze,
    entry: tuple[int, int],
    out: tuple[int, int],
) -> Route:
    """
    Solve maze using A* algorithm.

    Args:
        graph_maze (GraphMaze): Graph representation of the maze.
        entry (tuple[int, int]): Where to start.
        out (tuple[int, int]): Where to finish.

    Returns:
        Route: Solved route from entry to out.
    """
    walker = queue.PriorityQueue()
    walker.put((0, entry))

    came_from = {entry: None}
    score_of = {entry: 0}

    current = None

    while current != out and not walker.empty():
        priority, current = walker.get()

        for nieghbor in graph_maze[current]:
            new_score = score_of[current] + 1
            priority = distance(nieghbor, out) + new_score

            if nieghbor not in came_from or new_score < score_of[nieghbor]:
                walker.put((priority, nieghbor))

                score_of[nieghbor] = new_score
                came_from[nieghbor] = current

    route = []

    while current != entry:
        route.append(current)
        current = came_from[current]

    route.append(entry)
    route.reverse()

    return route
