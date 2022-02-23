import time
import requests
import os
import telegram
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from dotenv import load_dotenv


def save_file(file_, file_name):
    try:
        with open(file_name, 'wb') as file:
            file.write(file_)
            return 1
    except FileNotFoundError:
        print(f'unable to create {file_name} file')
        return 0


def get_picture(picture_url, file_name):

    try:
        response = requests.get(picture_url)
        response.raise_for_status()
    except (
        requests.exceptions.HTTPError,
        requests.exceptions.ConnectionError,
        requests.exceptions.MissingSchema
    ):
        print(f'couldn\'t open {picture_url} link')
        return 0

    return save_file(response.content, file_name)


def fetch_spacex_launch_images(path_to_save):

    print('fetching SpaceX launch fotos...')

    fetched_ok = 0
    url = 'https://api.spacexdata.com/v3/launches'
    payload = {"flight_number": 107}
    response = requests.get(url, params=payload)

    try:
        response.raise_for_status()
    except (
        requests.exceptions.HTTPError,
        requests.exceptions.ConnectionError,
        requests.exceptions.MissingSchema
    ):
        print(f'couldn\'t open {url} link')

    images = response.json()[0]['links']['flickr_images']

    if not path_to_save.endswith('/'):
        path_to_save += '/'

    for image_number, image in enumerate(images):
        get_picture(
            image,
            f'{path_to_save}spacex{image_number}.jpg'
            )


def fetch_nasa_apod_last(api_key):
    print('fetching NASA last APOD...')

    save_path = f'./images/nasa/apod/last/{datetime.today().date()}/'
    Path(save_path).mkdir(parents=True, exist_ok=True)

    url = 'https://api.nasa.gov/planetary/apod'
    try:
        response = requests.get(url, params={'api_key': api_key})
        response.raise_for_status()
    except (
        requests.exceptions.HTTPError,
        requests.exceptions.ConnectionError,
        requests.exceptions.MissingSchema
    ):
        print(f'failed to get NASA last APOD')
        return

    apod_url = response.json()['url']
    title = response.json()['title']
    extention = get_file_extention(apod_url)
    file_name = f'{save_path}{title}.{extention}'

    if get_picture(apod_url, file_name) == 1:
        print(f'successfully saved last APOD to {file_name}', '\n')
        return 1
    print('Fetching last NASA APOD was unsuccessful')
    print('\n')
    return


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
    for x in range(5):
        try:
            response = requests.get(url, params=payload)
            response.raise_for_status()
            image_url = response.json()[0]['url']
            if '.' not in image_url[-5:-2]:  # no file in the link
                print(f'not a valid link {image_url}, skipping')
                continue
            print(f'returning a valid link {image_url}')
            image[response.json()[0]['title']] = image_url
            return image
        except (
            requests.exceptions.HTTPError,
            requests.exceptions.ConnectionError,
            requests.exceptions.MissingSchema
        ):
            continue
    return


def get_apod_url_list(number_images, nasa_api_key):
    if not number_images:
        number_images = 5
    url_dict = {}
    url = 'https://api.nasa.gov/planetary/apod'
    payload = {
        'count': number_images,
        'api_key': nasa_api_key
        }

    try:
        response = requests.get(url, params=payload)
        response.raise_for_status()
    except (
        requests.exceptions.HTTPError,
        requests.exceptions.ConnectionError,
        requests.exceptions.MissingSchema
    ):
        print('Failed to get a set of random NASA APOD links')
        return

    links = response.json()

    for link in links:

        url = link['url']
        if '.' not in url[-5:-2]:        # link doesn't contain a vaild file
            continue
        title = link['title']
        url_dict[title] = url

    bad_links = number_images - len(url_dict)   # check if we got enough links
    if bad_links > 0:
        for x in range(bad_links):
            url_dict.update(return_single_apod_url(nasa_api_key))

    return url_dict


