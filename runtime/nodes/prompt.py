"""Prompt/context node."""
async def handle_prompt(node_config: dict, inputs: list[str], context: dict) -> str:
    return node_config.get("text", "")
