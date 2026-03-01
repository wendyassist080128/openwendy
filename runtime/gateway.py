#!/usr/bin/env python3
"""OpenWendy v2 Gateway — Telegram/Discord bot runner."""
import sys
import logging
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.schema import Config
from runtime.pipeline import load_pipeline
from runtime.providers.llm import LLMProvider

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("openwendy")


def main():
    parser = argparse.ArgumentParser(description="OpenWendy Gateway")
    parser.add_argument("--pipeline", required=True, help="Path to pipeline JSON")
    args = parser.parse_args()

    config = Config.load()
    pipeline = load_pipeline(args.pipeline)
    logger.info(f"🌸 OpenWendy starting — pipeline: {pipeline.name} ({len(pipeline.nodes)} nodes)")

    provider = LLMProvider(config)

    if config.channels.telegram.enabled and config.channels.telegram.token:
        from runtime.channels.telegram import TelegramChannel
        channel = TelegramChannel(config, pipeline, provider)
        channel.start()
    else:
        logger.info("No channel enabled. Running in CLI mode.")
        import asyncio
        from runtime.runner import PipelineRunner
        async def cli_loop():
            while True:
                try:
                    text = input("You: ")
                except (EOFError, KeyboardInterrupt):
                    break
                runner = PipelineRunner(pipeline, {"provider": provider, "config": config, "user_id": "cli"})
                results = await runner.run(text)
                for k, v in results.items():
                    if isinstance(v, str) and v.strip():
                        print(f"Wendy: {v}")
        asyncio.run(cli_loop())


if __name__ == "__main__":
    main()
