import requests
from random import shuffle
from utilities import download_pictures



def get_actual_spacex_media():

    image_links = []
    url = 'https://api.spacexdata.com/v4/launches'

    response = requests.get(url)
    response.raise_for_status()
    launches = response.json()

    for launch in launches:
        links = launch['links']['flickr']['original']
        image_links.extend(links)
        
    return image_links


def fetch_spacex_images(spacex_urls, save_dir):
    urls = []
    for _ in range(3):
        urls.append(spacex_urls.pop(0))
    
    download_pictures(urls, save_dir)