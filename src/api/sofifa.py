import requests


def get_league_info():
    try:
        url = "http://sofifa-api.herokuapp.com/api/v1/players/?name=Neymar"
        response = requests.get(url)
        print(response.text)
        return response.json()
        
    except Exception as e:
        print(f"Error fetching league info: {e}")
        return None