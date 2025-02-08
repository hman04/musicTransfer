from celery import Celery
from ytmusicapi import YTMusic
import time
import json

# Initialize Celery
celery = Celery('tasks', broker='redis://localhost:6379/0')

@celery.task
def process_playlist(playlist_id, tracks, auth_headers):
    try:
        ytmusic = YTMusic(auth=auth_headers)
        successful_transfers = 0
        failed_transfers = 0
        total = len(tracks)

        # Process tracks in batches of 50
        batch_size = 50
        for i in range(0, len(tracks), batch_size):
            batch = tracks[i:i + batch_size]
            video_ids = []
            
            for track in batch:
                try:
                    search_query = f"{track['name']} {' '.join(track['artists'])}"
                    search_results = ytmusic.search(search_query, filter="songs")
                    
                    if search_results:
                        video_ids.append(search_results[0]['videoId'])
                        successful_transfers += 1
                    else:
                        failed_transfers += 1
                        
                except Exception as e:
                    failed_transfers += 1
                    print(f"Error searching track {track['name']}: {str(e)}")
            
            # Add batch of songs to playlist
            if video_ids:
                try:
                    ytmusic.add_playlist_items(playlist_id, video_ids)
                    time.sleep(2)  # Small delay between batches
                except Exception as e:
                    print(f"Error adding batch to playlist: {str(e)}")
                    time.sleep(5)  # Longer delay if error occurs
            
            # Update progress in Redis
            celery.backend.set(
                f'playlist_progress_{playlist_id}',
                json.dumps({
                    'current': min(i + batch_size, total),
                    'total': total,
                    'successful': successful_transfers,
                    'failed': failed_transfers,
                    'status': 'In Progress'
                })
            )
        
        # Update final status
        celery.backend.set(
            f'playlist_progress_{playlist_id}',
            json.dumps({
                'current': total,
                'total': total,
                'successful': successful_transfers,
                'failed': failed_transfers,
                'status': 'Complete'
            })
        )
        
        return {
            'successful_transfers': successful_transfers,
            'failed_transfers': failed_transfers,
            'total_tracks': total
        }
        
    except Exception as e:
        print(f"Error in process_playlist: {str(e)}")
        return None 