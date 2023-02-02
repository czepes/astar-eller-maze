"""Module with CLI"""

import argparse
import os.path

from maze import EllerMaze, draw_maze, stringify_maze, solve_maze


def main():
    """
    CLI function.
    """
    parser = argparse.ArgumentParser(
        prog='EllerMaze-A*',
        description="Program that builds Mazes using Eller's algorithm" +
        " and solves Mazes using A* algorithm",
    )
    parser.add_argument('width', help='number of maze cells in width')
    parser.add_argument('height', help='number of maze cells in height')
    parser.add_argument('-s', '--solve', action='store_false',
                        help='do not solve maze')
    parser.add_argument('-d', '--draw', dest='image',
                        help='file name to save maze and route as an image')
    parser.add_argument('-p', '--print', action='store_true',
                        help='print maze')
    parser.add_argument('-w', '--write', help='text file to write maze')

    args = parser.parse_args()

    width, height = map(int, (args.width, args.height))

    maze = EllerMaze(width, height)
    width, height = maze.width, maze.height

    route = None

    stringified = stringify_maze(maze.list_maze)

    if args.solve:
        print('Solving...')
        route = solve_maze(maze.as_graph(), (0, 0), (height - 1, width - 1))

    if args.write:
        print('Writing...')
        with open(args.write, mode='w', encoding='UTF-8') as file:
            file.write(stringified)

    if args.image:
        print('Drawing...')
        filepath, ext = os.path.splitext(args.image)

        img, frames = draw_maze(maze.list_maze, route)

        img.save(args.image)

        if frames:
            frames[-1].save(f'{filepath}-route{ext}')
            frames[0].save(
                f'{filepath}-route.gif',
                save_all=True,
                append_images=frames[1:],
                optimize=True,
                duration=100,
                loop=0
            )

    if args.print:
        print(stringified)

    if route and not args.image:
        print('Route:')
        print(' > '.join((f'({x}, {y})' for x, y in route)))

    print('Completed!')


if __name__ == '__main__':
    main()
