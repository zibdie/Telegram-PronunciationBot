#Just to trigger requirements.txt
import gtts
from telegram.ext import Updater
import speech_recognition as sr
import string, random
import os
import io
import sys
import logging
from os import path
import time
import ffmpeg
import argparse
from dotenv import load_dotenv
load_dotenv()

import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


#Edit the .env file to the correct values
TOKEN = os.getenv("TELEGRAM_TOKEN")
PORT = int(os.getenv('PORT'))
WEBHOOK = os.getenv("WEBHOOK_URL_MAIN")
BOTNAME = os.getenv("BOT_NAME")
MODE = os.getenv("MODE")


updater = Updater(TOKEN, use_context=True)
dispatcher = updater.dispatcher
WEBHOOK_URL = WEBHOOK + "/" + TOKEN

def randomString(stringLength=10):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))

#Add Start Context
def start(update, context):
    context.bot.send_message(chat_id=update.message.chat_id, text= "*Hey! Send me a text message ✉️ and I will turn it into an audio clip 🎧*",  parse_mode=ParseMode.MARKDOWN)
    context.bot.send_message(chat_id=update.message.chat_id, text= "*Otherwise, send me a voice clip 🎤 and I will get it in text form 📜 *",  parse_mode=ParseMode.MARKDOWN)


from telegram.ext import CommandHandler
from telegram import ChatAction, ParseMode
start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

def text_to_audio_tg(update, context):
    context.bot.send_message(chat_id=update.message.chat_id, text="*Getting Audio Recording For:* " + update.message.text, parse_mode=ParseMode.MARKDOWN)
    context.bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)
    filename = randomString() + '.mp3'
    tts = gtts.gTTS(update.message.text)
    tts.save(filename)

    context.bot.send_audio(
    chat_id=update.message.chat_id, 
    audio=open(filename, 'rb'),
    performer=BOTNAME,
    title=update.message.text,
    caption="*Pronouncation for: *" + update.message.text,
    parse_mode=ParseMode.MARKDOWN
    )

    context.bot.send_message(chat_id=update.message.chat_id, text="*Did you know that I support Audio 🎤 => Text 📜 ? Send a voice clip to me!*", parse_mode=ParseMode.MARKDOWN)

    os.remove(filename)


def audio_to_text_tg(update, context):
    AUDIO_FILE_MP3 = path.join(path.dirname(path.realpath(__file__)), randomString() + '.mp3')
    AUDIO_FILE_WAV = path.join(path.dirname(path.realpath(__file__)), randomString() + '.wav')
    file_id = update.message.voice.file_id
    newFile = context.bot.get_file(file_id)
    #Saves the file to the current directory
    newFile.download(AUDIO_FILE_MP3)
    context.bot.send_message(chat_id=update.message.chat_id, text="*Transcribing your voice message...* ", parse_mode=ParseMode.MARKDOWN)
    time.sleep(2)
    context.bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)
    stream = ffmpeg.input(AUDIO_FILE_MP3)
    stream = ffmpeg.output(stream, AUDIO_FILE_WAV)
    ffmpeg.run(stream)

    r = sr.Recognizer()
    with sr.AudioFile(AUDIO_FILE_WAV) as source:
        audio = r.record(source)  # read the entire audio file
        said = ""

    try:
        said = r.recognize_google(audio)
        context.bot.send_message(chat_id=update.message.chat_id, text="*It sounds like you said:*", parse_mode=ParseMode.MARKDOWN)
        context.bot.send_message(chat_id=update.message.chat_id, text=said)

        context.bot.send_message(chat_id=update.message.chat_id, text="*Did you know that I support Text 📜 => Audio 🎧 ? Send a message to me!*", parse_mode=ParseMode.MARKDOWN)


    except Exception as e:
        err_msg = "An Error Occured - Exception: " + str(e)
        context.bot.send_message(chat_id=update.message.chat_id, text=err_msg)

    os.remove(AUDIO_FILE_WAV)
    os.remove(AUDIO_FILE_MP3)
        

from telegram.ext import MessageHandler, Filters
text_to_audio_tg_handler = MessageHandler(Filters.text, text_to_audio_tg)
audio_to_text_tg_handler = MessageHandler(Filters.voice, audio_to_text_tg)
dispatcher.add_handler(text_to_audio_tg_handler)
dispatcher.add_handler(audio_to_text_tg_handler)

#Main Code Here:
if TOKEN == "" or not TOKEN:
    sys.exit("No Telegram Bot Token found in .env! Exiting...")
elif BOTNAME == "" or not BOTNAME:
    sys.exit("Please set your bot's name in the .env file before starting! Now Exiting...")
elif MODE == "server":
    if WEBHOOK == "" or not WEBHOOK:
        sys.exit("No Webhook URL found in .env! Exiting...")
    else:
        print("Attempting to listen on port {}".format(PORT))
        updater.start_webhook(listen="0.0.0.0",
                            #port=PORT,
                            url_path=TOKEN)
        print("Setting Webhook URL to {} \n".format(WEBHOOK_URL))
        updater.bot.set_webhook(WEBHOOK_URL)
        print("{} is running on server mode under port {} with the webhook URL set too {} ... \n".format(BOTNAME, PORT, WEBHOOK_URL))
elif MODE == "local":
    updater.start_polling()
    print("{} is running on local mode ... \n".format(BOTNAME))
updater.idle()
