from selenium import webdriver
import bs4 as bs
BASE_URL = 'https://www.oddsportal.com/soccer'
MONTH_DICT = {
    'Jan':'01',
    'Feb':'02',
    'Mar':'03',
    'Apr':'04',
    'May':'05',
    'Jun':'06'
}
SERIE_A_URL = BASE_URL+'/italy/serie-a/'
driver = webdriver.Chrome('chromedriver.exe')
driver.get(SERIE_A_URL)

match_urls = [] # qui ci metterò le partite
table = driver.find_element_by_id('tournamentTable')
for i,row in enumerate(table.find_elements_by_css_selector('tr')):
    el_class = row.get_attribute("class")
    if el_class!='dark center' and el_class!='table-dummyrow' and el_class!='center nob-border':
        t = driver.find_elements_by_xpath(f'//*[@id="tournamentTable"]/tbody/tr[{i+1}]/td[2]/a[2]')
        match_urls.append(t[0].get_attribute('href'))
print(match_urls)
for m in match_urls:
    print('================================================================================')
    driver.get(m)
    match_name = driver.find_element_by_xpath('//*[@id="col-content"]/h1').text.lower().split('-')
    team_1 = match_name[0].strip()
    team_2 = match_name[1].strip()
    print(f'TEAM 1: {team_1}')
    print(f'TEAM 2: {team_2}')
    date = driver.find_element_by_xpath('//*[@id="col-content"]/p[1]').text
    date = date.replace(',','').split(' ')
    date[2] = MONTH_DICT[date[2]]
    day_name, day_number, month, year = date[0], date[1], date[2], date[3]
    print(f'DAY OF THE WEEK: {day_name}')
    print(f"DAY: {day_number + '/' + month + '/' + year}")
