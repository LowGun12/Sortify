import os
import json
import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

load_dotenv()

auth_manager = SpotifyOAuth(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
    redirect_uri="http://127.0.0.1:8888/callback",
    scope="user-library-read playlist-read-private playlist-modify-public playlist-modify-private",
    cache_path=".spotify_cache"
)

if not auth_manager.get_cached_token():
    print("No Spotify token found. A browser window will open for you to log in.")
    print("After clicking Allow, you may see a blank page — that's normal, just wait.")
    print()
    auth_manager.get_access_token(as_dict=False)
    print("Authentication successful!\n")

sp = spotipy.Spotify(auth_manager=auth_manager)


def get_headers():
    token = auth_manager.get_access_token(as_dict=False)
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def get_user_id():
    return sp.current_user()["id"]


def get_existing_playlists(user_id):
    existing = {}
    offset = 0
    while True:
        results = sp.current_user_playlists(limit=50, offset=offset)
        for p in results["items"]:
            if p["owner"]["id"] == user_id:
                existing[p["name"]] = p["id"]
        if not results["next"]:
            break
        offset += 50
    return existing


def create_playlist(user_id, name):
    response = requests.post(
        f"https://api.spotify.com/v1/users/{user_id}/playlists",
        headers=get_headers(),
        json={"name": name, "public": False}
    )
    response.raise_for_status()
    return response.json()["id"]


def get_or_create_playlist(user_id, name, existing):
    if name in existing:
        print(f"  Found existing playlist: {name}")
        return existing[name]
    print(f"  Creating new playlist: {name}")
    return create_playlist(user_id, name)


def get_playlist_track_ids(playlist_id):
    track_ids = set()
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/items"
    params = {"limit": 50, "offset": 0, "additional_types": "track"}
    while url:
        response = requests.get(url, headers=get_headers(), params=params)
        response.raise_for_status()
        data = response.json()
        for item in data.get("items", []):
            track = item.get("track") or item.get("item")
            if track and track.get("id"):
                track_ids.add(track["id"])
        url = data.get("next")
        params = {}
    return track_ids


def add_tracks_to_playlist(playlist_id, track_ids):
    uris = [f"spotify:track:{tid}" for tid in track_ids]
    for i in range(0, len(uris), 100):
        response = requests.post(
            f"https://api.spotify.com/v1/playlists/{playlist_id}/items",
            headers=get_headers(),
            json={"uris": uris[i:i + 100]}
        )
        response.raise_for_status()


if __name__ == "__main__":
    with open("data/songs.json", encoding="utf-8") as f:
        songs = json.load(f)

    classified = [s for s in songs if s.get("sorted") and s.get("playlist")]
    unclassified = [s for s in songs if not s.get("sorted")]

    print(f"{len(classified)} classified songs to upload")
    if unclassified:
        print(f"  ({len(unclassified)} songs not yet classified — run classify.py first)\n")

    if not classified:
        print("Nothing to upload.")
        exit()

    playlist_songs = {}
    for song in classified:
        name = song["playlist"]
        playlist_songs.setdefault(name, []).append(song["id"])

    print(f"Playlists to update: {', '.join(playlist_songs.keys())}\n")

    with open("config/playlists.json", encoding="utf-8") as f:
        playlist_config = {p["name"]: p.get("spotify_id") for p in json.load(f)}

    for playlist_name, track_ids in playlist_songs.items():
        print(f"\n{playlist_name} ({len(track_ids)} songs)")
        playlist_id = playlist_config.get(playlist_name)

        if not playlist_id:
            print(f"  Skipping — no spotify_id set in playlists.json. Create the playlist in Spotify and add the ID.")
            continue

        try:
            already_there = get_playlist_track_ids(playlist_id)
            new_tracks = [tid for tid in track_ids if tid not in already_there]

            if not new_tracks:
                print(f"  All songs already in playlist, skipping.")
                continue

            print(f"  Adding {len(new_tracks)} new songs ({len(track_ids) - len(new_tracks)} already present)...")
            add_tracks_to_playlist(playlist_id, new_tracks)
            print(f"  Done.")
        except Exception as e:
            print(f"  Error: {e}")

    print("\nAll playlists updated!")
