import itertools
from natsort import natsorted
import networkx as nx
from pyvis.network import Network
import os


def create_map(folder_path):
    G = nx.DiGraph()
    files = os.listdir(folder_path)
    nodes = []
    edges = []
    edge_colors = {'red': 0, 'blue': 0, 'green': 0, 'purple': 0, 'pink': 0, 'black': 0}

    shortest_paths = []
    color_paths = {'red': [], 'blue': [], 'green': [], 'purple': [], 'pink': []}

    def color_line(file, color_str):
        with open(file, "r") as f:
            lines = f.readlines()
            for line in lines:
                path_nodes = line.strip().replace(' -> ', ' ').split()
                shortest_paths.append(path_nodes)
                for i in range(len(path_nodes) - 1):
                    if G.has_edge(path_nodes[i], path_nodes[i + 1]):
                        old_color = G[path_nodes[i]][path_nodes[i + 1]]['color']
                        if old_color != color_str:
                            color_paths[old_color].remove((path_nodes[i], path_nodes[i + 1]))
                    G.add_edge(path_nodes[i], path_nodes[i + 1], color=color_str, width=5)
                    edge_colors[color_str] += 1
                    color_paths[color_str].append((path_nodes[i], path_nodes[i + 1]))

    files_pu = os.path.join(folder_path, 'shortest_path3.txt')
    files_g = os.path.join(folder_path, 'shortest_path2.txt')
    files_b = os.path.join(folder_path, 'shortest_path1.txt')
    files_r = os.path.join(folder_path, 'shortest_path.txt')
    color_line(files_pu, 'purple')
    color_line(files_g, 'green')
    color_line(files_b, 'blue')
    color_line(files_r, 'red')

    node_files = []
    for file in files:
        if file.endswith(".png"):
            node_files.append(file)

    sorted_node_files = natsorted(node_files, key=lambda x: int(x.split("--")[0].split("-")[-1]))

    hash_file_input = os.path.join(folder_path, 'file_hashes.txt')
    for i, file in enumerate(itertools.islice(sorted_node_files, 2000)):
        if file.endswith(".png"):
            node_id = file.split("--")[0].split("-")[-1]
            node = file.split(".")[0]
            image_path = os.path.join(folder_path, file)
            xml_file = f"{node}.xml"
            xml_path = os.path.join(folder_path, xml_file)

            code = ""
            with open(hash_file_input, "r") as f:
                for line in f:
                    if line.startswith(f"{xml_file}:"):
                        code = line.split(":")[1].strip()
                        break

            if len(nodes) == 0:
                nodes.append({"id": node_id, "shape": "image", "image": image_path, "content": xml_path, "code": code})
                G.add_node(node_id, shape="image", image=image_path, content=xml_path, code=code)
                # G.add_node(node_id, image=image_path, content=xml_path, code=code)
            else:
                found_match = False
                for node in nodes:
                    if code == node["code"]:
                        G.add_edge(nodes[-1]["id"], node["id"])
                        edges.append((nodes[-1]["id"], node["id"]))
                        nodes[-1] = node
                        found_match = True
                        break
                if not found_match:
                    nodes.append({"id": node_id, "shape": "image", "image": image_path, "content": xml_path, "code": code})
                    G.add_node(node_id, shape="image", image=image_path, content=xml_path, code=code)
                    # G.add_node(node_id, image=image_path, content=xml_path, code=code)
                    G.add_edge(nodes[-2]["id"], node_id)
                    edges.append((nodes[-2]["id"], node_id))

    nt = Network(height="1100px", width="100%", directed=True, notebook=True)
    for node in G.nodes:
        nt.add_node(node, **G.nodes[node])

    for edge in G.edges:
        edge_color = G.edges[edge].get('color', 'black')
        edge_width = G.edges[edge].get('width', 1)
        nt.add_edge(edge[0], edge[1], color=edge_color, width=edge_width)
        edge_colors['black'] += 1

    color_counts = {}

    total_edges = G.number_of_edges()

    for (node1, node2, data) in G.edges(data=True):

        color = data.get('color', 'black')
        color_counts[color] = color_counts.get(color, 0) + 1

    def save_color_path(color_name, color_paths, file_path, xml_file_path):
        if color_name not in color_paths or len(color_paths[color_name]) == 0:
            print(f"No paths found for color {color_name}")
            with open(file_path, 'w') as file1:
                file1.write('')
            with open(xml_file_path, 'w') as file2:
                file2.write('')
            return
        path = [color_paths[color_name][0][0]]
        print(color_paths)
        for pair in color_paths[color_name]:
            path.append(pair[1])
        path_str = ' '.join(path)

        with open(file_path, 'w') as file:
            file.write(path_str)

        full_path = [int(node) for node in path_str.split()]
        full_path_str = [str(node) for node in full_path]
        xml_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith('.xml')]

        matching_xml_files = ["step-{}--".format(node) for node in full_path_str]
        matching_xml_files = [xml_file for xml_file in xml_files if any(matching_str in xml_file for matching_str in matching_xml_files)]
        ordered_matching_xml_files = [next(file for file in matching_xml_files if f"step-{node}--" in file) for node in full_path_str]

        with open(xml_file_path, 'w') as file:
            file.write("\n".join(ordered_matching_xml_files))

    co_purple = os.path.join(folder_path, 'color_path_purple.txt')
    co_xml_purple = os.path.join(folder_path, 'color_path_purple_xml.txt')
    co_green = os.path.join(folder_path, 'color_path_green.txt')
    co_xml_green = os.path.join(folder_path, 'color_path_green_xml.txt')
    co_blue = os.path.join(folder_path, 'color_path_blue.txt')
    co_xml_blue = os.path.join(folder_path, 'color_path_blue_xml.txt')
    co_red = os.path.join(folder_path, 'color_path_red.txt')
    co_xml_red = os.path.join(folder_path, 'color_path_red_xml.txt')

    save_color_path('purple', color_paths, co_purple, co_xml_purple)
    save_color_path('green', color_paths, co_green, co_xml_green)
    save_color_path('blue', color_paths, co_blue, co_xml_blue)
    save_color_path('red', color_paths, co_red, co_xml_red)

    print("Total edges:", total_edges)

    colors_order = ['red', 'blue', 'green', 'purple', 'black']

    for color in colors_order:
        count = color_counts.get(color, 0)
        print(f"Color {color}: count {count}, percentage {count / total_edges * 100:.2f}%")

    output_graph = os.path.join(folder_path, 'graph2.html')
    nt.show(output_graph)
