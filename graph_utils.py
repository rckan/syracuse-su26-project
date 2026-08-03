from __future__ import annotations

import ast
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd


def _prepare_node_frame(nodes: pd.DataFrame) -> pd.DataFrame:
    """Normalize node metadata for graph construction."""
    node_frame = nodes.copy()
    if "properties" in node_frame.columns:
        node_frame["properties"] = node_frame["properties"].apply(
            lambda value: ast.literal_eval(value) if isinstance(value, str) else value
        )

    if "type" not in node_frame.columns:
        node_frame["type"] = "Unknown"
    else:
        node_frame["type"] = node_frame["type"].fillna("Unknown")

    return node_frame


def build_networkx_graph(
    edges: pd.DataFrame,
    nodes: pd.DataFrame | None = None,
    min_degree: int = 2,
    directed: bool = True,
):
    """Build a NetworkX graph from merged node and edge data and optionally filter it."""
    graph_type = nx.DiGraph if directed else nx.Graph
    graph = nx.from_pandas_edgelist(
        edges,
        source="source",
        target="target",
        create_using=graph_type(),
    )

    if nodes is not None:
        node_frame = _prepare_node_frame(nodes)

        for _, row in node_frame.iterrows():
            node_id = row["id"]
            if node_id not in graph:
                graph.add_node(node_id)

            attributes = {}
            if "type" in node_frame.columns and pd.notna(row["type"]):
                attributes["type"] = row["type"]
            if "properties" in node_frame.columns and isinstance(row["properties"], dict):
                attributes.update(row["properties"])
            if "mentions" in node_frame.columns:
                attributes["mentions"] = row["mentions"]
            if "article_id" in node_frame.columns:
                attributes["article_id"] = row["article_id"]

            graph.nodes[node_id].update(attributes)

    nodes_to_keep = [node for node, degree in graph.degree() if degree >= min_degree]
    filtered_graph = graph.subgraph(nodes_to_keep).copy()

    return graph, filtered_graph, nodes_to_keep


def build_type_specific_graphs(
    edges: pd.DataFrame,
    nodes: pd.DataFrame | None = None,
    min_degree: int = 0,
    directed: bool = True,
):
    """Build one graph per node type using only nodes of that type.

    The per-type graphs preserve every node belonging to the requested type, even
    if it is isolated in the edge list. The optional ``min_degree`` argument is
    retained for compatibility but does not remove nodes from these type-specific
    graphs.
    """
    graph_type = nx.DiGraph if directed else nx.Graph
    graph = nx.from_pandas_edgelist(
        edges,
        source="source",
        target="target",
        create_using=graph_type(),
    )

    if nodes is not None:
        node_frame = _prepare_node_frame(nodes)
        for _, row in node_frame.iterrows():
            node_id = row["id"]
            if node_id not in graph:
                graph.add_node(node_id)

            attributes = {"type": row["type"]}
            if "properties" in node_frame.columns and isinstance(row["properties"], dict):
                attributes.update(row["properties"])
            if "mentions" in node_frame.columns:
                attributes["mentions"] = row["mentions"]
            if "article_id" in node_frame.columns:
                attributes["article_id"] = row["article_id"]
            graph.nodes[node_id].update(attributes)

    node_types = sorted(
        {
            graph.nodes[node_id].get("type", "Unknown")
            for node_id in graph.nodes
        }
    )
    if not node_types:
        node_types = ["Unknown"]

    type_graphs = {}
    for node_type in node_types:
        type_nodes = [
            node_id for node_id in graph.nodes if graph.nodes[node_id].get("type", "Unknown") == node_type
        ]
        type_graph = graph_type()
        type_graph.add_nodes_from((node_id, graph.nodes[node_id].copy()) for node_id in type_nodes)

        for source, target, attrs in graph.edges(data=True):
            if source in type_nodes and target in type_nodes:
                type_graph.add_edge(source, target, **attrs)

        nodes_to_keep = list(type_graph.nodes())
        filtered_graph = type_graph.copy()
        type_graphs[node_type] = (type_graph, filtered_graph, nodes_to_keep)

    return type_graphs


