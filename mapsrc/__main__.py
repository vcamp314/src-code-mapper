#!/usr/bin/env python3

import argparse
from .mapsrc import run_mapping
# todo: Add documentation explaining how to update the below


def apply_src_mapping(arg):
    run_mapping(arg.path)


def get_arguments():
    parser = argparse.ArgumentParser(
        description='sample arg parser implementation')
    parser.set_defaults(func=apply_src_mapping)
    parser.add_argument('path', help='path to source code folder to be mapped')

    return parser.parse_args()


def main():
    args = get_arguments()
    args.func(args)


if __name__ == '__main__':
    main()

