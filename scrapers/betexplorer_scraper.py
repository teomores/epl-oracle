import pandas as pd
from selenium import webdriver
import time
from datetime import datetime
from selenium.common.exceptions import NoSuchElementException
import pickle
import os

BASE_URL = 'https://www.betexplorer.com/soccer/'

def _scrape_league_matches(league_url: str) -> list:
    match_urls_list = [] # to keep match urls

    # get ChromeDriver
    driver = webdriver.Chrome('chromedriver.exe')
    driver.get(league_url)

    try:
        driver.find_element_by_xpath('//*[@id="league-summary-results"]/ul[1]/li[2]/div/ul/li').click()
        driver.find_element_by_xpath('//*[@id="league-summary-results"]/ul[1]/li[2]/div/ul/li[10]').click()
        driver.implicitly_wait(3)
    except NoSuchElementException:
        pass

    table = driver.find_element_by_xpath('//*[@id="js-leagueresults-all"]/div/div/table')
    for row in table.find_elements_by_css_selector('tr'):
        if row.text[0].isdigit() == False:
            url = row.find_elements_by_css_selector('a')[0].get_attribute('href')
            match_urls_list.append(url)
    print(f'Total matches: {len(match_urls_list)}')

    with open('betexplorer_urls', 'wb') as fp:
        pickle.dump(match_urls_list, fp)
    return match_urls_list

def scrape(country: str, league: str, start_year: int) -> None:
    # create pandas dataframe
    columns = ['current_timestamp','match_date','match_day', # per ora attacco il timestamp, poi pulirò
                'match_hour','team_1','team_2','bookmaker','1','X','2']
    df_results = pd.DataFrame(columns=columns)

    try:
        with open ('betexplorer_urls', 'rb') as fp:
            match_urls_list = pickle.load(fp)
    except IOError:
        # se non c'è il file con tutte le urls me lo ricreo
        league_url = BASE_URL + f'{country}/{league}-{start_year}-{start_year+1}/' # url to get matches from
        match_urls_list = _scrape_league_matches(league_url)

    # get ChromeDriver
    driver = webdriver.Chrome('chromedriver.exe')
    count = 0
    for url in match_urls_list[:1]:
        print('==============================================')
        driver.get(url)
        match_teams = driver.find_element_by_xpath('/html/body/div[4]/div[4]/div/div/div[1]/section/ul[1]/li[5]/span').text.split('-')
        home_team, away_team = match_teams[0].strip(), match_teams[1].strip() 
        match_date = driver.find_element_by_xpath('//*[@id="match-date"]').text.split('-')
        date, hour = match_date[0].strip(), match_date[1].strip()
        match_result =  driver.find_element_by_xpath('//*[@id="js-score"]').text.split(':')
        home_goals, away_goals = match_result[0].strip(), match_result[1].strip() 
        count += 1
        print(f'{count}: {home_team} - {away_team} - {date} - {hour} - {home_goals}:{away_goals}')

        driver.implicitly_wait(0.5)
        table = driver.find_elements_by_id('sortable-1')[0]
        for row in table.find_elements_by_css_selector('tr')[:-1]: # tolgo l'ultima perché fa average odds
            for i,odds in enumerate(row.find_elements_by_css_selector('td')):
                if i == 0:
                    print(odds.text)
                elif i == 1 or i == 2:
                    pass
                else:
                    print(f"ODD: {odds.get_attribute('data-odd')}")
                    print(f"OPENING ODD: {odds.get_attribute('data-opening-odd')}")




if __name__=='__main__':
    scrape('italy','serie-a',2018)
