import os
from datetime import datetime, timedelta
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    filters
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('BOT_TOKEN')
RENDER_EXTERNAL_URL = os.getenv('RENDER_EXTERNAL_URL')

async def delete_message(context: ContextTypes.DEFAULT_TYPE):
    try:
        await context.bot.delete_message(context.job.chat_id, context.job.data)
    except Exception as e:
        logger.error(f"Failed to delete message: {e}")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message
    
    # Verify bot admin status
    try:
        bot_member = await chat.get_member(context.bot.id)
        if not (bot_member.status == 'administrator' and bot_member.can_delete_messages):
            logger.warning(f"Missing permissions in {chat.title} ({chat.id})")
            return
    except Exception as e:
        logger.error(f"Admin check failed: {e}")
        return

    # Schedule deletion after 5 minutes
    context.job_queue.run_once(
        delete_message,
        timedelta(minutes=5),
        chat_id=chat.id,
        data=message.message_id,
        name=f"del_{message.message_id}"
    )

if __name__ == '__main__':
    # Configure async scheduler
    scheduler = AsyncIOScheduler()
    scheduler.start()
    
    # Create application
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Register handlers
    application.add_handler(MessageHandler(filters.ALL, message_handler))
    
    # Webhook configuration
    port = int(os.environ.get('PORT', 10000))
    webhook_path = f"/{BOT_TOKEN}"
    webhook_url = f"{RENDER_EXTERNAL_URL}{webhook_path}"
    
    # Start webhook
    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=webhook_path,
        webhook_url=webhook_url,
        drop_pending_updates=True
    )
