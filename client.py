"""Module with CLI"""

import argparse
import os.path

from maze import EllerMaze, \
    draw_maze, stringify_maze, solve_maze, \
    DEFAULT_SCALE, MIN_SCALE, MAX_SCALE


def main():
    """
    CLI function.
    """
    parser = argparse.ArgumentParser(
        prog='EllerMaze-A*',
        description="Program that builds Mazes using Eller's algorithm" +
        " and solves Mazes using A* algorithm",
    )
    parser.add_argument(
        'width', type=int,
        help='number of maze cells in width'
    )
    parser.add_argument(
        'height', type=int,
        help='number of maze cells in height'
    )

    parser.add_argument(
        '-p', '--print',
        action='store_true',
        help='print maze'
    )
    parser.add_argument('-w', '--write', help='text file to write maze')

    subparsers = parser.add_subparsers(dest='options')

    solve_parser = subparsers.add_parser('solve', help='solve maze')
    solve_parser.add_argument(
        'xs', nargs='?', type=int, default=EllerMaze.MIN_SIZE,
        help='where to start on x axes [default: 0]'
    )
    solve_parser.add_argument(
        'ys', nargs='?', type=int, default=EllerMaze.MIN_SIZE,
        help='where to start on y axes [default: 0]'
    )
    solve_parser.add_argument(
        'xe', nargs='?', type=int, default=EllerMaze.MAX_SIZE,
        help='where to end on x axes [default: width - 1]'
    )
    solve_parser.add_argument(
        'ye', nargs='?', type=int, default=EllerMaze.MAX_SIZE,
        help='where to end on y axes [default: height - 1]'
    )

    draw_group = parser.add_argument_group(
        'draw', description='draw maze as an image'
    )
    draw_group.add_argument(
        '-d', '--draw',
        action='store_true',
        help='draw maze as an image'
    )
    draw_group.add_argument(
        '-i', '--image',
        default='maze.png',
        help='file name to save maze and route as an image [default: maze.png]'
    )
    draw_group.add_argument(
        '-s', '--scale',
        type=int, default=DEFAULT_SCALE,
        help=f'number of pixels for one cell [default: {DEFAULT_SCALE}]'
    )
    draw_group.add_argument(
        '--gif', action='store_true',
        help='save route as gif'
    )

    args = parser.parse_args()
    run(args)


def run(args: argparse.Namespace):
    """
    Run program. Build, solve, draw or print maze.

    Args:
        args (argparse.Namespace): CLI arguments.
    """
    maze = EllerMaze(args.width, args.height)
    width, height = maze.width, maze.height

    def parse_coord(row: int, col: int):
        return (
            min(max(col, 0), height - 1),
            min(max(row, 0), width - 1),
        )

    route = None
    stringified = ''

    if args.print or args.write:
        stringified = stringify_maze(maze.list_maze)

    if args.options == 'solve':
        print('Solving...')
        route = solve_maze(
            maze.as_graph(),
            parse_coord(args.xs, args.ys),
            parse_coord(args.xe, args.ye)
        )

    if args.write:
        print('Writing...')
        with open(args.write, mode='w', encoding='UTF-8') as file:
            file.write(stringified)

    if args.draw:
        print('Drawing...')

        scale = min(max(args.scale, MIN_SCALE), MAX_SCALE)

        filepath, ext = os.path.splitext(args.image)
        ext = ext or '.png'

        img, frames = draw_maze(maze.list_maze, route, scale=scale)

        img.save(args.image)

        if frames:
            frames[-1].save(f'{filepath}-route{ext}')
            if args.gif:
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

    if route and not args.draw:
        print('Route:', ' > '.join((f'({x}, {y})' for x, y in route)))

    print('Completed!')


if __name__ == '__main__':
    main()
