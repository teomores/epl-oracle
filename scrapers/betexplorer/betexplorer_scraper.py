import pandas as pd
from selenium import webdriver
import time
from datetime import datetime
from selenium.common.exceptions import NoSuchElementException
import pickle
import os
from csv import DictWriter

"""
Questo script scrapa betexplorer per gli anni passati. 
Dal 2019/2020 hanno iniziato a mettere anche le quote giorno per giorno, per fare scraping
anche di quelle:
    try:
        odds.click()
        time.sleep(2)
        element = driver.find_element_by_xpath('//*[@id="js-popup"]/div/div/div/span')
        driver.execute_script("arguments[0].click();", element) # perché c'è del js
    except NoSuchElementException:
        pass
"""

BASE_URL = 'https://www.betexplorer.com/soccer/'

def _scrape_league_matches(league_url: str) -> list:
    match_urls_list = [] # to keep match urls

    # get ChromeDriver
    driver = webdriver.Chrome('E:/USDE/scrapers/chromedriver.exe')
    driver.get(league_url)

    # se non visualizza tutte le partita aumenta il tempo
    try:
        driver.find_element_by_xpath('//*[@id="league-summary-results"]/ul[1]/li[2]/div/ul/li').click()
        driver.find_element_by_xpath('//*[@id="league-summary-results"]/ul[1]/li[2]/div/ul/li[9]').click() # questo cambialo perché a volte è 10 e a volte è 9
        driver.implicitly_wait(3)
    except NoSuchElementException:
        pass

    table = driver.find_element_by_xpath('//*[@id="js-leagueresults-all"]/div/div/table')
    for row in table.find_elements_by_css_selector('tr'):
        if row.text[0].isdigit() == False:
            url = row.find_elements_by_css_selector('a')[0].get_attribute('href')
            match_urls_list.append((url,match_round))
        else:
            match_round = row.text.split('.')[0]
    print(f'Total matches: {len(match_urls_list)}')
    return match_urls_list

def scrape(country: str, league: str, start_year: int) -> None:
    # create pandas dataframe
    columns = ['match_date', 'match_hour', 'match_round', 'home_team','away_team','home_goals','away_goals','bookmaker','1','X','2','opening_1','opening_X','opening_2']
    df_results = pd.DataFrame(columns=columns)
    with open(f'{league}_{start_year}.csv', 'a+', newline='') as f:
                    dict_writer = DictWriter(f, fieldnames=df_results.columns)
                    dict_writer.writerow(
                        {
                        'match_date' : 'match_date',
                        'match_hour' : 'match_hour',
                        'match_round' : 'match_round',
                        'home_team' : 'home_team',
                        'away_team' : 'away_team',
                        'home_goals' : 'home_goals',
                        'away_goals' : 'away_goals',
                        'bookmaker' : 'bookmaker',
                        '1' : '1',
                        'X' : 'X',
                        '2' : '2',
                        'opening_1' : 'opening_1',
                        'opening_X' : 'opening_X',
                        'opening_2' : 'opening_2'
                        }
                    )

    league_url = BASE_URL + f'{country}/{league}-{start_year}-{start_year+1}/' # url to get matches from
    match_urls_list = _scrape_league_matches(league_url)

    # get ChromeDriver
    driver = webdriver.Chrome('E:/USDE/scrapers/chromedriver.exe')
    count = 0
    for url, match_round in match_urls_list:
        print('==============================================')
        driver.get(url)
        match_teams = driver.find_element_by_xpath('/html/body/div[4]/div[4]/div/div/div[1]/section/ul[1]/li[5]/span').text.split('-')
        home_team, away_team = match_teams[0].strip(), match_teams[1].strip() 
        match_date = driver.find_element_by_xpath('//*[@id="match-date"]').text.split('-')
        date, hour = match_date[0].strip(), match_date[1].strip()
        match_result =  driver.find_element_by_xpath('//*[@id="js-score"]').text.split(':')
        home_goals, away_goals = match_result[0].strip(), match_result[1].strip() 
        count += 1
        print(f'{count}/{len(match_urls_list)}: {match_round} - {home_team} - {away_team} - {date} - {hour} - {home_goals}:{away_goals}')

        driver.implicitly_wait(2)
        table = driver.find_elements_by_id('sortable-1')[0]
        bookmaker = hw_odd = hw_opening_odd = draw_odd = draw_opening_odd = aw_odd = aw_opening_odd =''
        for row in table.find_elements_by_css_selector('tr')[:-1]: # tolgo l'ultima perché fa average odds
            for i,odds in enumerate(row.find_elements_by_css_selector('td')):
                if i == 0:
                    bookmaker = odds.text.lower()
                    #print(f"BOOKMAKER: {bookmaker}")
                elif i == 1 or i == 2:
                    pass
                elif i == 3:
                    hw_odd = odds.get_attribute('data-odd')
                    #print(f"1 ODD: {hw_odd}")
                    hw_opening_odd = odds.get_attribute('data-opening-odd')
                    #print(f"1 OPENING ODD: {hw_opening_odd}")
                elif i == 4:
                    draw_odd = odds.get_attribute('data-odd')
                    #print(f"X ODD: {draw_odd}")
                    draw_opening_odd = odds.get_attribute('data-opening-odd')
                    #print(f"X OPENING ODD: {draw_opening_odd}")
                elif i ==5:
                    aw_odd = odds.get_attribute('data-odd')
                    #print(f"2 ODD: {aw_odd}")
                    aw_opening_odd = odds.get_attribute('data-opening-odd')
                    #print(f"2 OPENING ODD: {aw_opening_odd}")
            if bookmaker != '':
                with open(f'{league}_{start_year}.csv', 'a+', newline='') as f:
                    dict_writer = DictWriter(f, fieldnames=df_results.columns)
                    dict_writer.writerow(
                        {
                        'match_date' : date,
                        'match_hour' : hour,
                        'match_round' : match_round,
                        'home_team' : home_team,
                        'away_team' : away_team,
                        'home_goals' : home_goals,
                        'away_goals' : away_goals,
                        'bookmaker' : bookmaker,
                        '1' : hw_odd,
                        'X' : draw_odd,
                        '2' : aw_odd,
                        'opening_1' : hw_opening_odd,
                        'opening_X' : draw_opening_odd,
                        'opening_2' : aw_opening_odd
                        }
                    )

if __name__=='__main__':
    scrape('germany','bundesliga',2018)
