"""Output node handler."""
async def handle_output(node_config: dict, inputs: list[str], context: dict) -> str:
    return "\n".join(i for i in inputs if i)
