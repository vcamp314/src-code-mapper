def generate_puml(src_data: dict, mapping_scheme: dict) -> str:
    puml = '@startuml\n'

    data_list_to_map = mapping_scheme['data_list_to_map']
    data_grouping_map = mapping_scheme['data_grouping_map']

    if src_data[data_list_to_map] and src_data[data_grouping_map]:
        # root_group_name = src_data[data_grouping_map][]
        root_name = src_data['starting_point']
        root_key = src_data['starting_point']
        puml_inits = generate_puml_initialization(root_name, root_key, src_data[data_grouping_map], '')
        puml += puml_inits
        puml_connections = ''
        for key, data_list in src_data[data_list_to_map].items():
            puml_connections += generate_puml_connections(data_list, key, mapping_scheme)

        puml += puml_connections

    puml += '@enduml'
    return puml


def generate_puml_initialization(group_name: str, group_key: str, grouping_map: dict, indent: str) -> str:
    (key, subgroups, entities) = grouping_map.get(group_key, (group_key, [], []))
    if not subgroups and not entities:
        return ''

    puml_str = '\n'
    puml_str += indent + 'namespace ' + pumlify_text(group_name) + ' {\n'
    new_indent = indent + '    '
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


def resolve_duplicates(subgroup_name: str, entities: list) -> str:
    for entity in entities:
        # todo: remove extension rsplitting and add this logic to when grouping_map is first created in scan
        if subgroup_name == entity.rsplit('.', 1)[0]:
            return subgroup_name + '_'

    return subgroup_name


def generate_puml_connections(data_list: list, curr_dir: str, mapping_scheme: dict) -> str:
    puml_str = '\n'
    starting_chars = ['./', '..']
    entity_name_field = mapping_scheme['entity_name']
    connect_by = mapping_scheme['connect_by']
    connection_path_field = mapping_scheme['connect_path']
    include_non_code_imports = mapping_scheme.get('include_non_code_imports')

    for item in data_list:
        connection_list = item[item._fields.index(connect_by)]

        item_name = item[item._fields.index(entity_name_field)]
        item_puml_name = pumlify_text('.'.join(curr_dir.split('/')) + '.' + item_name)

        for connection in connection_list:
            connection_path = connection[connection_path_field]
            if is_connection_to_be_in_drawing(connection_path, starting_chars, include_non_code_imports):
                puml_line = item_puml_name + ' <-- ' + pumlify_text(
                    resolve_connection_to_puml(connection_path, curr_dir))
                puml_line += '\n'
                if puml_line not in puml_str:
                    puml_str += puml_line

    return puml_str


def is_connection_to_be_in_drawing(connection_path: str, starting_chars: list, include_non_code_imports: bool):
    if any([connection_path.startswith(starting) for starting in starting_chars]):
        return '.' not in connection_path.split('/')[-1] or include_non_code_imports
    return False


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
