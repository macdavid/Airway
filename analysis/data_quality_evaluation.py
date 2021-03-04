from pathlib import Path
from typing import List

import networkx as nx
import yaml

from classification.clustering import generate_pdf_report
from util.util import get_data_paths_from_args


def get_input():
    output_data_path, tree_input_path, render_path = get_data_paths_from_args(inputs=2)
    config_path = Path("configs") / "classification.yaml"
    with open(config_path) as config_file:
        classification_config = yaml.load(config_file, yaml.FullLoader)
    trees: List[nx.Graph] = []
    for tree_path in Path(tree_input_path).glob('*/tree.graphml'):
        trees.append(nx.read_graphml(tree_path))
    return output_data_path, trees, classification_config, render_path


def main():
    output_path, trees, classification_config, render_path = get_input()
    print(render_path)
    content = ["# Airway Auto-Generated Data Quality Evaluation\n"]
    for index, tree in enumerate(trees, 1):
        patient = tree.graph['patient']
        img_path = Path(render_path) / str(patient) / 'left_upper_lobe0.png'
        content.append(f"![{patient}]({img_path})\n\n")
        content.append(f"#### {index}. Patient {patient}\n\n")
        total_cost = sum(tree.nodes[node_id]["cost"] for node_id in tree.nodes)
        content.append(f"Total cost: {total_cost:.2f}\n\n")
        content.append(f"Total nodes: {len(tree.nodes)}\n\n")

        content.append("\n")

    generate_pdf_report(output_path, "data_quality_evaluation", "".join(content))


if __name__ == "__main__":
    main()