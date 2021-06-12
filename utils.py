from getpass import getpass
from sys import exit


def inputter(text: str, min_int: int=None, max_int: int=None, yesno=False):
    text = text + '\n>>> '
    _inp = input(text).lower()

    if min_int and max_int:
        while not _inp.isdecimal() or not int(_inp) >= min_int or not int(_inp) <= max_int:
            print()
            _inp = input(text)

        print()

        return int(_inp) - 1

    elif yesno:
        if _inp in ['да', 'д', 'yes', 'y']:
            return True

        return False


def _exit():
    print('\nНажмите ENTER, чтобы закрыть программу!')
    getpass('')
    exit(1)
