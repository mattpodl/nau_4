# Imports
import argparse
import json

import numpy as np
import pandas as pd


def build_arg_parser():
    parser = argparse.ArgumentParser(description='Find users who are similar to the input user')
    parser.add_argument('--user', dest='user', required=True,
                        help='Input user')
    return parser


# Compute the Euclidean distance score between user1 and user2
def euclidean_score(dataset, user1, user2, min_common_ratings=2):
    if user1 not in dataset:
        raise TypeError('Cannot find ' + user1 + ' in the dataset')

    if user2 not in dataset:
        raise TypeError('Cannot find ' + user2 + ' in the dataset')

    # Movies rated by both user1 and user2
    common_movies = {}

    for item in dataset[user1]:
        if item in dataset[user2]:
            common_movies[item] = 1

    # If there are no common movies between the users, 
    # then the score is 0 
    if len(common_movies) < min_common_ratings:
        return 0

    squared_diff = []

    for item in dataset[user1]:
        if item in dataset[user2]:
            squared_diff.append(np.square(dataset[user1][item] - dataset[user2][item]))

    return 1 / (1 + np.sqrt(np.sum(squared_diff)))


# Compute the Pearson correlation score between user1 and user2
def pearson_score(dataset, user1, user2, min_common_ratings=2):
    if user1 not in dataset:
        raise TypeError('Cannot find ' + user1 + ' in the dataset')

    if user2 not in dataset:
        raise TypeError('Cannot find ' + user2 + ' in the dataset')

    # Movies rated by both user1 and user2
    common_movies = {}

    for item in dataset[user1]:
        if item in dataset[user2]:
            common_movies[item] = 1

    num_ratings = len(common_movies)

    # If there are no common movies between user1 and user2, then the score is 0 
    if num_ratings < min_common_ratings:
        return 0

    # Calculate the sum of ratings of all the common movies 
    user1_sum = np.sum([dataset[user1][item] for item in common_movies])
    user2_sum = np.sum([dataset[user2][item] for item in common_movies])

    # Calculate the sum of squares of ratings of all the common movies 
    user1_squared_sum = np.sum([np.square(dataset[user1][item]) for item in common_movies])
    user2_squared_sum = np.sum([np.square(dataset[user2][item]) for item in common_movies])

    # Calculate the sum of products of the ratings of the common movies
    sum_of_products = np.sum([dataset[user1][item] * dataset[user2][item] for item in common_movies])

    # Calculate the Pearson correlation score
    Sxy = sum_of_products - (user1_sum * user2_sum / num_ratings)
    Sxx = user1_squared_sum - np.square(user1_sum) / num_ratings
    Syy = user2_squared_sum - np.square(user2_sum) / num_ratings

    if Sxx * Syy == 0:
        return 0

    return Sxy / np.sqrt(Sxx * Syy)


# Finds users in the dataset that are similar to the input user
def find_similar_users(dataset, user, num_users, score_method='pearson', min_common_ratings=2):
    if user not in dataset:
        raise TypeError('Cannot find ' + user + ' in the dataset')

    # Compute score between input user and all the users in the dataset
    if score_method == 'euclidean':
        # Euclidean distance
        scores = np.array([[x, euclidean_score(dataset, user, x, min_common_ratings)] for x in dataset if x != user])
    else:
        # Pearson coefficient
        scores = np.array([[x, pearson_score(dataset, user, x, min_common_ratings)] for x in dataset if x != user])

    # Sort the scores in decreasing order
    scores_squared = np.square(scores[:, 1].astype(float))
    scores_sorted = np.argsort(scores_squared)[::-1]

    # Extract the top 'num_users' scores
    top_users = scores_sorted[:num_users]

    return scores[top_users]


def find_recommended_movies(data, user, min_common_ratings=2, corr_users_count=8, min_users_count=1):
    # Wyliczenie podobnych osób i zamiana na pandas.DataFrame
    similar_users_numpy = find_similar_users(data, user, corr_users_count, min_common_ratings=min_common_ratings)
    similar_users = pd.DataFrame(similar_users_numpy[:, 1], similar_users_numpy[:, 0], {'Score'},
                                 dtype=float).sort_values('Score', ascending=False)

    # Zamiana głównego zbioru na pandas.DataFrame
    datas = pd.DataFrame(data)

    # Lista istotnie skorelowanych osób (aka Drużyna A)
    similar_users_names = similar_users.index.to_list()

    # Lista filmów Usera do wyrzucenia ze dataFrame
    movies_todrop = datas[user].dropna().index.to_list()

    # DataFrame wyłącznie z Drużyną A i bez filmów Usera
    suggestions = datas[similar_users_names].drop(movies_todrop)

    # Czyszczenie zbioru z filmów, których nikt z Drużyny A nie ocenił
    suggestions = suggestions.dropna(0, 'all')

    # Czyszczenie zbioru z osobników z Drużyny A, którzy nie obejrzeli nic innego niż User
    suggestions = suggestions.dropna(1, 'all')

    # Zmiana wartości ocen o -5.5 po to, aby do rekomendacji wykorzystać też negatywną korelację
    suggestions = suggestions - 5.5

    # Przygotowanie słownika z wynikami
    movie_scores = {}

    # Główna pętla wyliczania skorelowanych ocen
    for movie, m_ratings in suggestions.iterrows():
        rates_sum = 0.0
        factors_sum = 0.0
        users_count = 0

        for user_name, user_rate in m_ratings.items():
            # if user has no rate for the movie, skip
            if np.isnan(user_rate):
                continue

            factor = similar_users.loc[user_name].iloc[0]
            rates_sum += user_rate * factor
            factors_sum += abs(factor)
            users_count += 1

        # if the sum of correlation or number of user's ratings are too small, skip
        if factors_sum < 1 or users_count < min_users_count:
            continue

        movie_score = rates_sum / factors_sum
        movie_scores[movie] = [movie_score, users_count, rates_sum, factors_sum]
    movie_scores = pd.DataFrame(movie_scores.values(), movie_scores.keys(),
                                ('Score', 'users_count', 'rates_sum', 'factors_sum'), dtype=float).dropna()

    return movie_scores.sort_values(['Score', 'factors_sum'], ascending=False)


# Parse user name and open data file

if __name__ == '__main__':
    args = build_arg_parser().parse_args()
    user = args.user

    ratings_file = 'ratings.json'

    with open(ratings_file, 'r') as f:
        data = json.loads(f.read())

    print('\nUsers similar to ' + user + ':\n')
    similar_users_numpy = find_similar_users(data, user, 8)
    similar_users = pd.DataFrame(similar_users_numpy[:, 1], similar_users_numpy[:, 0], {'Score'},
                                 dtype=float).sort_values('Score', ascending=False)
    print(similar_users)
    print()
    print(user, ' polecamy Ci:')
    
    recommended = find_recommended_movies(data, user, min_common_ratings=2, corr_users_count=8, min_users_count=2)
    for f in recommended.head(10).index.to_list():
        print(' - "' + f + '"')

    print()
    print(user, ' NIE polecamy Ci')
    
    notRecommended = recommended.sort_values('Score', ascending=True)
    for f in notRecommended.head(10).index.to_list():
        print(' - "' + f + '"')
)
