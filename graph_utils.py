from __future__ import annotations

import ast
from pathlib import Path

import networkx as nx
import pandas as pd


def build_networkx_graph(
    edges: pd.DataFrame,
    nodes: pd.DataFrame | None = None,
    min_degree: int = 2,
    directed: bool = True,
):
    """Build a NetworkX graph from merged node and edge data and optionally filter it.

    Parameters
    ----------
    edges : pandas.DataFrame
        DataFrame containing `source` and `target` columns.
    nodes : pandas.DataFrame | None, default None
        Optional DataFrame with node metadata, typically containing `id`, `type`,
        and `properties` columns.
    min_degree : int, default 2
        Minimum degree required for a node to be retained in the filtered graph.
    directed : bool, default True
        Whether to build a directed graph.

    Returns
    -------
    tuple[nx.DiGraph | nx.Graph, nx.DiGraph | nx.Graph, list]
        The original graph, the filtered graph, and the list of retained nodes.
    """
    graph_type = nx.DiGraph if directed else nx.Graph
    graph = nx.from_pandas_edgelist(
        edges,
        source="source",
        target="target",
        create_using=graph_type(),
    )

    if nodes is not None:
        node_frame = nodes.copy()
        if "properties" in node_frame.columns:
            node_frame["properties"] = node_frame["properties"].apply(
                lambda value: ast.literal_eval(value) if isinstance(value, str) else value
            )

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


def summarize_graph(graph: nx.Graph, filtered_graph: nx.Graph | None = None) -> None:
    """Print a compact summary of the original and filtered graph."""
    print(f"Original: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
    if filtered_graph is not None:
        print(f"Filtered: {filtered_graph.number_of_nodes()} nodes, {filtered_graph.number_of_edges()} edges")
