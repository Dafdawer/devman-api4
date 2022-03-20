import requests


def get_earth_dates(nasa_api_key):
    url = 'https://api.nasa.gov/EPIC/api/natural/all'
    payload = {'api_key': nasa_api_key}
    dates = []

    response = requests.get(url, params=payload)
    response.raise_for_status()
    dates_raw = response.json()

    for date in dates_raw:
        dates.append(date['date'])

    return dates


def get_earth_filenames(date):  # date should be 'YYYY-MM-DD' string
    url = f'https://epic.gsfc.nasa.gov/api/enhanced/date/{date}'
    image_names = []

    response = requests.get(url)
    response.raise_for_status()
    response_content = response.json()

    for item in response_content:
        image_names.append(item['image'])

    return image_names          # list could be empty


def get_guaranteed_earth_imagenames(dates):
    for date in dates:
        image_names = get_earth_filenames(date)
        if image_names:
            image_names.insert(0, date)    # to know the date used
            return image_names


def convert_names_to_links(earth_image_names, date):

    earth_image_urls = []
    date = date.replace('-', '/')
    basic_url = 'https://epic.gsfc.nasa.gov/archive/enhanced'
    url = f'{basic_url}/{date}/png'

    for name in earth_image_names:
        image_url = f'{url}/{name}.png'
        earth_image_urls.append(image_url)

    return earth_image_urls


def return_single_apod_url(nasa_api_key):
    url = 'https://api.nasa.gov/planetary/apod'
    payload = {
        'count': 1,
        'api_key': nasa_api_key
        }

    for _ in range(5):      # 5 attempts to find image type
        response = requests.get(url, params=payload)
        response.raise_for_status()

        response_decoded = response.json()[0]
        if response_decoded['media_type'] != 'image':
            continue
        return response_decoded['url']


def return_three_apod_urls(nasa_api_key):
    apod_urls = []

    for _ in range(3):
        url = return_single_apod_url(nasa_api_key)
        apod_urls.append(url)

    return apod_urls
