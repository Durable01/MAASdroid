import os.path
import xml.etree.ElementTree as ET
import re


def parse_bounds(bounds_string):
    # Form: "[left,top][right,bottom]"
    b_left, b_top, b_right, b_bottom = map(int, bounds_string.strip('[]').replace('][', ',').split(','))
    return b_left, b_top, b_right, b_bottom

def is_adjacent(bound1, bound2):
    _, (_, bound1_bottom) = bound1
    (_, bound2_top), _ = bound2
    return bound1_bottom == bound2_top


def find_bounds_in_xml(xml_path, node_bounds):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    xml_bounds = []
    for elem in root.iter():
        if 'bounds' in elem.attrib:
            bounds_str = elem.attrib['bounds']
            bounds = parse_bounds(bounds_str)
            xml_bounds.append(((bounds[0], bounds[1]), (bounds[2], bounds[3])))

    return all(nb in xml_bounds for nb in node_bounds)


def get_bounds(landmark_file_input, xml_file_input, bounds_file_output):
    with open(xml_file_input, 'r', encoding='utf-8') as file:
        xml_paths = file.readlines()
    if not xml_paths:
        with open(bounds_file_output, 'w', encoding='utf-8') as file:
            file.write('')
        return
    xml_paths = [path.strip() for path in xml_paths]

    for xml_path in xml_paths:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        parent_node = root
        parent_node_bounds = parent_node.attrib.get('bounds')
        page_left, page_top, page_right, page_bottom = parse_bounds(parent_node_bounds)

        bounds_pattern = re.compile(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]')
        bounds = []
        for elem in root.iter():
            if 'bounds' in elem.attrib:
                bounds_str = elem.attrib['bounds']
                match = bounds_pattern.match(bounds_str)
                if match:
                    left = int(match.group(1))
                    top = int(match.group(2))
                    right = int(match.group(3))
                    bottom = int(match.group(4))
                    if left == page_left and right == page_right:
                        bounds.append(((left, top), (right, bottom)))

        bounds_chains = []
        for i in range(len(bounds)):
            for j in range(i + 1, len(bounds)):
                if is_adjacent(bounds[i], bounds[j]):
                    added_to_chain = False
                    for chain in bounds_chains:
                        if chain[-1] == bounds[i]:
                            chain.append(bounds[j])
                            added_to_chain = True
                            break
                        elif chain[0] == bounds[j]:
                            chain.insert(0, bounds[i])
                            added_to_chain = True
                            break
                    if not added_to_chain:
                        bounds_chains.append([bounds[i], bounds[j]])

        with open(landmark_file_input, 'r', encoding='utf-8') as lm_file:
            lm_data = lm_file.read()
        node_bounds = re.findall(r'Node bounds: \[(\d+),(\d+)\]\[(\d+),(\d+)\]', lm_data)
        node_bounds = [((int(x[0]), int(x[1])), (int(x[2]), int(x[3]))) for x in node_bounds]
        lm_bounds = re.findall(r'Landmark bounds:\[\(\((\d+), (\d+)\), \((\d+), (\d+)\)\)\]', lm_data)
        lm_bounds = [((int(x[0]), int(x[1])), (int(x[2]), int(x[3]))) for x in lm_bounds]

        if bounds_chains:
            longest_chain = max(bounds_chains, key=len)
            if longest_chain[0][0][1] > page_top:
                longest_chain.insert(0, ((0, 0), (page_right, longest_chain[0][0][1])))
            if longest_chain[-1][1][1] < page_bottom:
                longest_chain.append(((0, longest_chain[-1][1][1]), (page_right, page_bottom)))
        else:
            longest_chain = [((page_left, page_top), (page_right, page_bottom))]

        bounds_exist_in_xml = find_bounds_in_xml(xml_path, node_bounds)
        if bounds_exist_in_xml and lm_bounds:
            if longest_chain[-1] != lm_bounds[0]:
                longest_chain.extend(lm_bounds)

        with open(bounds_file_output, 'a', encoding='utf-8') as file:
            file.write(f'{xml_path}: {longest_chain}\n')
            file.write('\n')



