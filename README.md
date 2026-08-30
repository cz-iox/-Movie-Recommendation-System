# CineMatch — Movie Recommendation System

A full-stack movie recommendation system built from scratch as a learning project — from raw MovieLens data to a working web app with a Python/scikit-learn backend and a vanilla JS frontend.

The goal wasn't just to ship a working recommender, but to actually understand why each piece works: why TF-IDF beats a plain word count, why a naive rating average is misleading, why SVD needs mean-centering, and why a "cold start" user breaks a collaborative filtering model. Every design decision below came out of hitting a real bug or a real limitation first, then fixing it.

## Features

- **Search** — find any movie in the MovieLens catalog by title
- **Content-Based Recommendations** — click a movie, get similar ones based on genre (TF-IDF + cosine similarity)
- **Personalized Recommendations** — SVD-based collaborative filtering trained on ~100k real user ratings, continuously retrained on new user activity
- **New-user onboarding (KNN cold-start)** — pick 3+ movies, and the system maps your taste to the most similar existing MovieLens users (via a KNN model over the user-item matrix, filtered by a minimum rating-overlap threshold to avoid spurious matches) and borrows their SVD recommendations, weighted by similarity
- **Genre-based onboarding** — pick 3+ genres and get instant recommendations, no rating history required
- **Rate movies** — 1-5 star rating on any movie card with a real movieId; ratings sync from the server so they persist across page reloads and devices, and already-rated movies are excluded from "Recommended for You"
- **Movie detail view** — click the info icon on any movie card to see its plot summary, release date, runtime, and poster, fetched live from TMDB, in a themed modal
- **Anonymous user identity** — a server-issued random token (not IP-based) stored in the browser identifies a returning viewer without requiring login
- **Continuous learning** — new ratings feed a scheduled retraining job that periodically rebuilds the SVD model so the collaborative filter improves over time
- Bilingual UI (English/Arabic, with RTL support)
- Posters via TMDB, taste profile persisted locally across visits

## How it works

| Layer | Technique | Why |
|---|---|---|
| Content-Based | TF-IDF over genres + Cosine Similarity | Works for any movie, even ones with almost no ratings |
| Collaborative Filtering | SVD (custom scipy implementation + scikit-surprise), periodically retrained | Captures taste patterns genres can't explain (e.g. users who loved Taxi Driver also loved Casablanca); retraining lets it learn from real usage instead of staying frozen on the original dataset |
| Cold Start — movie picks | KNN over the user-item matrix (cosine distance) to find the most similar existing users, filtered by minimum rating overlap so a match isn't based on 1-2 coincidental shared ratings, then a distance-weighted vote over their SVD recommendations | New users have no rating history for SVD to work with directly — this borrows the taste of real users who *do* have one |
| Cold Start — genre picks | Content-Based genre filtering ranked by a Bayesian weighted rating | Fallback for users who'd rather pick genres than specific movies |
| Ranking | Weighted Rating (IMDB-style Bayesian average) | A movie with one 5-star rating shouldn't outrank one with 300 ratings averaging 4.5 |
| Identity | Server-issued UUID token stored in `localStorage`, mapped to a numeric userId at retrain time | Lets ratings and recommendations persist per-viewer without building a login system |
| Movie Details | `movieId` → `tmdbId` lookup via `links.csv`, then a live TMDB fetch (cached in memory per movie) | MovieLens has no plot summaries — TMDB fills that gap on demand, only for movies the user actually opens |

## Tech Stack

**Data & ML:** Python, Pandas, NumPy, scikit-learn, scikit-surprise, SciPy, APScheduler
**Backend:** FastAPI, Uvicorn, httpx, python-dotenv
**Frontend:** HTML, CSS, vanilla JavaScript (no framework)
**Dataset:** MovieLens ml-latest-small (~100k ratings, 9,700 movies)
**Posters & Plot Data:** TMDB API

## Project Structure

```
movie-recommender/
├── data/
│   ├── raw/                # MovieLens CSVs (not committed — see setup)
│   └── new_ratings.csv     # ratings submitted by app users (generated at runtime)
├── notebooks/               # EDA, feature engineering, model training
├── models/                  # Trained models (TF-IDF matrix, SVD model, KNN model, user-item matrices, token map)
├── scripts/
│   └── retrain_svd.py       # rebuilds the SVD model from original + new ratings
├── api/
│   └── main.py               # FastAPI app — all endpoints + retraining scheduler
├── frontend/
│   ├── index.html
│   ├── style.css
│   ├── app.js
│   └── config.example.js     # copy to config.js and add your TMDB key
├── .env                       # TMDB_API_KEY for the backend (not committed — see setup)
├── requirements.txt
└── .gitignore
```

