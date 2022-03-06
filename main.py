""" Get a bunch of NASA space images and send them to a Telegram bot"""

from asyncio.log import logger
from operator import indexOf
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

    if not response:
        logging.error(f'{url} cannot be accessed')
        return

    images = response.json()[0]['links']['flickr_images']
    for number, image in enumerate(images):
        filepath = os.path.join(
            path_to_save,
            f'spacex{number}.jpg'
            )
        download_picture(image, filepath)


def get_file_extention(url):
    parsed = urlparse(url).path
    return parsed.split('.')[-1]


def return_single_apod_url(nasa_api_key):
    url = 'https://api.nasa.gov/planetary/apod'
    payload = {
        'count': 1,
        'api_key': nasa_api_key
        }
    image = {}
    for x in range(5):      # to make sure we get an image, not video
        response = requests.get(url, params=payload)
        response.raise_for_status()

        if not response:
            continue

        resp_json = response.json()[0]
        image_url = resp_json['url']
        if '.' not in image_url[-5:-2]:  # no file in the link
            continue

        image[resp_json['title']] = image_url   # matching name with the link
        return image

    return


def get_apod_urls(number_images, nasa_api_key):
    if not number_images:
        number_images = 5
    urls = {}
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
        if '.' not in url[-5:-2]:        # link doesn't contain a vaild file
            continue
        title = link['title']
        urls[title] = url

    bad_links = number_images - len(urls)   # check if we got enough links
    if bad_links > 0:
        for x in range(bad_links):
            urls.update(return_single_apod_url(nasa_api_key))

    return urls


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
    for i in range(len(image_urls)):
        image_url = f'{base_url}{image_urls[i]}.png'  # adding link to the name
        image_urls[i] = image_url

    return image_urls


def find_files_in_dir(dir_path):
    files = []

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
            files.append(full_path)

    return files


def post_in_tg(file, tg_token, tg_chat_id):       # tg = Telegram;
    bot = telegram.Bot(token=tg_token)

    with open(file, 'rb') as doc:
        bot.send_document(
            chat_id=tg_chat_id,
            document=doc
        )


def main():

    load_dotenv()
    nasa_api_key = os.getenv('NASA_API_KEY')
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    tg_chat_id = os.getenv('TELEGRAM_CHAT_ID')
    delay_ = int(os.getenv('IMAGE_POSTING_DELAY_TIME'))
    daily_number = os.getenv('NUMBER_OF_APOD_IMAGES')
    if daily_number:
        daily_number = int(daily_number)
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
            response = requests.get(url, params=payload)
            response.raise_for_status()

            parsed = urlparse(url).path
            filename = parsed.split('/')[-1]
            filepath = os.path.join(
                working_dir,
                filename
                )

            save_file(response.content, filepath)
        except Exception as e:
            logger.error(e)
            continue

    print('Sending images to the bot')

    hello_text = 'Hey there! Some earth and SpaceX photos to start with'
    bot.send_message(chat_id=tg_chat_id, text=hello_text)
    files = find_files_in_dir(working_dir)

    for file in files:
        try:
            post_in_tg(file, telegram_token, tg_chat_id)
            time.sleep(3.0)     # to avoid triggering flood control
        except (FileNotFoundError):
            continue
        except (telegram.error.RetryAfter):
            logging.warning(
                'Telegram flood control triggered. Waiting 1 minute'
                )
            time.sleep(60.0)

    hello_text = 'Hey again! Your daily bunch of groovy NASA images. Enjoy!'

    while True:

        time_ = datetime.now().strftime('%H:%M:%S')
        apods = get_apod_urls(daily_number, nasa_api_key)
        apod_path = f'{working_dir}/{time_}'
        Path(apod_path).mkdir(parents=True)
        print('Fetching NASA APOD images')
        download_apod_images(apods, apod_path)
        files = find_files_in_dir(apod_path)

        print('Sending daily NASA images to the bot')
        bot.send_message(chat_id=tg_chat_id, text=hello_text)

        for file in files:
            try:
                post_in_tg(file, telegram_token, tg_chat_id)
            except (FileNotFoundError):
                continue
            except (telegram.error.RetryAfter):
                logging.warning(
                    'Telegram flood control triggered. Waiting 1 minute'
                )
                time.sleep(60.0)

        bye_text = f'That\'s it for today! Next bunch is in {delay_/3600} hrs'
        bot.send_message(tg_chat_id, bye_text)
        print('Images have been sent. Wating for the next iteration')
        time.sleep(delay_)


if __name__ == "__main__":
    main()
