import requests
import telegram
import logging
from random import choice
from datetime import datetime
from pathlib import Path
from os import path
from os import listdir
from time import sleep


def make_filepath(url, dirpath):

    filename = path.basename(url)
    filepath = path.join(dirpath, filename)

    return filepath


def download_pictures(urls, dirpath, payload=None):

    for url in urls:
        filepath = make_filepath(url, dirpath)
        response = requests.get(url, params=payload)
        response.raise_for_status()

        with open(filepath, 'wb') as file:
            file.write(response.content)


def make_working_dir():

    today = datetime.today().date()
    time = datetime.now().strftime('%H:%M:%S')
    dir_ = f'./images/{today}/{time}'
    Path(dir_).mkdir(parents=True, exist_ok=True)

    return dir_


def return_filepaths(dir_path):
    filepaths = []

    dir_content = listdir(dir_path)
    for item in dir_content:
        if path.isfile(path.join(dir_path, item)):
            full_path = path.join(
                dir_path,
                item
            )
            filepaths.append(full_path)

    return filepaths


def post_files_in_tg(filepaths, bot, tg_chat_id):
    for filepath in filepaths:
        try:
            with open(filepath, 'rb') as image:
                bot.send_photo(
                    chat_id=tg_chat_id,
                    photo=image
                )
            sleep(3.0)
        except (FileNotFoundError):
            continue
        except (telegram.error.RetryAfter):
            logging.warning(
                'Telegram flood control triggered. Waiting 1 minute'
                )
            sleep(60.0)


def do_tg_posting(bot, dirpath, tg_chat_id):
        hello_text = 'Hey there! Get ready for some cool space pictures'
        bot.send_message(chat_id=tg_chat_id, text=hello_text)

        filepaths = return_filepaths(dirpath)
        post_files_in_tg(filepaths, bot, tg_chat_id)

        bye_text = f'That\'s it for now, wait for the next bunch!'
        bot.send_message(chat_id=tg_chat_id, text=bye_text)
