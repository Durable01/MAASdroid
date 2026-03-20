import os.path
import re
from collections import Counter


def get_node_count(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as file:
        text = file.read()

    sections = ''.join(text).split('\n\n')
    value_counts = Counter()

    for section in sections:
        section = section.strip()
        pattern = r'\[@(text|content-desc)="(.*?)"\]'
        matches = re.findall(pattern, section)

        if len(matches) == 2 and all(match[1] == '' for match in matches):
            value_counts['No label'] += 1
        else:
            all_values = [match[1] for match in matches if match[1] != '']
            value_counts.update(all_values)

    total_count = sum(value_counts.values())
    sorted_values = sorted(value_counts.items(), key=lambda x: x[1], reverse=True)

    with open(output_file, 'w', encoding='utf-8') as output_file:
        rank = 1
        for value, count in sorted_values:
            output_file.write(f'{rank}. Content: {value}, Num: {count}\n')
            rank += 1
        output_file.write(f'Total Num: {total_count}\n')
