import os
import requests
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

load_dotenv()

auth_manager = SpotifyOAuth(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
    redirect_uri="http://127.0.0.1:8888/callback",
    scope="playlist-read-private",
    cache_path=".spotify_cache"
)

token = auth_manager.get_access_token(as_dict=False)
headers = {"Authorization": f"Bearer {token}"}

ids = [
    "3gvuunefs5Kd4wSyfxqzcj",
    "1Nv6HITkivKyPoVvQUiZpB",
    "5LkJys9Yp19hmBh1S0wyQK",
    "55Fy1cEpcAefts9e7te5F6",
    "489zrTcbiL2fwh4LqKXqa9",
    "1OPlKlsviaesrEMwh89908",
    "7kSBvfRufclGJyqIqBh1hh",
    "5iXu1Lhn6Rg5APr3Pcifso",
    "0XLaxN6R4KEApSWrRFVW5S",
    "5kFOmQXUqH5aXAwBJxfu85",
    "65AONAKlf8yP9Rg3KXwtGA",
    "1QS9FWLY37sipCegxspEHm",
    "0er4qrITlecerconGodPHT",
]

for pid in ids:
    r = requests.get(f"https://api.spotify.com/v1/playlists/{pid}?fields=name", headers=headers)
    name = r.json().get("name", "ERROR")
    print(f"{pid}  ->  {name}")
