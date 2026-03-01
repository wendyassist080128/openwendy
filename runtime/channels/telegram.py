"""Telegram channel."""
import logging
from pathlib import Path
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
from runtime.pipeline import Pipeline
from runtime.runner import PipelineRunner

logger = logging.getLogger("openwendy.telegram")


class TelegramChannel:
    def __init__(self, config, pipeline: Pipeline, provider):
        self.config = config
        self.pipeline = pipeline
        self.provider = provider

    def start(self):
        token = self.config.channels.telegram.token
        app = Application.builder().token(token).build()
        app.add_handler(CommandHandler("start", self._cmd_start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._on_message))
        logger.info("🌸 OpenWendy Telegram bot starting...")
        app.run_polling(drop_pending_updates=True)

    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🌸 Hi! I'm Wendy. How can I help you?")

    async def _on_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = update.message
        if not msg or not msg.text:
            return
        ctx = {"provider": self.provider, "config": self.config, "user_id": str(msg.from_user.id)}
        runner = PipelineRunner(self.pipeline, ctx)
        try:
            results = await runner.run(msg.text)
            for key, value in results.items():
                if key.startswith("voice_") and value and Path(value).exists():
                    await msg.reply_voice(voice=open(value, "rb"))
                elif isinstance(value, str) and value.strip():
                    await msg.reply_text(value)
        except Exception as e:
            logger.exception(f"Pipeline error: {e}")
            await msg.reply_text(f"Sorry, something went wrong 😅")
