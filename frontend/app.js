
  // ============================================================
  // 1. Configuration & Constants
  // ============================================================
  const API_BASE = "http://127.0.0.1:8000";

  // TMDB is used ONLY for posters (our backend has no poster data).

  const TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie";
  const TMDB_IMG_BASE = "https://image.tmdb.org/t/p/w300";

  // No TMDB ids here — these are just labels we use for the onboarding UI.
  const GENRES_LIST = [
    { key: "Action", name_en: "Action", name_ar: "أكشن", icon: "💥" },
    { key: "Adventure", name_en: "Adventure", name_ar: "مغامرة", icon: "🗺️" },
    { key: "Animation", name_en: "Animation", name_ar: "رسوم متحركة", icon: "🎨" },
    { key: "Children", name_en: "Children", name_ar: "أطفال", icon: "🧸" },
    { key: "Comedy", name_en: "Comedy", name_ar: "كوميديا", icon: "😂" },
    { key: "Crime", name_en: "Crime", name_ar: "جريمة", icon: "🔫" },
    { key: "Documentary", name_en: "Documentary", name_ar: "وثائقي", icon: "🎥" },
    { key: "Drama", name_en: "Drama", name_ar: "دراما", icon: "🎭" },
    { key: "Fantasy", name_en: "Fantasy", name_ar: "فانتازيا", icon: "🧙" },
    { key: "Film-Noir", name_en: "Film-Noir", name_ar: "فيلم نوار", icon: "🕵️" },
    { key: "Horror", name_en: "Horror", name_ar: "رعب", icon: "👻" },
    { key: "Musical", name_en: "Musical", name_ar: "موسيقي", icon: "🎵" },
    { key: "Mystery", name_en: "Mystery", name_ar: "غموض", icon: "🔎" },
    { key: "Romance", name_en: "Romance", name_ar: "رومانسية", icon: "❤️" },
    { key: "Sci-Fi", name_en: "Sci-Fi", name_ar: "خيال علمي", icon: "🚀" },
    { key: "Thriller", name_en: "Thriller", name_ar: "إثارة", icon: "😱" },
    { key: "War", name_en: "War", name_ar: "حرب", icon: "⚔️" },
    { key: "Western", name_en: "Western", name_ar: "غربي", icon: "🤠" },
  ];

  // ============================================================
  // 2. Centralized Application State
  // ============================================================
  const state = {
    language: localStorage.getItem("cineMatchLanguage") || "en",
    currentView: "home",
    selectedGenres: new Set(),
    selectedMovies: [], // [{ movieId, title, genres }]
    onboardingStep: "mode",
    userTasteConfigured: false,
  };

  // ============================================================
  // 3. Translations Dictionary
  // ============================================================
  const translations = {
    en: {
      home: "Home", explore: "Explore", recommendations: "For You",
      favoriteGenres: "YOUR FAVORITE GENRES", noGenres: "No preferences set yet",
      editPreferences: "Edit preferences",
      searchPlaceholder: "Search for a movie and discover similar ones...",
      newViewer: "New Viewer", viewer: "Viewer", switch: "Switch",
      pickedForYou: "PICKED FOR YOU", heroTitle: "Find a movie you'll love",
      heroDescription: "Search for a movie you love, or tell us what you like so we can build personalized recommendations for you.",
      chooseTaste: "Choose your taste", searchResults: "Search Results",
      similarMovies: "Movies with the same vibe", recommendedForYou: "Recommended for You",
      viewAll: "View all ›",
      recommendationHint: "Choose 3 or more movies, or select your favorite genres to get personalized recommendations.",
      trending: "Trending Now",
      welcome: "Welcome 👋 Let's get to know your taste",
      onboardingDescription: "Choose one way to build your first recommendations. You can change it later.",
      favoriteGenresMode: "Choose your favorite genres",
      favoriteGenresModeDesc: "The fastest way — choose 3 or more genres",
      favoriteMoviesMode: "Choose movies you love",
      favoriteMoviesModeDesc: "More accurate — choose 3 or more movies",
      chooseThreeGenres: "Choose at least 3 genres",
      chooseThreeMovies: "Choose at least 3 movies you love",
      ofThree: "of 3 minimum selected", back: "Back", saveAndStart: "Save & Start",
      movieSearchPlaceholder: "Search for a movie to add...",
      noImage: "No image", loading: "Loading...", noResults: "No movies found.",
      apiError: "Couldn't reach the recommender API. Is the server running?",
    },
    ar: {
      home: "الرئيسية", explore: "استكشاف", recommendations: "توصياتي",
      favoriteGenres: "الأنواع المفضلة", noGenres: "لم يتم تحديد تفضيلات بعد",
      editPreferences: "تعديل التفضيلات",
      searchPlaceholder: "ابحث عن فيلم لاكتشاف أفلام مشابهة...",
      newViewer: "مشاهد جديد", viewer: "مشاهد", switch: "تغيير",
      pickedForYou: "مختار لك", heroTitle: "اعثر على فيلم ستحبه",
      heroDescription: "ابحث عن فيلم تحبه، أو حدد ذوقك لنبني لك توصيات مخصصة.",
      chooseTaste: "حدد ذوقك السينمائي", searchResults: "نتائج البحث",
      similarMovies: "أفلام تحمل نفس الطابع", recommendedForYou: "موصى به لك",
      viewAll: "عرض الكل ›",
      recommendationHint: "اختر 3 أفلام أو أكثر، أو حدد أنواعك المفضلة للحصول على توصيات مخصصة.",
      trending: "الأكثر رواجاً الآن",
      welcome: "أهلاً بك 👋 دعنا نتعرف على ذوقك",
      onboardingDescription: "اختر طريقة واحدة لبناء توصياتك الأولى. يمكنك تغييرها لاحقاً.",
      favoriteGenresMode: "اختر أنواعك المفضلة",
      favoriteGenresModeDesc: "الطريقة الأسرع — اختر 3 أنواع أو أكثر",
      favoriteMoviesMode: "اختر أفلاماً تحبها",
      favoriteMoviesModeDesc: "الطريقة الأدق — اختر 3 أفلام أو أكثر",
      chooseThreeGenres: "اختر 3 أنواع على الأقل",
      chooseThreeMovies: "اختر 3 أفلام على الأقل بتحبها",
      ofThree: "من 3 على الأقل محددة", back: "رجوع", saveAndStart: "حفظ وابدأ",
      movieSearchPlaceholder: "ابحث عن فيلم لتضيفه...",
      noImage: "لا توجد صورة", loading: "جاري التحميل...", noResults: "لم يتم العثور على أفلام.",
      apiError: "تعذّر الوصول لسيرفر الـ API — تأكد إن الـ FastAPI شغال.",
    },
  };

  function t(key) {
    return translations[state.language]?.[key] || key;
  }

  // ============================================================
  // 4. DOM References
  // ============================================================
  const dom = {
    activeUserLabel: document.getElementById("active-user-label"),
    switchUserBtn: document.getElementById("switch-user-btn"),
    tasteChips: document.getElementById("taste-chips"),
    editTasteBtn: document.getElementById("edit-taste-btn"),

    searchForm: document.getElementById("search-form"),
    searchBox: document.getElementById("search-box"),
    searchResultsSection: document.getElementById("search-results-section"),
    searchResults: document.getElementById("search-results"),

    heroSection: document.getElementById("hero-section"),
    heroCtaBtn: document.getElementById("hero-cta-btn"),

    similarSection: document.getElementById("similar-section"),
    similarMovieName: document.getElementById("similar-movie-name"),
    similarResults: document.getElementById("similar-results"),

    foryouSection: document.getElementById("foryou-section"),
    foryouResults: document.getElementById("foryou-results"),

    onboardingOverlay: document.getElementById("onboarding-overlay"),
    modalCloseBtn: document.getElementById("modal-close-btn"),
    stepMode: document.getElementById("step-mode"),
    stepGenres: document.getElementById("step-genres"),
    stepMovies: document.getElementById("step-movies"),

    modeGenresBtn: document.getElementById("mode-genres-btn"),
    modeMoviesBtn: document.getElementById("mode-movies-btn"),

    genreGrid: document.getElementById("genre-grid"),
    genresCounter: document.getElementById("genres-counter"),
    genresBackBtn: document.getElementById("genres-back-btn"),
    genresConfirmBtn: document.getElementById("genres-confirm-btn"),

    onboardingMovieSearch: document.getElementById("onboarding-movie-search"),
    onboardingSearchResults: document.getElementById("onboarding-search-results"),
    pickedMovies: document.getElementById("picked-movies"),
    moviesCounter: document.getElementById("movies-counter"),
    moviesBackBtn: document.getElementById("movies-back-btn"),
    moviesConfirmBtn: document.getElementById("movies-confirm-btn"),

    navItems: document.querySelectorAll("[data-view]"),
    langSwitcher: document.getElementById("language-switcher"),

    posterCardTemplate: document.getElementById("poster-card-template"),
    genrePillTemplate: document.getElementById("genre-pill-template"),
  };

  // ============================================================
  // 5. API Layer — real endpoints only, no silent mock fallback.
  //    A failed request throws; callers decide how to show that.
  // ============================================================
  async function apiGet(path) {
    const res = await fetch(`${API_BASE}${path}`);
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || `API error ${res.status}`);
    }
    return res.json();
  }

  async function apiPost(path, data) {
    const res = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || `API error ${res.status}`);
    }
    return res.json();
  }

  const searchMovies = (query, limit = 10) =>
    apiGet(`/movies/search?query=${encodeURIComponent(query)}&limit=${limit}`);

  const getContentRecommendations = (movieTitle) =>
    apiGet(`/recommendations/content/${encodeURIComponent(movieTitle)}`);

  const getOnboardingRecommendationsByMovies = (titles, userToken) =>
    apiPost(`/recommendations/onboarding/movies`, { titles, userToken });

  const getOnboardingRecommendationsByGenres = (genres, userToken) =>
    apiPost(`/recommendations/onboarding/genres`, { genres, userToken });

  // ============================================================
  // 6. TMDB poster lookup (by title — our API has no tmdbId field)
  // ============================================================
  const posterCache = new Map();

  function splitTitleYear(fullTitle) {
    const m = fullTitle.match(/^(.*)\s\((\d{4})\)\s*$/);
    return m ? { title: m[1].trim(), year: m[2] } : { title: fullTitle.trim(), year: null };
  }

  async function getPosterUrl(fullTitle) {
    if (posterCache.has(fullTitle)) return posterCache.get(fullTitle);
    const { title, year } = splitTitleYear(fullTitle);
    const params = new URLSearchParams({ api_key: TMDB_API_KEY, query: title, ...(year ? { year } : {}) });
    try {
      const res = await fetch(`${TMDB_SEARCH_URL}?${params}`);
      const data = await res.json();
      const first = data.results?.[0];
      const url = first?.poster_path ? `${TMDB_IMG_BASE}${first.poster_path}` : null;
      posterCache.set(fullTitle, url);
      return url;
    } catch {
      posterCache.set(fullTitle, null);
      return null;
    }
  }

  // ============================================================
  // 7. Language & i18n
  // ============================================================
  function updateLanguage() {
    document.documentElement.lang = state.language;
    document.documentElement.dir = state.language === "ar" ? "rtl" : "ltr";

    document.querySelectorAll("[data-i18n]").forEach((el) => {
      const key = el.dataset.i18n;
      if (t(key)) el.textContent = t(key);
    });
    document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
      const key = el.dataset.i18nPlaceholder;
      if (t(key)) el.placeholder = t(key);
    });

    const languageLabel = document.getElementById("language-label");
    if (languageLabel) languageLabel.textContent = state.language === "en" ? "العربية" : "English";

    document.title = state.language === "en" ? "CineMatch | Movie Recommendation System" : "CineMatch | نظام توصية الأفلام";
    localStorage.setItem("cineMatchLanguage", state.language);

    renderGenres();
    updateTasteChipsUI();
  }

  // ============================================================
  // 8. Modal & Onboarding
  // ============================================================
  function openModal() {
    dom.onboardingOverlay.hidden = false;
    showStep("mode");
  }
  function closeModal() {
    dom.onboardingOverlay.hidden = true;
  }
  function showStep(stepName) {
    state.onboardingStep = stepName;
    dom.stepMode.hidden = stepName !== "mode";
    dom.stepGenres.hidden = stepName !== "genres";
    dom.stepMovies.hidden = stepName !== "movies";
  }

  // ============================================================
  // 9. Navigation & View Routing
  // ============================================================
  function setView(viewName) {
    state.currentView = viewName;
    dom.navItems.forEach((item) => {
      if (item.classList.contains("nav-item")) {
        item.classList.toggle("active", item.dataset.view === viewName);
      }
    });

    const isHome = viewName === "home";
    const isForYou = viewName === "foryou";
    dom.heroSection.hidden = !isHome;
    dom.foryouSection.hidden = !(isHome || isForYou);
    dom.searchResultsSection.hidden = true;
  }

  // ============================================================
  // 10. Genre Selection
  // ============================================================
  function renderGenres() {
    dom.genreGrid.innerHTML = "";
    GENRES_LIST.forEach((genre) => {
      const clone = dom.genrePillTemplate.content.firstElementChild.cloneNode(true);
      clone.querySelector(".genre-pill-icon").textContent = genre.icon;
      clone.querySelector(".genre-pill-name").textContent = state.language === "ar" ? genre.name_ar : genre.name_en;
      if (state.selectedGenres.has(genre.key)) clone.classList.add("selected");

      clone.addEventListener("click", () => {
        if (state.selectedGenres.has(genre.key)) {
          state.selectedGenres.delete(genre.key);
          clone.classList.remove("selected");
        } else {
          state.selectedGenres.add(genre.key);
          clone.classList.add("selected");
        }
        updateGenreCounter();
      });
      dom.genreGrid.appendChild(clone);
    });
  }

  function updateGenreCounter() {
    const count = state.selectedGenres.size;
    dom.genresCounter.textContent = count;
    dom.genresConfirmBtn.disabled = count < 3;
  }

  // ============================================================
  // 11. Movie Selection (onboarding "pick movies" mode)
  // ============================================================
  function updateMovieCounter() {
    const count = state.selectedMovies.length;
    dom.moviesCounter.textContent = count;
    dom.moviesConfirmBtn.disabled = count < 3;
  }

  function renderPickedMovies() {
    dom.pickedMovies.innerHTML = "";
    state.selectedMovies.forEach((movie, index) => {
      const chip = document.createElement("div");
      chip.className = "picked-chip";
      chip.innerHTML = `<span>${movie.title}</span><button type="button" aria-label="Remove">&times;</button>`;
      chip.querySelector("button").addEventListener("click", () => {
        state.selectedMovies.splice(index, 1);
        renderPickedMovies();
        updateMovieCounter();
      });
      dom.pickedMovies.appendChild(chip);
    });
  }

  let onboardingSearchToken = 0;

  async function handleModalMovieSearch(query) {
    if (query.trim().length < 2) {
      dom.onboardingSearchResults.innerHTML = "";
      return;
    }
    const token = ++onboardingSearchToken; // avoid race conditions between fast keystrokes
    try {
      const results = await searchMovies(query, 6);
      if (token !== onboardingSearchToken) return; // a newer search already started
      renderModalSearchResults(results);
    } catch (err) {
      if (token !== onboardingSearchToken) return;
      dom.onboardingSearchResults.innerHTML = `<p class="empty-hint">${t("apiError")}</p>`;
    }
  }

  function renderModalSearchResults(movies) {
    dom.onboardingSearchResults.innerHTML = "";
    if (!movies.length) {
      dom.onboardingSearchResults.innerHTML = `<p class="empty-hint">${t("noResults")}</p>`;
      return;
    }
    movies.forEach((movie) => {
      const isSelected = state.selectedMovies.some((m) => m.movieId === movie.movieId);
      const row = document.createElement("div");
      row.className = "onboarding-result-row";
      row.innerHTML = `
        <div><strong>${movie.title}</strong></div>
        <button type="button" ${isSelected ? "disabled" : ""}>${isSelected ? "✓" : "+"}</button>
      `;
      if (!isSelected) {
        row.querySelector("button").addEventListener("click", () => {
          state.selectedMovies.push(movie);
          renderPickedMovies();
          updateMovieCounter();
          renderModalSearchResults(movies);
        });
      }
      dom.onboardingSearchResults.appendChild(row);
    });
  }

  // ============================================================
  // 12. Movie Cards & Rows
  //     Our API returns { movieId, title, genres? } — no poster/rating,
  //     so posters come from TMDB (async) and rating is hidden for now.
  // ============================================================
  function renderMovieCard(movie, container) {
    const card = dom.posterCardTemplate.content.firstElementChild.cloneNode(true);
    const img = card.querySelector(".poster-img");
    const fallback = card.querySelector(".poster-fallback");
    const starsContainer = card.querySelector(".poster-rate-stars");

    card.querySelector(".poster-title").textContent = movie.title;
    card.querySelector(".poster-meta").textContent = movie.genres ? movie.genres.replaceAll("|", " · ") : "";

    img.hidden = true;
    fallback.hidden = false;
    fallback.textContent = t("loading");

    getPosterUrl(movie.title).then((url) => {
      if (url) {
        img.src = url;
        img.alt = movie.title;
        img.hidden = false;
        fallback.hidden = true;
        img.onerror = () => { img.hidden = true; fallback.hidden = false; fallback.textContent = t("noImage"); };
      } else {
        fallback.textContent = t("noImage");
      }
    });

    if (movie.movieId != null) {
      const existingRating = state.userRatings[movie.movieId] || 0;
      renderRatingStars(starsContainer, movie.movieId, existingRating);
    }

    card.addEventListener("click", () => fetchSimilarMovies(movie.title));
    container.appendChild(card);
  }

  function renderRatingStars(container, movieId, initialValue = 0) {
    container.innerHTML = "";
    container.dataset.selectedValue = initialValue;
    for (let i = 1; i <= 5; i++) {
      const star = document.createElement("button");
      star.type = "button";
      star.className = "rate-star";
      star.textContent = "★";
      star.dataset.value = i;

      star.addEventListener("mouseenter", () => highlightStars(container, i));
      star.addEventListener("mouseleave", () => {
        const savedValue = container.dataset.selectedValue || 0;
        highlightStars(container, Number(savedValue));
      });

      star.addEventListener("click", async (e) => {
        e.stopPropagation();
        container.dataset.selectedValue = i;
        state.userRatings[movieId] = i;
        highlightStars(container, i);
        try {
          await submitRating(movieId, i);
        } catch (err) {
          console.error("Failed to submit rating", err);
        }
      });

      container.appendChild(star);
    }

    highlightStars(container, initialValue); 
  }

  state.userRatings = {}; 

  async function loadUserRatings() {
    const userToken = localStorage.getItem(USER_TOKEN_KEY);
    if (!userToken) return; 

    try {
      state.userRatings = await apiGet(`/ratings/${userToken}`);
    } catch (err) {
      console.error("Failed to load user ratings", err);
    }
  }

  function highlightStars(container, value) {
    container.querySelectorAll(".rate-star").forEach((star) => {
      star.classList.toggle("active", Number(star.dataset.value) <= value);
    });
  }

  function renderRow(container, movies) {
    container.innerHTML = "";
    if (!movies.length) {
      container.innerHTML = `<p class="empty-hint">${t("noResults")}</p>`;
      return;
    }
    movies.forEach((m) => renderMovieCard(m, container));
  }

  async function fetchSimilarMovies(movieTitle) {
    dom.similarMovieName.textContent = movieTitle;
    dom.similarResults.innerHTML = `<p>${t("loading")}</p>`;
    dom.similarSection.hidden = false;
    dom.similarSection.scrollIntoView({ behavior: "smooth" });

    try {
      // /recommendations/content/{title} returns an array of title strings
      const titles = await getContentRecommendations(movieTitle);
      renderRow(dom.similarResults, titles.map((title) => ({ title })));
    } catch (err) {
      dom.similarResults.innerHTML = `<p class="empty-hint">${t("apiError")}</p>`;
    }
  }

  // ============================================================
  // 13. Primary Search
  // ============================================================
  async function executeMainSearch(query) {
    if (!query.trim()) return;
    dom.searchResultsSection.hidden = false;
    dom.searchResults.innerHTML = `<p>${t("loading")}</p>`;
    dom.searchResultsSection.scrollIntoView({ behavior: "smooth" });

    try {
      const results = await searchMovies(query, 12);
      renderRow(dom.searchResults, results);
    } catch (err) {
      dom.searchResults.innerHTML = `<p class="empty-hint">${t("apiError")}</p>`;
    }
  }

  // ============================================================
  // 14. Taste Profile & Personalized Recommendations
  // ============================================================
  function updateTasteChipsUI() {
    dom.tasteChips.innerHTML = "";
    state.userTasteConfigured = state.selectedGenres.size > 0 || state.selectedMovies.length > 0;

    if (!state.userTasteConfigured) {
      const chip = document.createElement("span");
      chip.className = "chip muted";
      chip.textContent = t("noGenres");
      dom.tasteChips.appendChild(chip);
      dom.activeUserLabel.textContent = t("newViewer");
      return;
    }

    dom.activeUserLabel.textContent = t("viewer");

    if (state.selectedGenres.size > 0) {
      state.selectedGenres.forEach((key) => {
        const g = GENRES_LIST.find((item) => item.key === key);
        if (!g) return;
        const chip = document.createElement("span");
        chip.className = "chip";
        chip.textContent = state.language === "ar" ? g.name_ar : g.name_en;
        dom.tasteChips.appendChild(chip);
      });
    } else if (state.selectedMovies.length > 0) {
      const chip = document.createElement("span");
      chip.className = "chip";
      chip.textContent =
        state.language === "ar" ? `${state.selectedMovies.length} أفلام` : `${state.selectedMovies.length} movies`;
      dom.tasteChips.appendChild(chip);
    }

    loadPersonalizedRecommendations();
  }

  async function loadPersonalizedRecommendations() {
    dom.foryouResults.innerHTML = `<p>${t("loading")}</p>`;
    try {
      const userToken = localStorage.getItem(USER_TOKEN_KEY);
      let movies;
      if (state.selectedMovies.length > 0) {
        movies = await getOnboardingRecommendationsByMovies(state.selectedMovies.map((m) => m.title), userToken);
      } else {
        movies = await getOnboardingRecommendationsByGenres([...state.selectedGenres], userToken);
      }
      renderRow(dom.foryouResults, movies); 
    } catch (err) {
      dom.foryouResults.innerHTML = `<p class="empty-hint">${t("apiError")}</p>`;
    }
  }

  // ============================================================
  // 15. Event Binding & Init
  // ============================================================
  function bindEvents() {
    [dom.heroCtaBtn, dom.editTasteBtn, dom.switchUserBtn].forEach((btn) => {
      if (btn) btn.addEventListener("click", openModal);
    });

    dom.modalCloseBtn.addEventListener("click", closeModal);
    dom.onboardingOverlay.addEventListener("click", (e) => {
      if (e.target === dom.onboardingOverlay) closeModal();
    });

    dom.modeGenresBtn.addEventListener("click", () => {
      showStep("genres");
      renderGenres();
      updateGenreCounter();
    });
    dom.modeMoviesBtn.addEventListener("click", () => {
      showStep("movies");
      renderPickedMovies();
      updateMovieCounter();
    });

    dom.genresBackBtn.addEventListener("click", () => showStep("mode"));
    dom.moviesBackBtn.addEventListener("click", () => showStep("mode"));

    dom.genresConfirmBtn.addEventListener("click", () => {
      if (state.selectedGenres.size >= 3) {
        state.selectedMovies = []; // genres and movies are mutually exclusive modes
        saveTasteToStorage();
        updateTasteChipsUI();
        closeModal();
      }
    });
    dom.moviesConfirmBtn.addEventListener("click", () => {
      if (state.selectedMovies.length >= 3) {
        state.selectedGenres.clear();
        saveTasteToStorage();
        updateTasteChipsUI();
        closeModal();
      }
    });

    dom.onboardingMovieSearch.addEventListener("input", (e) => handleModalMovieSearch(e.target.value));

    dom.langSwitcher.addEventListener("click", () => {
      state.language = state.language === "en" ? "ar" : "en";
      updateLanguage();
    });

    dom.searchForm.addEventListener("submit", (e) => {
      e.preventDefault();
      executeMainSearch(dom.searchBox.value);
    });

    dom.navItems.forEach((item) => {
      item.addEventListener("click", (e) => {
        e.preventDefault();
        if (item.dataset.view) setView(item.dataset.view);
      });
    });
  }

  // ============================================================
  // 16. Persisting taste across visits (localStorage)
  // ============================================================
  const TASTE_STORAGE_KEY = "cineMatchTaste";
  const USER_TOKEN_KEY = "cineMatchUserToken";

  function saveTasteToStorage() {
    const data = {
      mode: state.selectedGenres.size > 0 ? "genres" : "movies",
      genres: [...state.selectedGenres],
      movieTitles: state.selectedMovies.map((m) => m.title),
    };
    localStorage.setItem(TASTE_STORAGE_KEY, JSON.stringify(data));
  }

