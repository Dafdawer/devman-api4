from datetime import datetime
import requests
from pathlib import Path
from urllib.parse import urlparse

def get_picture(picture_url, file_name):
    #Path(path_to_save).mkdir(parents=True, exist_ok=True)

    response = requests.get(picture_url)
    response.raise_for_status()

    try:
        with open(file_name, 'wb') as file:
            file.write(response.content)
            return 1
    except FileNotFoundError:
        return 0

def fetch_spacex_last_launch():

    Path('./images/').mkdir(parents=True, exist_ok=True)
    url = 'https://api.spacexdata.com/v3/launches'
    payload = {"flight_number": 107}
    #payload = {'launch_success': 'true', 'offset': 99}
    response = requests.get(url, params = payload)
    response.raise_for_status()
    print(response.url)

    images = response.json()[0]['links']['flickr_images']

    for image_number, image in enumerate(images):
        get_picture(image, f'./images/spacex{image_number}.jpg')


def fetch_nasa_apod_last(api_key, save_path):

    Path(save_path).mkdir(parents=True, exist_ok=True)

    url = 'https://api.nasa.gov/planetary/apod'
    response = requests.get(url, params={'api_key': api_key})
    response.raise_for_status()

    apod_url = response.json()['url']
    title = response.json()['title']
    extention = get_file_extention(apod_url)
    file_name = f'{save_path}/{title}.{extention}'

    get_picture(apod_url, file_name)
    print(apod_url)


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
    response = requests.get(url, params=payload)
    response.raise_for_status()
    links = response.json()
    
    for link in links:
        url = link['url']
        title = link['title']
        url_list[title] = url
    
    return url_list

def get_apod_images(url_list):
    save_path = f'./images/{datetime.today().date()}'
    Path(save_path).mkdir(parents=True, exist_ok=True)
    successfully_downloaded = 0

    print(f'saving {len(url_list)} images to the {save_path} folder')
    for title, url in url_list.items():
        extension_ = get_file_extention(url)
        file_name = f'{save_path}/{title}.{extension_}'
        successfully_downloaded += get_picture(url, file_name)
    print(f'images downloaded: {successfully_downloaded}')
    print(f"couldn't download images: {len(url_list) - successfully_downloaded}")


def main():

    #Path("./images").mkdir(parents=True, exist_ok=True)
    # filename = './images/hubble.jpeg'
    #path = './images/'
    #url = 'https://upload.wikimedia.org/wikipedia/commons/3/3f/HST-SM4.jpeg'
    #get_picture(url, path)
    #fetch_spacex_last_launch()
    nasa_api_key = 'lkksr8w3HaiBV7H8PrWpLj3Se8WU0vR0tJhencOV'
    #url = 'https://api.nasa.gov/planetary/apod'
    #payload = {'count': 30, 'api_key': nasa_api_key}
    #response = requests.get(url, params=payload)
    #print(response.json())
    #apod_links = get_apod_url_list(30, nasa_api_key)
    #for title, url in apod_links.items():
    #    print(title, url, sep=", ")
    #print(datetime.today().date())
    #fetch_nasa_apod(nasa_api_key)
    url_list = get_apod_url_list(30, nasa_api_key)
    get_apod_images(url_list)



if __name__ == "__main__":
    nasa_api_key = 'lkksr8w3HaiBV7H8PrWpLj3Se8WU0vR0tJhencOV'
    main()
 