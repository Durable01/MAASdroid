import os.path
import re
from xml.etree import ElementTree as ET


def analyze_xml(xml_path):
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        parent_node = root

        def parse_bounds(bounds_str):
            # "[left,top][right,bottom]"
            left, top, right, bottom = map(int, bounds_str.strip('[]').replace('][', ',').split(','))
            return left, top, right, bottom

        bounds_str = parent_node.attrib.get('bounds')

        def find_matching_nodes(page_bounds):
            page_left, page_top, page_right, page_bottom = parse_bounds(page_bounds)
            page_bottom = 1794 # Non-full-screen needs to remove the system bar standing at the bottom
            upper_boundary_threshold = page_top + (7 * (page_bottom - page_top) // 8)
            matching_nodes = []
            processed_nodes = set()

            for node in root.iter():
                if node in processed_nodes:
                    continue

                node_bounds = node.attrib.get('bounds')
                if node_bounds:
                    _, node_top, _, node_bottom = parse_bounds(node_bounds)
                    if node_bottom >= page_bottom - 80 and node_top >= upper_boundary_threshold:
                        text = node.attrib.get('text', '') or node.attrib.get('content-desc', '')
                        if not text:
                            child_texts = []
                            for child_node in node:
                                if child_node.get('text') or child_node.get('content-desc'):
                                    child_texts.append(child_node.get('text') or child_node.get('content-desc'))
                                    processed_nodes.add(child_node)
                            text = '|'.join(child_texts)
                            matching_nodes.append({'bounds': node_bounds, 'text': text})
                            processed_nodes.add(node)
                            lm_bounds = [((page_left, node_top), (page_right, page_bottom))]
                        else:
                            matching_nodes.append({'bounds': node_bounds, 'text': text})
                            processed_nodes.add(node)
                            lm_bounds = [((page_left, node_top), (page_right, page_bottom))]
            additional_nodes = []
            for node in root.iter():
                if node in processed_nodes:
                    continue
                node_bounds = node.attrib.get('bounds')
                if node_bounds:
                    _, node_top, _, node_bottom = parse_bounds(node_bounds)
                    for match in matching_nodes:
                        _, match_top, _, match_bottom = parse_bounds(match['bounds'])
                        if node_top >= match_top and node_bottom <= match_bottom:
                            text = node.attrib.get('text', '') or node.attrib.get('content-desc', '')
                            if not text:
                                child_texts = []
                                for child_node in node:
                                    if child_node.get('text') or child_node.get('content-desc'):
                                        child_texts.append(child_node.get('text') or child_node.get('content-desc'))
                                        processed_nodes.add(child_node)
                                text = '|'.join(child_texts)
                            if {'bounds': node_bounds, 'text': text} not in matching_nodes:
                                additional_nodes.append({'bounds': node_bounds, 'text': text})

            matching_nodes.extend(additional_nodes)
            return matching_nodes, lm_bounds

        matching_nodes, lm_bounds = find_matching_nodes(bounds_str)

        if not matching_nodes and len(root) > 0:
            first_child = root[0]
            bounds_str = first_child.attrib.get('bounds')

            matching_nodes, lm_bounds = find_matching_nodes(bounds_str)

        return matching_nodes, lm_bounds

    except Exception as e:
        return f"Error: {e}"


def get_landmark(folder_path, output_file_path):
    files = os.listdir(folder_path)
    xml_files = [f for f in files if f.startswith('step-') and f.endswith('.xml')]

    min_number = float('inf')
    min_file = None
    for file in xml_files:
        match = re.search(r'step-(\d+)--', file)
        if match:
            number = int(match.group(1))
            if number < min_number:
                min_number = number
                min_file = file

    if min_file:
        xml_file_path = os.path.join(folder_path, min_file)
        matching_nodes, lm_bounds = analyze_xml(xml_file_path)

        with open(output_file_path, 'w', encoding='utf-8') as output_file:
            for node in matching_nodes:
                output_file.write(f"Node bounds: {node['bounds']}\n")
                output_file.write(f"Node text: {node['text']}\n")
                output_file.write("\n")
            output_file.write(f"Landmark bounds:{lm_bounds}")

