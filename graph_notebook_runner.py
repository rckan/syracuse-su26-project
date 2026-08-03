from pathlib import Path

from graph_utils import (
    build_networkx_graph,
    build_type_specific_graphs,
    calculate_graph_metrics,
    load_merged_graph_inputs,
    summarize_graph,
    visualize_graph,
)


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


def build_and_report_type_specific_graphs(min_degree: int = 2):
    nodes, edges = load_graph_inputs()
    type_graphs = build_type_specific_graphs(edges, nodes=nodes, min_degree=min_degree)

    for node_type, (graph, filtered_graph, _) in type_graphs.items():
        metrics = calculate_graph_metrics(graph, filtered_graph)
        print(
            f"{node_type}: {metrics['nodes']} nodes, {metrics['edges']} edges, "
            f"density={metrics['density']:.3f}, avg_degree={metrics['average_degree']:.2f}, "
            f"components={metrics['components']}"
        )
        visualize_graph(filtered_graph, title=f"{node_type} graph")

    return type_graphs


if __name__ == "__main__":
    build_and_report_graph()
    build_and_report_type_specific_graphs()
