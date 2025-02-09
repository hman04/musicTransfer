from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from bs4 import BeautifulSoup
import requests
from ytmusicapi import YTMusic
import re
import json
import threading
import time
from ytmusicapi import setup
import base64
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
import os
from celery_worker import process_playlist
from redis import Redis
from celery import Celery

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Spotify API credentials
CLIENT_ID = 'c8602cd477be4b759815de3b72ac484a'
CLIENT_SECRET = '2b77d9718ff448a9848b836988e0392f'  # Add your actual Client Secret here

# Google/YouTube OAuth2 credentials
GOOGLE_CLIENT_ID = '1058288589592-qskl3i44hfp43h54k9tunc3cpmar4nh3.apps.googleusercontent.com'
GOOGLE_CLIENT_SECRET = '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'
GOOGLE_REDIRECT_URI = 'http://127.0.0.1:5001/oauth2callback'

# OAuth2 configuration
CLIENT_SECRETS_FILE = "client_secrets.json"
SCOPES = [
    'https://www.googleapis.com/auth/youtube',
    'https://www.googleapis.com/auth/youtube.force-ssl'
]
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # Only for development

# Get Redis URL from environment variable
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')

# Initialize Redis and Celery with the URL
redis_client = Redis.from_url(REDIS_URL)
celery = Celery('tasks', broker=REDIS_URL, backend=REDIS_URL)

# Global dictionary to store transfer status
transfer_status = {}

class SpotifyScraperException(Exception):
    pass

def get_spotify_access_token():
    """Get Spotify API access token."""
    auth_string = f"{CLIENT_ID}:{CLIENT_SECRET}"
    auth_bytes = auth_string.encode('utf-8')
    auth_base64 = str(base64.b64encode(auth_bytes), 'utf-8')
    
    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": f"Basic {auth_base64}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    
    result = requests.post(url, headers=headers, data=data)
    json_result = json.loads(result.content)
    token = json_result.get("access_token")
    print(f"Got Spotify access token: {token[:10]}...")  # Debug log
    return token

def get_spotify_playlist_tracks(playlist_url):
    """Get tracks from Spotify playlist using official API."""
    try:
        # Clean and validate the URL
        playlist_url = playlist_url.strip()
        if not playlist_url.startswith('https://open.spotify.com/playlist/'):
            raise ValueError("Invalid Spotify playlist URL")
            
        # Extract playlist ID
        playlist_id = playlist_url.split('playlist/')[1].split('?')[0]
        print(f"Playlist ID: {playlist_id}")  # Debug log
        
        # Get access token
        token = get_spotify_access_token()
        
        # Initialize variables
        tracks = []
        offset = 0
        limit = 100
        
        while True:
            # Get playlist tracks with pagination
            url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            params = {
                "offset": offset,
                "limit": limit,
                "fields": "items(track(name,artists(name))),total"
            }
            
            print(f"Fetching tracks from offset {offset}")  # Debug log
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 404:
                print("Playlist not found or not accessible")
                return None
            elif response.status_code != 200:
                print(f"API Error: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
            data = response.json()
            
            # Process tracks from current batch
            for item in data['items']:
                if item['track']:  # Skip null tracks
                    track = item['track']
                    tracks.append({
                        'name': track['name'],
                        'artists': [artist['name'] for artist in track['artists']]
                    })
            
            # Update progress
            print(f"Fetched {len(tracks)} tracks so far")
            
            # Check if we've got all tracks
            if len(data['items']) < limit:
                break
                
            # Move to next batch
            offset += limit
        
        print(f"Successfully fetched {len(tracks)} tracks")
        return tracks
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def create_youtube_playlist(ytmusic, playlist_name):
    """Create a new YouTube Music playlist."""
    return ytmusic.create_playlist(playlist_name, "Transferred from Spotify")

def search_and_add_to_playlist(ytmusic, track, playlist_id):
    """Search for a track on YouTube Music and add it to playlist."""
    search_query = f"{track['name']} {' '.join(track['artists'])}"
    search_results = ytmusic.search(search_query, filter="songs")
    
    if search_results:
        video_id = search_results[0]['videoId']
        ytmusic.add_playlist_items(playlist_id, [video_id])
        return True
    return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/transfer', methods=['POST'])
def transfer():
    spotify_url = request.form['spotify_url']
    print(f"Processing URL: {spotify_url}")
    
    try:
        # Get tracks from Spotify
        tracks = get_spotify_playlist_tracks(spotify_url)
        if not tracks:
            print("No tracks found in playlist")
            return jsonify({'error': 'Could not fetch Spotify playlist'})
        
        print(f"Found {len(tracks)} tracks")
        
        # Initialize YTMusic
        ytmusic = YTMusic()
        
        # Search for first 5 tracks on YouTube Music
        results = []
        for track in tracks[:5]:
            search_query = f"{track['name']} {' '.join(track['artists'])}"
            print(f"Searching for: {search_query}")
            
            search_results = ytmusic.search(search_query, filter="songs")
            if search_results:
                results.append({
                    'spotify_track': track,
                    'youtube_track': search_results[0]
                })
        
        return jsonify({
            'message': 'Search successful!',
            'total_tracks': len(tracks),
            'preview_results': results
        })
        
    except Exception as e:
        print(f"Error during transfer: {e}")
        return jsonify({'error': str(e)})

# Add new route for processing transfer
@app.route('/process_transfer')
def process_transfer():
    try:
        ytmusic = YTMusic("oauth.json")
        tracks = get_spotify_playlist_tracks(session['spotify_url'])
        playlist_id = create_youtube_playlist(ytmusic, "Transferred Songs")
        
        # Store initial progress in session
        session['progress'] = {
            'current': 0,
            'total': len(tracks),
            'success': True
        }
        
        def transfer_process():
            for i, track in enumerate(tracks):
                success = search_and_add_to_playlist(ytmusic, track, playlist_id)
                # Store progress in a file or database instead of session
                with app.app_context():
                    session['progress'] = {
                        'current': i + 1,
                        'total': len(tracks),
                        'success': success
                    }
                time.sleep(1)  # Add small delay to prevent rate limiting
        
        thread = threading.Thread(target=transfer_process)
        thread.start()
        
        return redirect(url_for('progress'))
    
    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/progress')
def progress():
    if 'transfer_progress' not in session:
        return jsonify({'progress': 0, 'status': 'No transfer in progress'})
    return jsonify(session['transfer_progress'])

@app.route('/login')
def login():
    try:
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            scopes=SCOPES,
            redirect_uri='https://musictransfer.onrender.com/oauth2callback'  # Updated!
        )
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        
        session['state'] = state
        return redirect(authorization_url)
        
    except Exception as e:
        print(f"Login error: {str(e)}")
        return "Error during login. Please try again."

