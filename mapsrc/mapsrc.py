"""
This is the module that acts as an interface for the src code mapping modules.

The module provides the below function to run the mapping of src code at a given path:

"""

import os


def run_mapping(path: str):
    """run mapping of src code at a given path location
    >>> run_mapping('./path/to/src')
    sample text

    :param path:
    :return: None
    """
    config = {
        'extensions': ['.js', '.jsx', '.ts', '.tsx', '.vue', '.py', '.txt', '.rst']
    }
    print(scan(path, config['extensions']))


def scan(path: str, extensions: list):
    """run scan of src files of a given list of extensions at a given path
    >>> scan('./path/to/src')
    sample text

    :param extensions: list of file extensions to be scanned
    :param path: path of src code
    :return: Dict - dictionary of results
    """

    # get list of file paths, filtered for given extensions, or unfiltered if no
    # extensions are given:
    file_list = [
        os.path.join(root, file)
        for root, _, files in os.walk(path)
        for file in files
        if any(file.endswith(ext) for ext in extensions) or not extensions
    ]

    return {'file_list': file_list}


#############################################################


def draw(src_map: str):
    """run mapping of src code at a given path location
    >>> draw('./path/to/src')
    sample text

    :param src_map:
    :return: None
    """
    print(src_map)
