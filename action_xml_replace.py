import os
import re


def xml_replace(action_repair_file, replace_file, output_file):
    with open(replace_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    replace_dict = {}
    for line in lines:
        old, new = line.strip().split('->')
        old_base = os.path.basename(old).replace('.xml', '')
        new_base = os.path.basename(new).replace('.xml', '')
        replace_dict[old_base] = new_base

    with open(action_repair_file, 'r', encoding='utf-8') as file:
        paragraphs = file.read().split('\n\n')

    new_paragraphs = []
    for paragraph in paragraphs:
        for old, new in replace_dict.items():
            paragraph = re.sub(old + r'\.xml', new + '.xml', paragraph)
            paragraph = re.sub(old + r'\.png', new + '.png', paragraph)
        new_paragraphs.append(paragraph)

    new_text = '\n\n'.join(new_paragraphs)

    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(new_text)
