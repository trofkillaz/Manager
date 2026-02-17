import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ParseMode
from aiogram.utils import executor
import aiohttp

API_TOKEN = 'YOUR_API_TOKEN'
WEBHOOK_URL = 'https://<your_domain>/<your_webhook_path>'

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dispatcher = Dispatcher(bot, storage=storage)

async def on_startup(dp):
    # Set the webhook
    await bot.set_webhook(WEBHOOK_URL)
    logging.info('Webhook set successfully')

@dispatcher.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.reply('Welcome!')

@dispatcher.message_handler(commands=['help'])
async def cmd_help(message: types.Message):
    await message.reply('This is a help message!')

@dispatcher.errors_handler()
async def error_handler(update, exception):
    logging.error(f'Update: {update} caused error: {exception}')

async def on_shutdown(dp):
    # Remove webhook (you may want to enable long polling instead)
    await bot.delete_webhook()
    logging.info('Webhook removed')

if __name__ == '__main__':
    executor.start_webhook(dispatcher, webhook_path='/<your_webhook_path>', on_startup=on_startup, on_shutdown=on_shutdown)