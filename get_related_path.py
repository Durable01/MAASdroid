import re


def get_related(input_file, out_file):
    with open(input_file, 'r', encoding='utf-8') as file:
        text = file.read()
    sections = ''.join(text).split('\n\n')
    step_numbers = []

    for section in sections:
        section = section.strip()
        pattern = r'step-(\d+)--[^.]+\.xml'
        match = re.search(pattern, section)
        if match:
            step_number = match.group(1)
            step_numbers.append(step_number)

    unique_edges = []

    for i in range(len(step_numbers) - 1):
        edge = step_numbers[i] + " -> " + step_numbers[i + 1]
        if edge not in unique_edges:
            unique_edges.append(edge)

    with open(out_file, 'w', encoding='utf-8') as file:
        for i in range(len(step_numbers)):
            file.write(step_numbers[i] + ' ')
