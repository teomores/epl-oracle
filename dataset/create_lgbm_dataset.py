import pandas as pd
import os

def merge_df(league: str) -> None:
    frames = []
    for f in os.listdir(f'E:/USDE/dataset/{league}/transformed'):
        if f.endswith('_2.csv'):
            frames.append(pd.read_csv(f'E:/USDE/dataset/{league}/transformed/{f}'))
    pd.concat(frames).reset_index(drop=True).to_csv(f'E:/USDE/dataset/{league}/transformed/transformed_merged_{league}.csv', index = False)

def merge_user_pref(league:str) -> None:
    frames = []
    for f in os.listdir(f'E:/USDE/dataset/{league}/original/3'):
        frames.append(pd.read_csv(f'E:/USDE/dataset/{league}/original/3/{f}'))
    pd.concat(frames).reset_index(drop=True).to_csv(f'E:/USDE/dataset/{league}/transformed/user_prefs_{league}.csv', index = False)


def set_label(df: pd.DataFrame) -> pd.DataFrame:
    label = []
    for hg,ag in zip(df.home_goals, df.away_goals):
        if hg == ag:
            label.append(0)
        elif hg > ag:
            label.append(1)
        else:
            label.append(2)
    df['label'] = label
    return df

def to_lgb_format(df: pd.DataFrame, league: str) -> None:
    df = set_label(df)
    # clean hour to keep only hour, not minute
    for i in range(df.shape[0]):
        df.at[i, 'match_hour'] = int(df.at[i, 'match_hour'].split(':')[0])
    # divide date in ddmmyyyy format
    match_month, match_day, match_year = [], [], []
    for date in df.match_date:
        match_day.append(int(date.split('.')[0]))
        match_month.append(int(date.split('.')[1]))
        match_year.append(int(date.split('.')[2]))
    df['match_day'] = match_day
    df['match_month'] = match_month
    df['match_year'] = match_year
    df.match_hour = df.match_hour.astype(int)
    df.sort_values(by=['match_year','match_round','home_team','away_team']).reset_index(drop=True)
    df.to_csv(f'E:/USDE/dataset/{league}/lightgbm/lightgbm_base_odds_{league}.csv', index = False)

if __name__ == '__main__':
    #merge_user_pref('serie_a')
    league = 'serie_a'
    merge_df(league)
    merged = pd.read_csv(f'E:/USDE/dataset/{league}/transformed/transformed_merged_{league}.csv')
    to_lgb_format(merged, league)