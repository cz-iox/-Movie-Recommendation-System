import pandas as pd
from surprise import Dataset, Reader, SVD
import pickle
import os

RAW_RATINGS_PATH = "data/raw/ratings.csv"
NEW_RATINGS_PATH = "data/new_ratings.csv"
MODEL_OUTPUT_PATH = "models/algorithm_svd.pkl"
TOKEN_MAP_PATH = "models/token_to_userid.pkl"

def retrain():
    original_ratings = pd.read_csv(RAW_RATINGS_PATH)[["userId", "movieId", "rating"]]
    if os.path.isfile(NEW_RATINGS_PATH):
        new_ratings =  pd.read_csv(NEW_RATINGS_PATH)[["userToken", "movieId", "rating"]]
    else:
        new_ratings = pd.DataFrame(columns=["userToken", "movieId", "rating"])
        
    if os.path.isfile(TOKEN_MAP_PATH):
        with open(TOKEN_MAP_PATH, "rb")as f:
            token_to_userid = pickle.load(f)
    else:
        token_to_userid = {}

    max_existing_id = max(original_ratings["userId"].max(), max(token_to_userid.values(), default=0))
    unique_tokens = new_ratings["userToken"].unique()
    for token in unique_tokens:
        if token not in token_to_userid:
            max_existing_id += 1
            token_to_userid[token] = max_existing_id
    new_ratings["userId"] = new_ratings["userToken"].map(token_to_userid)
    new_ratings = new_ratings[["userId", "movieId", "rating"]]
    all_ratings = pd.concat([original_ratings, new_ratings], ignore_index=True)

    reader = Reader(rating_scale=(0.5, 5.0))
    data = Dataset.load_from_df(all_ratings, reader)
    trainset = data.build_full_trainset()
    algorithm = SVD()
    algorithm.fit(trainset)

    with open(MODEL_OUTPUT_PATH, "wb") as f:
        pickle.dump(algorithm, f)
    with open(TOKEN_MAP_PATH, "wb") as f:
        pickle.dump(token_to_userid, f)

    print(f"Retrained on {len(all_ratings)} ratings ({len(token_to_userid)} total mapped users, {len(unique_tokens)} tokens seen this run). Model saved.")
    return algorithm
if __name__ == "__main__":
    retrain()