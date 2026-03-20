import os
import re
import sys
import xml.etree.ElementTree as ET


def parse_bounds(bound_str):
    bounds = re.findall('\d+', bound_str)
    bounds = [tuple(map(int, bounds[i:i + 2])) for i in range(0, len(bounds), 2)]
    return bounds


def parse_root_bounds(bounds_string):
    b_left, b_top, b_right, b_bottom = map(int, bounds_string.strip('[]').replace('][', ',').split(','))
    return b_left, b_top, b_right, b_bottom


def calculate_distance(bound1, bound2):
    return abs(bound1[0] - bound2[0]) + abs(bound1[1] - bound2[1])


def find_nearest_bounds(action_bound, bounds_list):
    for bound in bounds_list:
        if check_bounds_inclusion(action_bound, bound):
            break
    else:
        return [(0, 0), (1080, 2400)]

    min_distance = sys.maxsize
    nearest_bound = None
    for bound in bounds_list:
        distance = calculate_distance(action_bound[0], bound[0]) + calculate_distance(action_bound[1], bound[1])
        if distance < min_distance:
            min_distance = distance
            nearest_bound = bound
    return nearest_bound


def check_bounds_inclusion(bound1, bound2):
    (bound1_left, bound1_top), (bound1_right, bound1_bottom) = bound1
    (bound2_left, bound2_top), (bound2_right, bound2_bottom) = bound2
    return bound1_left >= bound2_left and bound1_right <= bound2_right and bound1_top >= bound2_top and bound1_bottom <= bound2_bottom


def find_node_in_bounds(root, nearest_bound, bounds_data):
    path = []
    prev_node_bounds = None
    all_nodes = root.findall(".//node")

    filtered_nodes = []
    for node in all_nodes:
        if node.get('text') or node.get('content-desc'):
            text = node.get('text') or node.get('content-desc')
        else:
            text = None
        bounds = node.get('bounds')
        b_left, b_top, b_right, b_bottom = parse_root_bounds(bounds)
        if b_bottom >= 0 and b_top >= 0 and b_left >= 0 and b_right >=0:
            bounds_available = True
        else:
            bounds_available = False
        if node.get('class') == 'android.widget.TextView':
            if (node.get('focusable') == 'true' or node.get('clickable') == 'true' or node.get('long-clickable') == 'true') and bounds_available is True:
                filtered_nodes.append(node)
        elif (node.get('focusable') == 'true' or node.get('clickable') == 'true' or node.get('long-clickable') == 'true' or text is not None) and bounds_available is True:
            filtered_nodes.append(node)
    for node in filtered_nodes:
        node_bounds_str = node.get('bounds')
        node_bounds = parse_bounds(node_bounds_str)
        node_class = node.get('class')

        for bounds_index in range(len(bounds_data)):
            if check_bounds_inclusion(node_bounds, bounds_data[bounds_index]):
                if node.get('text') or node.get('content-desc'):
                    text = node.get('text') or node.get('content-desc')
                    if len(list(node)) > 0:
                        child_text = '|'.join(
                            child_node.get('text') or child_node.get('content-desc') for child_node in node)
                        if text:
                            text += '|' + child_text
                        else:
                            text = child_text
                else:
                    text = None
                path.append((node_bounds, text, node_class))
                bounds_index += 1

                if prev_node_bounds is not None:
                    _, (_, bound1_bottom) = prev_node_bounds
                    (_, bound2_top), _ = node_bounds
                    if bound1_bottom >= bound2_top:
                        if node.get('text') or node.get('content-desc'):
                            text = node.get('text') or node.get('content-desc')
                            if len(list(node)) > 0:
                                child_text = '|'.join(
                                    child_node.get('text') or child_node.get('content-desc') for child_node in node)
                                if text:
                                    text += '|' + child_text
                                else:
                                    text = child_text
                        else:
                            text = None
                        path.append((node_bounds, text, node_class))

        if check_bounds_inclusion(node_bounds, nearest_bound):
            return node, path
        prev_node_bounds = node_bounds

    return None, path


def build_parent_map(root):
    parent_map = {c: p for p in root.iter() for c in p}
    return parent_map


