import networkx as nx

from backend.models.discovery import TableInfo


def build_dependency_graph(tables: list[TableInfo]) -> nx.DiGraph:
    g = nx.DiGraph()
    for table in tables:
        g.add_node(table.name)
        for fk in table.foreign_keys:
            g.add_edge(table.name, fk.referred_table)
    return g


def get_load_order(graph: nx.DiGraph) -> list[str]:
    """Reverse topological sort — tables with no dependencies first."""
    return list(reversed(list(nx.topological_sort(graph))))


def export_dot(graph: nx.DiGraph) -> str:
    """Export as DOT format string for Graphviz rendering."""
    lines = ["digraph dependencies {", "    rankdir=LR;"]
    for src, dst in graph.edges():
        lines.append(f'    "{src}" -> "{dst}";')
    lines.append("}")
    return "\n".join(lines)
