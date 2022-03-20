import requests
import telegram
import logging
from random import choice
from datetime import datetime
from pathlib import Path
from os import path
from os import listdir
from time import sleep


def make_fullpath(url, dirpath):

    filename = path.basename(url)
    filepath = path.join(dirpath, filename)

    return filepath


def download_picture(url, dirpath, payload=None):

    filepath = make_fullpath(url, dirpath)
    response = requests.get(url, params=payload)
    response.raise_for_status()

    with open(filepath, 'wb') as file:
        file.write(response.content)


def pop_three_random(image_links):  # not a clean function
    images_to_post = []
    for _ in range(3):
        url = choice(image_links)
        images_to_post.append(url)
        image_links.remove(url)

    return images_to_post


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


def post_file_in_tg(filepath, tg_token, tg_chat_id):       # tg = Telegram;
    bot = telegram.Bot(token=tg_token)

    with open(filepath, 'rb') as doc:
        bot.send_document(
            chat_id=tg_chat_id,
            document=doc
        )


def post_files_in_tg(filepaths, tg_token, tg_chat_id):
    for filepath in filepaths:
        try:
            post_file_in_tg(filepath, tg_token, tg_chat_id)
            sleep(3.0)
        except (FileNotFoundError):
            continue
        except (telegram.error.RetryAfter):
            logging.warning(
                'Telegram flood control triggered. Waiting 1 minute'
                )
            sleep(60.0)
