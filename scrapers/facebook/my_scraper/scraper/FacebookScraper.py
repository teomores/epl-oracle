import codecs
from bs4 import BeautifulSoup
import csv
import itertools
import json
import re
import sys
import time
import warnings
from datetime import datetime
from urllib import parse as urlparse
import requests
from tqdm import tqdm
import pandas as pd
import os

from requests import RequestException
from requests_html import HTML, HTMLSession

"""
This is the Facebook scraper class used to gather information from the public pages
of the EPL soccer teams.
In order to use this script one needs to insert the credentials.

Note: this script may need some little changes to work, due to changes on the Facebook side
(anyways it worked until 07/10/20()
"""



class FacebookScraper:
    def __init__(self, credentials:dict):
        self.s = requests.Session()
        self.EMAIL = credentials['email']
        self.PASS = credentials['pass']

        self._BASE_URL = 'https://m.facebook.com'
        _user_agent = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/76.0.3809.87 Safari/537.36")
        _cookie = ('locale=en_US;')
        self._HEADERS = {'User-Agent': _user_agent, 'Accept-Language': 'en-US,en;q=0.5', 'cookie': _cookie}

        self._session = None
        self._timeout = None

        self._LIKES_REGEX = re.compile(r'like_def[^>]*>([0-9,.]+)')
        self._COMMENT_REGEX = re.compile(r'cmt_def[^>]*>([0-9,.]+)')
        self._SHARES_REGEX = re.compile(r'([0-9,.]+)\s+Shares', re.IGNORECASE)
        self._LINK_REGEX = re.compile(r"href=\"https:\/\/lm\.facebook\.com\/l\.php\?u=(.+?)\&amp;h=")

        self._CURSOR_REGEX = re.compile(r'href:"(/page_content[^"]+)"')  # First request
        self._CURSOR_REGEX_2 = re.compile(r'href":"(\\/page_content[^"]+)"')  # Other requests

        self._PHOTO_LINK = re.compile(r"href=\"(/[^\"]+/photos/[^\"]+?)\"")
        self._IMAGE_REGEX = re.compile(r"<a href=\"([^\"]+?)\" target=\"_blank\" class=\"sec\">View Full Size<\/a>", re.IGNORECASE)
        self._IMAGE_REGEX_LQ = re.compile(r"background-image: url\('(.+)'\)")
        self._POST_URL_REGEX = re.compile(r'/story.php\?story_fbid=')

        self._MORE_URL_REGEX = re.compile(r'(?<=…\s)<a href="([^"]+)')
        self._POST_STORY_REGEX = re.compile(r'href="(\/story[^"]+)" aria')

        self._SHARES_AND_REACTIONS_REGEX = re.compile(
            r'<script>.*bigPipe.onPageletArrive\((?P<data>\{.*RelayPrefetchedStreamCache.*\})\);.*</script>')
        self._BAD_JSON_KEY_REGEX = re.compile(r'(?P<prefix>[{,])(?P<key>\w+):')

        self.login()

    def login(self):
        LOGIN_URL = "https://www.facebook.com/login.php?refsrc=https%3A%2F%2Fm.facebook.com%2F&amp;refid=8"
        r = self.s.get(self._BASE_URL)
        soup = BeautifulSoup(r.text, features="lxml")
        tmp = soup.find(attrs={"name": "lsd"})
        lsd = tmp["value"]
        data = {
            'lsd': lsd
        }
        data['email'] = self.EMAIL
        data['pass'] = self.PASS
        data['login'] = 'Log In'
        r = self.s.post(LOGIN_URL, data=data)
    
    def scrape_ajax(self, n_pages=1, url="https://www.facebook.com/pg/Arsenal/posts/?ref=page_internal", get_reactions=True):
        print(f"Scraping {url}...")
        page_id_regex = re.compile(r'page_id=(.*?)&')
        cursor_regex = re.compile(r"timeline_cursor%22%3A%22(.*?)%")
        post_id_regex = re.compile(r'"story_fbid":\["(.*?)"]')
        new_cursor_regex = re.compile(r'timeline_cursor\\\\u002522\\\\u00253A\\\\u002522(.*?)\\\\')

        posts = []
        urls = []

        response = requests.get(url)
        soup = BeautifulSoup(response.content, features="lxml")
        divs = soup.find_all("div", id=re.compile("^feed_subtitle_"))
        for d in divs:
            try:
                posts.append(d.get("id").split(";")[1])
                urls.append(url)
            except IndexError:
                print(f"{d.get('id')} strano...")
        first_url = soup.find(id='www_pages_reaction_see_more_unitwww_pages_posts').div.a.get('ajaxify')
        # print(first_url)
        page_id = page_id_regex.search(first_url).group(1)
        first_cursor = cursor_regex.search(first_url).group(1)
        
        new_url = f"https://m.facebook.com/page_content_list_view/more/?page_id={page_id}&start_cursor=%7B%22timeline_cursor%22%3A%22{first_cursor}%22%2C%22timeline_section_cursor%22%3Anull%2C%22has_next_page%22%3Atrue%7D&num_to_fetch={8}&surface_type=posts_tab"
        print(f"NEW URL: {new_url}")
        first_page = str(BeautifulSoup(requests.get(new_url, headers=self._HEADERS).content, features="html.parser"))
        for pi in post_id_regex.findall(first_page):
            posts.append(pi)
            urls.append(new_url)
        new_cursor = new_cursor_regex.search(first_page).group(1)
        new_url = f"https://m.facebook.com/page_content_list_view/more/?page_id={page_id}&start_cursor=%7B%22timeline_cursor%22%3A%22{new_cursor}%22%2C%22timeline_section_cursor%22%3Anull%2C%22has_next_page%22%3Atrue%7D&num_to_fetch={8}&surface_type=posts_tab"
        print(f"NEW URL: {new_url}")
        for i in tqdm(range(n_pages)):
            old_len = len(posts)
            p = str(BeautifulSoup(requests.get(new_url, headers=self._HEADERS).content, features="html.parser"))
            for pi in post_id_regex.findall(p):
                posts.append(pi)
                urls.append(new_url)
            # print(f"Iteration {i+1}: scraped {len(posts)-old_len} posts at url {new_url}")
            try:
                new_cursor = new_cursor_regex.search(p).group(1)
            except AttributeError: # in questo caso esce dal loop perché non ci sono più posts
                print(f"Cannot find cursor in at url {new_url}")
                break
            new_url = f"https://m.facebook.com/page_content_list_view/more/?page_id={page_id}&start_cursor=%7B%22timeline_cursor%22%3A%22{new_cursor}%22%2C%22timeline_section_cursor%22%3Anull%2C%22has_next_page%22%3Atrue%7D&num_to_fetch={8}&surface_type=posts_tab"
            # print(f"NEW URL: {new_url}")
        # for i,pii in enumerate(posts):
        #     print(f"Post {i}: {pii}")
        df_results = pd.DataFrame(columns = ['post_id','post_url'])
        df_results['post_id'] = posts
        df_results['post_url'] = urls
        if os.path.exists(f'{url.split("/")[-3]}_post_ids.csv'):
            os.remove(f'{url.split("/")[-3]}_post_ids.csv')
        df_results = df_results.drop_duplicates().reset_index(drop=True)
        df_results.to_csv(f'{url.split("/")[-3]}_post_ids_urls.csv', index=False)
        print(len(posts))
        print(len(list(set(posts))))
        print(df_results.shape[0])

        if get_reactions == True:
            self._fetch_reactions_df(df_results, page=url.split("/")[-3])

    def scrape_mobile(self, n_posts=10,url="https://www.facebook.com/pg/Arsenal/posts/?ref=page_internal", get_reactions=False):
        print(f"Scraping {url}...")
        page_id_regex = re.compile(r'page_id=(.*?)&')
        cursor_regex = re.compile(r"timeline_cursor%22%3A%22(.*?)%")
        post_id_regex = re.compile(r'"story_fbid":\["(.*?)"]')
        new_cursor_regex = re.compile(r'timeline_cursor\\\\u002522\\\\u00253A\\\\u002522(.*?)\\\\')
        line_regex = re.compile(r'{"object_fbtype":266,"publish_time":(.*?)"\]}')
        posts = []
        urls = []
        timestamps = []

        response = requests.get(url)
        soup = BeautifulSoup(response.content, features="lxml")
        divs = soup.find_all("div", id=re.compile("^feed_subtitle_"))
        for d in divs:
            try:
                posts.append(d.get("id").split(";")[1])
                urls.append(url)
                timestamps.append(0)
            except IndexError:
                print(f"{d.get('id')} strano...")
        first_url = soup.find(id='www_pages_reaction_see_more_unitwww_pages_posts').div.a.get('ajaxify')
        # print(first_url)
        page_id = page_id_regex.search(first_url).group(1)
        first_cursor = cursor_regex.search(first_url).group(1)
        
        new_url = f"https://m.facebook.com/page_content_list_view/more/?page_id={page_id}&start_cursor=%7B%22timeline_cursor%22%3A%22{first_cursor}%22%2C%22timeline_section_cursor%22%3Anull%2C%22has_next_page%22%3Atrue%7D&num_to_fetch={8}&surface_type=posts_tab"
        # print(f"NEW URL: {new_url}")
        first_page = str(BeautifulSoup(requests.get(new_url, headers=self._HEADERS).content, features="html.parser"))
        results = line_regex.findall(first_page)
        for r in results:
            timestamps.append(r.split(',"story_name"')[0])
            urls.append(new_url)
            posts.append(r.split('story_fbid":["')[1])
        new_cursor = new_cursor_regex.search(first_page).group(1)
        new_url = f"https://m.facebook.com/page_content_list_view/more/?page_id={page_id}&start_cursor=%7B%22timeline_cursor%22%3A%22{new_cursor}%22%2C%22timeline_section_cursor%22%3Anull%2C%22has_next_page%22%3Atrue%7D&num_to_fetch={8}&surface_type=posts_tab"
        # print(f"NEW URL: {new_url}")
        for _ in tqdm(range(n_posts)):
            p = str(BeautifulSoup(requests.get(new_url, headers=self._HEADERS).content, features="html.parser"))
            for r in line_regex.findall(p):
                timestamps.append(r.split(',"story_name"')[0])
                urls.append(new_url)
                posts.append(r.split('story_fbid":["')[1])
            # print(f"Iteration {i+1}: scraped {len(posts)-old_len} posts at url {new_url}")
            try:
                new_cursor = new_cursor_regex.search(p).group(1)
            except AttributeError: # in questo caso esce dal loop perché non ci sono più posts
                print(f"Cannot find cursor in at url {new_url}")
                break
            new_url = f"https://m.facebook.com/page_content_list_view/more/?page_id={page_id}&start_cursor=%7B%22timeline_cursor%22%3A%22{new_cursor}%22%2C%22timeline_section_cursor%22%3Anull%2C%22has_next_page%22%3Atrue%7D&num_to_fetch={8}&surface_type=posts_tab"
            # print(f"NEW URL: {new_url}")
        # for i,pii in enumerate(posts):
        #     print(f"Post {i}: {pii}")
        df_results = pd.DataFrame(columns = ['post_id','timestamp','post_url'])
        df_results['post_id'] = posts
        df_results['post_url'] = urls
        df_results['timestamp'] = timestamps
        if os.path.exists(f'{url.split("/")[-3]}_post_ids.csv'):
            os.remove(f'{url.split("/")[-3]}_post_ids.csv')
        df_results = df_results.drop_duplicates().reset_index(drop=True)
        df_results.to_csv(f'{url.split("/")[-3]}_post_ids_urls.csv', index=False)
        print(len(posts))
        print(len(list(set(posts))))
        print(df_results.shape[0])

        if get_reactions == True:
            self._fetch_reactions_df(df_results, page=url.split("/")[-3])
    
    def scrape(self, url="https://www.facebook.com/pg/mancity/posts/?ref=page_internal", get_reactions=True):
        print(f"Scraping {url}...")
        page_id_regex = re.compile(r'page_id=(.*?)&')
        cursor_regex = re.compile(r"timeline_cursor%22%3A%22(.*?)%")
        post_id_regex = re.compile(r'"story_fbid":\["(.*?)"]')
        new_cursor_regex = re.compile(r'timeline_cursor\\u002522\\u00253A\\u002522(.*?)\\')

        posts = []

        response = requests.get(url)
        soup = BeautifulSoup(response.content, features="lxml")
        divs = soup.find_all("div", id=re.compile("^feed_subtitle_"))
        for d in divs:
            try:
                posts.append(d.get("id").split(";")[1])
            except IndexError:
                print(f"{d.get('id')} strano...")
        first_url = soup.find(id='www_pages_reaction_see_more_unitwww_pages_posts').div.a.get('ajaxify')
        # print(first_url)
        page_id = page_id_regex.search(first_url).group(1)
        first_cursor = cursor_regex.search(first_url).group(1)
        new_url = f"https://www.facebook.com/pages_reaction_units/more/?page_id={page_id}&cursor=%7B%22timeline_cursor%22%3A%22{first_cursor}%22%2C%22timeline_section_cursor%22%3A%7B%7D%2C%22has_next_page%22%3Atrue%7D&surface=www_pages_posts&unit_count=8&fb_dtsg_ag=AQwSAFHaqzuvPRzR3U6eg9XAE82Nde6V0kRD9eMX1WYHxA%3AAQwIG4jrI8moeLzAGZPDnpGzMQE9GOKvFbfQ0VhPK77I1Q&__user=100050524896349&__a=1&__dyn=7AgNe-4amaWxd2u6aJGi9FxqeCwAyoyGgmAGt94WqK4UqwCzob4q5-agjGqK6omCyEnCG2S8BDyUJu9xK5uF8iBCBXxWAcUeUG5E-44cAy8K26ih4-e-mdx11ycyAUOESqt38x0Gxum4qKm8yEqx6cwYG5kUvCypHh43Hg-ezFEmUC2J0FDBgS6ojxKaCCy89pEhKFprzooAnyrxKq9BQnjG3tumm78iyXCAzUCcBAxC1dx3xiGz_AUhK2i5azEtUW8Bz9eawG-UrAJ4UjUC6olULz9rBxe4UgwAyE-9zo-2a8G5WwCyWz9aGm8ypAqV8ym68K5oWiaKE-16jDjKFpUgy88bxOuqECeCgSUigK7pV98R38Si78K8xa48kx1a5UcVUhAGi58ixy5qxNDxe12GeAy8kyb-6oCfxWcUC5pob89EjxyEtwGwUwUwwwwx22m3i4E&__csr=&__req=14&__beoa=0&__pc=PHASED%3ADEFAULT&dpr=1&__ccg=GOOD&__rev=1002077662&__s=zc7gno%3A48wp56%3Azcbhbm&__hsi=6822294017086049017-0&__comet_req=0&jazoest=27656&__spin_r=1002077662&__spin_b=trunk&__spin_t=1588437431"
        
        # new_url = f"https://m.facebook.com/page_content_list_view/more/?page_id={page_id}&start_cursor=%7B%22timeline_cursor%22%3A%22{first_cursor}%22%2C%22timeline_section_cursor%22%3Anull%2C%22has_next_page%22%3Atrue%7D&num_to_fetch={8}&surface_type=posts_tab"
        print(f"NEW URL: {new_url}")
        _user_agent = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/76.0.3809.87 Safari/537.36")
        custom_headers= {'User-Agent': _user_agent, 'Accept-Language': 'en-US,en;q=0.5', 'cookie': ('datr=pqGtXsjuVqzV4QLWsiOfnxqw; sb=taGtXsf1Q0imn1F9qdKf_R09; c_user=100050524896349; xs=49%3ACyLTjc3MRHsdOg%3A2%3A1588437429%3A-1%3A-1; spin=r.1002077662_b.trunk_t.1588437431_s.1_v.2_; fr=3fGhZBYxFGkLjbd7Y.AWXKl7xaqCOyxYafs_i-LmhQQ6Y.BeraG1.xN.AAA.0.0.Beragp.AWX8Y1mp; wd=1201x1009; presence=EDvF3EtimeF1588439112EuserFA21B50524896349A2EstateFDutF1588439112995CEchF_7bCC; act=1588439115247%2F2')}

        first_page = str(BeautifulSoup(requests.get(new_url, headers=custom_headers).content, features="html.parser"))
        for pi in post_id_regex.findall(first_page):
            posts.append(pi)
        # print(first_page)
        new_cursor = new_cursor_regex.search(first_page).group(1)
        # new_url = f"https://m.facebook.com/page_content_list_view/more/?page_id={page_id}&start_cursor=%7B%22timeline_cursor%22%3A%22{new_cursor}%22%2C%22timeline_section_cursor%22%3Anull%2C%22has_next_page%22%3Atrue%7D&num_to_fetch={8}&surface_type=posts_tab"
        new_url = f"https://www.facebook.com/pages_reaction_units/more/?page_id={page_id}&cursor=%7B%22timeline_cursor%22%3A%22{new_cursor}%22%2C%22timeline_section_cursor%22%3A%7B%7D%2C%22has_next_page%22%3Atrue%7D&surface=www_pages_posts&unit_count=8&fb_dtsg_ag=AQwSAFHaqzuvPRzR3U6eg9XAE82Nde6V0kRD9eMX1WYHxA%3AAQwIG4jrI8moeLzAGZPDnpGzMQE9GOKvFbfQ0VhPK77I1Q&__user=100050524896349&__a=1&__dyn=7AgNe-4amaWxd2u6aJGi9FxqeCwAyoyGgmAGt94WqK4UqwCzob4q5-agjGqK6omCyEnCG2S8BDyUJu9xK5uF8iBCBXxWAcUeUG5E-44cAy8K26ih4-e-mdx11ycyAUOESqt38x0Gxum4qKm8yEqx6cwYG5kUvCypHh43Hg-ezFEmUC2J0FDBgS6ojxKaCCy89pEhKFprzooAnyrxKq9BQnjG3tumm78iyXCAzUCcBAxC1dx3xiGz_AUhK2i5azEtUW8Bz9eawG-UrAJ4UjUC6olULz9rBxe4UgwAyE-9zo-2a8G5WwCyWz9aGm8ypAqV8ym68K5oWiaKE-16jDjKFpUgy88bxOuqECeCgSUigK7pV98R38Si78K8xa48kx1a5UcVUhAGi58ixy5qxNDxe12GeAy8kyb-6oCfxWcUC5pob89EjxyEtwGwUwUwwwwx22m3i4E&__csr=&__req=14&__beoa=0&__pc=PHASED%3ADEFAULT&dpr=1&__ccg=GOOD&__rev=1002077662&__s=zc7gno%3A48wp56%3Azcbhbm&__hsi=6822294017086049017-0&__comet_req=0&jazoest=27656&__spin_r=1002077662&__spin_b=trunk&__spin_t=1588437431"
                    # https://www.facebook.com/pages_reaction_units/more/?page_id=208411345454&cursor=%7B%22timeline_cursor%22%3A%22AQHRbrpnbPzbRDQlGj1KLmOMlxl9_qHg6q-8OnD6RRW7ZaZt0h8iISoPay6LcnmZLg5twT9VDshas_next_page%22%3  www_pages_posts&unit_count=8&fb_dtsg_ag=AQwSAFHaqzuvPRzR3U6eg9XAE82Nde6V0kRD9eMX1WYHxA%3AAQwIG4jrI8moeLzAGZPDnpGzMQE9GOKvFbfQ0VhPK77I1Q&__user=100050524896349&__a=1&__dyn=7AgNe-4amaWxd2u6aJGi9FxqeCwAyoyGgmAGt94WqK4UqwCzob4q6oF1eFGUpxqqaxuqEboymubyRUC6UlWAxamqnK7GgPwXyEmzUggOi8yU8p94jUXVoS4468OajzazpFQcy42G5VohGVoyaxG4oO3OEljx-q9CJ4geJ3UWeCxryoaQ2Cul3opxe6UGqq8wBCx6WBBKdxyhu9K6VECnhteEdRVposxabKqifyoOmi6o4S4e5aGf-jx6U98kGexTzEymcAUG2HXxKiQjxfyopxny-cBKm4Ujx22iazUCdzU8EK5WwCyWz9aGm8ypAqV8ym68K5oWiaKE-16jDhWBDx28wwK79VGyoWp3rx92UtDAAzkczp8syUy4Egxi44EnwPDx6iF8kxa68lG76u4U4aEWi8xi8LUpyo-7EPyolBwIwCxe6axS2G3y3y2222489od8iw&__csr=&__req=s&__beoa=0&__pc=PHASED%3ADEFAULT&dpr=1&__ccg=GOOD&__rev=1002077662&__s=28u36m%3A09bpuc%3Ajm0z09&__hsi=6822289215994334814-0&__comet_req=0&jazoest=27656&__spin_r=1002077662&__spin_b=trunk&__spin_t=1588437431
        print(f"NEW URL: {new_url}")
        for i in tqdm(range(0)):
            old_len = len(posts)
            p = str(BeautifulSoup(requests.get(new_url, headers=custom_headers).content, features="html.parser"))
            for pi in post_id_regex.findall(p):
                posts.append(pi)
            # print(f"Iteration {i+1}: scraped {len(posts)-old_len} posts at url {new_url}")
            try:
                new_cursor = new_cursor_regex.search(p).group(1)
            except AttributeError: # in questo caso esce dal loop perché non ci sono più posts
                print(f"Cannot find cursor in at url {new_url}")
                break
            new_url = f"https://www.facebook.com/pages_reaction_units/more/?page_id={page_id}&cursor=%7B%22timeline_cursor%22%3A%22{new_cursor}%22%2C%22timeline_section_cursor%22%3A%7B%7D%2C%22has_next_page%22%3Atrue%7D&surface=www_pages_posts&unit_count=8&fb_dtsg_ag=AQwSAFHaqzuvPRzR3U6eg9XAE82Nde6V0kRD9eMX1WYHxA%3AAQwIG4jrI8moeLzAGZPDnpGzMQE9GOKvFbfQ0VhPK77I1Q&__user=100050524896349&__a=1&__dyn=7AgNe-4amaWxd2u6aJGi9FxqeCwAyoyGgmAGt94WqK4UqwCzob4q5-agjGqK6omCyEnCG2S8BDyUJu9xK5uF8iBCBXxWAcUeUG5E-44cAy8K26ih4-e-mdx11ycyAUOESqt38x0Gxum4qKm8yEqx6cwYG5kUvCypHh43Hg-ezFEmUC2J0FDBgS6ojxKaCCy89pEhKFprzooAnyrxKq9BQnjG3tumm78iyXCAzUCcBAxC1dx3xiGz_AUhK2i5azEtUW8Bz9eawG-UrAJ4UjUC6olULz9rBxe4UgwAyE-9zo-2a8G5WwCyWz9aGm8ypAqV8ym68K5oWiaKE-16jDjKFpUgy88bxOuqECeCgSUigK7pV98R38Si78K8xa48kx1a5UcVUhAGi58ixy5qxNDxe12GeAy8kyb-6oCfxWcUC5pob89EjxyEtwGwUwUwwwwx22m3i4E&__csr=&__req=14&__beoa=0&__pc=PHASED%3ADEFAULT&dpr=1&__ccg=GOOD&__rev=1002077662&__s=zc7gno%3A48wp56%3Azcbhbm&__hsi=6822294017086049017-0&__comet_req=0&jazoest=27656&__spin_r=1002077662&__spin_b=trunk&__spin_t=1588437431"
            # new_url = f"https://m.facebook.com/page_content_list_view/more/?page_id={page_id}&start_cursor=%7B%22timeline_cursor%22%3A%22{new_cursor}%22%2C%22timeline_section_cursor%22%3Anull%2C%22has_next_page%22%3Atrue%7D&num_to_fetch={8}&surface_type=posts_tab"
        # for i,pii in enumerate(posts):
        #     print(f"Post {i}: {pii}")
        df_results = pd.DataFrame(columns = ['post_id'])
        df_results['post_id'] = posts
        if os.path.exists(f'{url.split("/")[-3]}_post_ids.csv'):
            os.remove(f'{url.split("/")[-3]}_post_ids.csv')
        df_results = df_results.drop_duplicates().reset_index(drop=True)
        df_results.to_csv(f'{url.split("/")[-3]}_post_ids.csv', index=False)
        print(len(posts))
        print(len(list(set(posts))))
        print(df_results.shape[0])

        if get_reactions == True:
            df = self._fetch_timestamp(df_results, page_id=page_id, page=f'{url.split("/")[-3]}')
            self._fetch_reactions_df(df_results, page=url.split("/")[-3])

    def _fetch_reactions_df(self, df: pd.DataFrame, page: str):
        reaction_regex = re.compile(r'reaction_type=(.*?)&')
        reaction_count_regex = re.compile(r'total_count=(.*?)&')
        df['like'] = 0
        df['love'] = 0
        df['wow'] = 0
        df['haha'] = 0
        df['sorry'] = 0
        df['anger'] = 0

        for ind,post_id in tqdm(enumerate(df.post_id)):
            url = f'https://m.facebook.com/ufi/reaction/profile/browser/?ft_ent_identifier={post_id}'

            req = self.s.get(url)
            new_soup = BeautifulSoup(req.text, features="lxml")
            tmp = {}
            print(new_soup)
            imgs = new_soup.findAll("a", {"class": "u"})

            for i in imgs:
                try:
                    r = reaction_regex.findall(i.get('href'))[0]
                    tc = reaction_count_regex.findall(i.get('href'))[0]
                    print(r)
                    print(tc)
                    tmp[r] = int(tc.replace('.', ''))
                except IndexError:
                    pass

            df.at[ind, 'like'] = tmp['1'] if '1' in tmp else 0
            df.at[ind, 'love'] = tmp['2'] if '2' in tmp else 0
            df.at[ind, 'wow'] = tmp['3'] if '3' in tmp else 0
            df.at[ind, 'haha'] = tmp['4'] if '4' in tmp else 0
            df.at[ind, 'sorry'] = tmp['7'] if '7' in tmp else 0
            df.at[ind, 'anger'] = tmp['8'] if '8' in tmp else 0
        df.to_csv(f"{page}_reactions_2.csv", index=False)

    def _fetch_timestamp(self, df: pd.DataFrame, page_id: str, page: str) -> pd.DataFrame:
        ts_regex = re.compile(r'data-store="&#123;&quot;time&quot;:(.*?),')
        vid_regex = re.compile(r'publish_time&quot;:(.*?),&')

        _user_agent = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/76.0.3809.87 Safari/537.36")
        custom_headers= {'User-Agent': _user_agent, 'Accept-Language': 'en-US,en;q=0.5', 'cookie': ('datr=a5-bXRZQ4VDI0IIS9gsjzuhR; sb=bp-bXdpZ-MkyQTaysy4KZVxc; locale=it_IT; c_user=1477543313; xs=11%3At_Qc8tpXmVMCfg%3A2%3A1588876420%3A4847%3A5893; fr=3r7dKEqZJNuqGoGhm.AWX6kzjDd5J73VeLR2TrwKtTPuY.Bdm59u.Y3.F6z.0.0.BetFSC.AWWKKwvj; spin=r.1002097027_b.trunk_t.1588876421_s.1_v.2_; presence=EDvF3EtimeF1588876607EuserFA21477543313A2EstateFDutF1588876607436CEchF_7bCC; m_pixel_ratio=1; wd=1858x1009')}


        df['timestamp'] = 0
        for ind,post_id in tqdm(enumerate(df.post_id)):
            # time.sleep(1)
            post_url = f"https://m.facebook.com/story.php?story_fbid={post_id}&id={page_id}"
            print(post_url)
            res = BeautifulSoup(self.s.get(post_url, headers=custom_headers).content, features="html.parser")
            # print(res)
            try:
                dic = eval(res.find('div', class_='_3f50').div['data-ft'])
                if page_id in dic['page_insights']:
                    ts = dic['page_insights'][page_id]['post_context']['publish_time']
                else:
                    print(f"Error at url: {post_url}")
                    ts = -1
            except (KeyError, AttributeError):
                try: #caso in cui cambia l'url tipo per video
                    ts = vid_regex.findall(str(res))[0]
                    # print(ts)
                except IndexError: # ultimo caso
                    try:
                        ts = ts_regex.findall(str(res))[0]
                    except:
                        print(f"Error at url: {post_url}")
                        ts = -1
                    # print(ts)
            df.at[ind, 'timestamp'] = ts
            if int(ts)!=-1 and int(ts) < 1533154350: 
                break
        df.to_csv(f"{page}_timestamp.csv", index=False)
        return df
        
    # aggiungi per virgolette "10156099746872746","10156099744802746"
    # https://m.facebook.com/manchesterunited/photos/a.10156099744802746/10156099746872746/?type=3&theater

