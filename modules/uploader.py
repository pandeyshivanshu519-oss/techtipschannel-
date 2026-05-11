import os
import pickle
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import google.auth

class YouTubeUploader:
    def __init__(self):
        self.SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
        self.service = None

    def authenticate(self):
        """Use secrets from GitHub Actions"""
        try:
            from google.oauth2.credentials import Credentials

            creds = Credentials(
                token=None,
                refresh_token=os.getenv("YOUTUBE_REFRESH_TOKEN"),
                token_uri="https://oauth2.googleapis.com/token",
                client_id=os.getenv("YOUTUBE_CLIENT_ID"),
                client_secret=os.getenv("YOUTUBE_CLIENT_SECRET"),
                scopes=self.SCOPES
            )

            creds.refresh(google.auth.transport.requests.Request())

            self.service = build('youtube', 'v3', credentials=creds)
            print("✅ YouTube authentication successful")
            return True

        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            return False

    def upload(self, video_path, title, description, thumbnail_path=None, tags=None, privacy="public"):
        """
        Upload video with optional thumbnail
        """
        if not os.path.exists(video_path):
            print(f"❌ Video file not found: {video_path}")
            return None

        if not self.authenticate():
            return None

        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags or ["didyouknow", "hindi facts", "mind blowing facts", "ancient history"],
                'categoryId': '22'
            },
            'status': {
                'privacyStatus': privacy,
                'selfDeclaredMadeForKids': False
            }
        }

        media = MediaFileUpload(video_path, chunksize=-1, resumable=True)

        try:
            print("📤 Uploading to YouTube... (this may take 20-60 seconds)")

            request = self.service.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media
            )

            response = request.execute()
            video_id = response['id']

            # Thumbnail attach karo (agar diya gaya ho)
            if thumbnail_path and os.path.exists(thumbnail_path):
                print("🖼️ Attaching custom thumbnail...")
                try:
                    media_thumbnail = MediaFileUpload(thumbnail_path, mimetype='image/png')
                    self.service.thumbnails().set(
                        videoId=video_id,
                        media_body=media_thumbnail
                    ).execute()
                    print("✅ Thumbnail attached successfully")
                except Exception as e:
                    print(f"⚠️ Thumbnail attach failed (but video uploaded): {e}")

            print(f"✅ UPLOAD SUCCESSFUL!")
            print(f"🔗 https://youtu.be/{video_id}")
            return video_id

        except Exception as e:
            print(f"❌ YouTube Upload Failed: {e}")
            return None