async function getUserToken() {
  let token = localStorage.getItem(USER_TOKEN_KEY);

  if (token && token !== "undefined" && token !== "null") {
    return token;
  }

  const response = await fetch(`${API_BASE}/users/new`, { method: "POST" });
  if (!response.ok) {
    throw new Error("Failed to create user token");
  }
  const data = await response.json();
  token = data.userToken;
  localStorage.setItem(USER_TOKEN_KEY, token);
  return token;
}

  async function submitRating(movieId, rating) {
    const userToken = await getUserToken();

    await fetch(`${API_BASE}/ratings`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ userToken, movieId, rating }),
    });
  }

  function loadTasteFromStorage() {
    const raw = localStorage.getItem(TASTE_STORAGE_KEY);
    if (!raw) return false;

    let data;
    try {
      data = JSON.parse(raw);
    } catch {
      return false; // corrupted/old data — treat as no saved taste
    }

    if (data.mode === "genres" && Array.isArray(data.genres) && data.genres.length >= 3) {
      state.selectedGenres = new Set(data.genres);
      return true;
    }

    if (data.mode === "movies" && Array.isArray(data.movieTitles) && data.movieTitles.length >= 3) {
      // We only ever stored titles (that's all /recommendations/onboarding/movies
      // needs) — movieId is intentionally absent here, see section 11's note.
      state.selectedMovies = data.movieTitles.map((title) => ({ title }));
      return true;
    }

    return false;
  }
  document.addEventListener("DOMContentLoaded", async () => {
    bindEvents();
    loadTasteFromStorage();
    await loadUserRatings();
    updateLanguage();
  });