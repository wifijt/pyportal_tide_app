"""
This app queries the NOAA Weather Predictions API to load the tide predictions for today - Tide predicions are given in 6 min interval (240 per day though there will only ever be 239 in a 24 hour period)
The STATION variable is the tide prediction point to query for - you can find your tide station by going to the NOAA tidesandcurrent.noaa.api site
NOTE this app uses a modified version of the Adafruit PyPortal library to allow the fetch() methpod to accept an updated URL - this was needed because the prediction API requires you to 
provide the beginning and end date for the query. To do that we need to set the date on the pyportal which requires calling the pyportal init script - the version of pyportal at the time
of writing did not allow you to update the DATA_SOURCE once it was set
Depending on the TFT on your pyportal the image background may or may not be too contrasty - on mine the image was washed out enough to see the text

"""
import sys
import time
import board
import json
import math
from adafruit_bitmap_font import bitmap_font
from adafruit_display_text.label import Label
from adafruit_pyportal import PyPortal
cwd = ("/"+__file__).rsplit('/', 1)[0] # the current working directory (where this file is)

# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise
# # Use cityname, country code where countrycode is ISO3166 format.
# # E.g. "New York, US" or "London, GB"

# set to your local the tide predition STATION from the NOAA tide prediction site
STATION = "8441241"

# Set up a placeholder for DATA_SOURCE that we will update later on 
DATA_SOURCE = " "
DATA_LOCATION = []


# Initialize the pyportal object and set the tides background
pyportal = PyPortal(url=DATA_SOURCE,
                    json_path=DATA_LOCATION,
                    status_neopixel=board.NEOPIXEL,
                    default_bg=cwd+"/tides.bmp")

pyportal.preload_font()
big_font = bitmap_font.load_font(cwd+"/fonts/Arial-Bold-24-Complete.bdf")
little_font = bitmap_font.load_font(cwd+"/fonts/Arial-Bold-12.bdf")
pyportal.preload_font(b'0123456789fallingrising') # pre-load glyphs for fast printing
 
directionp = (100, 195)
high1p = (25, 25)
low1p = (25, 85)
high2p = (210, 25)
low2p = (210, 85)
high1t = (25, 50)
low1t = (25, 110)
high2t = (210, 50)
low2t = (210, 110)
currentp = (120, 165)
timedisp = (120, 225)
text_color = 0x000000
 
text_areas = []
for pos in (directionp, high1p, low1p, high2p, low2p, currentp):
    textarea = Label(big_font, text='             ') #13 spaces to accomodate the longest text 'stay tuned...'
    textarea.x = pos[0]
    textarea.y = pos[1]
    textarea.color = text_color
    pyportal.splash.append(textarea)
    text_areas.append(textarea)
    
for pos in (high1t,low1t,high2t,low2t,timedisp):
    textarea = Label(little_font, text='          ')
    textarea.x = pos[0]
    textarea.y = pos[1]
    textarea.color = text_color
    pyportal.splash.append(textarea)
    text_areas.append(textarea)

