import sys
import argparse

from application_model import ApplicationModel


def parse_args():
    parser = argparse.ArgumentParser(prog='doubtter')

    # parser.add_argument('-d', '--dictionary', type=str, default="./assets/ejdict.sqlite3", help='path to help file.')
    
    return parser.parse_args(sys.argv[1:])


def main(in_args):
    return ApplicationModel().main()

if __name__ == '__main__':
    exit(main(parse_args()))
