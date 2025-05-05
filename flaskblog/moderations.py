import os
import requests
from dotenv import load_dotenv


load_dotenv()

# --- TEXT MODERATION (Perspective API) ---

PERSPECTIVE_API_KEY = os.getenv("PERSPECTIVE_API_KEY")
PERSPECTIVE_URL = f"https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze?key={PERSPECTIVE_API_KEY}"

def is_content_inappropriate(text):
    payload = {
        'comment': {'text': text},
        'requestedAttributes': {
            'TOXICITY': {}, 'INSULT': {}, 'PROFANITY': {}, 'THREAT': {}
        }
    }
    response = requests.post(PERSPECTIVE_URL, json=payload)
    result = response.json()
    for attr in result.get('attributeScores', {}):
        score = result['attributeScores'][attr]['summaryScore']['value']
        if score > 0.7:
            return True
    return False


# --- IMAGE & VIDEO MODERATION (Sightengine API) ---

SIGHTENGINE_USER = os.getenv("SIGHTENGINE_API_USER")
SIGHTENGINE_SECRET = os.getenv("SIGHTENGINE_API_SECRET")
SIGHTENGINE_URL = "https://api.sightengine.com/1.0/check.json"

def is_nsfw_image(image_path):
    with open(image_path, 'rb') as img:
        files = {'media': img}
        data = {
            'models': 'nudity,wad,offensive',
            'api_user': SIGHTENGINE_USER,
            'api_secret': SIGHTENGINE_SECRET
        }
        response = requests.post(SIGHTENGINE_URL, files=files, data=data)
        result = response.json()

        nudity = result.get('nudity', {})
        if nudity.get('sexual_activity', 0) > 0.7 or nudity.get('sexual_display', 0) > 0.7:
            return True
        if result.get('weapon', 0) > 0.7 or result.get('alcohol', 0) > 0.7 or result.get('drugs', 0) > 0.7:
            return True
    return False

def is_nsfw_video(video_path):
    url = "https://api.sightengine.com/1.0/video/check-sync.json"
    
    files = {'media': open(video_path, 'rb')}
    data = {
        'models': 'nudity,weapon,alcohol,offensive',
        'api_user': SIGHTENGINE_USER,
        'api_secret': SIGHTENGINE_SECRET
    }

    response = requests.post(url, files=files, data=data)
    result = response.json()

    if 'summary' in result:
        nudity_score = result['summary'].get('nudity', 0)
        if nudity_score > 0.7:  # You can fine-tune this
            return True  # NSFW detected

    return False
