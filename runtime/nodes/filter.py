"""Filter/router node."""
import json

async def handle_filter(node_config: dict, inputs: list[str], context: dict) -> dict[str, str]:
    provider = context["provider"]
    conditions = node_config.get("conditions", [])
    combined = "\n".join(i for i in inputs if i)
    if not combined.strip():
        return {"output_1": ""}
    cond_text = "\n".join(f"{i+1}. {c}" for i, c in enumerate(conditions) if c)
    prompt = f"Route the message to one or more outputs.\nConditions:\n{cond_text}\nReply with JSON array of output numbers, e.g. [1,2].\nMessage: {combined}"
    result = await provider.chat([{"role": "user", "content": prompt}], model=node_config.get("model"), temperature=0.1, max_tokens=50)
    try:
        nums = json.loads(result.strip()) if "[" in result else [1]
    except Exception:
        nums = [1]
    return {f"output_{n}": combined for n in nums}
