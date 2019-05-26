# We will read from csv
# Convert the csv to a dataframe
# Clean up the 0s and treat them as missing values
# 

import pandas as pd
from ast import literal_eval

def load_tv_shows(path):
    df = pd.read_csv(path)
    return df

def inspect_data(df):
    info = pd.DataFrame(df.dtypes).T.rename(index={0:'column_type'})
    info = info.append(pd.DataFrame(df.astype(bool).sum()).T.rename(index={0:'valid values'}))
    return info


def word_count(df, column, list)

df = load_tv_shows('tv_shows_with_features.csv')
df.keywords = df.keywords.apply(literal_eval)

print('Analysis of Data:')
print('Shape:', df.shape)
print(inspect_data(df))

# keywords = set([item for sublist in df['keywords'] for item in sublist])
keywords = set()

for keywords_list in df['keywords']:
    keywords = keywords.union(keywords_list)


