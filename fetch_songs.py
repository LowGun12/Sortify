import os
import json
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

load_dotenv()

auth_manager = SpotifyOAuth(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
    redirect_uri="http://127.0.0.1:8888/callback",
    scope="user-library-read playlist-read-private",
    cache_path=".spotify_cache"
)

if not auth_manager.get_cached_token():
    print("No Spotify token found. A browser window will open for you to log in.")
    print("After clicking Allow, you may see a blank page — that's normal, just wait.")
    print()
    auth_manager.get_access_token(as_dict=False)
    print("Authentication successful!\n")

sp = spotipy.Spotify(auth_manager=auth_manager)


def fetch_liked_songs():
    tracks = []
    offset = 0
    while True:
        results = sp.current_user_saved_tracks(limit=50, offset=offset)
        items = results["items"]
        if not items:
            break
        for item in items:
            tracks.append(item["track"])
        offset += 50
        if not results["next"]:
            break
    return tracks


def fetch_playlist_tracks(playlist_id, playlist_name):
    tracks = []
    offset = 0
    while True:
        results = sp.playlist_items(playlist_id, limit=50, offset=offset, additional_types=["track"])
        items = results["items"]
        if not items:
            break
        for item in items:
            track = item.get("track") or item.get("item")
            if track and track.get("id"):
                tracks.append(track)
        offset += 50
        if not results["next"]:
            break
    print(f"  Fetched {len(tracks)} songs from playlist: {playlist_name}")
    return tracks


def fetch_all_playlists(exclude_ids=None):
    exclude_ids = set(exclude_ids or [])
    playlists = []
    offset = 0
    while True:
        results = sp.current_user_playlists(limit=50, offset=offset)
        items = results["items"]
        if not items:
            break
        for p in items:
            if p["id"] not in exclude_ids:
                playlists.append({"id": p["id"], "name": p["name"]})
        offset += 50
        if not results["next"]:
            break
    return playlists


def track_to_song(track):
    return {
        "id": track["id"],
        "name": track["name"],
        "artist": ", ".join(a["name"] for a in track["artists"]),
        "album": track["album"]["name"],
    }


if __name__ == "__main__":
    with open("config/sources.json") as f:
        sources = json.load(f)

    # Load existing songs.json to preserve sorted status
    existing = {}
    try:
        with open("data/songs.json", encoding="utf-8") as f:
            for song in json.load(f):
                existing[song["id"]] = song
    except FileNotFoundError:
        pass

    seen_ids = set()
    songs = []

    def add_track(track):
        tid = track["id"]
        if tid in seen_ids:
            return
        seen_ids.add(tid)
        if tid in existing:
            songs.append(existing[tid])  # preserve sorted flag
        else:
            song = track_to_song(track)
            song["sorted"] = False
            songs.append(song)

    if sources.get("liked_songs"):
        print("Fetching liked songs...")
        for track in fetch_liked_songs():
            add_track(track)
        print(f"  {len(songs)} songs so far...")

    playlists = sources.get("playlists", [])

    # TODO: GUI — auto-fetch all playlists with deselect UI
    # if sources.get("all_playlists"):
    #     exclude = sources.get("exclude_playlists", [])
    #     auto = fetch_all_playlists(exclude_ids=exclude)
    #     existing_ids = {p["id"] for p in playlists}
    #     playlists += [p for p in auto if p["id"] not in existing_ids]
    #     print(f"Found {len(playlists)} playlists total...")

    for playlist in playlists:
        for track in fetch_playlist_tracks(playlist["id"], playlist["name"]):
            add_track(track)
        print(f"  {len(songs)} songs so far (after dedup)...")

    new_count = sum(1 for s in songs if not s.get("sorted"))

    with open("data/songs.json", "w", encoding="utf-8") as f:
        json.dump(songs, f, indent=2, ensure_ascii=False)

    print(f"\nDone! {len(songs)} unique songs saved to songs.json")
    print(f"  {new_count} unsorted (will be classified next run)")
    print(f"  {len(songs) - new_count} already sorted (will be skipped)")
