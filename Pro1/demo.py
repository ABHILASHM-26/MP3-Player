from flask import Flask, render_template, request
import os
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

def get_access_token(client_id, client_secret):
    token_url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": f"Basic {client_id}:{client_secret}",
    }
    data = {
        "grant_type": "client_credentials"
    }
    response = requests.post(token_url, headers=headers, data=data)
    access_token = response.json().get("access_token")
    return access_token

def get_artist_songs(access_token, artist_name):
    search_url = "https://api.spotify.com/v1/search"
    headers = {
        "Authorization": f"Bearer {access_token}",
    }
    params = {
        "q": artist_name,
        "type": "artist",
        "limit": 1
    }
    response = requests.get(search_url, headers=headers, params=params)
    artist_data = response.json().get("artists", {}).get("items", [])
    if artist_data:
        artist_id = artist_data[0].get("id")
        artist_albums_url = f"https://api.spotify.com/v1/artists/{artist_id}/albums"
        response = requests.get(artist_albums_url, headers=headers)
        albums_data = response.json().get("items", [])
        songs = []
        for album in albums_data:
            album_id = album.get("id")
            album_tracks_url = f"https://api.spotify.com/v1/albums/{album_id}/tracks"
            response = requests.get(album_tracks_url, headers=headers)
            tracks_data = response.json().get("items", [])
            for track in tracks_data:
                song_details = {
                    "name": track.get("name"),
                    "artist": artist_name,
                    "photo_url": track.get("album", {}).get("images", [])[0].get("url"),
                    "song_url": track.get("preview_url")
                }
                songs.append(song_details)
        return songs
    else:
        return []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/artists', methods=['POST'])
def artist():
    artist_name = request.form.get('artist_name')
    access_token = get_access_token(CLIENT_ID, CLIENT_SECRET)
    songs = get_artist_songs(access_token, artist_name)
    return render_template('artists.html', artist=artist_name, songs=songs)

if __name__ == '__main__':
    app.run(debug=True)
