# 🍳 Cozy Kitchen – Recipe Explorer

A Streamlit web app that lets you browse recipes from around the world, see
ingredients in a clean table, read step-by-step instructions, and watch a
video tutorial for each dish.

## Features

- **No API keys** – uses the free public [TheMealDB](https://www.themealdb.com/api.php) API
- Search by dish name, browse by category or cuisine, or hit **Surprise me**
- Metric cards (category, cuisine, ingredient count, tags)
- Ingredients table built with pandas
- Embedded YouTube video for each recipe (when available)
- Cute animated chef mascot (pure CSS)
- Expandable raw JSON viewer

## Project structure

```
.
├── app.py
├── requirements.txt
└── README.md
```

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud

1. Push these three files to a GitHub repository.
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Click **New app**, choose your repo and branch, and set the main file to `app.py`.
4. Click **Deploy**. No secrets or environment variables are needed.

## Notes

- Videos come from the YouTube links that TheMealDB provides for each recipe.
- TheMealDB's free tier uses the public test key `1` built into the URL, so
  you don't need to sign up for anything.

## Credits

Recipe data and images: [TheMealDB](https://www.themealdb.com/).
