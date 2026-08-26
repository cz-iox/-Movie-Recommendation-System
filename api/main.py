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


scheduler = BackgroundScheduler()

app = FastAPI(title="Movie Recommender API")

RATINGS_FILE = "data/new_ratings.csv"


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

movies_content = None
ratings = None 
tfidf_matrix = None
cosine_sim = None
algorithm = None
knn_model = None
knn_matrix = None
user_item_matrix = None

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
    global movies_content, ratings, tfidf_matrix, cosine_sim, algorithm,indices
    global knn_matrix, user_item_matrix, knn_model
    
    movies_content = pd.read_pickle("models/movies_content.pkl")
    ratings = pd.read_pickle("models/ratings.pkl")
    
    with open("models/tfidf_matrix.pkl", "rb") as f:
        tfidf_matrix = pickle.load(f)
    with open("models/algorithm_svd.pkl", "rb") as f:
        algorithm = pickle.load(f)
    with open("models/knn_model.pkl", "rb") as f:
        knn_model = pickle.load(f)
    with open("models/knn_matrix.pkl", "rb") as f:
        knn_matrix = pickle.load(f)
    with open("models/user_item_matrix.pkl", "rb") as f:
        user_item_matrix = pickle.load(f)
        
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
    indices = pd.Series(movies_content.index, index=movies_content["title"])
    print("All models loaded successfully! ")
    scheduler.add_job( scheduled_retrain, "interval", hours=24, id="retrain_svd_job")
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
    taste_vector = pd.Series(0.0, index=user_item_matrix.columns)
    taste_vector.loc[picked_movie_ids] = rating_value
    return taste_vector

def find_similar_users_filtered(taste_vector, picked_movie_ids, k=5, min_overlap=3, search_k=30):
    taste_vector_2d = taste_vector.values.reshape(1, -1)
    distances, indices_ = knn_model.kneighbors(taste_vector_2d, n_neighbors=search_k)
    candidate_ids = knn_matrix.index[indices_[0]]
    candidate_distances = distances[0]

    overlap_counts = user_item_matrix.loc[candidate_ids, picked_movie_ids].notna().sum(axis=1)
    valid_candidates = overlap_counts[overlap_counts >= min_overlap].index

    final_users, final_distances = [], []
    for uid, dist in zip(candidate_ids, candidate_distances):
        if uid in valid_candidates:
            final_users.append(uid)
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
def search_movies(query: str,  limit: int=10 ):
    results = movies_content[movies_content["title"].str.contains(query, case=False, na=False)]
    return results[["movieId","title","genres"]].head(limit).to_dict(orient="records")

@app.get("/recommendations/content/{movie_title}")
def content_recommendations(movie_title:str):
    if movie_title not in indices:
        raise HTTPException(status_code=404, detail="Movie not found")
    idx = indices[movie_title]
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = [s for s in sim_scores if s[0] !=idx]
    sim_scores = sim_scores[:10]
    movie_indices = [i[0] for i in sim_scores]
    return movies_content["title"].iloc[movie_indices].tolist()

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
    top_movie_ids = [movie_id for movie_id, _ in recs if movie_id not in rated_ids][:10]  # نرجع بس أول 10 بعد الفلترة

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

@app.on_event("shutdown")
def shutdown_scheduler():
    scheduler.shutdown()