## Setup & Run Locally

### 1. Clone and set up the environment
```bash
git clone https://github.com/cz-iox/-Movie-Recommendation-System.git
cd movie-recommender
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

### 2. Get the dataset
Download `ml-latest-small.zip` from grouplens.org/datasets/movielens, unzip it, and place `movies.csv`, `ratings.csv`, `tags.csv`, `links.csv` into `data/raw/`.

### 3. Generate the trained models
Open `notebooks/data_exploration_01.ipynb` in Jupyter and run all cells top to bottom. This performs the EDA, cleans the data, builds the TF-IDF matrix, trains the SVD model, builds the KNN cold-start model, and saves everything into `models/` as `.pkl` files — the API depends on these existing before it can start.

```bash
jupyter notebook
```

### 4. Set up your TMDB API key (used by both backend and frontend)
Create a `.env` file in the project root (same folder as `requirements.txt`):
```
TMDB_API_KEY=your_actual_key_here
```
This powers the backend's `/movies/{movie_id}/details` endpoint. Make sure `.env` is listed in `.gitignore` so the key is never committed.

### 5. Run the API
```bash
uvicorn api.main:app --reload
```
Visit `http://127.0.0.1:8000/docs` for interactive API docs (Swagger UI). On startup, the API also starts a background job that retrains the SVD model every 24 hours on any ratings submitted through the app.

