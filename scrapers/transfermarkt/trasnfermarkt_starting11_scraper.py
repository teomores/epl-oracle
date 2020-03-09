import pandas as pd
from selenium import webdriver
import time
from datetime import datetime
from selenium.common.exceptions import NoSuchElementException
import pickle
import os
from csv import DictWriter
from tqdm import tqdm
import pickle

"""
prendi url da qua
https://www.transfermarkt.com/serie-a/gesamtspielplan/wettbewerb/IT1/saison_id/2018 #serie a
https://www.transfermarkt.com/bundesliga/gesamtspielplan/wettbewerb/L1/saison_id/2018 # bundes
"""

def scrape(url: str, league: str, year: int, n_teams= 20) -> None:
    # get ChromeDriver
    driver = webdriver.Chrome('E:/USDE/scrapers/chromedriver.exe')

    # this snippet of code gets all the match urls, it's pretty slow so I don't want to do it everytime
    if os.path.exists(f'{league}_{year}_urls.pickle'):
        with open(f'{league}_{year}_urls.pickle','rb') as f:
            list_url = pickle.load(f)
    else:
        print(f'Non esiste {league}_{year}_urls.pickle')
        driver.get(url)
        driver.implicitly_wait(3)
        list_url = []

        for i in tqdm(range(2,(n_teams-1)*2+2)):
            table = driver.find_element_by_xpath(f'//*[@id="main"]/div[10]/div[{i}]/div/table')
            for row in table.find_elements_by_css_selector('tr'):
                if row.get_attribute('class') != 'bg_blau_20':
                    for td in row.find_elements_by_css_selector('td'):
                        if td.get_attribute('class') == 'zentriert hauptlink':
                            list_url.append(td.find_elements_by_css_selector('a')[0].get_attribute('href'))
        with open(f'{league}_{year}_urls.pickle','wb') as f:
            pickle.dump(list_url,f)
    print(f'Total matches: {len(list_url)}')

    if os.path.exists(f'{league}_{year}_lineup_urls.pickle'):
        with open(f'{league}_{year}_lineup_urls.pickle','rb') as f:
            lineup_url = pickle.load(f)
    else:
        lineup_url = []
        for u in tqdm(list_url):
            driver.get(u)
            driver.implicitly_wait(1)
            lineup_url.append(driver.find_element_by_xpath('//*[@id="line-ups"]/a').get_attribute('href'))
        with open(f'{league}_{year}_lineup_urls.pickle','wb') as f:
            pickle.dump(lineup_url,f)
    print(f'Total matches lineups: {len(lineup_url)}')

    


if __name__ == '__main__':
    scrape('https://www.transfermarkt.com/serie-a/gesamtspielplan/wettbewerb/IT1/saison_id/2018', 'serie_a', 2018)