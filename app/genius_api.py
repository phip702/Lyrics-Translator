import lyricsgenius
import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
from app.lyrics_handler import trim_lyrics
import logging
import json
from unidecode import unidecode

def get_genius_auth_token(): #*do not delete, this is called on the home page
    load_dotenv()
    genius_auth_token = os.getenv("GENIUS_AUTH_TOKEN")
    return genius_auth_token

def remove_accents(input_str):
    return unidecode(input_str) # Won't affect things like Kanji, it will just return the normal Kanji

def search_song_by_artist(track_artist, hits):
    '''This is used to find the top hit on the Genius song list that has the spotify track_artist's name.
    This solves the issue of a 'featuring xyz' ruining the search.
    This also solves issues with translations being returned first because they are more popular.
    '''

    try:
        artist_names_list = [] # For debugging
        for idx, hit in enumerate(hits, start = 1):
            artist_names = hit['result']['artist_names']
            artist_names_list.append(artist_names)
            if remove_accents(track_artist).lower() in remove_accents(artist_names).lower(): #used in because of issues where there's a (featuring XX)
                logging.debug(f"Genius Hit Number Returned: {idx}")
                genius_url = hit['result']['url'] 
                return genius_url
        
        return logging.error(f"No matching artist for: {track_artist} in {artist_names_list}")
    except:
        "No matching artist in hits" # Not sure if this will ever be used
        
         
# I wrote this scraper, not the lyricsgenius module creators
def scrape_song_lyrics(url):
    page = requests.get(url)
    html = BeautifulSoup(page.text, 'html.parser')
    lyrics_containers = html.find_all('div', attrs={'data-lyrics-container': 'true'})
    lyrics = ''
    if lyrics_containers:
        for container in lyrics_containers:
            lyrics += container.get_text(separator='\n') + '\n'
        lyrics = lyrics.replace('[', '\n[') # adds a line break before [chorus] [verse] etc #this line and the line above take <.0001s
        lyrics = trim_lyrics(lyrics)
        if lyrics:
            return lyrics
        else:
            logging.debug(f"Lyrics container for lyrics not found: {lyrics_containers}")
            return "Could not find lyrics"
    else:
        logging.error(f"URL where lyrics could not be found: {url}")
        return "Could not find lyrics" 


def get_song_lyrics(track_name, track_artist):
    genius_auth_token = os.getenv("GENIUS_AUTH_TOKEN")
    genius = lyricsgenius.Genius(genius_auth_token) #optimize; it might be faster to just use the Genius API from the beginning (or scrape) to get the search results based on track_name and track_artist

    try:
        search_results = genius.search_songs(f"{track_name} {track_artist}", per_page=3) #*track artist going after appears to be more accurate
        hits = search_results['hits']
        first_hit_url = search_song_by_artist(track_artist, hits)
        logging.debug(f"first hit url: {first_hit_url}")
        return scrape_song_lyrics(first_hit_url)
    except Exception as e:
        logging.error(f"Error while fetching lyrics: {e}")
        logging.error(f"All hits for lyrics not scraped: {json.dumps(hits, indent = 4)}")
        return "Could not find lyrics" #this error is to catch when genius.search_songs finds nothing



if __name__ == "__main__": #spot test songs
    from app.spotify_api import get_song_id_from_url, get_track_name_artist_image
    spotify_track_id = get_song_id_from_url("https://open.spotify.com/track/6Za3190Sbw39BBC77WSS1C?si=c57f5e2fa1b649e2")
    print(spotify_track_id)
    track_name, track_artist, track_image  = get_track_name_artist_image(spotify_track_id)
    print(track_name, track_artist)

    search_results = get_song_lyrics(track_name, track_artist)
    print(search_results)