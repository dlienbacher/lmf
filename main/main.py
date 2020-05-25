import curses
import sys
import management


def main(stdscr):
    curses.curs_set(0)
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_RED)
    curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_GREEN)
    curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_BLUE)
    management.main_dialog(stdscr)


if __name__ == '__main__':
    try:
        curses.wrapper(main)
        sys.exit()

    except curses.error:
        print('There was an Curses Error in the Code!')
