from fastapi import FastAPI, HTTPException
import pandas as pd 
from sklearn.metrics.pairwise import cosine_similarity
import pickle
from pydantic import BaseModel
import uuid
import csv
import os 
from fastapi.middleware.cors import CORSMiddleware
from scripts.retrain_svd import retrain
from apscheduler.schedulers.background import BackgroundScheduler
import httpx
from dotenv import load_dotenv



scheduler = BackgroundScheduler()

load_dotenv()
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

app = FastAPI(title="Movie Recommender API")

RATINGS_FILE = "data/new_ratings.csv"
links_df = pd.read_csv("data/raw/links.csv")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

movies_content = None
ratings = None 
tfidf_matrix = None
algorithm = None
knn_model = None
user_item_sparse = None
user_id_map = None
movie_id_to_idx = None

def scheduled_retrain():
    global algorithm
    try:
        new_algorithm = retrain()
        algorithm = new_algorithm
        print("In-memory SVD model updated after retrain")
    except Exception as e :
        print(f"Retrain failed — keeping the existing model in memory. Error: {e}")

@app.on_event("startup")
def load():
    global movies_content, ratings, tfidf_matrix, algorithm, indices
    global knn_model, user_item_sparse, user_id_map, movie_id_to_idx
    
    movies_content = pd.read_pickle("models/movies_content.pkl")
    ratings = pd.read_pickle("models/ratings.pkl")

    with open("models/tfidf_matrix.pkl", "rb") as f:
        tfidf_matrix = pickle.load(f)
    with open("models/algorithm_svd.pkl", "rb") as f:
        algorithm = pickle.load(f)
    with open("models/knn_model.pkl", "rb") as f:
        knn_model = pickle.load(f)
    with open("models/user_item_sparse.pkl", "rb") as f:
        user_item_sparse = pickle.load(f)
    with open("models/user_id_map.pkl", "rb") as f:
        user_id_map = pickle.load(f)
    with open("models/movie_id_to_idx.pkl", "rb") as f:
        movie_id_to_idx = pickle.load(f)
        
    indices = pd.Series(movies_content.index, index=movies_content["title"])
    print("All models loaded successfully! ")
    scheduler.add_job( scheduled_retrain, "interval", minutes=2, id="retrain_svd_job")
    scheduler.start()
    print("Retrain scheduler started — will run every 24 hours")

def get_surprise_svd(user_id: int, recommendations_n: int = 10):
    all_movies_ids = movies_content["movieId"].unique()
    rated_movies = ratings[ratings["userId"] == user_id]["movieId"].values
    unrated_movies = [m for m in all_movies_ids if m not in rated_movies]
    predictions = [algorithm.predict(uid=user_id, iid=movie_id) for movie_id in unrated_movies]
    predictions.sort(key=lambda x: x.est, reverse=True)
    top_predictions = predictions[:recommendations_n]
    top_movie_ids = [pred.iid for pred in top_predictions]
    return movies_content[movies_content["movieId"].isin(top_movie_ids)][["movieId", "title"]]


def build_taste_vector(picked_movie_ids, rating_value=5.0):
    n_movies = user_item_sparse.shape[1]
    col_idx = [movie_id_to_idx[m] for m in picked_movie_ids if m in movie_id_to_idx]
    data = [rating_value] * len(col_idx)
    row_idx = [0] * len(col_idx)
    from scipy.sparse import csr_matrix
    return csr_matrix((data, (row_idx, col_idx)), shape=(1, n_movies))

def find_similar_users_filtered(taste_vector, picked_movie_ids, k=5, min_overlap=3, search_k=30):
    distances, indices_ = knn_model.kneighbors(taste_vector, n_neighbors=search_k)
    candidate_idx = indices_[0]
    candidate_distances = distances[0]

    picked_cols = [movie_id_to_idx[m] for m in picked_movie_ids if m in movie_id_to_idx]
    candidate_rows = user_item_sparse[candidate_idx][:, picked_cols]
    overlap_counts = (candidate_rows != 0).sum(axis=1).A1

    final_users, final_distances = [], []
    for i, (idx_, dist) in enumerate(zip(candidate_idx, candidate_distances)):
        if overlap_counts[i] >= min_overlap:
            final_users.append(user_id_map[idx_])
            final_distances.append(dist)
        if len(final_users) == k:
            break
    return final_users, final_distances

