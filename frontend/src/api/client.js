import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' },
});

export const predictMatch = (homeTeam, awayTeam, neutral = true) =>
  api.post('/predict', { home_team: homeTeam, away_team: awayTeam, neutral });

export const submitUserPrediction = (username, matchId, predictedOutcome) =>
  api.post('/user/predict', { username, match_id: matchId, predicted_outcome: predictedOutcome });

export const getLeaderboard = () => api.get('/leaderboard');

export default api;
