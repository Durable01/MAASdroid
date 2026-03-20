import itertools
from natsort import natsorted
import networkx as nx
from pyvis.network import Network
import os

def get_graph(folder_path, hash_file, cycles_file, replace_xml_file, node_file, edge_file, graph_file):
    G = nx.DiGraph()
    files = os.listdir(folder_path)
    nodes = []
    edges = []
    node_files = []
    for file in files:
        if file.endswith(".png"):
            node_files.append(file)

    sorted_node_files = natsorted(node_files, key=lambda x: int(x.split("--")[0].split("-")[-1]))

    for i, file in enumerate(itertools.islice(sorted_node_files, 2000)):
        if file.endswith(".png"):
            node_id = file.split("--")[0].split("-")[-1]
            node = file.split(".")[0]

            image_path = os.path.join(folder_path, file)
            xml_file = f"{node}.xml"
            xml_path = os.path.join(folder_path, xml_file)

            code = ""
            with open(hash_file, "r") as f:
                for line in f:
                    if line.startswith(f"{xml_file}:"):
                        code = line.split(":")[1].strip()
                        break

            if not os.path.exists(cycles_file):
                with open(cycles_file, "w") as f:
                    pass

            if len(nodes) == 0:
                nodes.append({"id": node_id, "shape": "image", "image": image_path, "content": xml_path, "code": code})
                G.add_node(node_id, shape="image", image=image_path, content=xml_path, code=code)
            else:
                found_match = False

                for node in nodes:
                    if code == node["code"]:
                        G.add_edge(nodes[-1]["id"], node["id"])
                        edges.append((nodes[-1]["id"], node["id"]))

                        try:
                            cycle_path = nx.shortest_path(G, node["id"], nodes[-1]["id"])
                            cycle_code = ''.join(G.nodes[n]['code'] for n in cycle_path)
                            is_cycle_exist = False
                            with open(cycles_file, "r") as f:
                                for line in f:
                                    cycle_path_exist, cycle_code_exist = line.split(", Cycle code: ")
                                    cycle_code_exist = cycle_code_exist.strip()

                                    if cycle_code == cycle_code_exist:
                                        is_cycle_exist = True
                                        for j in range(len(cycle_path) - 1):
                                            node1 = cycle_path[j]
                                            node2 = cycle_path[j + 1]

                                            if G.has_edge(node1, node2):
                                                G.remove_edge(node1, node2)
                                            elif G.has_edge(node2, node1):
                                                G.remove_edge(node2, node1)

                            if not is_cycle_exist:
                                with open(cycles_file, "a") as f:
                                    f.write(f"Cycle path: {cycle_path}, Cycle code: {cycle_code}\n")

                            with open(replace_xml_file, "a") as replace_file:
                                replace_file.write(f"{xml_path}->{node['content']}\n")

                            nodes[-1] = node
                            found_match = True
                            break
                        except nx.NetworkXNoPath:
                            continue

                if not found_match:
                    nodes.append({"id": node_id, "shape": "image", "image": image_path, "content": xml_path, "code": code})
                    G.add_node(node_id, shape="image", image=image_path, content=xml_path, code=code)
                    G.add_edge(nodes[-2]["id"], node_id)
                    edges.append((nodes[-2]["id"], node_id))

    with open(node_file, "w") as f:
        for node in nodes:
            node_info = f'id: {node["id"]}, shape: {node["shape"]}, image: {node["image"]}, content: {node["content"]}, ' \
                        f'code: {node["code"]}\n '
            f.write(node_info)
    with open(edge_file, "w") as f:
        for edge in edges:
            edge_info = f'{edge[0]} -> {edge[1]}\n'
            f.write(edge_info)

    nt = Network(height="1100px", width="100%", directed=True, notebook=True)

    for node in nt.nodes:
        node_options = node["options"]
        node_id = node_options["id"]
        node_content = G.nodes[node_id]["content"]
        node_options["title"] = f'<iframe src="{node_content}" width="100%" height="500px"></iframe>'

    nt.from_nx(G)
    nt.show(graph_file)
