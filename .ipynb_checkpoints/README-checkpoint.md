#CineMatch — Movie Recommendation System

A full-stack movie recommendation system built from scratch as a learning project — from raw MovieLens data to a
working web app with a Python/scikit-learn backend and a vanilla JS frontend.

The goal wasn't just to ship a working recommender, but to actually understand *why* each piece works: why TF-IDF beats a plain word count,
why a naive rating average is misleading, why SVD needs mean-centering, and why a "cold start" user breaks a collaborative filtering model. Every design decision below came out of hitting a real bug or a real limitation first, then fixing it.

# Features

- **Search** — find any movie in the MovieLens catalog by title
- **Content-Based Recommendations** — click a movie, get similar ones based on genre (TF-IDF + cosine similarity)
- **Personalized Recommendations** — SVD-based collaborative filtering trained on ~100k real user ratings
- **New-user onboarding** — pick 3+ genres or 3+ favorite movies and get instant recommendations, no rating history required
- **Bilingual UI** (English/Arabic, with RTL support)
- **Posters via TMDB**, taste profile persisted locally across visits

#How it works

| Layer | Technique | Why |
|---|---|---|
| Content-Based | TF-IDF over genres + Cosine Similarity | Works for any movie, even ones with almost no ratings |
| Collaborative Filtering | SVD (custom `scipy` implementation + `scikit-surprise`) | Captures taste patterns genres can't explain (e.g. users who loved *Taxi Driver* also loved *Casablanca*) |
| Cold Start (new users) | Content-Based voting across 3+ picked movies, or genre filtering ranked by a Bayesian weighted rating | SVD can't predict for a user it never trained on — see *Known Limitations* below |
| Ranking | Weighted Rating (IMDB-style Bayesian average) | A movie with one 5-star rating shouldn't outrank one with 300 ratings averaging 4.5 |

# Tech Stack

**Data & ML:** Python, Pandas, NumPy, scikit-learn, scikit-surprise, SciPy
**Backend:** FastAPI, Uvicorn
**Frontend:** HTML, CSS, vanilla JavaScript (no framework)
**Dataset:** [MovieLens ml-latest-small](https://grouplens.org/datasets/movielens/) (~100k ratings, 9,700 movies)
**Posters:** [TMDB API](https://www.themoviedb.org/documentation/api)

# Project Structure

```
movie-recommender/
├── data/raw/              # MovieLens CSVs (not committed — see setup)
├── notebooks/             # EDA, feature engineering, model training
├── models/                # Trained models (TF-IDF matrix, SVD model, processed data)
├── api/
│   └── main.py             # FastAPI app — all endpoints
├── frontend/
│   ├── index.html
│   ├── style.css
│   ├── app.js
│   └── config.example.js   # copy to config.js and add your TMDB key
├── requirements.txt
└── .gitignore
```

# Setup & Run Locally

## 1. Clone and set up the environment
```bash
git clone https://github.com/cz-iox/-Movie-Recommendation-System.git
cd movie-recommender
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

## 2. Get the dataset
Download **ml-latest-small.zip** from [grouplens.org/datasets/movielens](https://grouplens.org/datasets/movielens/), unzip it, and place `movies.csv`, `ratings.csv`, `tags.csv`, `links.csv` into `data/raw/`.

## 3. Generate the trained models
Open `notebooks/data_exploration_01.ipynb` in Jupyter and run all cells top to bottom. This performs the EDA, cleans the data, builds the TF-IDF matrix, trains the SVD model, and saves everything into `models/` as `.pkl` files — the API depends on these existing before it can start.

```bash
jupyter notebook
```

## 4. Run the API
```bash
uvicorn api.main:app --reload
```
Visit `http://127.0.0.1:8000/docs` for interactive API docs (Swagger UI).

## 5. Set up the frontend
Copy `frontend/config.example.js` to `frontend/config.js` and add your own [TMDB API key](https://www.themoviedb.org/settings/api):
```js
const TMDB_API_KEY = "YOUR_KEY_HERE";
```
Then just open `frontend/index.html` in a browser.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/movies/search?query=&limit=` | Search movies by title |
| GET | `/recommendations/content/{movie_title}` | Top 10 similar movies (genre-based) |
| GET | `/recommendations/user/{user_id}` | Personalized SVD recommendations for an existing MovieLens user (1–610) |
| POST | `/recommendations/onboarding/movies` | Recommendations from 3+ picked movie titles (new users) |
| POST | `/recommendations/onboarding/genres` | Recommendations from 3+ picked genres (new users) |

# Challenges & What I Learned

Building this surfaced a lot of bugs and design questions that taught me more than the "happy path" ever would:

- **Weighted Rating vs. Average Rating** — a movie with a single 5★ rating was outranking Shawshank Redemption. Fixed by implementing a Bayesian weighted rating that only trusts a movie's average once it has enough ratings.
- **The Antz/Toy Story tie bug** — two movies with identical genre sets get a perfect 1.0 cosine similarity, which broke my "skip the first result" assumption for excluding a movie from its own recommendations. Fixed by excluding by identity (index), not by list position.
- **The 98.3% sparsity problem** — the user-item matrix is almost entirely empty, which made naive user-based filtering unreliable (a "top pick" based on a single rating from one similar user). This is exactly why SVD (matrix factorization) is the standard approach — it learns compressed latent factors instead of needing every cell filled in.
- **Genre voting bias in onboarding** — when combining recommendations from 3 picked movies, movies with generic, heavily-shared genres (like the Adventure|Animation|Children|Comedy|Fantasy combo) dominated the vote count. Fixed by capping candidates per source movie and summing similarity *scores* instead of raw counts.
- **`hidden` attribute vs. CSS specificity** — posters stayed invisible even after the `hidden` attribute was correctly removed, because a `.poster-fallback { display: flex }` rule was winning the CSS specificity fight against the browser's default `[hidden] { display: none }`. Fixed with an explicit `.poster-fallback[hidden] { display: none }` override.

# Known Limitations

- **Cold Start Problem**: the SVD model can only predict for the 610 users it was trained on. New users get content-based recommendations instead (see onboarding), not true collaborative filtering — a full fix would mean periodically retraining SVD on new ratings, which this project defers as a future improvement.
- **Genre-only content model**: recommendations are based purely on genre overlap, not plot, cast, or themes — two genre-identical movies are treated as 100% similar even if their stories are nothing alike.
- **No live deployment yet**: the app currently runs locally only.

# Future Improvements

- Nearest-neighbor cold-start matching (map a new user's taste vector to the most similar existing MovieLens user and borrow their SVD recommendations)
- Periodic SVD retraining pipeline to properly onboard new users into the collaborative model
- Richer content features (plot summaries via TMDB, not just genres)
- A `/trending` endpoint and Docker + cloud deployment

# License

This project was built for educational purposes using the public [MovieLens dataset](https://grouplens.org/datasets/movielens/) (GroupLens Research, University of Minnesota) and the [TMDB API](https://www.themoviedb.org/) for poster artwork.
