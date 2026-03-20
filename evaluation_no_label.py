import re
import os
import xml.etree.ElementTree as ET

shortest_paths_no_label = []
unreached = []

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


def evaluate_landmark_nodes(nodes):
    recorded_bounds = []
    no_label_count = 0
    for node in nodes:
        bounds = node.get('bounds')

        if bounds not in recorded_bounds:
            recorded_bounds.append(bounds)
            if node['text'] == 'None' or node['text'] is None:
                no_label_count += 1

    no_label_percentage = no_label_count / len(nodes)
    total_nodes = len(nodes)
    return no_label_count, total_nodes, no_label_percentage


def evaluate_nodes(nodes):
    recorded_bounds = []
    no_label_count = 0
    total_nodes = 0
    no_label_nodes = []
    excluded_keywords = [
        'RecyclerView',
        'ViewPager',
        'WebView',
        'LinearLayout',
        'RelativeLayout',
        'ListView',
        'FrameLayout'
    ]
    for node in nodes:
        node_class = node.get('node_class')
        if not any(keyword in node_class for keyword in excluded_keywords):
            bounds = node.get('bounds')
            if bounds[0][0] >= 0 and bounds[0][1] >= 0 and bounds[1][0] >= 0 and bounds[1][1] >= 0:
                bounds_available = True
            else:
                bounds_available = False

            if bounds not in recorded_bounds:
                recorded_bounds.append(bounds)
                if (node['text'] == 'None' or node['text'] is None) and bounds_available is True:
                    no_label_count += 1
                    no_label_nodes.append(node)
        total_nodes += 1

    no_label_percentage = no_label_count / total_nodes
    return no_label_count, total_nodes, no_label_percentage, no_label_nodes


def write_evaluation_to_file(file_path, nodes, no_label_count, total_nodes, no_label_percentage):
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(f'Percentage of None texts: {no_label_percentage:.4f}\n')
        file.write(f'No label count is :{no_label_count}, total_nodes is :{total_nodes}\n')
        for index, node in enumerate(nodes):
            if node['text'] == 'None':
                file.write(f"Node bounds: {node['bounds']}\n")
                file.write(f"Node text: {node['text']}\n")
                file.write("\n")
            if node['text'] is None:
                file.write(f"xml_file_path:{node['xml_file_path']}, action_bound: {node['action_bound']}\n")
                file.write(f"Node bounds: {node['bounds']}\n")
                file.write(f"Node text: {node['text']}\n")
                file.write("\n")


def run_no_label_landmark_evaluation(input_file, output_file):
    nodes = parse_landmark_file(input_file)
    no_label_count, total_nodes, no_label_percentage = evaluate_landmark_nodes(nodes)
    write_evaluation_to_file(output_file, nodes, no_label_count, total_nodes, no_label_percentage)


def run_no_label_path_evaluation(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    if not lines:
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write('Percentage: 0.0000\n')
            no_label_percentage = 0.0000
        return no_label_percentage
    nodes = parse_path_file(input_file)
    no_label_count, total_nodes, no_label_percentage, no_label_nodes = evaluate_nodes(nodes)
    write_evaluation_to_file(output_file, no_label_nodes, no_label_count, total_nodes, no_label_percentage)

    return no_label_percentage


def checked_node_no_label(file):
    with open(file, "r") as f:
        lines = f.readlines()
        for line in lines:
            path_nodes = line.strip().replace(' -> ', ' ').split()
            shortest_paths_no_label.append(path_nodes)


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


def unchecked_node_no_label(checked_node_path, folder_path, replace_file, output_file):
    replacements = read_replacements(replace_file)
    flat_checked_node_paths = set(sum(checked_node_path, []))

    for source_node, target_node in replacements.items():
        if target_node in flat_checked_node_paths:
            flat_checked_node_paths.add(source_node)

    total_focusable_count = 0
    total_text_none_count = 0
    recorded_bounds = []

    for filename in os.listdir(folder_path):
        if filename.endswith('.xml'):
            node_number = filename.split('--')[0].split('-')[1]

            if node_number not in flat_checked_node_paths:
                unreached.append(int(node_number))
                tree = ET.parse(os.path.join(folder_path, filename))
                root = tree.getroot()
                nodes_info = []
                focusable_count = 0
                text_none_count = 0
                excluded_keywords = [
                    'RecyclerView',
                    'ViewPager',
                    'WebView',
                    'LinearLayout',
                    'RelativeLayout',
                    'ViewGroup',
                    'ListView',
                    'FrameLayout'
                ]

                for elem in root.iter():
                    elem_class = elem.get('class')
                    if not any(keyword in elem_class for keyword in excluded_keywords):
                        # 首先获取一下节点的文字
                        if elem.get('text') or elem.get('content-desc'):
                            text = elem.get('text') or elem.get('content-desc')
                        else:
                            text = None
                        bounds = elem.get('bounds')
                        b_left, b_top, b_right, b_bottom = parse_root_bounds(bounds)
                        if b_left >= 0 and b_top >= 0 and b_right >= 0 and b_bottom >= 0:
                            bounds_available = True
                        else:
                            bounds_available = False
                        if (((elem.get('class') == 'android.widget.TextView' and
                              (elem.get('focusable') == 'true' or elem.get('clickable') == 'true' or elem.get('long-clickable') == 'true')) and
                             bounds_available is True) or
                                ((elem.get('class') != 'android.widget.TextView' and
                                  (elem.get('focusable') == 'true' or elem.get('clickable') == 'true' or elem.get('long-clickable') == 'true' or text is not None)) and
                                 bounds_available is True)):
                            focusable_count += 1

                            if bounds not in recorded_bounds:
                                recorded_bounds.append(bounds)
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
                                    nodes_info.append({'bounds': bounds, 'text': text})
                                    text_none_count += 1
                total_focusable_count += focusable_count
                total_text_none_count += text_none_count
                recorded_bounds = []
    total_no_text_percentage = (total_text_none_count / total_focusable_count) if total_focusable_count > 0 else 0
    unreached.sort()

    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(f'Percentage of nodes with: text as None in all unreached files is: {total_no_text_percentage:.4f}\n')

    return total_no_text_percentage




