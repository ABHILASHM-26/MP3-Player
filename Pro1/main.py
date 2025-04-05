from dotenv import load_dotenv
import os
import base64
from requests import post, get
import json
from flask import Flask, render_template, request 

load_dotenv()

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
    json_result = json.loads(result.content)
    token = json_result["access_token"]
    return token

def getAuthHeader(token):
    return {"Authorization": "Bearer " + token}

def searchArtist(token, artistName):
    url = "https://api.spotify.com/v1/search"
    headers = getAuthHeader(token)
    query = f"?q={artistName}&type=artist&limit=1"

    queryurl = url + query
    result = get(queryurl, headers=headers)
    json_result = json.loads(result.content)["artists"]["items"]
    if len(json_result) == 0:
        print("No artist found")
        return None

    return json_result[0]

def getAlbums(token, artist_id):
    url = f"https://api.spotify.com/v1/artists/{artist_id}/albums?include_groups=album,single&limit=50"
    headers = getAuthHeader(token)
    result = get(url, headers=headers)
    json_result = json.loads(result.content)["items"]
    return json_result

def getTracks(token, album_id):
    url = f"https://api.spotify.com/v1/albums/{album_id}/tracks"
    headers = getAuthHeader(token)
    result = get(url, headers=headers)
    json_result = json.loads(result.content)["items"]
    return json_result

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
        if len(songs_with_photo) >= 80:  # Stop if we've collected enough tracks
            break
    return songs_with_photo

def getPhoto(token, track_id):
    url = f"https://api.spotify.com/v1/tracks/{track_id}"
    headers = getAuthHeader(token)
    result = get(url, headers=headers)
    json_result = json.loads(result.content)
    if "album" in json_result and "images" in json_result["album"]:
        images = json_result["album"]["images"]
        if images:
            return images[0]["url"]
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



def search_artist_id(token, artist_name):
    url = "https://api.spotify.com/v1/search"
    headers = getAuthHeader(token)
    params = {
        "q": artist_name,
        "type": "artist",
        "limit": 1
    }
    response = get(url, headers=headers, params=params)
    data = response.json()
    artists = data.get('artists', {}).get('items', [])
    if not artists:
        return None
    return artists[0]['id']

def getTrendingSongs(token, artist_id):
    url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks?country=US"
    headers = getAuthHeader(token)
    result = get(url, headers=headers)
    json_result = json.loads(result.content)["tracks"]
    
    trending_songs = []
    for track in json_result:
        song_details = {
            "id": track["id"],
            "name": track["name"],
            "artist": track["artists"][0]["name"],
            "photo_url": getPhoto(token, track["id"]),  # Assuming you have a function to get album art
            "song_url": getSongs(token,track["id"])    # Assuming you have a function to get Spotify link
        }
        trending_songs.append(song_details)
        
    return trending_songs



def getFeaturedPlaylists(token):
    url = "https://api.spotify.com/v1/browse/featured-playlists"
    headers = getAuthHeader(token)
    response = get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Error fetching featured playlists: {response.status_code} - {response.text}")
        return []
    
    data = response.json()
    playlists = data.get('playlists', {}).get('items', [])
    return playlists

def getPlaylistTracks(token, playlist_id):
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    headers = getAuthHeader(token)
    response = get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Error fetching playlist tracks: {response.status_code} - {response.text}")
        return []

    data = response.json()
    tracks = data.get('items', [])
    return [track['track'] for track in tracks if 'track' in track]

def getTrendingSongs(token):
    playlists = getFeaturedPlaylists(token)
    if not playlists:
        return []

    trending_songs = []
    for playlist in playlists:
        playlist_tracks = getPlaylistTracks(token, playlist['id'])
        for track in playlist_tracks:
            song_details = {
                "id": track["id"],
                "name": track["name"],
                "artist": ", ".join(artist["name"] for artist in track["artists"]),
                "photo_url": track["album"]["images"][0]["url"] if track["album"]["images"] else None,
                "song_url": getSongUrl(token,track["id"])
            }
            trending_songs.append(song_details)
            if len(trending_songs) >= 80:  # Adjust the number of songs as needed
                break
        if len(trending_songs) >= 80:
            break
    return trending_songs


