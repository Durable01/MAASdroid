import math
import re


def node_action_path(keywords_file, input_file, output_file, edges_file, start, end):
    edges = []
    with open(edges_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    for line in lines:
        edge = re.findall(r'\d+', line)
        edges.extend(edge)
    edges = set(edges)

    with open(keywords_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    pattern = r'Content: (.*?),'
    content = []
    for line in lines:
        match = re.search(pattern, line)
        if match:
            extracted_text = match.group(1)
            content.append(extracted_text)

    start_index = math.ceil(len(content) * start)
    end_index = math.ceil(len(content) * end)
    keywords = content[start_index:end_index]

    pattern = r'\[@(text|content-desc)="([^"]+)"\]'
    step_pattern = r'step-(\d+)--[^.]+\.xml'

    with open(input_file, "r", encoding="utf-8") as infile:
        content = infile.read()

    sections = content.split('\n\n')

    with open(output_file, 'w', encoding="utf-8") as outfile:
        for keyword in keywords:
            found = False
            for i, section in enumerate(sections):
                if found:
                    break
                match = re.search(pattern, section)
                step_match = re.search(step_pattern, section)
                if match and keyword in match.group() and (step_match is None or step_match.group(1) in edges):
                    outfile.write(section + "\n\n")
                    found = True

