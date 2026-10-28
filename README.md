# CineMatch — Movie Recommendation System

A full-stack movie recommendation system built from scratch as a learning project — from raw MovieLens data to a working web app with a Python/scikit-learn backend and a vanilla JS frontend.

The goal wasn't just to ship a working recommender, but to actually understand why each piece works: why TF-IDF beats a plain word count, why a naive rating average is misleading, why SVD needs mean-centering, why a "cold start" user breaks a collaborative filtering model, and why a 33-million-rating dataset forces you to rethink data structures that worked fine at 100k rows. Every design decision below came out of hitting a real bug or a real limitation first, then fixing it.

## Features

- **Search** — find any movie in the MovieLens catalog by title
- **Content-Based Recommendations** — click a movie, get similar ones based on genre (TF-IDF + on-demand cosine similarity), excluding movies you've already rated
- **Personalized Recommendations** — SVD-based collaborative filtering trained on 33M+ real user ratings, continuously retrained on new user activity; new (token-based) users get real SVD-driven recommendations once they've been through a retrain cycle
- **New-user onboarding (KNN cold-start)** — pick 3+ movies, and the system maps your taste to the most similar existing MovieLens users (via a sparse-matrix KNN model, filtered by a minimum rating-overlap threshold to avoid spurious matches) and borrows their SVD recommendations, weighted by similarity
- **Genre-based onboarding** — pick 3+ genres and get instant recommendations, no rating history required
- **Rate movies** — 1-5 star rating on any movie card with a real movieId; ratings sync from the server so they persist across page reloads and devices, and already-rated movies are excluded from every recommendation surface (For You, same-vibe, onboarding)
- **Movie detail view** — click the info icon on any movie card to see its plot summary, release date, runtime, and poster, fetched live from TMDB, in a themed modal
- **Anonymous user identity** — a server-issued random token (not IP-based) stored in the browser identifies a returning viewer without requiring login; the token is mapped to a real numeric userId at each retrain, so token-based users eventually get first-class SVD predictions, not just cold-start approximations
- **Continuous learning** — new ratings feed a scheduled retraining job that periodically rebuilds the SVD model so the collaborative filter improves over time
- Bilingual UI (English/Arabic, with RTL support)
- Posters via TMDB, taste profile persisted locally across visits

## How it works

| Layer | Technique | Why |
|---|---|---|
| Content-Based | TF-IDF over genres, cosine similarity computed on demand for a single movie row | Works for any movie, even ones with almost no ratings — and avoids ever materializing a full movie × movie similarity matrix, which is unaffordable at ~86,000 movies |
| Collaborative Filtering | scikit-surprise SVD, periodically retrained on the full ratings set | Captures taste patterns genres can't explain (e.g. users who loved Taxi Driver also loved Casablanca); retraining lets it learn from real usage instead of staying frozen on the original dataset |
| Cold Start — movie picks | KNN over a sparse user-item matrix (cosine distance) to find the most similar existing users, filtered by minimum rating overlap so a match isn't based on 1-2 coincidental shared ratings, then a distance-weighted vote over their SVD recommendations | New users have no rating history for SVD to work with directly — this borrows the taste of real users who *do* have one |
| Cold Start — genre picks | Content-Based genre filtering ranked by a Bayesian weighted rating | Fallback for users who'd rather pick genres than specific movies |
| Ranking | Weighted Rating (IMDB-style Bayesian average) | A movie with one 5-star rating shouldn't outrank one with 300 ratings averaging 4.5 |
| Identity | Server-issued UUID token stored in `localStorage`, mapped to a numeric userId at retrain time and persisted in `token_to_userid.pkl` | Lets ratings and recommendations persist per-viewer without building a login system, and lets a token-based user eventually be looked up by the trained SVD model directly |
| Movie Details | `movieId` → `tmdbId` lookup via `links.csv`, then a live TMDB fetch (cached in memory per movie) | MovieLens has no plot summaries — TMDB fills that gap on demand, only for movies the user actually opens |

## Tech Stack