def getSongsByGenre(token, genre):
    url = "https://api.spotify.com/v1/recommendations"
    headers = getAuthHeader(token)
    params = {
        "seed_genres": genre,
        "limit": 80
    }
    response = get(url, headers=headers, params=params)
    

    if response.status_code != 200:
        print(f"Error fetching songs for genre {genre}: {response.status_code} - {response.text}")
        return []
    
    data = response.json()
    tracks = data.get('tracks', [])
    
    if not tracks:
        print(f"No tracks found for genre {genre}")
        return []
    
    songs = []
    for track in tracks:
        song_details = {
            "id": track["id"],
            "name": track["name"],
            "artist": ", ".join(artist["name"] for artist in track["artists"]),
            "photo_url": track["album"]["images"][0]["url"] if track["album"]["images"] else None,
            "song_url": getSongUrl(token,track["id"])
        }
        songs.append(song_details)
    
    return songs




app = Flask(__name__,static_url_path='/static')
@app.route('/')
def index():
    token = getToken()
    if not token:
        return "Error fetching token", 500
    
    songs = getTrendingSongs(token)
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
    return render_template('songs.html', songs=songs)

@app.route('/artist/<artist_id>')
def artist(artist_id):
    token = getToken()
    songs = getTrendingSongs(token, artist_id)
    for song in songs:
        song['photo_url'] = getPhoto(token, song['id'])
        song['song_url'] = getSpotifyLink(song['id'])
    return render_template('home.html', songs=songs)

@app.route('/artist/<artist_name>')
def artist_songs(artist_name):
    token = getToken()
    artist_id = search_artist_id(token, artist_name)
    if not artist_id:
        return "Artist not found", 404

    songs = getSongs(token, artist_id)
    for song in songs:
        song['photo_url'] = getPhoto(token, song['id'])
        song['song_url'] = getSpotifyLink(song['id'])
    return render_template('song.html', songs=songs)



@app.route('/artist.html')
def artists():
    return render_template('artist.html')


@app.route('/genres.html')
def genres():
    return render_template('genres.html')



@app.route('/artist.html/<artist_name>')
def song(artist_name):
    token = getToken()
    result = searchArtist(token, artist_name)
    if result:
        artist_id = result["id"]
        songs = getSongs(token, artist_id)
        for song in songs:
            song['photo_url'] = getPhoto(token, song['id'])
            song['song_url'] = getSongUrl(token,song['id'])
    else:
        songs = None  # Handle the case where no artist is found
    
    # Pass the artist and songs data to the template for rendering
    return render_template('songs.html', songs=songs)

@app.route('/search_songs', methods=['POST'])
def search_songs():
    query = request.form['query']
    token = getToken()
    if not token:
        return "Error fetching token", 500
    
    # Search for tracks
    url = "https://api.spotify.com/v1/search"
    headers = getAuthHeader(token)
    params = {
        "q": query,
        "type": "track",
        "limit": 30 # Adjust the limit as needed
    }
    response = get(url, headers=headers, params=params)
    
    if response.status_code != 200:
        return f"Error searching for songs: {response.status_code} - {response.text}", 500
    
    data = response.json()
    tracks = data.get('tracks', {}).get('items', [])
    
    songs = []
    for track in tracks:
        song_details = {
            "id": track["id"],
            "name": track["name"],
            "artist": ", ".join(artist["name"] for artist in track["artists"]),
            "photo_url": track["album"]["images"][0]["url"] if track["album"]["images"] else None,
           # "song_url": getSpotifyLink(track["id"])
            "song_url": getSongUrl(token,track['id'])
        }
        songs.append(song_details)
    
    return render_template('home.html', songs=songs)


@app.route('/genres/<genre_name>')
def genre_songs(genre_name):
    token = getToken()
    if not token:
        return "Error fetching token", 500

    songs = getSongsByGenre(token, genre_name)
    if not songs:
        return "No songs found for this genre", 404
    
    return render_template('songGenre.html', genre=genre_name, songs=songs)



if __name__ == '__main__':
    app.run(debug=True)