def calculate_graph_metrics(graph: nx.Graph, filtered_graph: nx.Graph | None = None) -> dict[str, float | int]:
    """Compute a compact set of graph metrics for quick inspection."""
    working_graph = filtered_graph if filtered_graph is not None else graph
    if working_graph.number_of_nodes() == 0:
        return {
            "nodes": 0,
            "edges": 0,
            "density": 0.0,
            "average_degree": 0.0,
            "components": 0,
            "largest_component_size": 0,
            "average_clustering": 0.0,
        }

    undirected_graph = working_graph.to_undirected()
    degree_values = [degree for _, degree in working_graph.degree()]
    components = list(nx.connected_components(undirected_graph))
    largest_component_size = max(len(component) for component in components) if components else 0

    return {
        "nodes": working_graph.number_of_nodes(),
        "edges": working_graph.number_of_edges(),
        "density": nx.density(working_graph),
        "average_degree": sum(degree_values) / len(degree_values) if degree_values else 0.0,
        "components": len(components),
        "largest_component_size": largest_component_size,
        "average_clustering": nx.average_clustering(undirected_graph),
    }


def load_merged_graph_inputs(root: str | Path | None = None):
    """Load the merged node and edge CSVs from the workspace root."""
    base_path = Path(root or Path(__file__).resolve().parent)
    nodes_path = base_path / "merged_nodes.csv"
    edges_path = base_path / "merged_edges.csv"

    if not nodes_path.exists() or not edges_path.exists():
        raise FileNotFoundError(f"Expected merged CSV files at {nodes_path} and {edges_path}")

    nodes = pd.read_csv(nodes_path)
    edges = pd.read_csv(edges_path)
    return nodes, edges


def visualize_graph(graph: nx.Graph, title: str | None = None, figsize: tuple[int, int] = (6, 4)) -> None:
    """Render a simple static visualization of a graph."""
    plt.figure(figsize=figsize)

    node_types = nx.get_node_attributes(graph, "type")
    edge_counts = {node: graph.degree(node) for node in graph.nodes}
    max_degree = max(edge_counts.values(), default=1)
    node_sizes = [max(220, 140 + (edge_counts[node] / max_degree) * 1100) for node in graph.nodes]

    degrees = {node: graph.degree(node) for node in graph.nodes}
    if degrees:
        max_degree_value = max(degrees.values())
        colors = [plt.cm.viridis(degrees[node] / max_degree_value if max_degree_value else 0.0) for node in graph.nodes]
    else:
        colors = []

    labels = {}
    for node in graph.nodes:
        properties = graph.nodes[node].get("properties") or {}
        if isinstance(properties, dict) and properties.get("name"):
            labels[node] = properties["name"]
        else:
            labels[node] = node

    if graph.number_of_nodes() <= 12:
        pos = nx.circular_layout(graph)
    else:
        seed = sum(ord(char) for char in (title or "")) % 1000
        pos = nx.spring_layout(graph, seed=seed, k=0.9)

    nx.draw_networkx_nodes(graph, pos, node_color=colors, node_size=node_sizes, edgecolors="#333333", linewidths=0.6)
    nx.draw_networkx_edges(graph, pos, width=1.2, alpha=0.6, edge_color="#999999")
    nx.draw_networkx_labels(graph, pos, labels=labels, font_size=8, font_family="sans-serif")

    if title:
        plt.title(title)
    plt.axis("off")
    plt.tight_layout()
    plt.show()


def summarize_graph(graph: nx.Graph, filtered_graph: nx.Graph | None = None) -> None:
    """Print a compact summary of the original and filtered graph."""
    print(f"Original: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
    if filtered_graph is not None:
        print(f"Filtered: {filtered_graph.number_of_nodes()} nodes, {filtered_graph.number_of_edges()} edges")
