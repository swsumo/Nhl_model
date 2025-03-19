from flask import Flask, request, jsonify
import pandas as pd
import pickle
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow requests from frontend

# Load the trained model
def load_model(model_path):
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
        print(f"Model loaded. Features expected: {model.feature_names_in_}")
        return model

try:
    model = load_model('best_rf_model.pkl')
    trained_features = model.feature_names_in_
except Exception as e:
    print(f"Error loading model: {e}")
    # Placeholder for when model can't be loaded initially
    model = None
    trained_features = []

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
            
            # Calculate additional features
            score_diff = home_score - away_score
            
            live_game_data.append({
                'Home_Team': home_team,
                'Away_Team': away_team,
                'Home_Score': home_score,
                'Away_Score': away_score,
                'Score_Diff': score_diff,
                'Game_State': game.get('gameState', ''),
                'Period': game.get('period', '')
            })
        return pd.DataFrame(live_game_data)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching live scores: {e}")
        return pd.DataFrame()

# Preprocess live scores to match model features
def preprocess_live_scores(live_scores):
    if live_scores.empty:
        return pd.DataFrame(columns=trained_features)

    # Create feature dataframe
    processed_data = pd.DataFrame()
    
    # Basic features
    processed_data['Score_Diff'] = live_scores['Home_Score'] - live_scores['Away_Score']
    
    # Team one-hot encoding
    all_teams = set()
    for team in set(live_scores['Home_Team'].tolist() + live_scores['Away_Team'].tolist()):
        all_teams.add(team)
        processed_data[f'Home_{team}'] = (live_scores['Home_Team'] == team).astype(int)
        processed_data[f'Away_{team}'] = (live_scores['Away_Team'] == team).astype(int)
    
    # Create all expected features
    model_features = pd.DataFrame(0, index=processed_data.index, columns=trained_features)
    
    # Fill in available features
    for col in processed_data.columns:
        if col in model_features.columns:
            model_features[col] = processed_data[col]
    
    return model_features

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    try:
        # Reload model if not loaded
        global model, trained_features
        if model is None:
            model = load_model('best_rf_model.pkl')
            trained_features = model.feature_names_in_
            
        # Fetch live scores
        live_scores = fetch_live_scores()

        if live_scores.empty:
            return jsonify({"error": "No live games available"}), 404

        # Preprocess data
        processed_scores = preprocess_live_scores(live_scores)
        
        # Make predictions
        predictions = model.predict(processed_scores)
        
        # Format response
        result = []
        for i, row in enumerate(live_scores.to_dict('records')):
            result.append({
                'homeTeam': row['Home_Team'],
                'awayTeam': row['Away_Team'],
                'homeScore': row['Home_Score'],
                'awayScore': row['Away_Score'],
                'gameState': row.get('Game_State', ''),
                'period': row.get('Period', ''),
                'predictedWinner': row['Home_Team'] if predictions[i] == 1 else row['Away_Team']
            })
            
        return jsonify({"games": result})
        
    except Exception as e:
        print(f"Error in prediction: {str(e)}")
        return jsonify({"error": f"Prediction error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
