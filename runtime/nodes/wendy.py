"""Wendy node — LLM call."""
async def handle_wendy(node_config: dict, inputs: list[str], context: dict) -> str:
    provider = context["provider"]
    prompt = node_config.get("prompt", "You are Wendy, a helpful AI assistant.")
    model = node_config.get("model", None)
    combined = "\n".join(i for i in inputs if i)
    if not combined.strip():
        return ""
    messages = [{"role": "system", "content": prompt}, {"role": "user", "content": combined}]
    return await provider.chat(messages, model=model)
