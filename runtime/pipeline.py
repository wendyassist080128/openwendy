"""Load and validate pipeline JSON."""
from __future__ import annotations
import json
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class PipelineNode:
    id: str
    type: str
    label: str
    config: dict = field(default_factory=dict)


@dataclass
class PipelineEdge:
    from_id: str
    to_id: str
    from_port: str = "output_1"
    to_port: str = "input_1"


@dataclass
class Pipeline:
    name: str
    nodes: dict[str, PipelineNode]
    edges: list[PipelineEdge]

    def get_node(self, node_id: str) -> PipelineNode:
        return self.nodes[node_id]

    def get_children(self, node_id: str) -> list[str]:
        return [e.to_id for e in self.edges if e.from_id == node_id]

    def get_parents(self, node_id: str) -> list[str]:
        return [e.from_id for e in self.edges if e.to_id == node_id]

    def get_input_nodes(self) -> list[PipelineNode]:
        return [n for n in self.nodes.values() if n.type == "input"]

    def get_output_nodes(self) -> list[PipelineNode]:
        return [n for n in self.nodes.values() if n.type == "output"]


def load_pipeline(path: str | Path) -> Pipeline:
    path = Path(path)
    data = json.loads(path.read_text())
    nodes = {}
    for n in data["nodes"]:
        nodes[n["id"]] = PipelineNode(
            id=n["id"], type=n["type"],
            label=n.get("label", n["type"]),
            config=n.get("config", {}),
        )
    edges = []
    for e in data.get("edges", []):
        edges.append(PipelineEdge(
            from_id=e["from"], to_id=e["to"],
            from_port=e.get("from_port", "output_1"),
            to_port=e.get("to_port", "input_1"),
        ))
    return Pipeline(name=data.get("name", "unnamed"), nodes=nodes, edges=edges)
