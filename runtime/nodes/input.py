"""Input node handler."""
async def handle_input(node_config: dict, context: dict) -> str:
    return context.get("user_message", "")
