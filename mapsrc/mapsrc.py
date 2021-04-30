"""
This is the module that acts as an interface for the src code mapping modules.

The module provides the below function to run the mapping of src code at a given path:

"""

import os
import re
import typing


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
        'extensions': ['.js', '.jsx', '.ts', '.tsx', '.vue', '.py', '.txt', '.rst'],
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

    try:
        src_data = scan(root, config)
        draw(src_data, config)
        print()
        print('generation completed!')
    except:
        print()
        print('error - mapping failed')


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
    dirs_by_path = {
        get_path_from_common_root(file_dir, root): (
            file_dir,
            dir_names,
            [name for name in file_names if name not in exceptions]
        )
        for file_dir, dir_names, file_names in os.walk(root)
    }

    # todo: refactor to combine list comprehension with below loop:

    # get list of file paths, filtered for given extensions, or unfiltered if no
    # extensions are given:
    file_path_list = [
        (file_dir, file_name)
        for file_dir, _, file_names in dirs_by_path.values()
        for file_name in file_names
        if any(file_name.endswith(ext) for ext in extensions) or not extensions
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
        apply_patterns(line.strip(), config['patterns'], file)


def apply_patterns(txt: str, patterns: list, file: CodeFile) -> None:
    for pattern in patterns:
        field_to_add_to = pattern['on_match']['add_to']
        pattern_matches = apply_pattern(txt, pattern)
        file[file._fields.index(field_to_add_to)].extend(pattern_matches)


def apply_pattern(txt: str, pattern: dict) -> list:
    if pattern['type'] == 'regex':
        return process_match(txt, pattern)

    if is_string_pattern_match(txt, pattern):
        return process_match(txt, pattern['on_match'])

    return []


def is_string_pattern_match(txt: str, pattern: dict) -> bool:
    if pattern['type'] == 'contains' and pattern['query'] in txt:
        return True

    pattern_func = getattr(txt, pattern['type'])
    if pattern_func(pattern['query']):
        return True

    return False


def process_match(txt: str, on_match_config: dict) -> list:
    properties = extract_properties(txt, on_match_config['other_property_patterns'])
    processed_txt = txt
    if 'preprocessing_patterns' in on_match_config:
        processed_txt = apply_preprocessing(txt, on_match_config['preprocessing_patterns'])
    names_list = re.findall(on_match_config['extraction_regex'], processed_txt)
    return [{'param': name, **properties} for name in names_list]


def apply_preprocessing(txt: str, preprocessing_patterns: list) -> str:
    processed_txt = txt
    for pattern in preprocessing_patterns:
        match = re.search(pattern, processed_txt)
        if not match:
            return ''
        processed_txt = match.group(1)

    return processed_txt


def extract_properties(txt: str, property_patterns: list) -> dict:
    properties = {}
    for pattern in property_patterns:
        match = re.search(pattern['regex'], txt)
        if match:
            properties[pattern['property_name']] = match.group(1)

    return properties


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
        puml = generate_puml(src_data, diagram_config['mapping_scheme'])
        # todo: ensure this works in windows
        write_file(puml, os.path.join('./docs', 'src-map.puml'))


def generate_puml(src_data: dict, mapping_scheme: dict) -> str:
    puml = '@startuml\n'

    data_list_to_map = mapping_scheme['data_list_to_map']
    data_grouping_map = mapping_scheme['data_grouping_map']
    entity_name = mapping_scheme['entity_name']
    connect_by = mapping_scheme['connect_by']
    connect_path = mapping_scheme['connect_path']

    if src_data[data_list_to_map] and src_data[data_grouping_map]:
        # root_group_name = src_data[data_grouping_map][]
        root_name = src_data['starting_point']
        root_key = src_data['starting_point']
        puml_inits = generate_puml_initialization(root_name, root_key, src_data[data_grouping_map], '')
        puml += puml_inits
        puml_connections = ''
        for key, data_list in src_data[data_list_to_map].items():
            puml_connections += generate_puml_connections(data_list, key, connect_by, entity_name, connect_path)

        puml += puml_connections

    puml += '@enduml'
    return puml


def generate_puml_initialization(group_name: str, group_key: str, grouping_map: dict, indent: str) -> str:
    puml_str = '\n'
    puml_str += indent + 'namespace ' + pumlify_text(group_name) + ' {\n'
    new_indent = indent + '    '
    (key, subgroups, entities) = grouping_map[group_key]
    for entity in entities:
        # todo: remove extension rsplitting and add this logic to when grouping_map is first created in scan
        entity_name = pumlify_text(entity.rsplit('.', 1)[0])
        puml_str += new_indent + f'class {entity_name}\n'

    for subgroup_name in subgroups:
        subgroup_key = group_key + '/' + subgroup_name
        resolved_name = resolve_duplicates(subgroup_name, entities)
        puml_str += generate_puml_initialization(resolved_name, subgroup_key, grouping_map, new_indent)

    puml_str += indent + '}\n'
    return puml_str


def pumlify_text(txt: str) -> str:
    return txt.replace('-', '_')


def resolve_duplicates(subgroup_name: str, entities: list) -> list:
    for entity in entities:
        # todo: remove extension rsplitting and add this logic to when grouping_map is first created in scan
        if subgroup_name == entity.rsplit('.', 1)[0]:
            return subgroup_name + '_'

    return subgroup_name


def generate_puml_connections(data_list: list, curr_dir: str, connect_by: str, entity_name_field: str,
                              connection_path_field: str) -> str:
    puml_str = '\n'
    starting_chars = ['./', '..']
    for item in data_list:
        connection_list = item[item._fields.index(connect_by)]

        item_name = item[item._fields.index(entity_name_field)]
        item_puml_name = pumlify_text('.'.join(curr_dir.split('/')) + '.' + item_name)

        for connection in connection_list:
            connection_path = connection[connection_path_field]
            if any([connection_path.startswith(starting) for starting in starting_chars]):
                puml_str += item_puml_name + ' <-- ' + pumlify_text(
                    resolve_connection_to_puml(connection_path, curr_dir))
                puml_str += '\n'

    return puml_str


# todo: make this generic (string [x:] part as well)
def resolve_connection_to_puml(connection_path: str, curr_dir: str) -> str:
    parent_dir_indicator = '../'
    curr_dir_indicator = './'
    root_dir_indicator = '@'
    curr_dir_folder_list = curr_dir.split('/')

    if connection_path.startswith(curr_dir_indicator):
        connection_folder_list = connection_path[2:].split('/')

        merged_folder_list = curr_dir_folder_list + connection_folder_list
        return '.'.join(merged_folder_list)

    if connection_path.startswith(root_dir_indicator):
        connection_folder_list = connection_path[1:].split('/')

        root = curr_dir.split('/', 1)[0]
        return root + '.' + '.'.join(connection_folder_list)

    to_parent_count = connection_path.count(parent_dir_indicator)

    if len(curr_dir_folder_list) > to_parent_count > 0:
        connection_folder_list = connection_path[3 * to_parent_count:].split('/')
        merged_folder_list = curr_dir_folder_list[:-to_parent_count] + connection_folder_list
        return '.'.join(merged_folder_list)

    return connection_path.split('/')[-1]


def ensure_dir_path_exists(file_path: str):
    dir_path = file_path.rpartition('/')[0]
    if dir_path != '':
        os.makedirs(dir_path, exist_ok=True)


def write_file(txt: str, file_path: str):
    ensure_dir_path_exists(file_path)
    with open(file_path, 'w') as file:
        file.write(txt)
