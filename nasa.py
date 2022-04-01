import requests


def get_earth_dates(nasa_api_key):
    dates = []
    url = 'https://api.nasa.gov/EPIC/api/natural/all'
    payload = {'api_key': nasa_api_key}


    response = requests.get(url, params=payload)
    response.raise_for_status()
    dates_raw = response.json()

    dates = [date['date'] for date in dates_raw]
    # for date in dates_raw:
    #     dates.append(date['date'])

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


def get_earth_links(date):

    earth_links = []

    url = f'https://epic.gsfc.nasa.gov/api/enhanced/date/{date}'
    response = requests.get(url)
    response.raise_for_status()
    response_content = response.json()

    for item in response_content:
        earth_links.append(item['image'])   # only image names so far

    if earth_links:         # could be empty list
        earth_links = convert_names_to_links(earth_links, date)
        return earth_links[:3]  # 3 are enough


def return_apod_urls(nasa_api_key, number=1):
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
