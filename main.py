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


def get_response(url, payload=None):
    try:
        response = requests.get(url, params=payload)
        response.raise_for_status()
        return response
    except (
        requests.exceptions.HTTPError,
        requests.exceptions.ConnectionError,
        requests.exceptions.MissingSchema
    ) as e:
        logger.error(e)
        return


def save_file(content, file_name):
    try:
        with open(file_name, 'wb') as file:
            file.write(content)
            return True
    except IOError as e:
        logger.error(e)
        return False


def check_path(path):
    try:
        if os.path.isdir(path):
            return 'dir'
        if os.path.isfile(path):
            return 'file'
    except FileNotFoundError as e:
        logger.error(e)
        return None


def check_file_access(path):
    try:
        if check_path(path).lower() == 'file':
            with open(path, 'rb') as file:
                return True
    except Exception as e:
        logger.error(e)

    return False


def get_picture(picture_url, file_name):

    response = get_response(picture_url)
    return save_file(response.content, file_name)


def fetch_spacex_launch_images(path_to_save):

    url = 'https://api.spacexdata.com/v3/launches'
    payload = {"flight_number": 107}
    response = get_response(url, payload)

    if not response:
        logging.error(f'{url} cannot be accessed')
        return

    images = response.json()[0]['links']['flickr_images']
    for number, image in enumerate(images):
        file_name = os.path.join(
            path_to_save,
            f'spacex{number}.jpg')
        get_picture(image, file_name)


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
        response = get_response(url, payload)
        if not response:
            continue

        resp_json = response.json()[0]
        image_url = resp_json['url']
        if '.' not in image_url[-5:-2]:  # no file in the link
            continue

        image[resp_json['title']] = image_url
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

    response = get_response(url, payload)
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


def get_apod_images(names_and_urls, save_path):

    if not names_and_urls:
        logging.warning('No APOS urls to get')
        return

    for title, url in names_and_urls.items():
        extension_ = get_file_extention(url)
        file_name = os.path.join(
            save_path,
            f'{title}.{extension_}'
            )
        get_picture(url, file_name)

    return save_path


def get_nasa_earth_images(
    year,
    month,
    day,
    path_to_save,
    nasa_api
):

    base_url = 'https://api.nasa.gov/EPIC/api/natural/date/'
    target_url = f'{base_url}{year}-{month}-{day}'
    payload = {'api_key': nasa_api}

    response = get_response(target_url, payload)
    resp_json = response.json()
    images = []

    for image_meta in resp_json[:5]:       # 5 images should be enough
        images.append(image_meta['image'])

    if not images:
        return 0

    base_url = f'https://api.nasa.gov/EPIC/archive/natural/{year}/{month}/{day}/png/'

    for file_name in images:
        url = f'{base_url}{file_name}.png'
        this_file_path = os.path.join(
            path_to_save,
            f'{file_name}.png'
            )

        response = get_response(url, payload)
        save_file(response.content, this_file_path)

    return 1


def find_files_in_dir(path_to_dir):
    files = []

    if check_path(path_to_dir).lower() != 'dir':
        logging.error(f'Couldn\'t open {path_to_dir}')
        return

    files_dirs = os.listdir(path_to_dir)
    for file in files_dirs:
        if os.path.isfile(os.path.join(path_to_dir, file)):
            full_path = os.path.join(
                path_to_dir,
                file
            )
            files.append(full_path)

    return files


def post_in_tg_bot(file, tg_token, tg_chat_id):       # tg = Telegram;
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
    fetch_spacex_launch_images(working_dir)
    print('Fetching NASA Earth images')
    get_nasa_earth_images('2022', '01', '15', working_dir, nasa_api_key)
    print('Sending images to the bot')

    hello_text = 'Hey there! Some earth and SpaceX photos to start with'
    bot.send_message(chat_id=tg_chat_id, text=hello_text)
    files = find_files_in_dir(working_dir)

    for file in files:
        try:
            post_in_tg_bot(file, telegram_token, tg_chat_id)
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
        get_apod_images(apods, apod_path)
        files = find_files_in_dir(apod_path)

        print('Sending daily NASA images to the bot')
        bot.send_message(chat_id=tg_chat_id, text=hello_text)

        for file in files:
            try:
                post_in_tg_bot(file, telegram_token, tg_chat_id)
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
