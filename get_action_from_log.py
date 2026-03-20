
import os.path
import re

def process_file(input_filename, output_filename):
    start_flag = "selected"
    end_flag = "Saving screen shot"
    extracting = False
    inside_section = False
    prev_section_xml = None
    seen_steps = set()

    with open(input_filename, "r", encoding="utf-8") as infile, open(output_filename, "w", encoding="utf-8") as outfile:
        current_section = []

        for line in infile:
            if start_flag in line:
                if inside_section:
                    current_section = []
                extracting = True
                inside_section = True
            if extracting:
                current_section.append(line)
            if end_flag in line:
                extracting = False
                if inside_section:
                    section_text = "".join(current_section)
                    xml_file_name_match = re.search(r'/sdcard/fastbot-report/([^/]*\.xml)', section_text)
                    step_match = re.search(r'/(step-[a-zA-Z0-9-]+\.xml)', section_text)
                    if xml_file_name_match and step_match:
                        xml_file_name = xml_file_name_match.group(1)
                        step = step_match.group(1)
                        if step not in seen_steps:
                            if xml_file_name != prev_section_xml:
                                outfile.write(section_text)
                                outfile.write("\n")
                            seen_steps.add(step)
                        prev_section_xml = xml_file_name
                    current_section = []
                    inside_section = False


def process_file_merge(filename):
    with open(filename, 'r', encoding="utf-8") as file:
        lines = file.readlines()

    new_lines = []
    for line in lines:
        if line.strip() == '':
            continue

        if re.match(r'\d{2}-\d{2}', line):
            new_lines.append(line)
        else:
            if new_lines:
                new_lines[-1] = new_lines[-1].rstrip('\n')
                new_lines[-1] += line
            else:
                new_lines.append(line)

    with open(filename, 'w', encoding="utf-8") as file:
        file.writelines(new_lines)

