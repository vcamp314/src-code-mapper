"""
This is the module that acts as an interface for the src code mapping modules.

The module provides the below function to run the mapping of src code at a given path:

"""

import os
import typing

from .parse import parse
from .pumlify import pumlify


# todo: change to extendible File class
class CodeFile(typing.NamedTuple):
    imports: list
    exports: list
    local_params: list
    blocks: list
    dir: str
    name: str
    extension: str


# todo: implement drawing using the below:
class MapNode(typing.NamedTuple):
    child_node_keys: list
    item_keys: list


def run_mapping(path: str):
    """run mapping of src code at a given path location
    >>> run_mapping('./path/to/src')
    sample text

    :param path:
    :return: None
    """
    config = {
        'extensions': ['.js', '.jsx', '.ts', '.tsx', '.vue'],
        'exceptions': [
            'react-app-env.d.ts',
            'reportWebVitals.ts',
            'setupTests.ts'
        ],
        'patterns': [
            {
                'type': 'startswith',
                'query': 'import',
                'on_match': {
                    'add_to': 'imports',
                    'extraction_regex': r'import (\w+)',
                    'other_property_patterns': [
                        {
                            'property_name': 'from_path',
                            'regex': r'from\s*?(?:"|\')(.*)(?:"|\')'
                        }
                    ]
                }
            },
            {
                'type': 'startswith',
                'query': 'import',
                'on_match': {
                    'add_to': 'imports',
                    'extraction_regex': r'(\w+)',
                    'preprocessing_patterns': [
                        '{(.*)}'
                    ],
                    'other_property_patterns': [
                        {
                            'property_name': 'from_path',
                            'regex': r'from\s*?(?:"|\')(.*)(?:"|\')'
                        }
                    ]
                }
            }
        ],
        'diagrams': [
            {
                'name': 'dependency-diagram',
                'mapping_scheme': {
                    'data_list_to_map': 'files_by_path',
                    'data_grouping_map': 'dirs_by_path',
                    'entity_types': [
                        {
                            'name': 'file_name',
                            'type': 'class',
                            'match_by': {
                                'field': 'extension',
                                'value': 'tsx'
                            }
                        }
                    ],
                    'entity_name': 'name',
                    'connect_by': 'imports',
                    'connect_path': 'from_path'

                }
            }
        ]
    }
    print('generating mapping diagram...')
    print()
    root = path[:-1] if path.endswith('/') else path

    # try:
    src_data = scan(root, config)
    draw(src_data, config)
    print()
    print('generation completed!')
    # except:
    #     print()
    #     print('error - mapping failed')


def scan(root: str, config: dict) -> dict:
    """run scan of src files of a given list of extensions at a given path
    >>> scan('./path/to/src')
    sample text

    :param config: configuration data for scan
    :param root: path of src code
    :return: Dict - dictionary of results
    """

    extensions = config['extensions']
    exceptions = config['exceptions']

    # get list of directories, with their contents (files and sub-directories)
    dirs_by_path = {
        get_path_from_common_root(dir_path, root): (
            dir_path,
            dir_names,
            [name for name in file_names if is_valid_file_name(name, config)]
        )
        for dir_path, dir_names, file_names in os.walk(root)
    }

    dirs_by_path = {key: value for key, value in dirs_by_path.items() if value[1] or value[2]}

    # get list of file paths
    file_path_list = [
        (file_dir, file_name)
        for file_dir, _, file_names in dirs_by_path.values()
        for file_name in file_names
    ]

    files_by_path = {}
    # todo: put below loop contents into function, used in above list comprehension
    for file_dir, file_name_with_extension in file_path_list:
        # todo: remove code file definition from here to allow this to be reused for non-code related files
        # todo: refactor to use inheritable File class instead of named tuple, to be reused for non-code files

        if file_name_with_extension in exceptions:
            continue

        file = CodeFile(
            imports=[],
            exports=[],
            local_params=[],
            blocks=[],
            dir=file_dir,
            name=file_name_with_extension.rsplit('.', 1)[0],
            extension=file_name_with_extension.rsplit('.', 1)[1]
        )

        parse_file(file, config)
        file_no_dupes = remove_duplicate_entries(file)

        dir_key = get_path_from_common_root(file_dir, root)
        if dir_key not in files_by_path:
            files_by_path[dir_key] = []

        files_by_path[dir_key].append(file_no_dupes)

    return {'dirs_by_path': dirs_by_path, 'files_by_path': files_by_path,
            'starting_point': get_path_from_common_root(root, root)}


def get_path_from_common_root(path: str, common_root: str) -> str:
    return path.replace(common_root.rsplit('/', 1)[0] + '/', '')


# for detecting if a file should not be mapped, either because its an exception
# or not in the acceptable extension list, if one was given
def is_valid_file_name(file_name: str, config: dict) -> bool:
    return file_name not in config['exceptions']\
           and (any(file_name.endswith(ext) for ext in config['extensions']) or not config['extensions']) \
           and '.test.' not in file_name


def remove_duplicate_entries(file: CodeFile) -> CodeFile:
    return CodeFile(
        imports=[dict(t) for t in {tuple(item.items()) for item in file.imports}],
        exports=[dict(t) for t in {tuple(item.items()) for item in file.exports}],
        local_params=[dict(t) for t in {tuple(item.items()) for item in file.local_params}],
        blocks=[dict(t) for t in {tuple(item.items()) for item in file.blocks}],
        dir=file.dir,
        name=file.name,
        extension=file.extension
    )


def parse_file(file: CodeFile, config: dict):
    """parse text based on config, return dictionary of results
    >>> parse_file('./path/to/src')
    sample text

    :param config: dictionary configuration with parsing scheme
    :param file: virtual file object to be populated by parsing physical file
    """
    path = os.path.join(file.dir, f'{file.name}.{file.extension}')
    print(path)
    file_gen = (line for line in open(path))
    for line in file_gen:
        parse.apply_patterns(line.strip(), config['patterns'], file)


#############################################################


def draw(src_data: dict, config: dict):
    """run mapping of src code at a given path location
    >>> draw('./path/to/src')
    sample text

    :param src_data:
    :return: None
    """
    puml = '@startuml'

    puml_inits = ''
    puml_connections = ''
    for diagram_config in config['diagrams']:
        puml = pumlify.generate_puml(src_data, diagram_config['mapping_scheme'])
        # todo: ensure this works in windows
        write_file(puml, os.path.join('./docs', 'src-map.puml'))


def ensure_dir_path_exists(file_path: str):
    dir_path = file_path.rpartition('/')[0]
    if dir_path != '':
        os.makedirs(dir_path, exist_ok=True)


def write_file(txt: str, file_path: str):
    ensure_dir_path_exists(file_path)
    with open(file_path, 'w') as file:
        file.write(txt)