while True:
    #get the time and build the datasource string
    pyportal.get_local_time()
    timeval = time.localtime()
    #add leading zeros to the day and month
    today=str(timeval.tm_year)+"{:02d}".format(timeval.tm_mon)+"{:02d}".format(timeval.tm_mday)
    day = "{:02d}".format(timeval.tm_mday)
    DATA_SOURCE = "https://tidesandcurrents.noaa.gov/api/datagetter?begin_date="+today
    DATA_SOURCE += "&end_date="+today
    DATA_SOURCE += "&station="+STATION
    DATA_SOURCE += "&product=predictions&datum=mllw&units=english&time_zone=lst_ldt&application=web_services&format=json"
    # Test URL 
    # I chose the MLLW (Mean Low Low water) dataum as this is the "normal" set of predictions  
    # https://tidesandcurrents.noaa.gov/api/datagetter?begin_date=20190419&end_date=20190419&station=8441241&product=predictions&datum=mllw&units=english&time_zone=lst_ldt&application=web_services&format=json
    print(DATA_SOURCE)
    update_clock= None
    value = pyportal.fetch(DATA_SOURCE) #modified pyportal to allow us to call the fetch AFTER we set the time to use the in the URL since the tide predicion use of date=today returns tomorrow after GMT midnight
    value = json.loads(value) #load the predictions into a python list/array/structure thingy
    hx=0
    #define the highlow array as 4 empty slots
    highlow = [None] * 4

    # for x in range(240): # Used to debug and read all of the predictions
    #     v = value['predictions'][x]['v']
    #     t = value['predictions'][x]['t']
    #     print ("{} {} {}".format(x,t,v))

    #loop through the tide prediction and figure out the 2 highs and 2 lows we will do this by looking at the next and previous predictions to see if we are in a peak or valley
    for x in range(240):
        # print(x)
        v = value['predictions'][x]['v']
        t = value['predictions'][x]['t']
        #print(x)
        if x != 239: # if we are at the end of the data set don't look for a next prediction
            vnext = value['predictions'][x+1]['v']
        else:
            vnext = None
        if x != 0: # if we are at the beginning of the data set don't look for a previous prediction if not set the previous prediction into vprev
            vprev = value['predictions'][x-1]['v']
        else:
            vprev = None    
        if vprev and float(v) > float(vprev) and vnext and float(v) >= float(vnext): 
            # we need to use float() because tides go negative check to make sure there is a next and previous value if not we ar eat the end of the dataset 
            # and it's unlikely there is a high tide = this WILL display incorrectly when the first or last prediction is the high or low tide, oh well ...
            print("Prediction #:", x)
            print("Prediction:", v)
            print("High Tide:", t)
            highlow[hx] = [v,t] #load the predition and time into the high tide array
            hx = hx+1
        elif vprev and float(v) < float(vprev) and vnext and float(v) <= float(vnext):
            print("Prediction #:", x)
            print("Prediction:", v)
            print("Low Tide:", t)
            highlow[hx] = [v,t] #load the predition and time into the high tide array
            hx = hx+1

    for x in highlow:
        print(x)	
  
#Loop through the highlow prediction array and format the AM PM of the time - wish I had datetime library to do this
    for x in range(4):
        if highlow[x]:
            text_areas[x+1].text = highlow[x][0]
            hm=highlow[x][1][-5:]
            m=hm[-3:]
            h=int(hm[:2]) if int(hm[:2]) <=12 else int(hm[:2])-12
            if h==0:
                h=12
            ampm = ' AM' if int(hm[:2]) <=11 else ' PM'
            hm=str(h) + m
            text_areas[x+6].text = hm + ampm

    pd_index = 0
    pd_run = 0
    while "{:02d}".format(timeval.tm_mday) == day: #stop the loop when the day changes so we can load the next day's tides
        # figure out where in the day we are to display the right prediction we do this by turning the current 
        # time into min elapsed since midnight and divide by 6 - we will use the floor function so we get an integer vs a decimal
        pd_index = math.floor(((timeval.tm_hour * 60) + timeval.tm_min)/6)
            # update the display when we are at the next tide prediction
        if (pd_run == 0) or pd_index != pd_run:
            try:
                timeval = time.localtime()
                # read the next prediction to see if we are rising or falling but stop at the last prediction
                if pd_index <239:
                    if float(value['predictions'][pd_index]['v']) > float(value['predictions'][pd_index + 1]['v']):
                    	direction = 'Falling ↓'
                    else:
                    	direction = 'Rising ↑'
                else:
                    direction = 'Stay Tuned...'
                print (pd_index)
                #print("Response is", value)
                print(value['predictions'][pd_index]['v'])
                print(value['predictions'][pd_index]['t'])
                print(direction)
                text_areas[0].text = direction
                text_areas[5].text = value['predictions'][pd_index]['v']
                pd_run = pd_index #update the prediction run variable so we can update on the next prediction time change
            except RuntimeError as e:
                print("Some error occured, retrying! -", e)
                continue
        # update the system clock every hour - the pyportal clock isn't very accurate 
        if (not update_clock) or (time.monotonic() - update_clock) > 3600:
            try:
                print("Getting time from internet!")
                pyportal.get_local_time()
                update_clock = time.monotonic()
            except RuntimeError as e:
                print("Some error occured, retrying! -", e)
                continue      
        #update the current time from the system clock          
        now = time.localtime()
        # Split out the min and hours to display 12 hour time 
        hour = now[3]
        minute = now[4]
        format_str = "%d:%02d"
        if hour >= 12:
            hour -= 12
            format_str = format_str+" PM"
        else:
            format_str = format_str+" AM"
        if hour == 0:
            hour = 12
        time_str = format_str % (hour, minute)
        print(time_str)
        text_areas[10].text = time_str
        #only update the clock every 30 sec - this isn't a clock for time it's a clock for tides!
        time.sleep(30)
        timeval = time.localtime()