"""Pipeline runner — executes nodes in topological order."""
from __future__ import annotations
import logging
from runtime.pipeline import Pipeline, PipelineNode
from runtime.nodes.input import handle_input
from runtime.nodes.output import handle_output
from runtime.nodes.wendy import handle_wendy
from runtime.nodes.filter import handle_filter
from runtime.nodes.prompt import handle_prompt
from runtime.nodes.voice import handle_voice

logger = logging.getLogger("openwendy.runner")


class PipelineRunner:
    def __init__(self, pipeline: Pipeline, context: dict):
        self.pipeline = pipeline
        self.context = context
        self.results: dict[str, any] = {}
        self.filter_outputs: dict[str, dict] = {}

    async def run(self, user_message: str, input_type: str = "text") -> dict:
        self.context["user_message"] = user_message
        self.context["input_type"] = input_type
        self.results = {}
        self.filter_outputs = {}

        order = self._topo_sort()
        for node in order:
            await self._execute_node(node)

        outputs = {}
        for node in self.pipeline.get_output_nodes():
            if node.id in self.results:
                outputs[node.id] = self.results[node.id]
        for nid, node in self.pipeline.nodes.items():
            if node.type == "voice" and nid in self.results:
                outputs[f"voice_{nid}"] = self.results[nid]
        return outputs

    async def _execute_node(self, node: PipelineNode):
        parents = self.pipeline.get_parents(node.id)
        inputs = []
        for pid in parents:
            parent = self.pipeline.get_node(pid)
            if parent.type == "filter":
                for edge in self.pipeline.edges:
                    if edge.from_id == pid and edge.to_id == node.id:
                        port = edge.from_port
                        filter_out = self.filter_outputs.get(pid, {})
                        if port in filter_out:
                            inputs.append(filter_out[port])
                        break
            elif pid in self.results:
                result = self.results[pid]
                if isinstance(result, str):
                    inputs.append(result)

        handlers = {
            "input": lambda: handle_input(node.config, self.context),
            "wendy": lambda: handle_wendy(node.config, inputs, self.context),
            "filter": lambda: handle_filter(node.config, inputs, self.context),
            "prompt": lambda: handle_prompt(node.config, inputs, self.context),
            "voice": lambda: handle_voice(node.config, inputs, self.context),
            "output": lambda: handle_output(node.config, inputs, self.context),
        }

        handler = handlers.get(node.type)
        if handler:
            result = await handler()
            if node.type == "filter":
                self.filter_outputs[node.id] = result
            self.results[node.id] = result
        else:
            self.results[node.id] = "\n".join(inputs) if inputs else ""

    def _topo_sort(self) -> list[PipelineNode]:
        in_degree = {nid: 0 for nid in self.pipeline.nodes}
        for edge in self.pipeline.edges:
            in_degree[edge.to_id] = in_degree.get(edge.to_id, 0) + 1
        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        order = []
        while queue:
            nid = queue.pop(0)
            order.append(self.pipeline.get_node(nid))
            for child_id in self.pipeline.get_children(nid):
                in_degree[child_id] -= 1
                if in_degree[child_id] == 0:
                    queue.append(child_id)
        return order