### 6. Set up the frontend
Copy `frontend/config.example.js` to `frontend/config.js` and add your own TMDB API key (used client-side for poster lookups):
```js
const TMDB_API_KEY = "YOUR_KEY_HERE";
```
Then just open `frontend/index.html` in a browser.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/movies/search?query=&limit=` | Search movies by title |
| GET | `/recommendations/content/{movie_title}` | Top 10 similar movies (genre-based), returned as `{movieId, title}` objects |
| GET | `/recommendations/user/{user_id}` | Personalized SVD recommendations for an existing MovieLens user (1–610) |
| POST | `/recommendations/onboarding/movies` | KNN cold-start recommendations from 3+ picked movie titles (new users), excludes already-rated movies |
| POST | `/recommendations/onboarding/genres` | Recommendations from 3+ picked genres (new users), excludes already-rated movies |
| POST | `/users/new` | Issues a new random UUID token identifying an anonymous viewer |
| POST | `/ratings` | Submits a 1-5 rating for a movie, tied to a user token |
| GET | `/ratings/{user_token}` | Returns a user's ratings (`{movieId: rating}`), used to restore star state on reload |
| GET | `/movies/{movie_id}/details` | Fetches plot summary, release date, runtime, and poster for a movie from TMDB (in-memory cached) |

## Challenges & What I Learned

Building this surfaced a lot of bugs and design questions that taught me more than the "happy path" ever would:

- **Weighted Rating vs. Average Rating** — a movie with a single 5★ rating was outranking Shawshank Redemption. Fixed by implementing a Bayesian weighted rating that only trusts a movie's average once it has enough ratings.
- **The Antz/Toy Story tie bug** — two movies with identical genre sets get a perfect 1.0 cosine similarity, which broke my "skip the first result" assumption for excluding a movie from its own recommendations. Fixed by excluding by identity (index), not by list position.
- **The 98.3% sparsity problem** — the user-item matrix is almost entirely empty, which made naive user-based filtering unreliable. This is exactly why SVD (matrix factorization) is the standard approach — it learns compressed latent factors instead of needing every cell filled in.
- **Genre voting bias in onboarding** — movies with generic, heavily-shared genres dominated the vote count. Fixed by capping candidates per source movie and summing similarity scores instead of raw counts.
- **`hidden` attribute vs. CSS specificity** — posters stayed invisible because a `.poster-fallback { display: flex }` rule was winning the CSS specificity fight against the browser's default `[hidden] { display: none }`. Fixed with an explicit override. The same bug resurfaced later with the movie-details info button and got the same fix (`.poster-info-btn[hidden] { display: none; }`).
- **Fake overlap from an all-zero matrix** — the KNN cold-start filter first used the dense (zero-filled) matrix to count rating overlap instead of the sparse (NaN) one, so the overlap filter silently did nothing. Fixed by computing overlap against the matrix that still has real NaNs.
- **A mis-scoped loop killed the distance weighting** — an indentation slip left the per-neighbor scoring loop outside the loop over neighbors, so every "aggregated" recommendation was silently just the last neighbor's list. Fixed by re-indenting.
- **RTL star-rating hover** — a CSS `:hover ~` sibling selector assumes LTR DOM order, so the star highlight ran backwards in Arabic. Fixed by driving the highlight with JS `mouseenter`/`mouseleave` instead of a direction-dependent CSS selector.
- **A duplicate function definition silently won** — an old version of `renderRatingStars` (without saved-rating support) was left further down the file; JavaScript just uses whichever same-named function is defined last, so it silently overrode the fixed version. Fixed by deleting the stale duplicate.
- **`localStorage.setItem` stringifies `undefined`** — an early endpoint mismatch (`/user/new` instead of `/users/new`) meant `data.userToken` was `undefined`, which `localStorage` happily stored as the literal string `"undefined"` — a truthy value that was then reused as a real token on every later visit, polluting `new_ratings.csv`. Fixed by rejecting `"undefined"`/`"null"` strings when reading the stored token, and by throwing on a failed `/users/new` request instead of proceeding with a bad value.
- **Filtering after truncation shrank the recommendation count** — already-rated movies were removed *after* slicing to the final top 10, so a user who'd rated several suggested movies saw fewer than 10 results. Fixed by requesting a larger candidate pool (25) from the scorer, filtering, then slicing to 10.
- **In-memory model vs. retrained model on disk** — retraining saved a new `algorithm_svd.pkl` to disk but the FastAPI process kept using the old model already loaded into memory. Fixed by having the retrain job return the new model and assigning it to the global variable immediately after a successful retrain, with a try/except so a failed retrain keeps serving the last good model instead of crashing the scheduler.
- **A misnamed `.env` file returned `None` silently** — `load_dotenv()` only looks for a file named exactly `.env` in the working directory; a file saved as `TMDB_KEY.env` was never read, so `os.getenv("TMDB_API_KEY")` returned `None` and every TMDB request failed with a generic 502. Fixed by renaming the file to `.env` and verifying the loaded value once with a temporary `print()`.
- **Two unrelated features silently shared one CSS class name** — the movie-details modal was first built reusing `.modal` / `.hidden`, which collided with the existing onboarding modal's styling and layout assumptions, producing a squashed, off-center popup. Fixed by giving it its own `.detail-modal-overlay` / `.detail-modal` classes and switching to the native `hidden` attribute (matching how the rest of the app already toggles modals) instead of a custom `.hidden` class.
- **Content-based recommendations had no `movieId`** — the "same vibe" results only ever returned movie titles as plain strings, so the new details button had nothing to call the details endpoint with and stayed invisible (correctly, given the `movie.movieId != null` guard) on every card in that row. Fixed by changing `/recommendations/content/{movie_title}` to return `{movieId, title}` objects instead of bare titles.

## Known Limitations

- **Cold Start Problem:** the original SVD model could only predict for the 610 users it was trained on; this is now mitigated by periodic retraining on new-user ratings and by KNN-based cold-start matching for users with no rating history yet.
- **Anonymous identity has no cross-device sync path yet:** the UUID token lives in browser `localStorage`, so clearing browser data, using a different browser, or switching devices starts a fresh identity with no rating history.
- **Genre-only content model:** recommendations are based purely on genre overlap, not plot, cast, or themes — though plot summaries are now available on-demand via the movie detail view, they aren't yet fed into the recommendation model itself.
- **No live deployment yet:** the app currently runs locally only; the scheduler only retrains while the server process is running.

## Future Improvements

- Feed TMDB plot summaries into the content-based model itself (TF-IDF over text + genres, not just genres) for richer similarity scoring
- A `/trending` endpoint and Docker + cloud deployment
- A proper account system for cross-device identity, if login is ever added

## License

This project was built for educational purposes using the public MovieLens dataset (GroupLens Research, University of Minnesota) and the TMDB API for poster artwork and plot data.