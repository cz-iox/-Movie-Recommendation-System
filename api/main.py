from fastapi import FastAPI, HTTPException
import pandas as pd 
from sklearn.metrics.pairwise import cosine_similarity
import pickle
from collections import Counter
from pydantic import BaseModel


app = FastAPI(title="Movie Recommender API")

from fastapi.middleware.cors import CORSMiddleware

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

@app.on_event("startup")
def load():
    global movies_content, ratings, tfidf_matrix, cosine_sim, algorithm,indices
    
    movies_content = pd.read_pickle("models/movies_content.pkl")
    ratings = pd.read_pickle("models/ratings.pkl")
    
    with open("models/tfidf_matrix.pkl", "rb") as f:
        tfidf_matrix = pickle.load(f)
    with open("models/algorithm_svd.pkl", "rb") as f:
        algorithm = pickle.load(f)
        
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
    indices = pd.Series(movies_content.index, index=movies_content["title"])
    print("All models loaded successfully! ")

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

@app.post("/recommendations/onboarding/movies")
def onboarding_by_movies(request: MovieOnBoardingRequest):
    score_total = Counter()
    for title in request.titles:
        if title not in indices:
            continue
        idx = indices[title]
        sim_scores = list(enumerate(cosine_sim[idx]))
        sim_scores = sorted(sim_scores, key= lambda x: x[1], reverse=True)
        sim_scores = [s for s in sim_scores if s[0] != idx][:5]
        for movie_idx, score in sim_scores:
            score_total[movie_idx] += score
    for title in request.titles:
        if title in indices:
            score_total.pop(indices[title], None)
    top_indices = [idx for idx, _ in score_total.most_common(10)]
    return movies_content.iloc[top_indices][["movieId", "title", "genres"]].to_dict(orient="records")

class GenresOnBoardingRequest(BaseModel):
    genres: list[str]

@app.post("/recommendations/onboarding/genres")
def onboarding_by_genres(request: GenresOnBoardingRequest):
    matches = movies_content[movies_content["genres_list"].apply(lambda genre_list: any(g in genre_list for g in request.genres))]
    top_matches = matches.sort_values("weighted_rating", ascending=False).head(10)
    return top_matches[["movieId", "title", "genres"]].to_dict(orient="records")