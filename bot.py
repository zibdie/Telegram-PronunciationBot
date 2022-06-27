#Just to trigger requirements.txt
import gtts
from telegram.ext import Updater
import speech_recognition as sr
import string, random
import os
import sys
import logging
from os import path
import time
import ffmpeg
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
DEBUG_USER=os.getenv("DEBUG_USER")
LOG= bool(os.getenv("LOG"))


updater = Updater(TOKEN, use_context=True)
dispatcher = updater.dispatcher
WEBHOOK_URL = WEBHOOK + "/" + TOKEN

def randomString(stringLength=10):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))


def debugLogger(context,fname, lname, uname, uid,  action, message=None, file=None):
    if DEBUG_USER is None:
        logging.error(f"There was an error attempting to send to DEBUG_USER - DEBUG_USER Does Not Exist - Value seen: {DEBUG_USER}")
        return
    try:
        if action == "START":
            context.bot.send_message(
                chat_id=DEBUG_USER,
                text=f"* {fname} {lname} (@{uname} - {uid}) '/start'ed the bot *",
                parse_mode=ParseMode.MARKDOWN,  
                disable_web_page_preview=True,
                disable_notification=True
            )
        elif action == "LISTEN":
            context.bot.send_message(
                chat_id=DEBUG_USER,
                text= f"* {fname} {lname} (@{uname} - {uid}) ' wanted to hear:* {message} ",
                parse_mode=ParseMode.MARKDOWN,  
                disable_web_page_preview=True,
                disable_notification=True
        )
        elif action == "SPEAK":
            context.bot.send_audio(
            chat_id = DEBUG_USER, 
            audio=open(file, 'rb'), 
            caption= f"* '{fname} {lname} (@{uname} - {uid}) 'asked Google TTS and TTS said:* {message} " ,
            performer=uid,
            title=message,
            parse_mode=ParseMode.MARKDOWN,
            disable_notification=True
            )

    except Exception as e:
        logging.error(f"An error occured while attempting to capture logs: {str(e)}")

#Add Start Context
def start(update, context):
    context.bot.send_message(chat_id=update.message.chat_id, text= "*Hey! Send me a text message ✉️ and I will turn it into an audio clip 🎧*",  parse_mode=ParseMode.MARKDOWN)
    context.bot.send_message(chat_id=update.message.chat_id, text= "*Otherwise, send me a voice clip 🎤 and I will get it in text form 📜 *",  parse_mode=ParseMode.MARKDOWN)
    if LOG == True:
        debugLogger(context, fname=str(update.message.from_user.first_name), lname=str(update.message.from_user.last_name), uname=str(update.message.from_user.username), uid=str(update.message.from_user.id), action="START")

from telegram.ext import CommandHandler
from telegram import ChatAction, ParseMode
start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

def text_to_audio_tg(update, context):
    try:
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

        if LOG == True:
            debugLogger(context, fname=str(update.message.from_user.first_name), lname=str(update.message.from_user.last_name), uname=str(update.message.from_user.username), uid=str(update.message.from_user.id), action="LISTEN", message=update.message.text)

        os.remove(filename)
    except Exception as e:
        logging.error(f"An error occured while attempting to use text_to_audio: {str(e)}")


def audio_to_text_tg(update, context):
    AUDIO_FILE_MP3 = path.join(path.dirname(path.realpath(__file__)), randomString() + '.mp3')
    AUDIO_FILE_WAV = path.join(path.dirname(path.realpath(__file__)), randomString() + '.wav')
    newFile = context.bot.get_file(update.message.voice.file_id)
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

        if LOG == True:
            debugLogger(context, fname=str(update.message.from_user.first_name), lname=str(update.message.from_user.last_name), uname=str(update.message.from_user.username), uid=str(update.message.from_user.id), action="SPEAK", message=said,file=AUDIO_FILE_MP3)

    except Exception as e:
        logging.error(f"An Error Occured - Exception: {str(e)}")
        #context.bot.send_message(chat_id=update.message.chat_id, text=f"An Error Occured - Exception: {str(e)}")

    os.remove(AUDIO_FILE_WAV)
    os.remove(AUDIO_FILE_MP3)
        

from telegram.ext import MessageHandler, Filters
text_to_audio_tg_handler = MessageHandler(Filters.text, text_to_audio_tg)
audio_to_text_tg_handler = MessageHandler(Filters.voice, audio_to_text_tg)
dispatcher.add_handler(text_to_audio_tg_handler)
dispatcher.add_handler(audio_to_text_tg_handler)

if __name__ == "__main__":
    #Main Code Here:
    if os.getenv("TELEGRAM_TOKEN") == "" or not os.getenv("TELEGRAM_TOKEN"):
        sys.exit("No Telegram Bot Token found in .env! Exiting...")
    elif os.getenv("BOT_NAME") == "" or not os.getenv("BOT_NAME"):
        sys.exit("Please set your bot's name in the .env file before starting! Now Exiting...")
    elif os.getenv("MODE") == "server":
        if os.getenv("WEBHOOK_URL_MAIN") == "" or not os.getenv("WEBHOOK_URL_MAIN"):
            sys.exit("No Webhook URL found in .env! Exiting...")
        else:
            print(f"Attempting to listen on port {PORT}")
            updater.start_webhook(listen="0.0.0.0",
                                port=int(PORT),
                                url_path=TOKEN,
                                webhook_url=WEBHOOK_URL)
            #updater.bot.set_webhook(WEBHOOK_URL)
            print(f"{BOTNAME} is running on server mode under port {PORT} with the webhook URL set too {WEBHOOK_URL}")
    elif os.getenv("MODE") == "local":
        updater.start_polling()
        print(f"{BOTNAME} is running on local mode ... \n")
    updater.idle()