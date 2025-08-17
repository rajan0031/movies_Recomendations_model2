import streamlit as st
import joblib
import pickle
import requests
import pandas as pd
import time


# Load external CSS
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

local_css("styles.css")


API_KEY = "87601b271228bd36a20a891f397e06ef"

#  ✅ Cache posters so we don’t re-download
@st.cache_data(show_spinner=False)
def fetch_poster(movie_id: int, retries: int = 3, delay: int = 5):
    """Fetch poster for given TMDB movie_id with retries + caching"""
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US"

    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=12)
            response.raise_for_status()
            data = response.json()

            poster_path = data.get("poster_path")
            if poster_path:
                return "https://image.tmdb.org/t/p/w500" + poster_path
            else:
                return "https://via.placeholder.com/500x750?text=Poster+Not+Available"

        except requests.exceptions.RequestException as e:
            print(f"⚠️ Attempt {attempt+1} failed for {movie_id}: {e}")
            if attempt < retries - 1:
                time.sleep(delay)  # wait before retry
            else:
                return "https://via.placeholder.com/500x750?text=Poster+Not+Available"


#  ✅ Recommend similar movies
def recommend(movie):
    movie_index = movies_list[movies_list["title"] == movie].index[0]
    distances = similarity[movie_index]
    movies = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

    recommend_movies = []
    recommend_posters = []
    for i in movies:
        movie_id = int(movies_list.iloc[i[0]].movie_id)
        recommend_movies.append(movies_list.iloc[i[0]].title)
        recommend_posters.append(movie_id)  # store id, fetch lazily later

    return recommend_movies, recommend_posters


# ✅ Load movie data + similarity matrix
movies_list = pickle.load(open("movies.pkl", "rb"))
similarity = joblib.load("similarity.pkl")

st.title("🎬 Movie Recommender System")

selected_movie_name = st.selectbox(
    "Choose a movie you like", movies_list["title"].values
)

if st.button("Suggest"):
    recommendations, poster_ids = recommend(selected_movie_name)

    st.info("⏳Model thinking....... (about 1 min).")

    posters = []
    with st.spinner("Fetching movie ..."):
        for movie_id in poster_ids:
            poster_url = fetch_poster(movie_id)  # retry-enabled
            posters.append(poster_url)
            time.sleep(12)  # ⏰ wait 12 sec before next API call (avoid TMDB block)

    st.success("✅ Movies loaded successfully!")

    # ✅ Show results in 5 columns after all are fetched
    cols = st.columns(5)
    for idx, col in enumerate(cols):
        with col:
            st.text(recommendations[idx])
            st.image(posters[idx])
