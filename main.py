from operator import contains
import requests
import os
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

    try:
        with open(file_name, 'wb') as file:
            file.write(response.content)
            return 1
    except FileNotFoundError:
        print(f'unable to create {file_name} file')
        return 0


def fetch_spacex_last_launch():

    print('fetching SpaceX launch fotos...')

    successfuly_fetched = 0
    path_ = './images/spacex/'
    Path(path_).mkdir(parents=True, exist_ok=True)

    url = 'https://api.spacexdata.com/v3/launches'
    payload = {"flight_number": 107}
    response = requests.get(url, params = payload)
    response.raise_for_status()
    images = response.json()[0]['links']['flickr_images']

    for image_number, image in enumerate(images):
        successfuly_fetched += get_picture(image, f'{path_}spacex{image_number}.jpg')

    print(f'successfully downloaded {successfuly_fetched} out of {len(images)} images,')
    print(f'destination folder: {path_}')
    print('\n')


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
        return
    print('Fetching last NASA APOD was unsuccessful')
    print('\n')


def get_file_extention(url):
    parsed = urlparse(url).path
    return parsed.split('.')[-1]


def get_apod_url_list(images_number, nasa_api_key):
    url_list = {}
    url = 'https://api.nasa.gov/planetary/apod'
    payload = {
        'count': images_number,
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
        print(f'failed to get a set of random NASA APOD links')
        return
    
    links = response.json()
    
    for link in links:
        url = link['url']
        title = link['title']
        url_list[title] = url
    
    return url_list


def get_apod_images(url_list):
    print('Fetching a set of random NASA APOD images...')

    save_path = f'./images/nasa/apod/random/{datetime.today().date()}/'
    Path(save_path).mkdir(parents=True, exist_ok=True)

    successfully_fetched = 0
    print(f'saving {len(url_list)} images to the {save_path} folder')
    
    for title, url in url_list.items():
        extension_ = get_file_extention(url)
        if ('embed' in url) or (len(extension_) > 4):
            pass
        file_name = f'{save_path}{title}.{extension_}'
        successfully_fetched += get_picture(url, file_name)
    
    print(f'NASA random APOD images downloaded: {successfully_fetched}')
    print(f"couldn't download: {len(url_list) - successfully_fetched} images", '\n')


def get_nasa_earth_images(year, month, day, nasa_api):
    print('Fetching NASA earth images...')

    base_url = 'https://api.nasa.gov/EPIC/api/natural/date/'
    target_url = f'{base_url}{year}-{month}-{day}'
    payload = {'api_key': nasa_api}
    response = requests.get(target_url, params = payload)
    response.raise_for_status()
    
    image_list = []
    successfully_fetched = 0

    for image_meta in response.json():
        image_list.append(image_meta['image'])

    if not image_list:
        print('Sorry, there are no images for the chosen date or wrong date format')
        return 0

    save_path = f'./images/nasa/earth/{year}-{month}-{day}/'
    base_url = f'https://api.nasa.gov/EPIC/archive/natural/{year}/{month}/{day}/png/'
    Path(save_path).mkdir(parents=True, exist_ok=True)

    for file_name in image_list:
        url = f'{base_url}{file_name}.png'
        this_file_path = f'{save_path}{file_name}.png'

        try:
            response = requests.get(url, params=payload)
            response.raise_for_status()
            successfully_fetched += save_file(response.content, this_file_path)
        except (
        requests.exceptions.HTTPError,
        requests.exceptions.ConnectionError,
        requests.exceptions.MissingSchema
        ):
            print(f'unable to open {url} link')
            pass

    print(f'images downloaded: {successfully_fetched}')
    print(f"couldn't download: {len(image_list) - successfully_fetched} images")


def main():
    load_dotenv()
    nasa_api_key = os.getenv('NASA_API_KEY')
    
    fetch_spacex_last_launch()
    fetch_nasa_apod_last(nasa_api_key)
    get_apod_images(get_apod_url_list(30, nasa_api_key))
    get_nasa_earth_images('2022', '01', '15', nasa_api_key)



if __name__ == "__main__":
    main()
 