def path_to_action_bound(nearest_bound, first_node_in_nearest_bound, action_bound, parent_map):
    path = []
    start_node = parent_map[first_node_in_nearest_bound]
    for node in start_node.iter():
        if node.get('text') or node.get('content-desc'):
            text = node.get('text') or node.get('content-desc')
        else:
            text = None
        bounds = node.get('bounds')
        b_left, b_top, b_right, b_bottom = parse_root_bounds(bounds)
        if b_bottom >= 0 and b_top >= 0 and b_left >= 0 and b_right >= 0:
            bounds_available = True
        else:
            bounds_available = False
        if (((node.get('class') == 'android.widget.TextView' and
              (node.get('focusable') == 'true' or node.get('clickable') == 'true' or node.get('long-clickable') == 'true')) and
             bounds_available is True) or
                ((node.get('class') != 'android.widget.TextView' and
                  (node.get('focusable') == 'true' or node.get('clickable') == 'true' or node.get('long-clickable') == 'true' or text is not None)) and
                 bounds_available is True)):
            node_bounds_str = node.get('bounds')
            node_bounds = parse_bounds(node_bounds_str)
            node_class = node.get('class')
            if check_bounds_inclusion(node_bounds, nearest_bound):
                if node.get('text') or node.get('content-desc'):
                    text = node.get('text') or node.get('content-desc')
                else:
                    if len(list(node)) > 0:
                        child_texts = [child_node.get('text') or child_node.get('content-desc') for child_node in node if
                                       child_node.get('text') or child_node.get('content-desc')]
                        if child_texts:
                            text = '|'.join(child_texts)
                        else:
                            text = None
                    else:
                        break
                path.append((node_bounds, text, node_class))
                if node_bounds == action_bound:
                    return path
    return path


def traverse_tree_focusable(root, action_bound):
    path = []

    def traverse(node):

        node_bounds_str = node.get('bounds')
        node_bounds = parse_bounds(node_bounds_str)
        node_class = node.get('class')
        if node.get('text') or node.get('content-desc'):
            text = node.get('text') or node.get('content-desc')
        else:
            text = None
        bounds = node.get('bounds')
        b_left, b_top, b_right, b_bottom = parse_root_bounds(bounds)
        if b_bottom >= 0 and b_top >= 0 and b_left >= 0 and b_right >= 0:
            bounds_available = True
        else:
            bounds_available = False
        if (((node.get('class') == 'android.widget.TextView' and
              (node.get('focusable') == 'true' or node.get('clickable') == 'true' or node.get('long-clickable') == 'true')) and
             bounds_available is True) or
                ((node.get('class') != 'android.widget.TextView' and
                  (node.get('focusable') == 'true' or node.get('clickable') == 'true' or node.get('long-clickable') == 'true' or text is not None)) and
                 bounds_available is True)):
            if node.get('text') or node.get('content-desc'):
                text = node.get('text') or node.get('content-desc')
            else:
                if len(list(node)) > 0:
                    child_texts = [child_node.get('text') or child_node.get('content-desc') for child_node in node if
                                   child_node.get('text') or child_node.get('content-desc')]
                    if child_texts:
                        text = '|'.join(child_texts)
                    else:
                        text = None
            path.append((node_bounds, text, node_class))
            if node_bounds == action_bound:
                return True

        for child in node:
            if traverse(child):
                return True
        return False

    traverse(root)
    return path


def traverse_tree_unfocusable(root, action_bound):
    path = []

    def traverse(node):

        node_bounds_str = node.get('bounds')
        node_bounds = parse_bounds(node_bounds_str)
        node_class = node.get('class')

        if node.get('text') or node.get('content-desc'):
            text = node.get('text') or node.get('content-desc')
        else:
            text = None
        bounds = node.get('bounds')
        b_left, b_top, b_right, b_bottom = parse_root_bounds(bounds)
        if b_bottom >= 0 and b_top >= 0 and b_left >= 0 and b_right >= 0:
            bounds_available = True
        else:
            bounds_available = False
        if (((node.get('class') == 'android.widget.TextView' and
              (node.get('focusable') == 'true' or node.get('clickable') == 'true' or node.get('long-clickable') == 'true')) and
             bounds_available is True) or
                ((node.get('class') != 'android.widget.TextView' and
                  (node.get('focusable') == 'true' or node.get('clickable') == 'true' or node.get('long-clickable') == 'true' or text is not None)) and
                 bounds_available is True)):
            if node.get('text') or node.get('content-desc'):
                text = node.get('text') or node.get('content-desc')
            else:
                if len(list(node)) > 0:
                    child_texts = [child_node.get('text') or child_node.get('content-desc') for child_node in node if
                                   child_node.get('text') or child_node.get('content-desc')]
                    if child_texts:
                        text = '|'.join(child_texts)
                    else:
                        text = None
            path.append((node_bounds, text, node_class))
            if node_bounds == action_bound:
                return True

            for child in node:
                if traverse(child):
                    return True
            return False

    traverse(root)
    return path


def find_action_bound_in_bounds_data(action_bound, bounds_data):
    for bound in bounds_data:
        if check_bounds_inclusion(action_bound, bound):
            return bound
    return None


def find_last_node_in_root(root, target_bound):
    def traverse(node):
        node_bounds_str = node.get('bounds')
        node_bounds = parse_bounds(node_bounds_str)

        if node_bounds == target_bound:
            return node

        for child in node:
            result = traverse(child)
            if result is not None:
                return result

        return None

    return traverse(root)


