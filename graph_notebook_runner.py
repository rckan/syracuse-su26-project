from pathlib import Path
import pandas as pd

from graph_utils import build_networkx_graph, load_merged_graph_inputs, summarize_graph


ROOT = Path(__file__).resolve().parent


def load_graph_inputs():
    nodes, edges = load_merged_graph_inputs(ROOT)
    return nodes, edges


def build_and_report_graph(min_degree: int = 2):
    nodes, edges = load_graph_inputs()
    graph, filtered_graph, nodes_to_keep = build_networkx_graph(
        edges,
        nodes=nodes,
        min_degree=min_degree,
    )
    summarize_graph(graph, filtered_graph)
    return graph, filtered_graph, nodes_to_keep, nodes


if __name__ == "__main__":
    build_and_report_graph()
