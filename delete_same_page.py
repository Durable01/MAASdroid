import os
import re

from natsort import natsorted
import xml.etree.ElementTree as ET

def remain(folder_path, input_file, output_file):
    def compare_nodes(node1, node2):
        for attr in ["node index", "resource-id",
                     "class", "package",
                     "checkable", "clickable", "enabled",
                     "focusable", "scrollable",
                     "long-clickable", "password", "bounds"]:
            if node1.get(attr) != node2.get(attr):
                return False
        return True

    def compare_xmls(root1, root2):
        count1 = sum(1 for _ in root1.iter())
        count2 = sum(1 for _ in root2.iter())

        if count1 != count2:
            return False
        for node1, node2 in zip(root1.iter(), root2.iter()):
            if not compare_nodes(node1.attrib, node2.attrib):
                return False
        return True

    def load_xml(file_path):
        if os.path.exists(file_path):
            tree = ET.parse(file_path)
            return tree.getroot()
        else:
            return None

    def file_exists_in_folder(filename, folder):
        return os.path.exists(os.path.join(folder, filename))

    files = os.listdir(folder_path)
    delete_filenames = []
    node_files = [file for file in files if file.endswith(".xml")]
    sorted_node_files = natsorted(node_files, key=lambda x: int(x.split("--")[0].split("-")[-1]))
    previous_root = None
    previous_node_path = None

    for node_file in sorted_node_files:
        node_path = os.path.join(folder_path, node_file)
        current_root = load_xml(node_path)

        if previous_root is not None and compare_xmls(previous_root, current_root):
            file_name_without_extension = os.path.splitext(os.path.basename(previous_node_path))[0]
            delete_filenames.append(file_name_without_extension)
            os.remove(previous_node_path)
            previous_png_file = file_name_without_extension + ".png"
            previous_png_path = os.path.join(folder_path, previous_png_file)
            if os.path.exists(previous_png_path):
                os.remove(previous_png_path)

        previous_root = current_root
        previous_node_path = node_path

    with open(input_file, "r", encoding="utf-8") as infile:
        content = infile.read()
    sections = content.split('\n\n')

    with open(output_file, 'w', encoding="utf-8") as outfile:
        for i, section in enumerate(sections):
            contains_names = False

            for name in delete_filenames:
                if name in section:
                    contains_names = True
                    break

            file_exists = False
            match = re.search(r'Saving GUI tree to /sdcard/fastbot-report/(.*?) at step', section)
            if match:
                xml_filename = match.group(1)
                file_exists = file_exists_in_folder(xml_filename, folder_path)

            if not contains_names and file_exists:
                outfile.write(section + "\n\n")
