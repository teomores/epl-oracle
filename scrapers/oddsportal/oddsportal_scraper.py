from selenium import webdriver
import bs4 as bs
from selenium.common.exceptions import NoSuchElementException
import time
from datetime import datetime
import pandas as pd
from csv import DictWriter

##################################
# YOU ONLY HAVE TO CHANGE THESE! #
##################################
# countries:
# inghilterra : england
# italia : italy
# francia : france
# spagna : spain
# germania : germany
#
# Serie A : serie-a
# Serie B : serie-b
#
# Ligue 1 : ligue-1
# Ligue 2 : ligue-2
#
# Liga : laliga
# Liga 2 : laliga2
#
# Premier League : premier-league
# Championship : championship
#
# Bundesliga : bundesliga
# Bundesliga 2 : 2-bundesliga
#################################
BASE_URL = 'https://www.oddsportal.com/soccer'
MONTH_DICT = {
    'Jan':'01',
    'Feb':'02',
    'Mar':'03',
    'Apr':'04',
    'May':'05',
    'Jun':'06'
}

def scrape_league(COUNTRY: str, LEAGUE: str) -> None:
    LEAGUE_URL = BASE_URL+f'/{COUNTRY}/{LEAGUE}/'

    # create pandas dataframe
    columns = ['current_timestamp','match_date','match_day', # per ora attacco il timestamp, poi pulirò
                'match_hour','team_1','team_2','bookmaker','1','X','2']
    df_results = pd.DataFrame(columns=columns)

    # get ChromDriver
    driver = webdriver.Chrome('../chromedriver.exe')
    driver.get(LEAGUE_URL)
    # controlla se mostra tutti i risultati o meno, se mai clicca il pulsante "Show all matches"
    try:
        driver.find_element_by_xpath('//*[@id="show-all-link"]/div/div/div/div/p/a').click()
    except NoSuchElementException:
        pass

    # first, get all match urls
    match_urls = [] # qui ci metterò le partite
    table = driver.find_element_by_id('tournamentTable')
    for i,row in enumerate(table.find_elements_by_css_selector('tr')):
        el_class = row.get_attribute("class")
        if el_class!='dark center' and el_class!='table-dummyrow' and el_class!='center nob-border':
            print(row.text)
            try:
                t = driver.find_elements_by_xpath(f'//*[@id="tournamentTable"]/tbody/tr[{i+1}]/td[2]/a[2]')
                match_urls.append(t[0].get_attribute('href'))
            except IndexError:
                t = driver.find_elements_by_xpath(f'//*[@id="tournamentTable"]/tbody/tr[{i+1}]/td[2]/a')
                match_urls.append(t[0].get_attribute('href'))
    print(match_urls)

    # now, for each match get the betting odds and the match date
    for m in match_urls:
        print('=====================================================================')
        i = 0
        while i<10: # riprova 10 volte, se in 10 volte non riesce a prendere le quote esce
            try:
                driver.get(m)
                match_name = driver.find_element_by_xpath('//*[@id="col-content"]/h1').text.lower().split('-')
                team_1 = match_name[0].strip()
                team_2 = match_name[1].strip()
                print(f'TEAM 1: {team_1}')
                print(f'TEAM 2: {team_2}')
                date = driver.find_element_by_xpath('//*[@id="col-content"]/p[1]').text
                date = date.replace(',','').split(' ')
                date[2] = MONTH_DICT[date[2]]
                day_name, day_number, month, year, hour = date[0], date[1], date[2], date[3], date[4]
                print(f'DAY OF THE WEEK: {day_name}')
                print(f"DAY: {day_number + '/' + month + '/' + year}")
                print(f'HOUR: {hour}')
                table = driver.find_element_by_xpath('//*[@id="odds-data-table"]/div[1]/table/tbody')
                for betting_site in table.find_elements_by_css_selector('tr')[:len(table.find_elements_by_css_selector('tr'))-1]:
                    site = betting_site.find_elements_by_css_selector("td")[0].text.lower().strip()
                    print(f'BETTING SITE: {site}')
                    for i,odds in enumerate(betting_site.find_elements_by_css_selector('td')[1:4]):
                        if i == 0:
                            odds_1 = odds.text
                            print(f'1: {odds_1}')
                        elif i == 1:
                            odds_X = odds.text
                            print(f'X: {odds_X}')
                        elif i == 2:
                            odds_2 = odds.text
                            print(f'2: {odds_2}')
                        else:
                            print(f'ERROR: {odds.text}')
                    # write results
                    with open(f'{LEAGUE}.csv', 'a+', newline='') as f:
                        dict_writer = DictWriter(f, fieldnames=df_results.columns)
                        dict_writer.writerow(
                            {
                            'current_timestamp' : int(time.time()),
                            'match_date' : f'{day_number}-{month}-{year}',
                            'match_day' : day_name,
                            'match_hour' : hour,
                            'team_1' : team_1,
                            'team_2' : team_2,
                            'bookmaker' : site,
                            '1' : odds_1,
                            'X' : odds_X,
                            '2' : odds_2
                            }
                        )
                i = 42 # serve solo per uscire dal loop
            except NoSuchElementException:
                time.sleep(2)
                i+=1

if __name__ == '__main__':
    # ITALIA
    scrape_league('italy', 'serie-a')
    scrape_league('italy', 'serie-b')
    # SPAGNA
    scrape_league('spain', 'laliga')
    scrape_league('spain', 'laliga2')
    # FRANCIA
    scrape_league('france', 'ligue-1')
    scrape_league('france', 'ligue-2')
    # GERMANIA
    scrape_league('germany', 'bundesliga')
    scrape_league('germany', '2-bundesliga')
    # INGHILTERRA
    scrape_league('england', 'premier-league')
    scrape_league('england', 'championship')
