import pandas as pd

def transform_df(dir: str, filename: str) -> None:
    original_df = pd.read_csv(f'dataset/{dir}/original/2/{filename}')
    bkm = sorted(set(original_df.bookmaker))
    expanded_bk_col = []
    for bs in bkm:
        expanded_bk_col.append(f'{bs}_1')
        expanded_bk_col.append(f'{bs}_X')
        expanded_bk_col.append(f'{bs}_2')
        expanded_bk_col.append(f'{bs}_opening_1')
        expanded_bk_col.append(f'{bs}_opening_X')
        expanded_bk_col.append(f'{bs}_opening_2')
    
    new_columns = list(original_df.columns[:7]) + expanded_bk_col
    transformed_df = pd.DataFrame(original_df[list(original_df.columns)[:7]].drop_duplicates().reset_index(drop=True),columns=new_columns)

    j = 0
    for i in range(transformed_df.shape[0]):
        while (j<original_df.shape[0] and transformed_df.at[i, 'match_round'] == original_df.at[j, 'match_round'] and 
            transformed_df.at[i, 'home_team'] == original_df.at[j, 'home_team'] and 
            transformed_df.at[i, 'away_team'] == original_df.at[j, 'away_team']):
            transformed_df.at[i, f"{original_df.at[j, 'bookmaker']}_1"] = original_df.at[j, '1']
            transformed_df.at[i, f"{original_df.at[j, 'bookmaker']}_X"] = original_df.at[j, 'X']
            transformed_df.at[i, f"{original_df.at[j, 'bookmaker']}_2"] = original_df.at[j, '2']
            transformed_df.at[i, f"{original_df.at[j, 'bookmaker']}_opening_1"] = original_df.at[j, 'opening_1']
            transformed_df.at[i, f"{original_df.at[j, 'bookmaker']}_opening_X"] = original_df.at[j, 'opening_X']
            transformed_df.at[i, f"{original_df.at[j, 'bookmaker']}_opening_2"] = original_df.at[j, 'opening_2']
            j=j+1

    transformed_df.to_csv(f'dataset/{dir}/transformed/transformed_{filename}', index=False)

if __name__ == '__main__':
    transform_df('serie_a', 'serie_a0910_2.csv')
    transform_df('serie_a', 'serie_a1011_2.csv')
    transform_df('serie_a', 'serie_a1112_2.csv')
    transform_df('serie_a', 'serie_a1213_2.csv')
    transform_df('serie_a', 'serie_a1314_2.csv')