import GetOldTweets3 as got
from textblob import TextBlob 
import re
import pandas as pd
from tqdm import tqdm
from datetime import datetime, date, timedelta
import time
from csv import DictWriter
import os

FILENAME = 'tweets_premier_1718.csv'

HASTAGS = {
    'Arsenal':  ['#afc','#coyg','#arsenal', '#arsenalfc','#gunners'],
    'Aston Villa': ['#avfc','#astonvilla', '#astonvillafc'],
    'Bournemouth': ['#afcb','#bournemouth'],
    'Brighton': ['#BHAFC', '#BrightonandHoveAlbion','#BrightonFC'],
    'Burnley': ['#clarets','#burnley', '#burnleyfc'],
    'Cardiff': ['#CardiffCity','#bluebirds','#CCFC'],
    'Chelsea': ['#cfc','#chelseafc','#chelsea'],
    'Crystal Palace': ['#cpfc','#crystalpalacefc','#crystalpalace'],
    'Everton': ['#efc','#everton', '#evertonfc'],
    'Fulham': ['#FFC', '#fulhamfc'],
    'Huddersfield': ["#htafc", "#Huddersfieldfc"],
    'Hull': ['#hcafc','#hullcity'],
    'Leicester': ['#lcfc','#leicestercity', '#leicestercityfc'],
    'Liverpool': ['#lfc','#liverpool','#liverpoolfc'],
    'Manchester City': ['#mcfc','#mancity','#manchestercity'],
    'Manchester Utd': ['#mufc','#manutd','#manchesterunited'],
    'Newcastle': ['#nufc','#newcastlefc'],
    'Norwich': ['#ncfc','#norwichcity'],
    'QPR': ['#qpr', '#qprfc'],
    'Southampton': ['#saintsfc','#Southamptonfc'],
    'Stoke': ['#scfc','#stokecity'],
    'Sunderland': ['#sufc','#sunderland'],
    'Swansea': ['#swans','#swanseafc'],
    'Tottenham': ['#thfc','#tottenhamhotspur','#tottenham'],
    'Watford':['#watfordfc','watford'],
    'West Brom': ['#wbafc','#wba','#westbrom','#westbromwichalbion'],
    'West Ham': ['#whufc','#westham','#hammers'],
    'Wolves': ['#wolverhamptonfc','#wolvesfc','#WWFC','#wolverhamptonwanderers']
}


df = pd.read_csv('dataset/premier/transformed/transformed_premier_1718_2.csv')

result = pd.DataFrame(
                    columns = [
                    'match_round','home_team','away_team','team','tweet_text','tweet_id','tweet_username',
                    'tweet_date', 'tweet_retweets', 'tweet_favorites', 'tweet_mentions', 'tweet_hashtags', 
                    'tweet_geo']
                    )

if not os.path.exists(FILENAME):
    result.to_csv(FILENAME, index = False)

for t in tqdm(zip(df.match_round, df.home_team, df.away_team, df.match_date)):
    d,m,y = map(int, t[3].split('.'))
    md = date(y, m, d)
    date_1_day_before = md - timedelta(days=1)
    date_4_day_before = md - timedelta(days=4)

    for h in HASTAGS[t[1]]:
        tweetCriteria = got.manager.TweetCriteria().setQuerySearch (h)\
                                            .setSince(date_4_day_before.strftime("%Y-%m-%d"))\
                                            .setUntil(date_1_day_before.strftime("%Y-%m-%d"))\
                                            .setMaxTweets(400)\
                                            .setLang('en')\
                                            .setEmoji("unicode")
        tweets = got.manager.TweetManager.getTweets(tweetCriteria)

        with open(FILENAME, 'a+', newline = '', encoding = 'utf-8') as f:
            dict_writer = DictWriter(f, fieldnames = result.columns)
            for tw in tweets:
                dict_writer.writerow(
                    {'match_round': t[0],
                    'home_team': t[1],
                    'away_team': t[2],
                    'team': t[1],
                    'tweet_text': tw.text,
                    'tweet_id': tw.id,
                    'tweet_username': tw.username,
                    'tweet_date': tw.date, 
                    'tweet_retweets': tw.retweets, 
                    'tweet_favorites': tw.favorites, 
                    'tweet_mentions': tw.mentions, 
                    'tweet_hashtags': tw.hashtags, 
                    'tweet_geo': tw.geo}
                )
        time.sleep(6)

    for h in HASTAGS[t[2]]:
        tweetCriteria = got.manager.TweetCriteria().setQuerySearch (h)\
                                            .setSince(date_4_day_before.strftime("%Y-%m-%d"))\
                                            .setUntil(date_1_day_before.strftime("%Y-%m-%d"))\
                                            .setMaxTweets(400)\
                                            .setLang('en')\
                                            .setEmoji("unicode")
        tweets = got.manager.TweetManager.getTweets(tweetCriteria)
        with open(FILENAME, 'a+', newline = '', encoding = 'utf-8') as f:
            dict_writer = DictWriter(f, fieldnames = result.columns)
            for tw in tweets:
                dict_writer.writerow(
                    {'match_round': t[0],
                    'home_team': t[1],
                    'away_team': t[2],
                    'team': t[2],
                    'tweet_text': tw.text,
                    'tweet_id': tw.id,
                    'tweet_username': tw.username,
                    'tweet_date': tw.date, 
                    'tweet_retweets': tw.retweets, 
                    'tweet_favorites': tw.favorites, 
                    'tweet_mentions': tw.mentions, 
                    'tweet_hashtags': tw.hashtags, 
                    'tweet_geo': tw.geo}
                )
        time.sleep(6)

    # pol = 0
    # tot = 0
    # for tw in tweets:
    #     tweet = ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t]) (\w+:\/\/\S+)", " ", tw.text).split())
    #     analysis = TextBlob(tweet)
    #     tp = analysis.sentiment.polarity
    #     if tp!=0:
    #         tot+=1
    #         pol += analysis.sentiment.polarity
    # away_pol = pol/tot if tot!=0 else 0