import pandas as pd
from selenium import webdriver
import time
from selenium.common.exceptions import NoSuchElementException
import pickle
import os
from tqdm import tqdm
from explicit import waiter, XPATH

"""
Questo per giornata di campionato tira fuori la classifica per ogni squadra.
"""

def get_table(league: str) -> None:
    print(f'Scraping league: {league}...')
    if league == 'bundesliga':
        n_matches = 34
    else:
        n_matches = 38
    years = [2013]
    match_rounds = [x for x in range(1,n_matches+1)]
    driver = webdriver.Chrome('E:/USDE/scrapers/chromedriver.exe')
    for year in years:
        print(f'Scraping the {n_matches} rounds of year {year}:')
        columns = ['match_year','match_round','team','rank','points','goal_difference']
        df_results = pd.DataFrame(columns=columns)
        for mr in tqdm(match_rounds):
            if league == 'serie-a':
                driver.get(f"https://www.transfermarkt.com/serie-a/spieltagtabelle/wettbewerb/IT1/saison_id/{year}/spieltag/{mr}")
            elif league == 'liga':
                driver.get(f'https://www.transfermarkt.com/laliga/spieltag/wettbewerb/ES1/plus/?saison_id={year}&spieltag={mr}')
            elif league == 'bundesliga':
                driver.get(f'https://www.transfermarkt.com/bundesliga/spieltag/wettbewerb/L1/plus/?saison_id={year}&spieltag={mr}')
            else: # in questo caso è la premier
                driver.get(f"https://www.transfermarkt.com/premier-league/spieltag/wettbewerb/GB1/plus/?saison_id={year}&spieltag={mr}")
            
            table = waiter.find_element(driver, '//*[@id="main"]/div[10]/div[1]/div[3]/table/tbody', by=XPATH)
            for i,team in enumerate(table.find_elements_by_class_name('no-border-links hauptlink')):
                print(team.text)
            
if __name__=='__main__':
    get_table('serie-a')