def get_coldstart_recommendations(filtered_users, distances, picked_movie_ids, top_n=10):
    svd_rec_list = [get_surprise_svd(uid, recommendations_n=10) for uid in filtered_users if uid > 0]
    movie_scores = {}
    for user_recs, dist in zip(svd_rec_list, distances):
        weight = 1 / (dist + 1e-6)
        n = len(user_recs)
        for rank, movie_id in enumerate(user_recs['movieId']):
            rank_score = (n - rank)
            movie_scores[movie_id] = movie_scores.get(movie_id, 0) + (rank_score * weight)
    for movie_id in picked_movie_ids:
        movie_scores.pop(movie_id, None)
    ranked = sorted(movie_scores.items(), key=lambda x: x[1], reverse=True)
    return ranked[:top_n]

def get_rated_movie_ids(user_token: str | None) -> set:
    if not user_token or not os.path.isfile(RATINGS_FILE):
        return set()
    ratings_df = pd.read_csv(RATINGS_FILE)
    user_ratings = ratings_df[ratings_df["userToken"] == user_token]
    return set(user_ratings["movieId"].unique())

@app.get("/")
def root():
    return {"message":"Movie Recommender API is running"}

@app.get("/movies/search")
def search_movies(query: str, limit: int = 10):
    results = movies_content[movies_content["title"].str.contains(query, case=False, na=False)]
    results = results.sort_values("weighted_rating", ascending=False)
    return results[["movieId","title","genres","weighted_rating"]].head(limit).to_dict(orient="records")

@app.get("/recommendations/content/{movie_title}")
def content_recommendations(movie_title: str, userToken: str | None = None):
    if movie_title not in indices:
        raise HTTPException(status_code=404, detail="Movie not found")
    idx = indices[movie_title]
    sim_row = cosine_similarity(tfidf_matrix[idx], tfidf_matrix).flatten()
    sim_scores = list(enumerate(sim_row))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = [s for s in sim_scores if s[0] != idx]
    movie_indices = [i[0] for i in sim_scores]

    rated_ids = get_rated_movie_ids(userToken)
    candidates = movies_content[["movieId", "title"]].iloc[movie_indices]
    candidates = candidates[~candidates["movieId"].isin(rated_ids)]
    return candidates.head(10).to_dict(orient="records")

@app.get("/recommendations/user/{user_id}")
def user_recommendations(user_id: int, n: int = 10):
    all_movies_ids = movies_content["movieId"].unique()
    rated_movies = ratings[ratings["userId"] == user_id]["movieId"].values
    
    if len(rated_movies) == 0:
        raise HTTPException(status_code=404, detail="User not found or has no ratings")
    unrated_movies = [m for m in all_movies_ids if m not in rated_movies]
    predictions = [algorithm.predict(uid=user_id, iid=movie_id) for movie_id in unrated_movies]
    predictions.sort(key= lambda x: x.est, reverse=True)
    top_predictions = predictions[:n]
    top_movie_ids = [pred.iid for pred in top_predictions]
    return movies_content[movies_content["movieId"].isin(top_movie_ids)][["movieId", "title"]].to_dict(orient="records")

@app.get("/recommendations/for-token/{user_token}")
def user_recommendations_by_token(user_token: str, n: int = 10):
    if not os.path.isfile("models/token_to_userid.pkl"):
        raise HTTPException(status_code=404, detail="No trained model with new users yet — run a retrain first")

    with open("models/token_to_userid.pkl", "rb") as f:
        token_to_userid = pickle.load(f)

    if user_token not in token_to_userid:
        raise HTTPException(
            status_code=404,
            detail="User not yet included in a trained model — try again after the next retrain"
        )

    user_id = token_to_userid[user_token]
    all_movies_ids = movies_content["movieId"].unique()
    rated_ids = get_rated_movie_ids(user_token)
    unrated_movies = [m for m in all_movies_ids if m not in rated_ids]

    predictions = [algorithm.predict(uid=user_id, iid=movie_id) for movie_id in unrated_movies]
    predictions.sort(key=lambda x: x.est, reverse=True)
    top_predictions = predictions[:n]
    top_movie_ids = [p.iid for p in top_predictions]

    return movies_content[movies_content["movieId"].isin(top_movie_ids)][["movieId", "title"]].to_dict(orient="records")

