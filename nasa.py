import requests
from dotenv import load_dotenv
from os import getenv
from utilities import download_pictures


load_dotenv()
nasa_api_key = getenv('NASA_API_KEY')
dates = []


def get_earth_dates():
    url = 'https://api.nasa.gov/EPIC/api/natural/all'
    payload = {'api_key': nasa_api_key}

    response = requests.get(url, params=payload)
    response.raise_for_status()
    dates_raw = response.json()

    for date in dates_raw:
        dates.append(date['date'])

    return dates


def convert_names_to_links(earth_image_names, date):

    earth_image_urls = []
    date = date.replace('-', '/')
    basic_url = 'https://epic.gsfc.nasa.gov/archive/enhanced'
    url = f'{basic_url}/{date}/png'

    for name in earth_image_names:
        image_url = f'{url}/{name}.png'
        earth_image_urls.append(image_url)

    return earth_image_urls


def get_earth_links(dates):

    earth_links = []

    for date in dates[-1::-1]:
        url = f'https://epic.gsfc.nasa.gov/api/enhanced/date/{date}'
        response = requests.get(url)
        response.raise_for_status()
        response_content = response.json()

        for item in response_content:
            earth_links.append(item['image'])   # only image names so far

        if earth_links:         # could be empty list
            earth_links = convert_names_to_links(earth_links, date)
            dates.remove(date)  # remove used date
            return earth_links[:3]  # 3 are enough

        dates.remove(date)      # remove date w/o images


def return_apod_urls(number=1):
    urls = []
    url = 'https://api.nasa.gov/planetary/apod'
    payload = {
        'count': number,
        'api_key': nasa_api_key
        }

    for _ in range(5):    # 5 tries should be enough
        response = requests.get(url, params=payload)
        response.raise_for_status()
        response_decoded = response.json()

        for item in response_decoded:
            if item['media_type'] != 'image':
                continue
            urls.append(item['url'])

            if len(urls) >= number:
                return urls[:number]


def fetch_nasa_images(dirpath, dates):
    links = get_earth_links(dates)
    links.extend(return_apod_urls(3))
    download_pictures(links, dirpath)
