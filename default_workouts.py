import requests

API_KEY = "LqCW9GJjn3K6qvSN0epbuAGvCK1HwfqdmZUJ5TQE"
BASE_URL = "https://api.api-ninjas.com/v1/exercises"

HEADERS = {
    "X-Api-Key": API_KEY
}

MUSCLE_QUERIES = {
    "Biceps": "biceps",
    "Triceps": "triceps",
    "Chest": "chest",
    "Back": "back",
    "Shoulders": "shoulders",
    "Quads": "quadriceps",
    "Hamstrings": "hamstrings",
    "Glutes": "glutes",
    "Calves": "calves",
    "Core": "abdominals"
}

MAX_EXERCISES = 150
API_LIMIT = 50  


def get_default_workouts():
    workouts = []

    for display_muscle, api_muscle in MUSCLE_QUERIES.items():
        response = requests.get(
            BASE_URL,
            headers=HEADERS,
            params={
                "muscle": api_muscle,
                "limit": API_LIMIT
            }
        )

        # handling error from api (had this error a lot)
        if response.status_code != 200:
            print(f"API error for muscle '{api_muscle}':")
            print(response.status_code, response.text)
            response.raise_for_status()

        data = response.json()

        for exercise in data:
            name = exercise.get("name")
            if name:
                workouts.append((name.title(), display_muscle))

            if len(workouts) >= MAX_EXERCISES:
                break

        if len(workouts) >= MAX_EXERCISES:
            break

    # Remove duplicates keeping order the same
    return list(dict.fromkeys(workouts))
