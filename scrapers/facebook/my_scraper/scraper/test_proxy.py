import requests
import re
from bs4 import BeautifulSoup
import ast

line_regex = re.compile(r'{"object_fbtype":266,"publish_time":(.*?)"\]}')
req = requests.get("https://m.facebook.com/page_content_list_view/more/?page_id=20669912712&start_cursor=%7B%22timeline_cursor%22%3A%22AQHRqvpJutMPsmEntgd_Dkt1JWnVcqGAb5tbS-PlP0T63Nwp-EV5NLs9BC4vuWxyGi5SLvwbo9WMLimTOxsKbOHPxiv8eL4m8ilc5jjcc9lICU8J4p2m3NmMrcOd64BgL1Qy%22%2C%22timeline_section_cursor%22%3Anull%2C%22has_next_page%22%3Atrue%7D&num_to_fetch=8&surface_type=posts_tab")
text = str(BeautifulSoup(req.content, features="html.parser"))
results = line_regex.findall(text)
print(len(results))
print(results)
time_regex = re.compile(r'"publish_time":(.*?),')
id_regex = re.compile(r'"story_fbid":\["(.*?)')
for r in results:
    print(r.split(',"story_name"')[0])
    print(r.split('story_fbid":["')[1])