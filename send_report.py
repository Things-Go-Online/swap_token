import telegram
import asyncio
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

chat_id = config.get('TELEGRAM', 'chat_id')
token = config.get('TELEGRAM', 'token')

def send_report(message):
    bot = telegram.Bot(token)
    asyncio.run(bot.send_message(chat_id, message))
