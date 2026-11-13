"""Real video links come from YouTube, never from model-generated URLs."""
import html
import re
from urllib.parse import urlencode

import httpx


def find_video_lessons(query, preferences, config):
    if not query:
        return {'items': [], 'search_url': '', 'notice': ''}
    search_url = 'https://www.youtube.com/results?' + urlencode({'search_query': query})
    fallback = {'items': [], 'search_url': search_url, 'notice': ''}
    # Demo must remain offline even if keys happen to be present in the environment.
    if config['AI_MODE'] == 'demo':
        return {**fallback, 'notice': 'Demo search link only. No videos were fetched or reviewed.'}
    if not config.get('YOUTUBE_API_KEY'):
        return {**fallback, 'notice': 'Open this topic search on YouTube. Individual video results are not connected yet.'}
    params = {
        'part': 'snippet', 'type': 'video', 'q': query, 'maxResults': 3,
        'safeSearch': 'strict', 'order': 'relevance',
        'videoDuration': preferences['video_duration'], 'key': config['YOUTUBE_API_KEY'],
    }
    if preferences['language'] != 'auto':
        params['relevanceLanguage'] = preferences['language']
    try:
        response = httpx.get('https://www.googleapis.com/youtube/v3/search', params=params, timeout=8.0)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict) or not isinstance(data.get('items'), list):
            raise ValueError('Invalid YouTube result')
        items = []
        seen = set()
        for item in data['items'][:3]:
            if not isinstance(item, dict):
                continue
            identity, snippet = item.get('id'), item.get('snippet')
            if not isinstance(identity, dict) or not isinstance(snippet, dict):
                continue
            video_id = identity.get('videoId', '')
            title, channel = snippet.get('title'), snippet.get('channelTitle')
            if not isinstance(video_id, str) or not re.fullmatch(r'[A-Za-z0-9_-]{11}', video_id):
                continue
            if video_id in seen or not isinstance(title, str) or not isinstance(channel, str):
                continue
            seen.add(video_id)
            items.append({'title': html.unescape(title[:300]), 'channel': html.unescape(channel[:200]),
                          'url': 'https://www.youtube.com/watch?' + urlencode({'v': video_id})})
        notice = ('YouTube search matches, not reviewed lessons. Language is a relevance preference.' if items else
                  'No matching videos were returned. Try a broader topic or another video length.')
        return {'items': items, 'search_url': search_url, 'notice': notice}
    except (httpx.HTTPError, ValueError):
        # Never return raw HTTP errors: their request URL may contain the API key.
        return {**fallback, 'notice': 'Video search is temporarily unavailable. You can still open the topic search on YouTube.'}
