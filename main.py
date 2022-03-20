""" Get a bunch of NASA space images and send them to a Telegram bot"""
import logging
import spacex
import nasa
import utilities
import os
import telegram
from time import sleep
from dotenv import load_dotenv


def main():

    load_dotenv()
    nasa_api_key = os.getenv('NASA_API_KEY')
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    tg_chat_id = os.getenv('TELEGRAM_CHAT_ID')
    delay_ = int(os.getenv('IMAGE_POSTING_DELAY_TIME'))
    bot = telegram.Bot(token=telegram_token)

    spacex_links = spacex.get_actual_spacex_media()
    earthimages_dates = nasa.get_earth_dates(nasa_api_key)
    earth_imagenames = []
    earth_to_post = []

    while True:
        links_for_tg = []
        working_dir = utilities.make_working_dir()
        print('Fetching links')

        # spacex part
        spacex_to_post = utilities.pop_three_random(spacex_links)
        links_for_tg.extend(spacex_to_post)

        # nasa earth images part
        if not earth_imagenames:
            earth_imagenames = nasa.get_guaranteed_earth_imagenames(earthimages_dates)
            date_ = earth_imagenames.pop(0)     # date used returned in [0] position
            index = earthimages_dates.index(date_) + 1      # including current used
            earthimages_dates = earthimages_dates[index:]   # remove used and empty

        earth_to_post = utilities.pop_three_random(earth_imagenames)    # 3 random filenames
        earth_to_post = nasa.convert_names_to_links(earth_to_post, date_)   # convert to links
        links_for_tg.extend(earth_to_post)

        # nasa APOD part
        apod_urls = nasa.return_three_apod_urls(nasa_api_key)
        links_for_tg.extend(apod_urls)

        print(f'Got {len(links_for_tg)} links. Starting download')

        # download images
        for link in links_for_tg:
            try:
                utilities.download_picture(link, working_dir)
            except Exception as e:
                logging.warning(e)
                continue

        print('Sending images to tg bot')

        # post images
        hello_text = 'Hey there! Get ready for some cool space pictures'
        bot.send_message(chat_id=tg_chat_id, text=hello_text)

        filepaths = utilities.return_filepaths(working_dir)
        utilities.post_files_in_tg(filepaths, telegram_token, tg_chat_id)

        bye_text = f'That\'s it for today! Next bunch is in {delay_/3600} hrs'
        bot.send_message(chat_id=tg_chat_id, text=bye_text)

        print('Images have been sent. Wating for the next iteration')
        sleep(delay_)


if __name__ == "__main__":
    main()