@app.route('/oauth2callback')
def oauth2callback():
    try:
        state = request.args.get('state', '')
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            scopes=SCOPES,
            state=state,
            redirect_uri='https://musictransfer.onrender.com/oauth2callback'  # Updated!
        )
        
        authorization_response = request.url
        if request.headers.get('X-Forwarded-Proto') == 'https':
            authorization_response = authorization_response.replace('http:', 'https:')
            
        flow.fetch_token(authorization_response=authorization_response)
        credentials = flow.credentials
        
        session['credentials'] = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
        
        return redirect('/')
        
    except Exception as e:
        print(f"OAuth callback error: {str(e)}")
        return redirect('/login')

def process_playlist_in_background(playlist_id, tracks, auth_token):
    try:
        # Initialize YTMusic
        auth = {
            'Authorization': f'Bearer {auth_token}'
        }
        ytmusic = YTMusic(auth=auth)
        
        successful_transfers = 0
        failed_transfers = 0
        
        for track in tracks:
            try:
                search_query = f"{track['name']} {' '.join(track['artists'])}"
                print(f"Searching for: {search_query}")
                search_results = ytmusic.search(search_query, filter="songs")
                
                if search_results:
                    video_id = search_results[0]['videoId']
                    print(f"Adding track: {search_query} ({video_id})")
                    ytmusic.add_playlist_items(playlist_id, [video_id])
                    successful_transfers += 1
                    
                    # Update status
                    transfer_status[playlist_id] = {
                        'current': successful_transfers + failed_transfers,
                        'total': len(tracks),
                        'successful': successful_transfers,
                        'failed': failed_transfers,
                        'complete': False
                    }
                    
                    time.sleep(1)  # Avoid rate limiting
                else:
                    print(f"No results found for: {search_query}")
                    failed_transfers += 1
                    
            except Exception as e:
                print(f"Error adding track {search_query}: {str(e)}")
                failed_transfers += 1
                time.sleep(2)
                
        # Update final status
        transfer_status[playlist_id]['complete'] = True
        print(f"Transfer complete. Success: {successful_transfers}, Failed: {failed_transfers}")
        
    except Exception as e:
        print(f"Background process error: {str(e)}")
        transfer_status[playlist_id] = {
            'error': str(e),
            'complete': True
        }

@app.route('/create_playlist', methods=['GET', 'POST'])
def create_playlist():
    if 'credentials' not in session:
        return jsonify({'redirect': '/login'})
        
    try:
        # Get tracks from Spotify
        spotify_url = request.form['spotify_url']
        tracks = get_spotify_playlist_tracks(spotify_url)
        
        if not tracks:
            return jsonify({'error': 'No tracks found'})
            
        # Initialize YTMusic and create playlist
        credentials = Credentials(**session['credentials'])
        auth = {
            'Authorization': f'Bearer {credentials.token}'
        }
        ytmusic = YTMusic(auth=auth)
        
        playlist_name = f"Spotify Import - {time.strftime('%Y-%m-%d %H:%M')}"
        playlist_id = ytmusic.create_playlist(playlist_name, "Imported from Spotify")
        
        # Start background process
        transfer_status[playlist_id] = {
            'current': 0,
            'total': len(tracks),
            'successful': 0,
            'failed': 0,
            'complete': False
        }
        
        thread = threading.Thread(
            target=process_playlist_in_background,
            args=(playlist_id, tracks, credentials.token)
        )
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Transfer started',
            'playlist_id': playlist_id
        })
        
    except Exception as e:
        print(f"Error in create_playlist: {str(e)}")
        if 'unauthorized' in str(e).lower():
            session.pop('credentials', None)
            return jsonify({'redirect': '/login'})
        return jsonify({'error': str(e)})

@app.route('/transfer_status/<playlist_id>')
def get_transfer_status(playlist_id):
    status = transfer_status.get(playlist_id, {
        'current': 0,
        'total': 0,
        'successful': 0,
        'failed': 0,
        'complete': False
    })
    return jsonify(status)

@app.route('/progress/<playlist_id>')
def get_progress(playlist_id):
    progress_data = redis_client.get(f'playlist_progress_{playlist_id}')
    if progress_data:
        return jsonify(json.loads(progress_data))
    return jsonify({'status': 'No progress data available'})

if __name__ == '__main__':
    app.run(debug=True, port=5001)