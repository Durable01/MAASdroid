import re

import networkx as nx
import os


def get_shortest_path(folder_path, edge_file, related_path_file, shortest_path_file, shortest_path_xml_file):
    with open(edge_file, "r", encoding="utf-8") as file:
        edges = [tuple(map(int, line.strip().split(" -> "))) for line in file.readlines()]

    with open(related_path_file, "r") as file:
        nodes = list(map(int, file.readline().strip().split(" ")))

    print("nodes:", nodes)

    G = nx.DiGraph()
    G.add_edges_from(edges)
    nodes.sort()

    paths = []
    for i in range(len(nodes) - 1):
        paths.append(nx.shortest_path(G, nodes[i], nodes[i + 1]))

    full_path = paths[0]
    for path in paths[1:]:
        full_path += path[1:]

    full_path_str = [str(node) for node in full_path]
    full_path_output = ' -> '.join(full_path_str)

    with open(shortest_path_file, 'w') as file:
        file.write(full_path_output)

    xml_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith('.xml')]
    matching_strs = ["step-{}--".format(node) for node in full_path_str]
    matching_xml_files = [xml_file for xml_file in xml_files if any(matching_str in xml_file for matching_str in matching_strs)]
    ordered_matching_xml_files = [next((file for file in matching_xml_files if f"step-{node}--" in file), None) for node in full_path_str]

    with open(shortest_path_xml_file, 'w') as file:
        file.write("\n".join(ordered_matching_xml_files))

