import os
import base64
import json
from flask import Flask, render_template, request, redirect, url_for
from requests import post, get
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

def getToken():
    authString = client_id + ":" + client_secret
    authBytes = authString.encode("utf-8")
    authBase64 = str(base64.b64encode(authBytes), "utf-8")

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + authBase64,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    result = post(url, headers=headers, data=data)
    
    if result.status_code != 200:
        print(f"Error fetching token: {result.status_code} - {result.text}")
        return None

    json_result = result.json()
    token = json_result["access_token"]
    return token

def getAuthHeader(token):
    return {"Authorization": "Bearer " + token}

def searchArtist(token, artist_name):
    url = "https://api.spotify.com/v1/search"
    headers = getAuthHeader(token)
    params = {
        "q": artist_name,
        "type": "artist",
        "limit": 1
    }
    response = get(url, headers=headers, params=params)
    
    if response.status_code != 200:
        print(f"Error searching for artist: {response.status_code} - {response.text}")
        return None
    
    data = response.json()
    artists = data.get('artists', {}).get('items', [])
    if not artists:
        return None
    return artists[0]['id']

def getAlbums(token, artist_id):
    url = f"https://api.spotify.com/v1/artists/{artist_id}/albums?include_groups=album,single&limit=50"
    headers = getAuthHeader(token)
    result = get(url, headers=headers)
    
    print(f"Response status: {result.status_code}")
    print(f"Response content: {result.content}")

    if result.status_code != 200:
        print(f"Error fetching albums: {result.status_code} - {result.text}")
        return []

    try:
        json_result = result.json()
        return json_result.get("items", [])
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e} - {result.content}")
        return []

def getTracks(token, album_id):
    url = f"https://api.spotify.com/v1/albums/{album_id}/tracks"
    headers = getAuthHeader(token)
    result = get(url, headers=headers)
    
    if result.status_code != 200:
        print(f"Error fetching tracks: {result.status_code} - {result.text}")
        return []

    try:
        json_result = result.json()
        return json_result.get("items", [])
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e} - {result.content}")
        return []

def getPhoto(token, track_id):
    url = f"https://api.spotify.com/v1/tracks/{track_id}"
    headers = getAuthHeader(token)
    result = get(url, headers=headers)
    
    if result.status_code != 200:
        print(f"Error fetching photo: {result.status_code} - {result.text}")
        return None

    try:
        json_result = result.json()
        if "album" in json_result and "images" in json_result["album"]:
            images = json_result["album"]["images"]
            if images:
                return images[0]["url"]
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e} - {result.content}")
        return None
    
def getSongUrl(token, track_id):
    url = f"https://api.spotify.com/v1/tracks/{track_id}"
    headers = getAuthHeader(token)
    result = get(url, headers=headers)
    json_result = json.loads(result.content)
    if "preview_url" in json_result and json_result["preview_url"]:
        return json_result["preview_url"]
    else:
        return None

def getSpotifyLink(track_id):
    return f"https://open.spotify.com/track/{track_id}"

def getSongs(token, artist_id):
    albums = getAlbums(token, artist_id)
    songs_with_photo = []
    for album in albums:
        tracks = getTracks(token, album["id"])
        for i, track in enumerate(tracks):
            if len(songs_with_photo) >= 40:  # Stop if we've collected enough tracks
                break
            if i > 0:  # Take at most 2 tracks from each album
                break
            song_details = {
                "id": track["id"],
                "name": track["name"],
                "artist": track["artists"][0]["name"],
                "photo_url": getPhoto(token, track["id"]),
                "song_url": getSpotifyLink(track["id"])  # Use Spotify link instead of preview URL
            }
            songs_with_photo.append(song_details)
        if len(songs_with_photo) >= 40:  # Stop if we've collected enough tracks
            break
    return songs_with_photo

@app.route('/home.html')
def index():
    token = getToken()
    if not token:
        return "Error fetching token", 500
    
    artist_name = "anirudh"
    artist_id = searchArtist(token, artist_name)
    if not artist_id:
        return "Artist not found", 404

    songs = getSongs(token, artist_id)
    for song in songs:
        song['photo_url'] = getPhoto(token, song['id'])
        song['song_url'] = getSpotifyLink(song['id'])
    
    return render_template('home.html', songs=songs)

@app.route('/search', methods=['POST'])
def search():
    artist_name = request.form['artist']
    token = getToken()
    result = searchArtist(token,artist_name)
    if result:
        artist_id = result["id"]
        songs = getSongs(token, artist_id)
        for song in songs:
            song['photo_url'] = getPhoto(token, song['id'])
            song['song_url'] = getSongUrl(token,song['id'])
    else:
        songs = None  # Handle the case where no artist is found
    return render_template('home.html', songs=songs)

@app.route('/artist')
def artists():
    return render_template('artist.html')

@app.route('/artist/<artist_name>')
def artist_songs(artist_name):
    token = getToken()
    if not token:
        return "Error fetching token", 500

    artist_id = searchArtist(token, artist_name)
    if not artist_id:
        return "Artist not found", 404

    songs = getSongs(token, artist_id)
    for song in songs:
        song['photo_url'] = getPhoto(token, song['id'])
        song['song_url'] = getSpotifyLink(song['id'])
    
    return render_template('song.html', songs=songs)

if __name__ == '__main__':
    app.run(debug=True)
