import re


def apply_patterns(txt: str, patterns: list, data) -> None:
    for pattern in patterns:
        field_to_add_to = pattern['on_match']['add_to']
        pattern_matches = apply_pattern(txt, pattern)
        data[data._fields.index(field_to_add_to)].extend(pattern_matches)


def apply_pattern(txt: str, pattern: dict) -> list:
    if pattern['type'] == 'regex':
        if re.search(pattern['query'], txt):
            return process_match(txt, pattern['on_match'])

    elif is_string_pattern_match(txt, pattern):
        return process_match(txt, pattern['on_match'])

    return []


def is_string_pattern_match(txt: str, pattern: dict) -> bool:
    if pattern['type'] == 'contains':
        return pattern['query'] in txt

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
        value_to_set = pattern.get('value')

        if value_to_set is not None:
            properties[pattern['property_name']] = value_to_set
            return properties

        match = re.search(pattern['regex'], txt)
        if match:
            properties[pattern['property_name']] = match.group(1)

    return properties
