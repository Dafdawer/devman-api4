## Download a bunch of space images in one go

Get a bunch of space images including NASA pictures of the day and SpaceX launch images


### **Installing**

You should have python3 working in your system. Use `pip` (or `pip3` in
case of dependency conflicts with python2):

```
pip install -r requirements.txt
```

[virtualenv/venv](https://docs.python.org/3/library/venv.html) is recommended for the means of project isolation


### __Running the script__

go to the folder with the script

```
cd ~/[path-to-thescript]
```

type
```
python3 main.py
```
to run the script


### __.env entries__

To run this script, you have to put the following variables into your
.env file:

- NASA_API_KEY
- TELEGRAM_BOT_TOKEN
- TELEGRAM_CHAT_ID
  
There is also `IMAGE_POSTING_DELAY_TIME` variable which determines how often the sript runs in seconds. The default value is 86400 (24hrs), which means the cript is run once a day. Changing it to 3600 would mean the script is run hourly, 1800 - every 30 minutes and so on.
Last but not least, alter `NUMBER_OF_APOD_IMAGES` (5 by default) to set desired number of NASA APOD images posted at a time.


### __Project objective__

The project is purely educational made during web developers course
in [dvmn.org](https://dvmn.org)