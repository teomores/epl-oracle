import pandas as pd
from selenium import webdriver
import time
from selenium.common.exceptions import NoSuchElementException
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
    years = [i for i in range(2009,2019)]
    match_rounds = [x for x in range(1,n_matches+1)]
    driver = webdriver.Chrome('E:/USDE/scrapers/chromedriver.exe')
    for year in years:
        if not os.path.exists(f'classifica_{league}_{year}{year+1}.csv'):
            print(f'Scraping the {n_matches} rounds of year {year}:')
            columns = ['match_year','match_round','team','team_rank','team_points','team_goal_difference','team_goal_fatti','team_goal_subiti']
            df_results = pd.DataFrame(columns=columns)
            for mr in tqdm(match_rounds):
                if league == 'serie-a':
                    driver.get(f"https://www.transfermarkt.com/serie-a/spieltagtabelle/wettbewerb/IT1/saison_id/{year}/spieltag/{mr}")
                elif league == 'liga':
                    driver.get(f'https://www.transfermarkt.com/laliga/spieltagtabelle/wettbewerb/ES1/saison_id/{year}/spieltag/{mr}')
                elif league == 'bundesliga':
                    driver.get(f'https://www.transfermarkt.com/bundesliga/spieltagtabelle/wettbewerb/L1/saison_id/{year}/spieltag/{mr}')
                else: # in questo caso è la premier
                    driver.get(f'https://www.transfermarkt.com/premier-league/spieltagtabelle/wettbewerb/GB1/saison_id/{year}/spieltag/{mr}')
                
                table = waiter.find_element(driver, '//*[@id="main"]/div[10]/div[1]/div[3]/table/tbody', by=XPATH)
                for row in table.find_elements_by_css_selector('tr'):
                    tds = row.find_elements_by_css_selector('td')
                    df_results = df_results.append({
                        'match_year' : year,
                        'match_round' : mr+1,
                        'team' : tds[2].text.strip(),
                        'team_rank' : int(tds[0].text),
                        'team_points' : int(tds[9].text),
                        'team_goal_difference' : int(tds[8].text),
                        'team_goal_fatti' : int(tds[7].text.strip().split(':')[0]),
                        'team_goal_subiti': int(tds[7].text.strip().split(':')[1])
                    }, ignore_index=True)
            df_results.to_csv(f'classifica_{league}_{year}{year+1}.csv', index=False)
        else:
            print(f'classifica_{league}_{year}{year+1}.csv already exists.')
            
if __name__=='__main__':
    get_table('bundesliga')
    get_table('laliga')
    get_table('premier-league')