**Data & ML:** Python, Pandas, NumPy, SciPy (sparse matrices), scikit-learn, scikit-surprise, APScheduler
**Backend:** FastAPI, Uvicorn, httpx, python-dotenv
**Frontend:** HTML, CSS, vanilla JavaScript (no framework)
**Dataset:** MovieLens ml-latest (~33 million ratings, ~86,000 movies)
**Posters & Plot Data:** TMDB API

## Project Structure

```
movie-recommender/
├── data/
│   ├── raw/                # MovieLens CSVs (not committed — see setup)
│   └── new_ratings.csv     # ratings submitted by app users (generated at runtime)
├── notebooks/               # EDA, feature engineering, model training
├── models/                  # Trained models — TF-IDF matrix, SVD model, KNN model,
│                             # sparse user-item matrix + id maps, token-to-userId map
├── scripts/
│   └── retrain_svd.py       # rebuilds the SVD model from original + new ratings, updates token map
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
Download `ml-latest.zip` from grouplens.org/datasets/movielens, unzip it, and place `movies.csv`, `ratings.csv`, `tags.csv`, `links.csv` into `data/raw/`.

> This project originally ran on `ml-latest-small` (~100k ratings) and was upgraded to `ml-latest` (~33M ratings) for a more realistic scale. `ml-latest` needs sparse-matrix handling throughout to run comfortably on an 8GB-RAM machine — see the notes under Challenges below if adapting this further. Note that `ml-latest` is a rolling snapshot that GroupLens updates over time, so exact counts and results may differ slightly depending on when you download it.

### 3. Generate the trained models
Open the notebook in `notebooks/` in Jupyter and run all cells top to bottom (Restart & Run All, not a partial re-run — several cells depend on execution order). This performs the EDA, cleans the data, builds the TF-IDF matrix, trains the SVD model on the full rating set, builds the sparse user-item matrix and KNN cold-start model, and saves everything into `models/` as `.pkl` files — the API depends on these existing before it can start.

```bash
jupyter notebook
```

Expect this to take a while at `ml-latest` scale — SVD training alone can take upwards of 10 minutes depending on hardware.

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
Visit `http://127.0.0.1:8000/docs` for interactive API docs (Swagger UI). Startup takes noticeably longer than it did on `ml-latest-small` — it's loading a 33M-row ratings table and a model trained on it. On startup, the API also starts a background job that retrains the SVD model every 24 hours on any ratings submitted through the app.

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
| GET | `/recommendations/content/{movie_title}?userToken=` | Top 10 similar movies (genre-based), returned as `{movieId, title}` objects, excluding movies the given token has already rated |
| GET | `/recommendations/user/{user_id}` | Personalized SVD recommendations for an existing MovieLens user by their original numeric userId |
| GET | `/recommendations/for-token/{user_token}` | Personalized SVD recommendations for a browser-token user, once that token has been through a retrain cycle (404 until then — see `token_to_userid.pkl`) |
| POST | `/recommendations/onboarding/movies` | KNN cold-start recommendations from 3+ picked movie titles (new users), excludes already-rated movies |
| POST | `/recommendations/onboarding/genres` | Recommendations from 3+ picked genres (new users), excludes already-rated movies |
| POST | `/users/new` | Issues a new random UUID token identifying an anonymous viewer |
| POST | `/ratings` | Submits a 1-5 rating for a movie, tied to a user token |
| GET | `/ratings/{user_token}` | Returns a user's ratings (`{movieId: rating}`), used to restore star state on reload |
| GET | `/movies/{movie_id}/details` | Fetches plot summary, release date, runtime, and poster for a movie from TMDB (in-memory cached) |

The frontend calls `/recommendations/for-token/{user_token}` first for the "For You" row and falls back to the KNN onboarding endpoints if the token isn't in the trained model yet — so a brand-new user gets cold-start recommendations immediately, and real SVD-based ones after the next scheduled retrain.

## Challenges & What I Learned

Building this surfaced a lot of bugs and design questions that taught me more than the "happy path" ever would:

