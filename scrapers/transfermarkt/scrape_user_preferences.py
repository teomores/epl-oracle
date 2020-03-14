import pandas as pd
from selenium import webdriver
import time
from selenium.common.exceptions import NoSuchElementException
import pickle
import os
from tqdm import tqdm
import re

"""
Questo per ogni match tira fuori le preferenze degli utenti nella lega di transfermarkt.
"""

def get_transfer_user_predictions(league: str) -> None:
    print(f'Scraping league: {league}...')
    if league == 'bundesliga':
        n_matches = 34
    else:
        n_matches = 38
    years = [2016,2017]
    match_rounds = [x for x in range(1,n_matches+1)]
    driver = webdriver.Chrome('E:/USDE/scrapers/chromedriver.exe')
    for year in years:
        print(f'Scraping the {n_matches} rounds of year {year}:')
        columns = ['match_year','match_round','home_team','away_team','ht_win_pred_transfer','draw_pred_transfer','at_win_pred_transfer']
        df_results = pd.DataFrame(columns=columns)
        for mr in tqdm(match_rounds):
            if league == 'serie-a':
                driver.get(f"https://www.transfermarkt.com/serie-a/spieltag/wettbewerb/IT1/plus/?saison_id={year}&spieltag={mr}")
            elif league == 'liga':
                driver.get(f'https://www.transfermarkt.com/laliga/spieltag/wettbewerb/ES1/plus/?saison_id={year}&spieltag={mr}')
            elif league == 'bundesliga':
                driver.get(f'https://www.transfermarkt.com/bundesliga/spieltag/wettbewerb/L1/plus/?saison_id={year}&spieltag={mr}')
            else: # in questo caso è la premier
                driver.get(f"https://www.transfermarkt.com/premier-league/spieltag/wettbewerb/GB1/plus/?saison_id={year}&spieltag={mr}")
            time.sleep(2)
            main_div = driver.find_element_by_xpath ('//*[@id="main"]/div[10]/div[1]')
            all_divs = main_div.find_elements_by_class_name('box')
            for i,m in enumerate(all_divs):
                if i!=0 and i!=len(all_divs)-1:
                    t = m.text.split('\n')[0]
                    ht, at = t.split(':')[0], t.split(':')[1]
                    ht = " ".join(re.split("[^a-zA-Z]+", ht)).strip()
                    at = " ".join(re.split("[^a-zA-Z]+", at)).strip()
                    predictions = m.text.split('\n')[-2].replace(',','.').strip()
                    if predictions.endswith('%'):
                        hw_pred, draw_pred, aw_pred = float(predictions.split('%')[0]), float(predictions.split('%')[1]), float(predictions.split('%')[2])
                    else:
                        hw_pred, draw_pred, aw_pred = -1, -1, -1
                    df_results = df_results.append({
                        'match_year' : year,
                            'match_round' : mr,
                            'home_team' : ht,
                            'away_team' : at,
                            'ht_win_pred_transfer' : hw_pred,
                            'draw_pred_transfer' : draw_pred,
                            'at_win_pred_transfer' : aw_pred,
                    }, ignore_index=True)
    
        if os.path.exists(f'{league}_{year}_transfer_user_preds.csv'):
            os.remove(f'{league}_{year}_transfer_user_preds.csv')
        df_results.to_csv(f'{league}_{year}_transfer_user_preds.csv', index=False)

if __name__ == '__main__':
    # la lega può essere : serie-a, liga, bundesliga o premier
    get_transfer_user_predictions('liga')