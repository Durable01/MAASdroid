import re
import os
import xml.etree.ElementTree as ET


def parse_landmark_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    nodes = []
    bounds = ""
    for line in lines:
        if "Node bounds:" in line:
            _, bounds = line.strip().split(": ")
        elif "Node text:" in line:
            _, text = line.strip().split(": ")
            nodes.append({"bounds": bounds, "text": text})

    return nodes


def parse_root_bounds(bounds_string):
    b_left, b_top, b_right, b_bottom = map(int, bounds_string.strip('[]').replace('][', ',').split(','))
    return b_left, b_top, b_right, b_bottom


def parse_path_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = file.read()

    pattern = r"For xml file ([^,]+), the path to action bound \[([^\]]+)\] is \[(.+?)\]\n"
    matches = re.findall(pattern, data)

    nodes = []
    for match in matches:
        xml_file_path, action_bound, bounds_text_pairs_str = match
        bounds_text_pairs = eval('[' + bounds_text_pairs_str + ']')
        if bounds_text_pairs:
            for bounds, text, node_class in bounds_text_pairs:
                node = {'xml_file_path': xml_file_path, 'action_bound': eval(action_bound), 'bounds': bounds, 'text': text, 'node_class': node_class}
                nodes.append(node)

    return nodes


def evaluate_nodes(nodes):
    image_count = 0
    no_label_image_count = 0
    image_node = []
    no_label_image_node = []

    for node in nodes:
        if node['bounds'][0][0] >= 0 and node['bounds'][0][1] >= 0 and node['bounds'][1][0] >= 0 and node['bounds'][1][1] >= 0:
            bounds_available = True
            # image_count += 1
        else:
            bounds_available = False
        # node['bounds'][0][0],node['bounds'][0][1],node['bounds'][1][0],node['bounds'][1][1]分别是左上右下
        if (node['node_class'] == 'android.widget.ImageView' or node['node_class'] == 'android.widget.ImageButton' or node[
            'node_class'] == 'android.widget.Image') and bounds_available is True:

            if (node['bounds'][1][0] - node['bounds'][0][0] >= 250) and (node['bounds'][1][1] - node['bounds'][0][1] >= 250):
                image_count += 1
                image_node.append(node)
                if node['text'] == 'None' or node['text'] is None:
                    no_label_image_count += 1
                    no_label_image_node.append(node)

    no_label_percentage = no_label_image_count / image_count if image_count > 0 else 0
    return no_label_image_node, no_label_image_count, image_count, no_label_percentage


def write_evaluation_to_file(file_path, no_label_image_node, no_label_image_count, image_count, no_label_percentage):
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(f'Percentage of No image label: {no_label_percentage:.4f}\n')
        file.write(f'Image count is :{image_count}\n')
        file.write(f'No label image count is :{no_label_image_count}\n')
        file.write(f'No label image node is :\n')
        for node in no_label_image_node:
            file.write(f'node{node}\n')


def run_image_no_label_path_evaluation(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    if not lines:
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write('Percentage: 0.0000\n')
            no_label_percentage = 0.0000
        return no_label_percentage
    nodes = parse_path_file(input_file)
    no_label_image_node, no_label_image_count, image_count, no_label_percentage = evaluate_nodes(nodes)
    write_evaluation_to_file(output_file, no_label_image_node, no_label_image_count, image_count, no_label_percentage)

    return no_label_percentage


shortest_paths_image = []
unreached = []


def checked_node_image(file):
    with open(file, "r") as f:
        lines = f.readlines()
        for line in lines:
            path_nodes = line.strip().replace(' -> ', ' ').split()
            shortest_paths_image.append(path_nodes)


def read_replacements(file_path):
    replacements = {}
    with open(file_path, 'r') as file:
        lines = file.readlines()
        for line in lines:
            pattern = r'step-(\d+)--g0a(\d+)-\d+\.xml->.*step-(\d+)--g0a(\d+)-\d+\.xml'
            matches = re.search(pattern, line)
            if matches:
                source = matches.group(1)
                target = matches.group(3)
            replacements[source] = target
    return replacements


def unchecked_node_image(checked_node_path, folder_path, replace_file, output_file):
    replacements = read_replacements(replace_file)
    flat_checked_node_paths = set(sum(checked_node_path, []))

    for source_node, target_node in replacements.items():
        if target_node in flat_checked_node_paths:
            flat_checked_node_paths.add(source_node)

    total_focus_image_count = 0
    total_image_no_label_count = 0

    for filename in os.listdir(folder_path):
        if filename.endswith('.xml'):
            node_number = filename.split('--')[0].split('-')[1]

            if node_number not in flat_checked_node_paths:
                unreached.append(int(node_number))
                tree = ET.parse(os.path.join(folder_path, filename))
                root = tree.getroot()

                focus_image_count = 0
                image_no_label_count = 0
                focus_image_node = []
                image_no_label_node = []

                for elem in root.iter():
                    if elem.get('text') or elem.get('content-desc'):
                        text = elem.get('text') or elem.get('content-desc')
                    else:
                        text = None
                    bounds_str = elem.get('bounds')
                    b_left, b_top, b_right, b_bottom = parse_root_bounds(bounds_str)
                    if b_bottom >= 0 and b_top >= 0 and b_left >= 0 and b_right >= 0:
                        bounds_available = True
                    else:
                        bounds_available = False
                    if (((elem.get('class') == 'android.widget.TextView' and
                          (elem.get('focusable') == 'true' or elem.get('clickable') == 'true' or elem.get('long-clickable') == 'true')) and
                         bounds_available is True) or
                            ((elem.get('class') != 'android.widget.TextView' and
                              (elem.get('focusable') == 'true' or elem.get('clickable') == 'true' or elem.get('long-clickable') == 'true' or text is not None)) and
                             bounds_available is True)):
                        left, top, right, bottom = map(int, elem.get('bounds').strip('[]').replace('][', ',').split(','))
                        if (right - left >= 500) and (bottom - top >= 500):
                            if elem.get('class') == 'android.widget.ImageView' or elem.get('class') == 'android.widget.ImageButton' or elem.get(
                                    'class') == 'android.widget.Image':
                                focus_image_count += 1
                                bounds = elem.get('bounds')
                                node_class = elem.get('class')
                                focus_image_node.append({'bounds': bounds, 'text': text, 'class': node_class})
                                if elem.get('text') or elem.get('content-desc'):
                                    text = elem.get('text') or elem.get('content-desc')
                                else:
                                    if len(list(elem)) > 0:
                                        child_texts = [child_node.get('text') or child_node.get('content-desc') for child_node in elem if child_node.get('text') or
                                                       child_node.get('content-desc')]
                                        if child_texts:
                                            text = '|'.join(child_texts)
                                        else:
                                            text = None
                                if text is None:
                                    image_no_label_node.append({'bounds': bounds, 'text': text, 'class': node_class})
                                    image_no_label_count += 1
                total_focus_image_count += focus_image_count
                total_image_no_label_count += image_no_label_count

    total_no_text_percentage = (total_image_no_label_count / total_focus_image_count) if total_focus_image_count > 0 else 0
    unreached.sort()

    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(f'The percentage of nodes with images without descriptions in all pages is :{total_no_text_percentage:.4f}\n')

    return total_no_text_percentage
