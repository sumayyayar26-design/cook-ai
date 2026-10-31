"""
Cozy Kitchen - Recipe Explorer
A Streamlit app that browses recipes from TheMealDB (free, no API key).
"""

import pandas as pd
import requests
import streamlit as st

BASE_URL = "https://www.themealdb.com/api/json/v1/1"

st.set_page_config(page_title="Cozy Kitchen", page_icon="🍳", layout="wide")

# ----------------------------------------------------------------------------
# Styling + cute animated chef mascot (pure CSS, no external assets)
# ----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    .block-container {padding-top: 2rem;}
    .hero {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        border-radius: 18px; padding: 1.2rem 1.6rem; margin-bottom: 1.2rem;
        display: flex; align-items: center; gap: 1.2rem; color: #4a2c1a;
    }
    .hero h1 {margin: 0; font-size: 2rem;}
    .hero p {margin: 0.2rem 0 0 0;}
    .mascot {font-size: 3.4rem; display: inline-block;
             animation: bounce 1.6s ease-in-out infinite;}
    .steam {font-size: 1.4rem; animation: float 2.4s ease-in-out infinite;}
    @keyframes bounce {0%,100% {transform: translateY(0) rotate(-4deg);}
                       50% {transform: translateY(-12px) rotate(4deg);}}
    @keyframes float {0% {opacity: 0; transform: translateY(8px);}
                      50% {opacity: 1;}
                      100% {opacity: 0; transform: translateY(-14px);}}
    .cute-card {
        background: #fff7f0; border: 2px dashed #fcb69f; border-radius: 16px;
        padding: 1rem 1.2rem; text-align: center; color: #4a2c1a;
    }
    </style>
    <div class="hero">
        <div><span class="mascot">🧑‍🍳</span><span class="steam">♨️</span></div>
        <div>
            <h1>Cozy Kitchen</h1>
            <p>Discover dishes from around the world, step by step.</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ----------------------------------------------------------------------------
