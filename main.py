""" Get a bunch of NASA space images and send them to a Telegram bot"""

from asyncio.log import logger
import time
import requests
import os
import telegram
import logging
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from dotenv import load_dotenv


def save_file(content, path):
    try:
        with open(path, 'wb') as file:
            file.write(content)
            return True
    except IOError as e:
        logger.error(e)


def download_picture(url, filepath, payload=None):

    response = requests.get(url, params=payload)
    response.raise_for_status()
    return save_file(response.content, filepath)


def download_spacex_images(path_to_save):

    url = 'https://api.spacexdata.com/v3/launches'
    payload = {"flight_number": 107}
    response = requests.get(url, params=payload)
    response.raise_for_status()

    image_links = response.json()[0]['links']['flickr_images']
    for number, link in enumerate(image_links):
        filepath = os.path.join(
            path_to_save,
            f'spacex{number}.jpg'
            )
        download_picture(link, filepath)


def get_file_extention(url):
    parsed = urlparse(url).path
    return parsed.split('.')[-1]


def return_single_apod_url(nasa_api_key):
    url = 'https://api.nasa.gov/planetary/apod'
    payload = {
        'count': 1,
        'api_key': nasa_api_key
        }
    image_title_and_link = {}
    for _ in range(5):      # 5 attempts to get 1 file for sure
        response = requests.get(url, params=payload)
        response.raise_for_status()

        response_decoded = response.json()[0]
        image_url = response_decoded['url']
        if '.' not in image_url[-5:-2]:  # it's video or other link
            continue
        # matching name with the link
        image_title_and_link[response_decoded['title']] = image_url
        return image_title_and_link

    return


def get_apod_urls(number_images, nasa_api_key):

    titles_urls = {}
    url = 'https://api.nasa.gov/planetary/apod'
    payload = {
        'count': number_images,
        'api_key': nasa_api_key
        }

    response = requests.get(url, params=payload)
    response.raise_for_status()
    links = response.json()

    for link in links:

        url = link['url']
        extension_ = os.path.splitext(url)[1]
        if not extension_ or len(extension_) > 5:
            continue    # link to a video not image
        title = link['title']
        titles_urls[title] = url

    bad_links = number_images - len(titles_urls)   # enough links check
    if bad_links > 0:
        for _ in range(bad_links):
            titles_urls.update(return_single_apod_url(nasa_api_key))

    return titles_urls


def download_apod_images(titles_urls, save_path):

    if not titles_urls:
        logging.warning('No APOS urls to get')
        return

    for title, url in titles_urls.items():
        extension_ = get_file_extention(url)
        filepath = os.path.join(
            save_path,
            f'{title}.{extension_}'
            )
        download_picture(url, filepath)

    return save_path


def return_nasa_earth_urls(
    year,
    month,
    day,
    nasa_api
):

    base_url = 'https://api.nasa.gov/EPIC/api/natural/date/'
    target_url = f'{base_url}{year}-{month}-{day}'
    payload = {'api_key': nasa_api}

    response = requests.get(target_url, params=payload)
    response.raise_for_status()
    resp_json = response.json()
    image_urls = []

    for image_meta in resp_json[:5]:            # 5 images should be enough
        image_urls.append(image_meta['image'])  # links added later

    if not image_urls:
        return

    base_url = f'https://api.nasa.gov/EPIC/archive/natural/{year}/{month}/{day}/png/'
    for count in enumerate(image_urls):
        image_url = f'{base_url}{image_urls[count[0]]}.png'
        image_urls[count[0]] = image_url

    return image_urls


def return_filepaths(dir_path):
    filepaths = []

    if not os.path.isdir(dir_path):   # check_path(dir_path).lower() != 'dir':
        logging.error(f'Couldn\'t open {dir_path}')
        return

    dir_content = os.listdir(dir_path)
    for item in dir_content:
        if os.path.isfile(os.path.join(dir_path, item)):
            full_path = os.path.join(
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
            time.sleep(3.0)
        except (FileNotFoundError):
            continue
        except (telegram.error.RetryAfter):
            logging.warning(
                'Telegram flood control triggered. Waiting 1 minute'
                )
            time.sleep(60.0)


def save_request(dir_path, url, payload=None):
    response = requests.get(url, params=payload)
    response.raise_for_status()
    parsed = urlparse(url).path
    filename = parsed.split('/')[-1]
    filepath = os.path.join(
        dir_path,
        filename
        )
    save_file(response.content, filepath)


def main():

    load_dotenv()
    nasa_api_key = os.getenv('NASA_API_KEY')
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    tg_chat_id = os.getenv('TELEGRAM_CHAT_ID')
    delay_ = int(os.getenv('IMAGE_POSTING_DELAY_TIME'))
    daily_number = os.getenv('NUMBER_OF_APOD_IMAGES')
    if daily_number:
        daily_number = int(daily_number)
    else:
        daily_number = 5
    bot = telegram.Bot(token=telegram_token)
    working_dir = f'./images/{datetime.today().date()}'
    Path(working_dir).mkdir(parents=True, exist_ok=True)

    print('Fetching SpaceX images')
    try:
        download_spacex_images(working_dir)
    except (
        requests.exceptions.HTTPError,
        requests.exceptions.ConnectionError
    ) as e:
        logger.error(e)
        logging.warning('Couldn\'t fetch SpaceX images')

    print('Fetching NASA Earth images')
    try:
        urls = return_nasa_earth_urls('2022', '01', '15', nasa_api_key)
    except (
        requests.exceptions.HTTPError,
        requests.exceptions.ConnectionError
    ) as e:
        logger.error(e)

    payload = {'api_key': nasa_api_key}
    for url in urls:
        try:
            save_request(working_dir, url, payload)
        except Exception as e:
            logger.error(e)
            continue

    print('Sending images to the bot')

    hello_text = 'Hey there! Some earth and SpaceX photos to start with'
    bot.send_message(chat_id=tg_chat_id, text=hello_text)
    filepaths = return_filepaths(working_dir)

    post_files_in_tg(filepaths, telegram_token, tg_chat_id)

    hello_text = 'Hey again! Your daily bunch of groovy NASA images. Enjoy!'

    while True:

        time_ = datetime.now().strftime('%H:%M:%S')
        apods = get_apod_urls(daily_number, nasa_api_key)
        apod_path = f'{working_dir}/{time_}'
        Path(apod_path).mkdir(parents=True)
        print('Fetching NASA APOD images')
        download_apod_images(apods, apod_path)
        filepaths = return_filepaths(apod_path)

        print('Sending daily NASA images to the bot')
        bot.send_message(chat_id=tg_chat_id, text=hello_text)

        post_files_in_tg(filepaths, telegram_token, tg_chat_id)

        bye_text = f'That\'s it for today! Next bunch is in {delay_/3600} hrs'
        bot.send_message(tg_chat_id, bye_text)
        print('Images have been sent. Wating for the next iteration')
        time.sleep(delay_)


if __name__ == "__main__":
    main()
