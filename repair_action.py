import os
import re
import xml.etree.ElementTree as ET


def repair_action_text(folder_path, input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as file:
        text = file.read()

    sections = ''.join(text).split('\n\n')

    with open(output_file, 'w', encoding='utf-8') as outfile:
        for section in sections:
            section = section.strip()
            pattern = r'\[@(text|content-desc)="(.*?)"\]'
            text_pattern = r'\[@text="(.*?)"\]'
            content_desc_pattern = r'\[@content-desc="(.*?)"\]'
            matches = re.findall(pattern, section)
            text_match = re.search(text_pattern, section)
            content_desc_match = re.search(content_desc_pattern, section)

            if text_match and text_match.group(1) != '':
                bounds_pattern = r'\[@bounds="(.*?)"\]'
                bounds_match = re.search(bounds_pattern, section)
                bounds_value = bounds_match.group(1)
                file_pattern = r'\/(step-[a-zA-Z0-9-]+\.xml)'
                file_match = re.search(file_pattern, section)
                file_name = file_match.group(1)
                xml_path = os.path.join(folder_path, file_name)
                if os.path.exists(xml_path):
                    tree = ET.parse(xml_path)
                    root = tree.getroot()
                    target_node = None
                    for node in root.iter():
                        bounds_attr = node.get('bounds')
                        if bounds_attr == bounds_value:
                            target_node = node
                            break

                    if target_node is not None:
                        new_text_attr = target_node.get('text')
                        if '[@text="' in section and '"]' in section:
                            old_text_attr = section.split('[@text="', 1)[1].split('"]', 1)[0]
                            section = section.replace(f'[@text="{old_text_attr}"]', f'[@text="{new_text_attr}"]')

            if content_desc_match and content_desc_match.group(1) != '':
                bounds_pattern = r'\[@bounds="(.*?)"\]'
                bounds_match = re.search(bounds_pattern, section)
                bounds_value = bounds_match.group(1)
                file_pattern = r'\/(step-[a-zA-Z0-9-]+\.xml)'
                file_match = re.search(file_pattern, section)
                file_name = file_match.group(1)
                xml_path = os.path.join(folder_path, file_name)
                if os.path.exists(xml_path):
                    tree = ET.parse(xml_path)
                    root = tree.getroot()
                    target_node = None
                    for node in root.iter():
                        bounds_attr = node.get('bounds')
                        if bounds_attr == bounds_value:
                            target_node = node
                            break

                    if target_node is not None:
                        new_content_desc_attr = target_node.get('content-desc')
                        if '[@content-desc="' in section and '"]' in section:
                            old_content_desc_attr = section.split('[@content-desc="', 1)[1].split('"]', 1)[0]
                            section = section.replace(f'[@content-desc="{old_content_desc_attr}"]', f'[@content-desc="{new_content_desc_attr}"]')

            if len(matches) == 2 and all(match[1] == '' for match in matches):
                bounds_pattern = r'\[@bounds="(.*?)"\]'
                bounds_match = re.search(bounds_pattern, section)
                bounds_value = bounds_match.group(1)
                file_pattern = r'\/(step-[a-zA-Z0-9-]+\.xml)'
                file_match = re.search(file_pattern, section)
                file_name = file_match.group(1)
                xml_path = os.path.join(folder_path, file_name)
                if os.path.exists(xml_path):
                    tree = ET.parse(xml_path)
                    root = tree.getroot()

                    target_node = None
                    for node in root.iter():
                        bounds_attr = node.get('bounds')
                        if bounds_attr == bounds_value:
                            target_node = node
                            break

                    if target_node is not None:
                        for child_node in target_node:
                            text_attr = child_node.get('text')
                            content_desc_attr = child_node.get('content-desc')

                            if text_attr is not None and text_attr != '':
                                if '[@text="' in section and '"]' in section:
                                    old_text_attr = section.split('[@text="', 1)[1].split('"]', 1)[0]
                                    if old_text_attr:
                                        new_text_attr = old_text_attr + '|' + text_attr
                                    else:
                                        new_text_attr = text_attr
                                    section = section.replace(f'[@text="{old_text_attr}"]', f'[@text="{new_text_attr}"]')
                                else:
                                    section = section.replace('[@text=""]', f'[@text="{text_attr}"]')

                            if content_desc_attr is not None and content_desc_attr != '':
                                if '[@content-desc="' in section and '"]' in section:
                                    old_content_desc_attr = section.split('[@content-desc="', 1)[1].split('"]', 1)[0]
                                    if old_content_desc_attr:
                                        new_content_desc_attr = old_content_desc_attr + '|' + content_desc_attr
                                    else:
                                        new_content_desc_attr = content_desc_attr
                                    section = section.replace(f'[@content-desc="{old_content_desc_attr}"]',
                                                              f'[@content-desc="{new_content_desc_attr}"]')
                                else:
                                    section = section.replace('[@content-desc=""]',
                                                              f'[@content-desc="{content_desc_attr}"]')
            outfile.write(section + '\n\n')