# API helpers
# ----------------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def api_get(endpoint: str, **params):
    """GET a TheMealDB endpoint and return parsed JSON (or None on failure)."""
    try:
        resp = requests.get(f"{BASE_URL}/{endpoint}", params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except (requests.RequestException, ValueError):
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def get_options(kind: str):
    """Return category ('c') or cuisine ('a') names."""
    data = api_get("list.php", **{kind: "list"})
    if not data or not data.get("meals"):
        return []
    key = "strCategory" if kind == "c" else "strArea"
    return sorted(m[key] for m in data["meals"])


def search_by_name(query: str):
    data = api_get("search.php", s=query)
    return (data or {}).get("meals") or []


def filter_meals(kind: str, value: str):
    data = api_get("filter.php", **{kind: value})
    return (data or {}).get("meals") or []


def lookup(meal_id: str):
    data = api_get("lookup.php", i=meal_id)
    meals = (data or {}).get("meals") or []
    return meals[0] if meals else None


def random_meal():
    # random.php must not be cached, otherwise it returns the same dish
    try:
        resp = requests.get(f"{BASE_URL}/random.php", timeout=10)
        resp.raise_for_status()
        meals = resp.json().get("meals") or []
        return meals[0] if meals else None
    except (requests.RequestException, ValueError):
        return None


def parse_ingredients(meal: dict) -> pd.DataFrame:
    rows = []
    for i in range(1, 21):
        name = (meal.get(f"strIngredient{i}") or "").strip()
        measure = (meal.get(f"strMeasure{i}") or "").strip()
        if name:
            rows.append({"Ingredient": name, "Measure": measure or "-"})
    return pd.DataFrame(rows)


def parse_steps(text: str):
    lines = [ln.strip() for ln in (text or "").replace("\r", "").split("\n")]
    steps = []
    for ln in lines:
        if not ln or ln.lower().startswith("step") and len(ln) < 10:
            continue
        steps.append(ln)
    return steps


# ----------------------------------------------------------------------------
# Sidebar: how to find a recipe
# ----------------------------------------------------------------------------
st.sidebar.header("🔎 Find a recipe")
mode = st.sidebar.radio(
    "Browse by",
    ["Search by name", "Category", "Cuisine", "Surprise me 🎲"],
)

if "random_meal" not in st.session_state:
    st.session_state.random_meal = None

candidates = []
selected_meal = None

if mode == "Search by name":
    query = st.sidebar.text_input("Dish name", value="Chicken").strip()
    if query:
        candidates = search_by_name(query)
elif mode == "Category":
    options = get_options("c")
    if options:
        choice = st.sidebar.selectbox("Category", options)
        candidates = filter_meals("c", choice)
    else:
        st.sidebar.error("Could not load categories.")
elif mode == "Cuisine":
    options = get_options("a")
    if options:
        choice = st.sidebar.selectbox("Cuisine", options)
        candidates = filter_meals("a", choice)
    else:
        st.sidebar.error("Could not load cuisines.")
else:
    if st.sidebar.button("Give me a random dish!", use_container_width=True) or (
        st.session_state.random_meal is None
    ):
        with st.spinner("Rolling the dice..."):
            st.session_state.random_meal = random_meal()
    selected_meal = st.session_state.random_meal

# Pick one dish from the candidate list
if mode != "Surprise me 🎲":
    if not candidates:
        st.info("No dishes found. Try another search or filter. 🥲")
        st.stop()

    names = {m["strMeal"]: m["idMeal"] for m in candidates}
    pick = st.sidebar.selectbox(f"Dishes found ({len(names)})", list(names.keys()))

    # Small thumbnail gallery of the first results
    with st.expander("📸 Browse thumbnails", expanded=False):
        cols = st.columns(4)
        for idx, m in enumerate(candidates[:8]):
            with cols[idx % 4]:
                thumb = m.get("strMealThumb")
                if thumb:
                    st.image(thumb + "/preview", caption=m["strMeal"])

    with st.spinner("Fetching recipe..."):
        selected_meal = lookup(names[pick])

if not selected_meal:
    st.error("Could not load the recipe right now. Please try again.")
    st.stop()

meal = selected_meal

# ----------------------------------------------------------------------------
# Recipe dashboard (2 columns)
# ----------------------------------------------------------------------------
st.subheader(meal["strMeal"])

ingredients_df = parse_ingredients(meal)
tags = [t.strip() for t in (meal.get("strTags") or "").split(",") if t.strip()]

m1, m2, m3, m4 = st.columns(4)
m1.metric("Category", meal.get("strCategory") or "-")
m2.metric("Cuisine", meal.get("strArea") or "-")
m3.metric("Ingredients", len(ingredients_df))
m4.metric("Tags", len(tags))

left, right = st.columns([1, 1.2], gap="large")

with left:
    if meal.get("strMealThumb"):
        st.image(meal["strMealThumb"], use_container_width=True)
    if tags:
        st.caption("Tags: " + " · ".join(f"`{t}`" for t in tags))

    st.markdown("#### 🛒 Ingredients")
    st.dataframe(ingredients_df, use_container_width=True, hide_index=True)

with right:
    st.markdown("#### 🎬 Watch & cook along")
    video_url = (meal.get("strYoutube") or "").strip()
    if video_url:
        st.video(video_url)
    else:
        search_url = (
            "https://www.youtube.com/results?search_query="
            + requests.utils.quote(f"{meal['strMeal']} recipe")
        )
        st.markdown(
            f"""
            <div class="cute-card">
                <div class="mascot">🍲</div>
                <p>No video for this dish yet!</p>
                <a href="{search_url}" target="_blank">Search YouTube for it ✨</a>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("#### 👩‍🍳 Instructions")
    for n, step in enumerate(parse_steps(meal.get("strInstructions")), start=1):
        st.markdown(f"**{n}.** {step}")

    if meal.get("strSource"):
        st.markdown(f"[Original source ↗]({meal['strSource']})")

with st.expander("🧾 Raw data viewer"):
    st.json(meal)

st.caption("Data from TheMealDB · Built with Streamlit")
