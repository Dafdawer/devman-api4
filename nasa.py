import requests


def get_earth_dates(nasa_api_key):

    url = 'https://api.nasa.gov/EPIC/api/natural/all'
    payload = {'api_key': nasa_api_key}

    response = requests.get(url, params=payload)
    response.raise_for_status()
    dates_raw = response.json()

    return [date['date'] for date in dates_raw]


def convert_names_to_links(earth_image_names, date):

    date = date.replace('-', '/')
    basic_url = 'https://epic.gsfc.nasa.gov/archive/enhanced'
    url = f'{basic_url}/{date}/png'  
    earth_image_urls = [f'{url}/{name}.png' for name in earth_image_names]

    return earth_image_urls


def get_earth_links(date):

    url = f'https://epic.gsfc.nasa.gov/api/enhanced/date/{date}'
    response = requests.get(url)
    response.raise_for_status()
    response_content = response.json()

    earth_links = [item['image'] for item in response_content] # only image names so far

    if earth_links:         # could be empty list
        earth_links = convert_names_to_links(earth_links, date)
        return earth_links[:3]  # 3 are enough


def return_apod_urls(nasa_api_key, number=1):

    url = 'https://api.nasa.gov/planetary/apod'
    payload = {
        'count': number,
        'api_key': nasa_api_key
        }

    for _ in range(5):    # 5 tries should be enough
        response = requests.get(url, params=payload)
        response.raise_for_status()
        response_decoded = response.json()

        urls = [item['url'] for item in response_decoded if item['media_type'] == 'image']

        return urls[:number]
