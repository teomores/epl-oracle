import GetOldTweets3 as got
from textblob import TextBlob 
import re
import pandas as pd
from tqdm import tqdm
from datetime import datetime, date, timedelta

HASTAGS = {
    'Arsenal': '#afc',
    'Aston Villa': '#avfc',
    'Burnley': '#burnley',
    'Chelsea': '#cfc',
    'Crystal Palace': '#cpfc',
    'Everton': '#efc',
    'Hull': '#hcafc',
    'Leicester': '#lcfc',
    'Liverpool': '#lfc',
    'Manchester City': '#mcfc',
    'Manchester Utd': '#mufc',
    'Newcastle': '#nufc',
    'QPR': '#QPR',
    'Southampton': '#saintsfc',
    'Stoke': '#scfc',
    'Sunderland': '#sufc',
    'Swansea': '#swans',
    'Tottenham': 'thfc',
    'West Brom': '#wbafc',
    'West Ham': '#whufc'
}

df = pd.read_csv('dataset/premier/transformed/transformed_premier_1415_2.csv')
result = pd.DataFrame(columns=['match_round','home_team','away_team','team','tweet_text','tweet_id','tweet_username',
                    'tweet_date', 'tweet_retweets', 'tweet_favorites', 'tweet_mentions', 'tweet_hashtags', 'tweet_geo'])
for t in tqdm(zip(df.match_round, df.home_team, df.away_team, df.match_date)):
    d,m,y = map(int, t[3].split('.'))
    md = date(y, m, d)
    date_1_day_before = md - timedelta(days=1)
    date_4_day_before = md - timedelta(days=4)

    tweetCriteria = got.manager.TweetCriteria().setQuerySearch (HASTAGS[t[1]])\
                                           .setSince(date_4_day_before.strftime("%Y-%m-%d"))\
                                           .setUntil(date_1_day_before.strftime("%Y-%m-%d"))\
                                           .setMaxTweets(100)\
                                           .setTopTweets(True)\
                                           .setEmoji("unicode")

    tweets = got.manager.TweetManager.getTweets(tweetCriteria)
    for tw in tweets:
        result = result.append({'match_round':t[0],
                                'home_team':t[1],
                                'away_team':t[2],
                                'team': t[1],
                                'tweet_text':tw.text,
                                'tweet_id': tw.id,
                                'tweet_username': tw.username,
                                'tweet_date': tw.date, 
                                'tweet_retweets': tw.retweets, 
                                'tweet_favorites': tw.favorites, 
                                'tweet_mentions': tw.mentions, 
                                'tweet_hashtags': tw.hashtags, 
                                'tweet_geo': tw.geo}, ignore_index=True)

    tweetCriteria = got.manager.TweetCriteria().setQuerySearch (HASTAGS[t[2]])\
                                           .setSince(date_4_day_before.strftime("%Y-%m-%d"))\
                                           .setUntil(date_1_day_before.strftime("%Y-%m-%d"))\
                                           .setTopTweets(True)\
                                           .setMaxTweets(100)\
                                           .setEmoji("unicode")
    tweets = got.manager.TweetManager.getTweets(tweetCriteria)
    for tw in tweets:
        result = result.append({'match_round':t[0],
                                'home_team':t[1],
                                'away_team':t[2],
                                'team': t[2],
                                'tweet_text':tw.text,
                                'tweet_id': tw.id,
                                'tweet_username': tw.username,
                                'tweet_date': tw.date, 
                                'tweet_retweets': tw.retweets, 
                                'tweet_favorites': tw.favorites, 
                                'tweet_mentions': tw.mentions, 
                                'tweet_hashtags': tw.hashtags, 
                                'tweet_geo': tw.geo}, ignore_index=True)


result.to_csv('prova.csv', index=False)


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