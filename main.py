import pandas as pd
import numpy as np
import pickle
import requests

# Load the trained model
def load_model(model_path):
    """Load the trained model from a pickle file."""
    try:
        with open(model_path, 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        print(f"Model file not found: {model_path}")
        return None

# Fetch live scores from the NHL API
def fetch_live_scores():
    """Fetch live game data from the NHL API."""
    url = "https://api-web.nhle.com/v1/score/now"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for non-200 responses
        live_scores = response.json()

        # Extract and process game data
        live_game_data = []
        for game in live_scores.get('games', []):
            home_team = game['homeTeam']['abbrev']
            away_team = game['awayTeam']['abbrev']
            home_score = game['homeTeam'].get('score', 0)
            away_score = game['awayTeam'].get('score', 0)
            period = game.get('currentPeriod', 0)
            live_game_data.append({
                'Home_Team': home_team,
                'Away_Team': away_team,
                'Home_Score': home_score,
                'Away_Score': away_score,
                'Goals_Diff': home_score - away_score,
                'Period': period
            })
        return pd.DataFrame(live_game_data)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching live scores: {e}")
        return pd.DataFrame()

# Preprocess live scores to match the trained model's features
def preprocess_live_scores(live_scores, trained_features):
    """Preprocess live game data to match the trained model's feature set."""
    if live_scores.empty:
        print("No live game data available.")
        return pd.DataFrame(columns=trained_features)

    # Ensure required columns are present
    live_scores = live_scores.copy()
    live_scores['Home'] = live_scores['Home_Team'].apply(lambda x: 1 if x == 'H' else 0)

    # Fill missing values with 0
    live_scores.fillna(0, inplace=True)

    # Process 'Overall' column if it exists
    if 'Overall' in live_scores.columns:
        try:
            live_scores[['Wins', 'Losses', 'Ties']] = live_scores['Overall'].str.split('-', expand=True).astype(float, errors='ignore')
            live_scores['WL'] = (live_scores['Wins'] > live_scores['Losses']).astype(int)
        except Exception as e:
            print(f"Error splitting 'Overall' column. Ensure data format is correct. {e}")
            live_scores[['Wins', 'Losses', 'Ties']] = 0, 0, 0  # Fallback

    # List of categorical columns to encode
    categorical_columns = ['EAS', 'WES', 'ATL', 'MET', 'CEN', 'PAC', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'Apr']

    # Only apply get_dummies to existing columns
    existing_categorical_columns = [col for col in categorical_columns if col in live_scores.columns]
    if existing_categorical_columns:
        live_scores = pd.get_dummies(live_scores, columns=existing_categorical_columns, drop_first=True)

    # Convert boolean-like columns to numeric (Yes=1, No=0)
    boolean_columns = ['Home', 'Road', 'Shootout', 'Overtime']
    for col in boolean_columns:
        if col in live_scores.columns:
            live_scores[col] = live_scores[col].map({'Yes': 1, 'No': 0})

    # Drop 'Overall' column if exists
    live_scores.drop(columns=['Overall'], errors='ignore', inplace=True)

    # Handle team columns dynamically: Only encode columns that exist
    team_columns = ['ANA', 'ARI', 'BOS', 'BUF', 'CAR', 'CBJ', 'CGY', 'CHI', 'COL', 'DAL', 'DET', 'EDM', 'FLA', 'LAK', 'MIN', 
                    'MTL', 'NJD', 'NSH', 'NYI', 'NYR', 'OTT', 'PHI', 'PIT', 'SEA', 'SJS', 'STL', 'TBL', 'TOR', 'VAN', 'VEG', 'WPG', 'WSH']
    
    # Only apply get_dummies to columns that exist in live_scores
    existing_team_columns = [col for col in team_columns if col in live_scores.columns]
    if existing_team_columns:
        live_scores = pd.get_dummies(live_scores, columns=existing_team_columns, drop_first=True)

    # Ensure the columns align with trained model features
    for col in trained_features:
        if col not in live_scores.columns:
            live_scores[col] = 0  # Fill missing columns with default values

    # Reorder columns to match the trained feature set
    live_scores = live_scores[trained_features]

    return live_scores

# Predict outcomes for live scores
def predict_outcomes(model, live_scores, trained_features):
    if live_scores.empty:
        print("No data available for predictions.")
        return pd.DataFrame()

    processed_scores = preprocess_live_scores(live_scores, trained_features)
    predictions = model.predict(processed_scores)

    # Map predicted outcome to the winning team
    live_scores['Predicted Outcome'] = live_scores.apply(
        lambda row: row['Home_Team'] if predictions[row.name] == 1 else row['Away_Team'],
        axis=1
    )

    return live_scores[['Home_Team', 'Away_Team', 'Predicted Outcome']]


# Main execution flow
if __name__ == "__main__":
    # Load the model
    best_rf_model = load_model('best_rf_model.pkl')
    if best_rf_model is None:
        exit(1)  # Exit if model loading fails

    # Fetch live scores from the NHL API
    live_scores = fetch_live_scores()
    
    if live_scores.empty:
        print("No live games to process.")
    else:
        # Get trained feature names from the model
        trained_features = best_rf_model.feature_names_in_

        # Predict outcomes
        prediction_results = predict_outcomes(best_rf_model, live_scores, trained_features)

        # Print prediction results
        if not prediction_results.empty:
            print(prediction_results)
        else:
            print("No predictions made.")
