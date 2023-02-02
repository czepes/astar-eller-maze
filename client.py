import argparse
import os.path

from maze import EllerMaze, draw_maze, stringify_maze, solve_maze


def main():
    parser = argparse.ArgumentParser(
        prog='EllerA*Maze',
        description="Program that builds Mazes using Eller's algorithm" +
        " and solves Mazes using A* algorithm",
    )
    parser.add_argument('width', help='Number of maze cells in width')
    parser.add_argument('height', help='Number of maze cells in height')
    parser.add_argument('-s', '--solve', action='store_false',
                        help='Solve maze and save found route as img')
    parser.add_argument('-d', '--draw', dest='image',
                        help='File name to save maze as image')
    parser.add_argument('-p', '--print', action='store_true',
                        help='Print maze as text')

    args = parser.parse_args()

    width, height = map(int, (args.width, args.height))

    maze = EllerMaze(width, height)
    route = None

    if args.solve:
        route = solve_maze(maze.as_graph(), (0, 0), (height - 1, width - 1))

    if args.print:
        print(stringify_maze(maze.list_maze))

    if args.image:
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

    return


if __name__ == '__main__':
    main()