def get_path(xml_folder, input_file, input_bounds_file, output_file):
    with open(input_bounds_file, 'r', encoding='utf-8') as file:
        bounds_text = file.read()
    if not bounds_text:
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write('')
        return
    bounds_data = dict()
    # print(bounds_text)

    readstepnum = []

    for line in bounds_text.splitlines():
        if line.startswith('E:'):
            xml_path, bounds_str = line.split(': ', 1)
            xml_file = os.path.basename(xml_path)
            bounds_data[xml_file] = eval(bounds_str)

            match = re.search(r'step-(\d+)--', xml_file)
            if match:
                num = match.group(1)
                readstepnum.append(num)

    landmark_file_path = os.path.join(xml_folder, 'landmark.txt')
    with open(landmark_file_path, 'r', encoding='utf-8') as landmark_file:
        landmark_bounds = landmark_file.read()
    landmark_bounds_match = re.search(r'Landmark bounds:\[\(\((\d+), (\d+)\), \((\d+), (\d+)\)\)\]', landmark_bounds)
    if landmark_bounds_match:
        left_top_x, left_top_y, right_bottom_x, right_bottom_y = landmark_bounds_match.groups()

    with open(input_file, 'r', encoding='utf-8') as file:
        action_text = file.read()
    sections = action_text.split('\n\n')
    processed_files = set()

    processed_sections = []
    for num in readstepnum:
        found = False

        for i, section in enumerate(sections):
            if i in processed_sections:
                continue

            xml_file = re.search(r'step-' + num + r'--.*?.xml', section)
            if xml_file:
                xml_file = xml_file.group()

                if found:
                    continue
                if xml_file in bounds_data:
                    action_bound_match = re.search('\[@bounds=".*?"\]', section)
                    if action_bound_match:
                        action_bound_str = action_bound_match.group()
                        action_bound = parse_bounds(action_bound_str)
                        xml_file_path = os.path.join(xml_folder, xml_file)
                        tree = ET.parse(xml_file_path)
                        root = tree.getroot()
                        parent_node = root
                        parent_node_bounds = parent_node.attrib.get('bounds')
                        page_left, page_top, page_right, page_bottom = parse_root_bounds(parent_node_bounds)
                        action_node = find_last_node_in_root(root, action_bound)
                        if action_node is not None:
                            node_class = action_node.get('class')
                            if action_node == root:
                                if action_node.get('text') or action_node.get('content-desc'):
                                    text = action_node.get('text') or action_node.get('content-desc')

                                else:
                                    text = None
                                full_path = [(action_bound, text, node_class)]

                                unique_path = []
                                for item in full_path:
                                    if item not in unique_path:
                                        unique_path.append(item)

                                print(f"For xml file {xml_file}, the path to action bound is {unique_path}")
                                parent_node_bounds_list = parse_bounds(parent_node_bounds)
                                if (parent_node_bounds_list[0][0] == 0 and parent_node_bounds_list[1][0] == 1080) and unique_path and len(unique_path) == 1 and unique_path[0][0] == parent_node_bounds_list:
                                    continue
                                with open(output_file, 'a', encoding='utf-8') as f:
                                    f.write(f'For xml file {xml_file}, the path to action bound {action_bound} is {unique_path}\n')
                                    f.write('\n')

                            else:
                                nearest_bound = find_nearest_bounds(action_bound, bounds_data[xml_file])
                                if not check_bounds_inclusion(action_bound, nearest_bound):
                                    nearest_bound = find_action_bound_in_bounds_data(action_bound, bounds_data[xml_file])
                                if nearest_bound:
                                    parent_map = build_parent_map(root)

                                    if nearest_bound == [(page_left, page_top), (page_right, page_bottom)] or ((page_left, page_top), (page_right, page_bottom)):
                                        path = traverse_tree_focusable(root, action_bound)
                                        full_path = path

                                    else:
                                        first_node_in_nearest_bound, path1 = find_node_in_bounds(root, nearest_bound, bounds_data[xml_file])
                                        if first_node_in_nearest_bound is not None:
                                            path2 = path_to_action_bound(nearest_bound, first_node_in_nearest_bound, action_bound, parent_map)
                                            path1 = path1 if path1 is not None else []
                                            path2 = path2 if path2 is not None else []
                                            full_path = path1 + path2

                                        if full_path[-1][0] != action_bound:
                                            last_node_in_full_path = find_last_node_in_root(root, full_path[-1][0])
                                            if last_node_in_full_path is not None:
                                                path3 = traverse_tree_unfocusable(last_node_in_full_path, full_path[-1][0])
                                                path3 = path3 if path3 is not None else []
                                                full_path += path3

                                    unique_path = []
                                    for item in full_path:
                                        if item not in unique_path:
                                            unique_path.append(item)

                                    print(f"For xml file {xml_file}, the path to action bound is {unique_path}")
                                    parent_node_bounds_list = parse_bounds(parent_node_bounds)
                                    if (parent_node_bounds_list[0][0] == 0 and parent_node_bounds_list[1][0] == 1080) and unique_path and len(unique_path) == 1 and unique_path[0][
                                        0] == parent_node_bounds_list:
                                        continue
                                    with open(output_file, 'a', encoding='utf-8') as f:
                                        f.write(f'For xml file {xml_file}, the path to action bound {action_bound} is {unique_path}\n')
                                        f.write('\n')

                    processed_files.add(xml_file)
                    processed_sections.append(i)
                    found = True

            elif found:
                break

        if not found:
            for i, section in enumerate(sections):
                if i in processed_sections:
                    continue

                xml_file = re.search(r'step-' + num + r'--.*?.xml', section)
                if xml_file:
                    xml_file = xml_file.group()

                    if xml_file in bounds_data:
                        action_bound_match = re.search('\[@bounds=".*?"\]', section)
                        if action_bound_match:
                            action_bound_str = action_bound_match.group()
                            action_bound = parse_bounds(action_bound_str)
                            xml_file_path = os.path.join(xml_folder, xml_file)
                            tree = ET.parse(xml_file_path)
                            root = tree.getroot()
                            parent_node = root
                            parent_node_bounds = parent_node.attrib.get('bounds')
                            page_left, page_top, page_right, page_bottom = parse_root_bounds(parent_node_bounds)
                            action_node = find_last_node_in_root(root, action_bound)
                            node_class = action_node.get('class')

                            if action_node == root:
                                if action_node.get('text') or action_node.get('content-desc'):
                                    text = action_node.get('text') or action_node.get('content-desc')

                                else:
                                    text = None
                                full_path = [(action_bound, text, node_class)]

                                unique_path = []
                                for item in full_path:
                                    if item not in unique_path:
                                        unique_path.append(item)

                                print(f"For xml file {xml_file}, the path to action bound is {unique_path}")
                                parent_node_bounds_list = parse_bounds(parent_node_bounds)
                                if (parent_node_bounds_list[0][0] == 0 and parent_node_bounds_list[1][0] == 1080) and unique_path and len(unique_path) == 1 and unique_path[0][
                                    0] == parent_node_bounds_list:
                                    continue
                                with open(output_file, 'a', encoding='utf-8') as f:
                                    f.write(f'For xml file {xml_file}, the path to action bound {action_bound} is {unique_path}\n')
                                    f.write('\n')

                            else:
                                nearest_bound = find_nearest_bounds(action_bound, bounds_data[xml_file])
                                if not check_bounds_inclusion(action_bound, nearest_bound):
                                    nearest_bound = find_action_bound_in_bounds_data(action_bound, bounds_data[xml_file])
                                if nearest_bound:
                                    parent_map = build_parent_map(root)

                                    if nearest_bound == [(page_left, page_top), (page_right, page_bottom)] or ((page_left, page_top), (page_right, page_bottom)):
                                        path = traverse_tree_focusable(root, action_bound)
                                        full_path = path
                                    else:
                                        first_node_in_nearest_bound, path1 = find_node_in_bounds(root, nearest_bound, bounds_data[xml_file])
                                        if first_node_in_nearest_bound is not None:
                                            path2 = path_to_action_bound(nearest_bound, first_node_in_nearest_bound, action_bound, parent_map)
                                            path1 = path1 if path1 is not None else []
                                            path2 = path2 if path2 is not None else []
                                            full_path = path1 + path2

                                        if full_path[-1][0] != action_bound:
                                            last_node_in_full_path = find_last_node_in_root(root, full_path[-1][0])
                                            if last_node_in_full_path is not None:
                                                path3 = traverse_tree_unfocusable(last_node_in_full_path, full_path[-1][0])
                                                path3 = path3 if path3 is not None else []
                                                full_path += path3

                                    unique_path = []
                                    for item in full_path:
                                        if item not in unique_path:
                                            unique_path.append(item)

                                    print(f"For xml file {xml_file}, the path to action bound is {unique_path}")
                                    parent_node_bounds_list = parse_bounds(parent_node_bounds)
                                    if (parent_node_bounds_list[0][0] == 0 and parent_node_bounds_list[1][0] == 1080) and unique_path and len(unique_path) == 1 and unique_path[0][
                                        0] == parent_node_bounds_list:
                                        continue
                                    with open(output_file, 'a', encoding='utf-8') as f:
                                        f.write(f'For xml file {xml_file}, the path to action bound {action_bound} is {unique_path}\n')
                                        f.write('\n')

                        processed_files.add(xml_file)

                    processed_sections.append(i)
                    break