def get_apod_images(name_and_url_dict, save_path):

    if not name_and_url_dict:
        print('unable to get a set of links, terminating process')
        return

    if not save_path.endswith('/'):
        save_path += '/'

    fetched_ok = 0
    print(f'saving {len(name_and_url_dict)} images to the {save_path} folder')

    for title, url in name_and_url_dict.items():
        extension_ = get_file_extention(url)
        file_name = f'{save_path}{title}.{extension_}'
        get_picture(url, file_name)

    return save_path


def get_nasa_earth_images(
    year,
    month,
    day,
    path_to_save,
    nasa_api
):

    print('Fetching NASA earth images...')
    base_url = 'https://api.nasa.gov/EPIC/api/natural/date/'
    target_url = f'{base_url}{year}-{month}-{day}'
    payload = {'api_key': nasa_api}
    response = requests.get(target_url, params=payload)

    try:
        response.raise_for_status()
    except (requests.HTTPError):
        print(response.text)
        return

    image_list = []
    successfully_fetched = 0

    for image_meta in response.json():
        image_list.append(image_meta['image'])

    if not image_list:
        print('Sorry, no images for the chosen date or wrong date format')
        return 0

    base_url = f'https://api.nasa.gov/EPIC/archive/natural/{year}/{month}/{day}/png/'

    if not path_to_save.endswith('/'):
        path_to_save += '/'

    for file_name in image_list:
        url = f'{base_url}{file_name}.png'
        this_file_path = f'{path_to_save}{file_name}.png'

        try:
            response = requests.get(url, params=payload)
            response.raise_for_status()
            save_file(response.content, this_file_path)
        except (
            requests.exceptions.HTTPError,
            requests.exceptions.ConnectionError,
            requests.exceptions.MissingSchema
        ):
            print(f'unable to open {url} link')
            pass

    return 1


def find_files_in_dir(path_to_dir):
    files_list = []

    try:
        files = os.listdir(path_to_dir)
    except (FileNotFoundError):
        return

    for file in files:
        if os.path.isfile(os.path.join(path_to_dir, file)):
            files_list.append(file)

    return files_list


def post_in_tg_bot(path_to_dir, tg_token, tg_chat_id):       # tg = Telegram;
    bot = telegram.Bot(token=tg_token)
    files_list = find_files_in_dir(path_to_dir)
    if not files_list:
        print('designated path has no valid files to post')
        return

    if not path_to_dir.endswith('/'):
        path_to_dir += '/'

    print(f'sending {len(files_list)} images tho the bot')

    for file in files_list:
        try:
            bot.send_document(
                chat_id=tg_chat_id,
                document=open(f'{path_to_dir}{file}', 'rb')
            )
            print(f'file {file} posted')
            time.sleep(3.0)                 # to avoid triggering flood control
        except (FileNotFoundError):
            print (f'path {path_to_dir}{file} not found')
            continue
        except (telegram.error.RetryAfter):
            print('Flood control raised. Waiting for 1 minute to surpass')
            time.sleep(60.0)
            continue

    print(f'done posting {len(files_list)} files')


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

    fetch_spacex_launch_images(working_dir)
    get_nasa_earth_images('2022', '01', '15', working_dir, nasa_api_key)

    hello_text = 'Hey there! Some earth and SpaceX photos to start with'
    bot.send_message(chat_id=tg_chat_id, text=hello_text)
    post_in_tg_bot(working_dir, telegram_token, tg_chat_id)

    hello_text = 'Hey again! Your daily bunch of groovy NASA images. Enjoy!'

    while(True):

        time_ = datetime.now().strftime('%H:%M:%S')
        apod_dict = get_apod_url_list(daily_number, nasa_api_key)
        apod_path = f'{working_dir}/{time_}'
        Path(apod_path).mkdir(parents=True)
        get_apod_images(apod_dict, apod_path)

        bot.send_message(chat_id=tg_chat_id, text=hello_text)
        post_in_tg_bot(apod_path, telegram_token, tg_chat_id)
        bye_text = f'That\'s it for today! Next bunch is in {delay_/3600} hrs'
        bot.send_message(tg_chat_id, bye_text)
        time.sleep(delay_)


if __name__ == "__main__":
    main()