- **Weighted Rating vs. Average Rating** — a movie with a single 5★ rating was outranking Shawshank Redemption. Fixed by implementing a Bayesian weighted rating that only trusts a movie's average once it has enough ratings.
- **The Antz/Toy Story tie bug** — two movies with identical genre sets get a perfect 1.0 cosine similarity, which broke my "skip the first result" assumption for excluding a movie from its own recommendations. Fixed by excluding by identity (index), not by list position.
- **The 98.3% sparsity problem** — the user-item matrix is almost entirely empty, which made naive user-based filtering unreliable. This is exactly why SVD (matrix factorization) is the standard approach — it learns compressed latent factors instead of needing every cell filled in.
- **Genre voting bias in onboarding** — movies with generic, heavily-shared genres dominated the vote count. Fixed by capping candidates per source movie and summing similarity scores instead of raw counts.
- **`hidden` attribute vs. CSS specificity** — posters (and later the movie-details info button) stayed invisible/visible incorrectly because a `display: flex` rule was winning the CSS specificity fight against the browser's default `[hidden] { display: none }`. Fixed with an explicit `[hidden]` override on each affected class.
- **Fake overlap from an all-zero matrix** — the KNN cold-start filter first used the dense (zero-filled) matrix to count rating overlap instead of the sparse (NaN) one, so the overlap filter silently did nothing. Fixed by computing overlap against the matrix that still has real missing values.
- **A mis-scoped loop killed the distance weighting** — an indentation slip left the per-neighbor scoring loop outside the loop over neighbors, so every "aggregated" recommendation was silently just the last neighbor's list. Fixed by re-indenting.
- **RTL star-rating hover** — a CSS `:hover ~` sibling selector assumes LTR DOM order, so the star highlight ran backwards in Arabic. Fixed by driving the highlight with JS `mouseenter`/`mouseleave` instead of a direction-dependent CSS selector.
- **A duplicate function definition silently won** — an old version of `renderRatingStars` (without saved-rating support) was left further down the file; JavaScript just uses whichever same-named function is defined last, so it silently overrode the fixed version. Fixed by deleting the stale duplicate.
- **`localStorage.setItem` stringifies `undefined`** — an early endpoint mismatch (`/user/new` instead of `/users/new`) meant `data.userToken` was `undefined`, which `localStorage` happily stored as the literal string `"undefined"` — a truthy value that was then reused as a real token on every later visit, polluting `new_ratings.csv`. Fixed by rejecting `"undefined"`/`"null"` strings when reading the stored token, and by throwing on a failed `/users/new` request instead of proceeding with a bad value.
- **Filtering after truncation shrank the recommendation count** — already-rated movies were removed *after* slicing to the final top 10 in more than one endpoint (onboarding, and later the content-based "same vibe" results), so a user who'd rated several suggested movies saw fewer than 10 results. Fixed by filtering against a larger candidate pool first, then slicing to 10.
- **In-memory model vs. retrained model on disk** — retraining saved a new `algorithm_svd.pkl` to disk but the FastAPI process kept using the old model already loaded into memory. Fixed by having the retrain job return the new model and assigning it to the global variable immediately after a successful retrain, with a try/except so a failed retrain keeps serving the last good model instead of crashing the scheduler.
- **A misnamed `.env` file returned `None` silently** — `load_dotenv()` only looks for a file named exactly `.env` in the working directory; a file saved as `TMDB_KEY.env` was never read, so `os.getenv("TMDB_API_KEY")` returned `None` and every TMDB request failed with a generic 502. Fixed by renaming the file to `.env` and verifying the loaded value once with a temporary `print()`.
- **Two unrelated features silently shared one CSS class name** — the movie-details modal was first built reusing the onboarding modal's `.modal` / `.hidden` classes, colliding with its styling and layout assumptions and producing a squashed, off-center popup. Fixed by giving it its own `.detail-modal-overlay` / `.detail-modal` classes and switching to the native `hidden` attribute (matching how the rest of the app already toggles modals).
- **Content-based recommendations had no `movieId`, and no rated-movie filtering at all** — the "same vibe" results only ever returned movie titles as plain strings, with no way to exclude already-rated movies. Fixed by changing `/recommendations/content/{movie_title}` to return `{movieId, title}` objects and accept an optional `userToken` query param to filter out rated movies, same as the onboarding endpoints.
- **A trained SVD model already "knows" a new user, but nothing could reach that knowledge** — after a retrain, a browser-token user's ratings get mapped to a real numeric userId and folded into the SVD model, but the only user-recommendations endpoint looked them up in the *original* static `ratings` table by numeric ID, which never contains token-based users. Realized the retrain script was already saving the missing piece (`token_to_userid.pkl`) but nothing read it. Fixed by adding `/recommendations/for-token/{user_token}`, which loads the map fresh from disk on every call (so it always reflects the latest retrain without needing a server restart) and falls through to a 404 the frontend already knows how to catch and fall back from.
- **Upgrading to `ml-latest` broke every "just materialize the full matrix" assumption at once** — going from ~9,700 to ~86,000 movies made a full movie × movie cosine similarity matrix (~7.5 billion cells) and a dense user × movie matrix (~331,000 × 86,000) both infeasible on 8GB of RAM. Fixed by computing content similarity on demand for a single movie row instead of precomputing the whole matrix, and by rebuilding the user-item matrix, its overlap counts, and the KNN cold-start logic entirely on `scipy.sparse` structures with explicit `userId`/`movieId` ↔ matrix-index maps, instead of a pandas `pivot_table` and `.loc[]` indexing.
- **A leftover exploratory cell broke `Run All`** — an early duplicate TF-IDF cell (left over from initial development, before `movies_content` existed yet) executed *before* the cell that actually defines `movies_content`, causing a `NameError` on any full top-to-bottom notebook run even though the notebook worked fine when cells were run out of order by hand during development. A same-shaped issue existed with a custom SVD-via-`svds` exploration block that was never the model actually used in production but still referenced now-removed dense variables. Fixed by deleting both once it was clear neither fed anything the saved `.pkl` files or the API depended on.
- **A relative-path notebook only works from its own directory** — CSVs loaded fine when the notebook's working directory was the project root, but silently pointed at the wrong (nonexistent) folder once opened from inside `notebooks/`. `os.getcwd()` made the mismatch obvious; fixed by prefixing all data/model paths in the notebook with `../`.

