# Updated bot.py for aiogram 3 and aiohttp webhook implementation
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher, types

API_TOKEN = 'YOUR_API_TOKEN'

bot = Bot(token=API_TOKEN)
dispatcher = Dispatcher(bot)

async def on_startup(app):
    print('Starting webhook...')

@dispatcher.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Welcome!"
    
async def handle(request):
    update = types.Update(**await request.json())
    await dispatcher.process_update(update)
    return web.Response()

app = web.Application()
app.router.add_post('/webhook', handle)

if __name__ == '__main__':
    web.run_app(app, skip_static=True, port=3000)