if __name__ == '__main__':
    DIR_TEAM_PAGES = {
        'Arsenal': 'Arsenal',
        'Bournemouth': 'afcbournemouth',
        'Brighton': 'officialbhafc',
        'Burnley': 'officialburnleyfc',
        'Cardiff': 'cardiffcityfc',
        'Chelsea': 'ChelseaFC',
        'Crystal Palace': 'officialcpfc',
        'Everton': 'Everton',
        'Fulham': 'FulhamFC',
        'Huddersfield': 'htafc',
        'Hull': 'hullcity',
        'Leicester': 'lcfc',
        'Liverpool': 'LiverpoolFC',
        'Manchester City': 'mancity',
        'Manchester Utd': 'manchesterunited',
        'Middlesbrough': 'MFCofficial',
        'Newcastle': 'newcastleunited',
        'Southampton': 'southamptonfc',
        'Stoke': 'stokecity',
        'Sunderland': 'sunderlandafc',
        'Swansea': 'SwanseaCityFC',
        'Tottenham': 'TottenhamHotspur',
        'Watford': 'watfordfc',
        'West Brom': 'westbromwichalbionofficial',
        'West Ham': 'WestHam',
        'Wolves': 'Wolves'
    }

    DIR_TEAM_ID = {
        'Arsenal': '20669912712',
        'afcbournemouth': '246692125365496',
        'officialbhafc': '95602073138',
        'officialburnleyfc': '157574800929706',
        'cardiffcityfc': '108487214050',
        'ChelseaFC': '86037497258',
        'officialcpfc': '168089120761', #rifai questi sopra
        'Everton': '56909226276',
        'FulhamFC': '108857709161298',
        'htafc': '325426564157781',
        'hullcity': '258479264536',
        'lcfc': '324520502768',
        'LiverpoolFC': '67920382572',
        'mancity': '208411345454',
        'manchesterunited': '7724542745',
        'MFCofficial': '386636354690970',
        'newcastleunited': '124119160931672',
        'southamptonfc': '220396037973624',
        'stokecity': '28928779637',
        'sunderlandafc': '118389841508479',
        'SwanseaCityFC': '87328379939',
        'TottenhamHotspur': '351687753504',
        'watfordfc': '21223691814',
        'westbromwichalbionofficial': '44784315079',
        'WestHam': '129911763708715',
        'Wolves': '125767659596'
    }

    credentials = {
        "email": "YOUR_EMAIL",
        "pass": "YOUR_PASSWORD"
    }
    fs = FacebookScraper(credentials=credentials)

    # for team in DIR_TEAM_PAGES:
    #     fs.scrape_ajax(url=f"https://www.facebook.com/pg/{DIR_TEAM_PAGES[team]}/posts/?ref=page_internal",
    #                     get_reactions=True)
    # for f in os.listdir('data_clean'):
    #     if f.endswith('ids.csv'):
    #         print(f)
    #         df = pd.read_csv(f"data_clean/{f}")
    #         fs._fetch_reactions_df(df, f.split("_")[0])

    