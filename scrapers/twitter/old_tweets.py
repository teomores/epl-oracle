import pandas as pd
from selenium import webdriver
import time
from selenium.common.exceptions import NoSuchElementException
from explicit import waiter, ID, XPATH
import os
from twython import Twython
DIRNAME = os.path.dirname(__file__)
N_TWEETS = 100

hashtag = 'afc'
date_1 = '2019-05-11'
date_2 = '2019-05-09'

url = f"https://twitter.com/search?q=%23{hashtag}%20until%3A{date_1}%20since%3A{date_2}&src=typed_query&f=live"
driver = webdriver.Chrome('E:/USDE/scrapers/chromedriver.exe')
driver.get(url)
time.sleep(2)
tweet_box = waiter.find_element(driver,'//*[@id="react-root"]/div/div/div[2]/main/div/div/div/div/div/div/div/div/section/div/div/div', by=XPATH)
tweet_ids = []
for i in range(N_TWEETS):
    try: # se non lo trova è perché non lo ha caricato
        tw_id = driver.find_element_by_xpath(f'//*[@id="react-root"]/div/div/div[2]/main/div/div/div/div/div/div/div/div/section/div/div/div/div[{i+1}]/div/article/div/div/div[2]/div[2]/div[1]/div/div/div[1]/a')\
                    .get_attribute('href')\
                    .split('/')[-1]
        tweet_ids.append(tw_id)
    except NoSuchElementException:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        try: # se non lo trova vuol dire che non è un tweet
            tw_id = driver.find_element_by_xpath(f'//*[@id="react-root"]/div/div/div[2]/main/div/div/div/div/div/div/div/div/section/div/div/div/div[{i+1}]/div/article/div/div/div[2]/div[2]/div[1]/div/div/div[1]/a')\
                        .get_attribute('href')\
                        .split('/')[-1]
            tweet_ids.append(tw_id)
        except NoSuchElementException:
            pass
print(f'Found {len(tweet_ids)} tweets.')
# get id
login_dict = eval(open(os.path.join(DIRNAME, 'twitter_login.txt'), 'r').read()) 
twitter = Twython(
    login_dict['API_key'], login_dict['API_secret_key'],
    login_dict['Access_token'], login_dict['Access_token_secret'])

for tw_id in tweet_ids:
    tweet = twitter.show_status(id=tw_id)
    print(tweet['text'])

# SCROLL_PAUSE_TIME = 1

# # Get scroll height
# last_height = driver.execute_script("return document.body.scrollHeight")

# while True:
#     # Scroll down to bottom
#     driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

#     # Wait to load page
#     time.sleep(1)

#     # Calculate new scroll height and compare with last scroll height
#     new_height = driver.execute_script("return document.body.scrollHeight")
#     if new_height == last_height:
#         break
#     last_height = new_height