class MovieOnBoardingRequest(BaseModel):
    titles: list[str]
    userToken: str | None = None

@app.post("/recommendations/onboarding/movies")
def onboarding_by_movies(request: MovieOnBoardingRequest):
    picked_movie_ids = [movies_content.loc[indices[title], "movieId"] for title in request.titles if title in indices]
    if not picked_movie_ids:
        raise HTTPException(status_code=404, detail="No matching movies found")

    taste_vector = build_taste_vector(picked_movie_ids)
    filtered_users, filtered_distances = find_similar_users_filtered(taste_vector, picked_movie_ids)
    if not filtered_users:
        raise HTTPException(status_code=404, detail="No similar users found — try picking more popular movies")
    recs = get_coldstart_recommendations(filtered_users, filtered_distances, picked_movie_ids, top_n=25)
    rated_ids = get_rated_movie_ids(request.userToken)
    top_movie_ids = [movie_id for movie_id, _ in recs if movie_id not in rated_ids][:10]

    return movies_content[movies_content["movieId"].isin(top_movie_ids)][["movieId", "title", "genres"]].to_dict(orient="records")

class GenresOnBoardingRequest(BaseModel):
    genres: list[str]
    userToken: str | None = None
    
@app.post("/recommendations/onboarding/genres")
def onboarding_by_genres(request: GenresOnBoardingRequest):
    matches = movies_content[movies_content["genres_list"].apply(lambda genre_list: any(g in genre_list for g in request.genres))]
    rated_ids = get_rated_movie_ids(request.userToken)
    matches = matches[~matches["movieId"].isin(rated_ids)]

    top_matches = matches.sort_values("weighted_rating", ascending=False).head(10)
    return top_matches[["movieId", "title", "genres"]].to_dict(orient="records")

@app.post("/users/new")
def creat_user():
    new_token = str(uuid.uuid4())
    return {"userToken": new_token}

class RatingRequest(BaseModel):
    userToken: str
    movieId:int
    rating:float
    
@app.post("/ratings")
def sumbit_rating(request: RatingRequest):
    file_exists = os.path.isfile(RATINGS_FILE)
    with open(RATINGS_FILE, "a", newline="", encoding="utf-8")as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["userToken", "movieId", "rating", "timestamp"])
        writer.writerow([request.userToken, request.movieId, request.rating, pd.Timestamp.now().isoformat()])
    return{"status": "saved"}

@app.get("/ratings/{user_token}")
def get_user_rating(user_token: str):
    if not os.path.isfile(RATINGS_FILE):
        return {}
    user_ratings_df = pd.read_csv(RATINGS_FILE)
    user_ratings_df = user_ratings_df[user_ratings_df["userToken"] == user_token]
    user_ratings_df = user_ratings_df = user_ratings_df.sort_values("timestamp").drop_duplicates("movieId", keep="last")
    return dict(zip(user_ratings_df["movieId"], user_ratings_df["rating"]))

movie_details_cache = {}

@app.get("/movies/{movie_id}/details")
async def get_movie_details(movie_id:int):
    if movie_id in movie_details_cache:
            return movie_details_cache[movie_id]
    tmdb_id = links_df.loc[links_df["movieId"] == movie_id, "tmdbId"].values
    
    if len(tmdb_id) == 0 or pd.isna(tmdb_id[0]):
        raise HTTPException(status_code=404, detail="No TMDB mapping for this movie")
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"https://api.themoviedb.org/3/movie/{int(tmdb_id[0])}", params={"api_key": TMDB_API_KEY, "language": "en-US"})
    
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="TMDB fetch failed")
    
    data = resp.json()
    result = {
        "movieId": movie_id,
        "title": data.get("title"),
        "overview": data.get("overview"),
        "release_date": data.get("release_date"),
        "runtime": data.get("runtime"),
        "poster_path": data.get("poster_path"),
    }

    movie_details_cache[movie_id] = result
    return result


@app.on_event("shutdown")
def shutdown_scheduler():
    scheduler.shutdown()