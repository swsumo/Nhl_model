import streamlit as st
import pandas as pd
import numpy as np
import pickle
import requests

def load_model(model_path):
    """Load the trained model from a pickle file."""
    with open(model_path, 'rb') as f:
        return pickle.load(f)

# Load the trained model
model = load_model('best_rf_model.pkl')
trained_features = model.feature_names_in_

# Preprocess live scores to match the trained model's features
def preprocess_live_scores(live_scores, trained_features):
    """Preprocess live game data to match the trained model's feature set."""
    if live_scores.empty:
        return pd.DataFrame(columns=trained_features)

    # Fill missing values and preprocess columns
    live_scores.fillna(0, inplace=True)

    # Ensure the columns align with trained model features
    for col in trained_features:
        if col not in live_scores.columns:
            live_scores[col] = 0

    # Reorder columns to match the trained feature set
    return live_scores[trained_features]

# Fetch live scores from the NHL API
def fetch_live_scores():
    url = "https://api-web.nhle.com/v1/score/now"
    try:
        response = requests.get(url)
        response.raise_for_status()
        live_scores = response.json()

        # Extract and process game data
        live_game_data = []
        for game in live_scores.get('games', []):
            home_team = game['homeTeam']['abbrev']
            away_team = game['awayTeam']['abbrev']
            home_score = game['homeTeam'].get('score', 0)
            away_score = game['awayTeam'].get('score', 0)
            live_game_data.append({
                'Home_Team': home_team,
                'Away_Team': away_team,
                'Home_Score': home_score,
                'Away_Score': away_score,
            })
        return pd.DataFrame(live_game_data)
    except requests.exceptions.RequestException:
        return pd.DataFrame()

# Streamlit app
def main():
    st.set_page_config(page_title="NHL Predictions", layout="wide")

    st.title("Live Prediction")

    if st.button("Fetch Live Scores"):
        live_scores = fetch_live_scores()
        if live_scores.empty:
            st.warning("No live games available.")
        else:
            st.write("Live Scores:", live_scores)

            # Preprocess and predict
            processed_scores = preprocess_live_scores(live_scores, trained_features)
            predictions = model.predict(processed_scores)

            live_scores['Predicted Winner'] = [
                row['Home_Team'] if pred == 1 else row['Away_Team']
                for row, pred in zip(live_scores.to_dict('records'), predictions)
            ]
            st.write("Predictions:", live_scores[["Home_Team", "Away_Team", "Predicted Winner"]])

if __name__ == "__main__":
    main()
