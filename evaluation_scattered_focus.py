import os
import re
import ast
import xml.etree.ElementTree as ET

def parse_bounds_str(bound_str):
    bounds = re.findall('\d+', bound_str)
    bounds = [tuple(map(int, bounds[i:i + 2])) for i in range(0, len(bounds), 2)]
    return bounds


def parse_bounds(bound_str):
    bounds = list(map(int, re.findall(r'\d+', bound_str)))
    return tuple(bounds)


def parse_root_bounds(bounds_string):
    b_left, b_top, b_right, b_bottom = map(int, bounds_string.strip('[]').replace('][', ',').split(','))
    return b_left, b_top, b_right, b_bottom


def bounds_to_str(bounds):
    return f"[{bounds[0][0]},{bounds[0][1]}][{bounds[1][0]},{bounds[1][1]}]"


def check_bounds_inclusion_in_index(bound1, bound2):
    bound1_left, bound1_top, bound1_right, bound1_bottom = parse_bounds(bound1)
    bound2_left, bound2_top, bound2_right, bound2_bottom = parse_bounds(bound2)
    contains_bound1 = (bound2_left <= bound1_left <= bound2_right and
                       bound2_left <= bound1_right <= bound2_right and
                       bound2_top <= bound1_top <= bound2_bottom and
                       bound2_top <= bound1_bottom <= bound2_bottom)

    return not contains_bound1


def check_bounds_inclusion(bound1, bound2):
    (bound1_left, bound1_top), (bound1_right, bound1_bottom) = bound1
    (bound2_left, bound2_top), (bound2_right, bound2_bottom) = bound2
    return bound1_left >= bound2_left and bound1_right <= bound2_right and bound1_top >= bound2_top and bound1_bottom <= bound2_bottom


def count_inversions(focusable_children, xml_file, bound, output_file):
    inversions = 0
    right_num = 0
    children_list = list(focusable_children)
    for i in range(len(focusable_children)):
        for j in range(i + 1, len(focusable_children)):
            after_id_i = focusable_children[i].get('AfterId', 'null')
            before_id_j = focusable_children[j].get('BeforeId', 'null')
            if after_id_i != 'null' and before_id_j != 'null':
                after_bounds_i = focusable_children[i].get('AfterBounds')
                before_bounds_j = focusable_children[j].get('BeforeBounds')

                if after_bounds_i == before_bounds_j:
                    right_num += 1
                    continue
            if check_bounds_inclusion_in_index(focusable_children[j].get('bounds'), focusable_children[i].get('bounds')):
                left_i, top_i, right_i, bottom_i = parse_bounds(focusable_children[i].get('bounds'))
                left_j, top_j, right_j, bottom_j = parse_bounds(focusable_children[j].get('bounds'))

                if ((bottom_j + top_j) / 2 >= (bottom_i + top_i) / 2) and left_j >= (left_i + right_i) / 2:
                    right_num += 1
                elif ((bottom_i + top_i) / 2) - ((bottom_j + top_j) / 2) <= 60 and left_j >= (left_i + right_i) / 2:
                    right_num += 1
                elif top_j >= (bottom_i + top_i) / 2:
                    right_num += 1
                elif left_j <= left_i <= right_j <= right_i and top_j >= (bottom_i + top_i) / 2 and bottom_j >= bottom_i:
                    right_num += 1
                else:
                    inversions += 1
                    write_inversion_info(output_file, xml_file, bound, children_list[i].get('bounds'), children_list[j].get('bounds'))

    total_num = right_num + inversions
    return inversions, total_num


def count_inversions_unchecked(focusable_children, xml_file, output_file):
    inversions = 0
    right_num = 0
    for i in range(len(focusable_children)):
        for j in range(i + 1, len(focusable_children)):
            after_id_i = focusable_children[i].get('AfterId', 'null')
            before_id_j = focusable_children[j].get('BeforeId', 'null')
            if after_id_i != 'null' and before_id_j != 'null':
                after_bounds_i = focusable_children[i].get('AfterBounds')
                before_bounds_j = focusable_children[j].get('BeforeBounds')

                if after_bounds_i == before_bounds_j:
                    right_num += 1
                    continue
            if check_bounds_inclusion_in_index(focusable_children[j].get('bounds'), focusable_children[i].get('bounds')):
                left_i, top_i, right_i, bottom_i = parse_bounds(focusable_children[i].get('bounds'))
                left_j, top_j, right_j, bottom_j = parse_bounds(focusable_children[j].get('bounds'))
                # 右侧
                if ((bottom_j + top_j) / 2 >= (bottom_i + top_i) / 2) and left_j >= (left_i + right_i) / 2:
                    right_num += 1
                # 右侧偏上
                elif ((bottom_i + top_i) / 2) - ((bottom_j + top_j) / 2) <= 60 and left_j >= (left_i + right_i) / 2:
                    right_num += 1
                # 下侧包括左下
                elif top_j >= (bottom_i + top_i) / 2:
                    right_num += 1
                elif left_j <= left_i <= right_j <= right_i and top_j >= (bottom_i + top_i) / 2 and bottom_j >= bottom_i:
                    right_num += 1
                else:
                    inversions += 1
    total_num = right_num + inversions
    return inversions, total_num


def write_inversion_info(output_file, xml_file, bound, child1_bounds, child2_bounds):
    with open(output_file, "a", encoding='utf-8') as f:
        f.write(f'Inversion in {xml_file}, bound {bound}: {child1_bounds} and {child2_bounds}\n')