## Known Limitations

- **Cold Start Problem:** brand-new users have no rating history for the SVD model to use directly; this is mitigated by KNN-based cold-start matching immediately after onboarding, and by real SVD predictions becoming available for that user after the next scheduled retrain (up to 24 hours later).
- **Anonymous identity has no cross-device sync path yet:** the UUID token lives in browser `localStorage`, so clearing browser data, using a different browser, or switching devices starts a fresh identity with no rating history.
- **Genre-only content model:** recommendations are based purely on genre overlap, not plot, cast, or themes — though plot summaries are now available on-demand via the movie detail view, they aren't yet fed into the recommendation model itself.
- **No live deployment yet:** the app currently runs locally only; the scheduler only retrains while the server process is running.
- **Startup is noticeably slower at `ml-latest` scale:** loading the ratings table, the trained SVD model, and the sparse matrices at process startup takes longer than it did on `ml-latest-small`; not yet profiled/optimized beyond confirming it's a one-time cost at boot, not a per-request one.

## Future Improvements

- Feed TMDB plot summaries into the content-based model itself (TF-IDF over text + genres, not just genres) for richer similarity scoring
- A `/trending` endpoint and Docker + cloud deployment
- A proper account system for cross-device identity, if login is ever added
- Profile and reduce the ml-latest startup time (e.g. lazy-loading the static `ratings` table, which is only needed by the legacy numeric-userId endpoint)

## License

This project was built for educational purposes using the public MovieLens dataset (GroupLens Research, University of Minnesota) and the TMDB API for poster artwork and plot data.
