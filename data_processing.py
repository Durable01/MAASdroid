import os
import pandas as pd

from get_action_from_log import process_file, process_file_merge
from file_to_hashcode import get_code
from repair_action import repair_action_text
from delete_same_page import remain
from graph import get_graph
from action_xml_replace import xml_replace
from frequent_node_count import get_node_count
from most_node_action_path import node_action_path
from get_related_path import get_related
from shortest_node_path import get_shortest_path
from landmark import get_landmark
from bounds import get_bounds
from path import get_path
from evaluation_image_label import run_image_no_label_path_evaluation
from evaluation_no_label import run_no_label_path_evaluation
from evaluation_false_label import run_false_label_path_evaluation
from evaluation_scattered_focus import inversions_in_xml_bounds
from evaluation import eva


def main(folder_path, eval_folder):
    input_file = os.path.join(folder_path, 'Logcat.txt')
    out_action_file = os.path.join(folder_path, 'action.txt')
    out_code_file = os.path.join(folder_path, 'file_hashes.txt')
    out_repair_file = os.path.join(folder_path, 'action_repair.txt')
    out_remain_file = os.path.join(folder_path, 'action_remain.txt')

    cycles_file = os.path.join(folder_path, 'cycles.txt')
    replace_xml_file = os.path.join(folder_path, 'replace_xml.txt')
    node_file = os.path.join(folder_path, 'nodes.txt')
    edge_file = os.path.join(folder_path, 'edges.txt')
    graph_file = os.path.join(folder_path, 'graph.html')

    out_repair_new_file = os.path.join(folder_path, 'action_repair_new.txt')
    out_keywords_file = os.path.join(folder_path, 'any-node.txt')

    output_action_file = os.path.join(folder_path, 'related_page.txt')
    out_node_file = os.path.join(folder_path, 'related_path.txt')
    shortest_path_file = os.path.join(folder_path, 'shortest_path.txt')
    shortest_path_xml_file = os.path.join(folder_path, 'shortest_path_xml.txt')

    process_file_merge(input_file)
    process_file(input_file, out_action_file)
    get_code(folder_path, out_code_file)
    repair_action_text(folder_path, out_action_file, out_repair_file)
    remain(folder_path, out_repair_file, out_remain_file)
    get_graph(folder_path, out_code_file, cycles_file, replace_xml_file, node_file, edge_file, graph_file)
    xml_replace(out_remain_file, replace_xml_file, out_repair_new_file)
    get_node_count(out_repair_new_file, out_keywords_file)

    node_action_path(out_keywords_file, out_repair_new_file, output_action_file, edge_file, 0, 0.25)
    get_related(output_action_file, out_node_file)
    get_shortest_path(folder_path, edge_file, out_node_file, shortest_path_file, shortest_path_xml_file)

    landmark_path = os.path.join(folder_path, 'landmark.txt')
    get_landmark(folder_path, landmark_path)

    xml_file_input = os.path.join(folder_path, 'shortest_path_xml.txt')
    bounds_file_output = os.path.join(folder_path, 'bounds.txt')
    get_bounds(landmark_path, xml_file_input, bounds_file_output)

    input_bounds_file = os.path.join(folder_path, 'bounds.txt')
    final_path_file = os.path.join(folder_path, 'path.txt')
    get_path(folder_path, out_repair_new_file, input_bounds_file, final_path_file)

    final_path_file = os.path.join(folder_path, 'path.txt')
    output_no_label_file = os.path.join(folder_path, 'evaluation_no_label_path.txt')

    a = run_no_label_path_evaluation(final_path_file, output_no_label_file)

    output_image_file = os.path.join(folder_path, 'evaluation_image_no_label_path.txt')
    b = run_image_no_label_path_evaluation(final_path_file, output_image_file)

    output_false_file = os.path.join(folder_path, 'evaluation_false_label_path.txt')
    c = run_false_label_path_evaluation(final_path_file, output_false_file)

    bounds_file_path = os.path.join(folder_path, 'bounds.txt')
    output_focus_file = os.path.join(folder_path, 'evaluation_inversion_ratio.txt')
    d = inversions_in_xml_bounds(bounds_file_path, folder_path, output_focus_file)

    a = a if a != 0 else 1e-8
    b = b if b != 0 else 1e-8
    c = c if c != 0 else 1e-8
    d = d if d != 0 else 1e-8

    part_after_fastbot = folder_path.split("fastbot-")[-1]
    excel_path = os.path.join(eval_folder, 'eval.xlsx')
    data = pd.read_excel(excel_path, usecols='A:E')

    new_row = {'App': part_after_fastbot, 'A1(No label)': a, 'A2(Image with no description)': b, 'A3(False label)': c, 'A4(Focus disorder)': d}
    new_row_df = pd.DataFrame([new_row])
    data = pd.concat([data, new_row_df], ignore_index=True)
    data.to_excel(excel_path, index=False)
    eva(data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process and evaluate Fastbot data.')
    parser.add_argument('-f', '--folder', required=True, help='Path to the folder containing Fastbot logs.')
    parser.add_argument('-e', '--eval_folder', required=True, help='Path to the folder where evaluation results will be saved.')

    args = parser.parse_args()
    main(args.folder, args.eval_folder)
