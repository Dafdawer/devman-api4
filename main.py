""" Get a bunch of NASA space images and send them to a Telegram bot"""
import logging
from urllib.error import HTTPError
import os
import telegram
from utilities import make_working_dir, do_tg_posting
from time import sleep
from dotenv import load_dotenv
from random import shuffle
from utilities import download_pictures
from spacex import get_actual_spacex_media
from nasa import get_earth_dates, get_earth_links, return_apod_urls


def main():

    load_dotenv()
    nasa_api_key = os.getenv('NASA_API_KEY')
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    tg_chat_id = os.getenv('TELEGRAM_CHAT_ID')
    delay_ = int(os.getenv('IMAGE_POSTING_DELAY_TIME'))
    tg_bot = telegram.Bot(token=telegram_token)

    spacex_links = []
    earth_dates = []

    while True:
        # getting links
        print('Fetching links')
        try:
            if not spacex_links:
                spacex_links = get_actual_spacex_media()
                shuffle(spacex_links)
            if not earth_dates:
                earth_dates = get_earth_dates(nasa_api_key)
                earth_dates.reverse()
        except HTTPError as e:
            logging.warning(e)

        # downloading
        working_dir = make_working_dir()
        print('Downloading images')
        try:
            download_pictures(spacex_links[-3:], working_dir)
            spacex_links = spacex_links[:-3]

            earth_links = []
            while not earth_links:
                earth_links = get_earth_links(earth_dates.pop(0))
            download_pictures(earth_links, working_dir)

            apod_links = return_apod_urls(nasa_api_key, 3)
            download_pictures(apod_links, working_dir)

        except HTTPError as e:
            logging.warning(e)

        # posting
        print('Sending images to the bot')
        do_tg_posting(tg_bot, working_dir, tg_chat_id)
        print('Images have been sent. Wating for the next iteration')

        sleep(delay_)


if __name__ == "__main__":
    main()