def inversions_in_xml_bounds(bounds_file_path, xml_folder, output_file):
    with open(bounds_file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    if not lines:
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write('Percentage: 0.0000\n')
            no_label_percentage = 0.0000
        return no_label_percentage
    bounds_data = {}
    total_inversions_num = 0
    total_num = 0

    with open(bounds_file_path, 'r', encoding='utf-8') as file:
        for line in file:
            if line.startswith('F:'):
                xml_path, bounds_str = line.split(': ', 1)
                xml_file = os.path.basename(xml_path)

                if xml_file in bounds_data:
                    continue

                bounds = ast.literal_eval(bounds_str)
                bounds_data[xml_file] = bounds

    for xml_file, bounds in bounds_data.items():
        xml_path = os.path.join(xml_folder, xml_file)
        if not os.path.exists(xml_path):
            print(f"XML file {xml_path} does not exist.")
            continue
        tree = ET.parse(xml_path)
        root = tree.getroot()

        for index in range(len(bounds)):
            for node in root.iter():
                node_bounds_str = node.get('bounds')
                if node_bounds_str:
                    node_bounds = parse_bounds_str(node_bounds_str)
                    if check_bounds_inclusion(node_bounds, bounds[index]):
                        if node.get('text') or node.get('content-desc'):
                            text = node.get('text') or node.get('content-desc')
                        else:
                            text = None

                        focusable_children = []
                        for child in node:
                            bounds_child = child.get('bounds')
                            b_left, b_top, b_right, b_bottom = parse_root_bounds(bounds_child)
                            if b_left >= 0 and b_top >= 0 and b_right >= 0 and b_bottom >= 0:
                                bounds_available = True
                            else:
                                bounds_available = False
                            if child.get('class') == 'android.widget.TextView':
                                if (child.get('focusable') == 'true' or child.get('clickable') == 'true' or child.get(
                                        'long-clickable') == 'true') and bounds_available is True:
                                    focusable_children.append(child)
                            else:
                                if (child.get('focusable') == 'true' or child.get('clickable') == 'true' or child.get(
                                        'long-clickable') == 'true' or text is not None) and bounds_available is True:
                                    focusable_children.append(child)

                        inversions_num, total = count_inversions(focusable_children, xml_file, bounds[index], output_file)
                        total_inversions_num += inversions_num
                        total_num += total

    inversion_ratio = total_inversions_num / total_num if total_num > 0 else 0
    print(f"Total Inversions: {total_inversions_num}, Total Combinations: {total_num}, Inversion Ratio: {inversion_ratio:.4f}")

    with open(output_file, "a", encoding='utf-8') as f:
        f.write(f"\nTotal Inversions: {total_inversions_num}, Total Combinations: {total_num}, Inversion Ratio: {inversion_ratio:.4f}\n")

    return inversion_ratio


shortest_paths_focus = []
unreached = []


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


def checked_node_focus(file):
    with open(file, "r") as f:
        lines = f.readlines()
        for line in lines:
            path_nodes = line.strip().replace(' -> ', ' ').split()
            shortest_paths_focus.append(path_nodes)


def unchecked_node_focus(checked_node_path, folder_path, replace_file, output_file):
    replacements = read_replacements(replace_file)
    flat_checked_node_paths = set(sum(checked_node_path, []))

    for source_node, target_node in replacements.items():
        if target_node in flat_checked_node_paths:
            flat_checked_node_paths.add(source_node)

    total_inversions_num = 0
    total_num = 0

    for filename in os.listdir(folder_path):
        if filename.endswith('.xml'):
            node_number = filename.split('--')[0].split('-')[1]

            if node_number not in flat_checked_node_paths:
                unreached.append(int(node_number))
                tree = ET.parse(os.path.join(folder_path, filename))
                root = tree.getroot()

                for node in root.iter():
                    if node.get('text') or node.get('content-desc'):
                        text = node.get('text') or node.get('content-desc')
                    else:
                        text = None

                    focusable_children = []
                    for child in node:
                        bounds = child.get('bounds')
                        b_left, b_top, b_right, b_bottom = parse_root_bounds(bounds)
                        if b_left >= 0 and b_top >= 0 and b_right >= 0 and b_bottom >= 0:
                            bounds_available = True
                        else:
                            bounds_available = False
                        if child.get('class') == 'android.widget.TextView':
                            if (child.get('focusable') == 'true' or child.get('clickable') == 'true' or child.get(
                                    'long-clickable') == 'true') and bounds_available is True:
                                focusable_children.append(child)
                        else:
                            if (child.get('focusable') == 'true' or child.get('clickable') == 'true' or child.get(
                                    'long-clickable') == 'true' or text is not None) and bounds_available is True:
                                focusable_children.append(child)

                        inversions_num, total = count_inversions_unchecked(focusable_children, filename, output_file)
                        total_inversions_num += inversions_num
                        total_num += total

    inversion_ratio = total_inversions_num / total_num if total_num > 0 else 0
    print(f"Total Inversions: {total_inversions_num}, Total Combinations: {total_num}, Inversion Ratio: {inversion_ratio:.4f}")

    unreached.sort()
    with open(output_file, "a", encoding='utf-8') as f:
        f.write(f'Of all the documents that have not arrived:\n')
        f.write(f"\nTotal Inversions: {total_inversions_num}, Total Combinations: {total_num}, Inversion Ratio: {inversion_ratio:.4f}\n")

    return inversion_ratio

