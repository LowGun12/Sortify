# Sortify

Automatically sort your Spotify liked songs and playlists into categorised playlists using Claude AI.

Instead of relying on BPM or energy scores, Sortify uses Claude to understand the actual feel of a song — so a sad indie folk track with a high BPM ends up in the right place.

---

## Setup

### 1. Install Python

Download and install Python from [python.org/downloads](https://python.org/downloads).

> **Important:** During installation, check **"Add Python to PATH"** before clicking Install.

---

### 2. Clone the repo

```
git clone https://github.com/LowGun12/Sortify.git
cd Sortify
```

---

### 3. Install dependencies

```
pip install -r requirements.txt
```

---

### 4. Create a Spotify Developer App

1. Go to [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard) and log in
2. Click **Create app**
3. Fill in any name and description
4. Set the **Redirect URI** to: `http://127.0.0.1:8888/callback`
5. Check **Web API** under APIs used
6. Click **Save**, then go to **Settings** to find your **Client ID** and **Client Secret**

---

### 5. Configure your credentials

Copy `.env.example` to a new file called `.env`:

```
cp .env.example .env
```

Open `.env` and fill in your keys:

```
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

> Your `.env` file is gitignored and will never be committed.

---

### 6. Configure your sources

Copy `config/sources.example.json` to `config/sources.json`:

```
cp config/sources.example.json config/sources.json
```

Edit `config/sources.json` to set which playlists to pull songs from. You can find a playlist's ID in its Spotify URL — it's the string between `/playlist/` and `?`.

```json
{
  "liked_songs": true,
  "playlists": [
    { "id": "37i9dQZF1DXcBWIGoYBM5M", "name": "My Playlist" }
  ]
}
```

---

### 7. Configure your target playlists

Copy `config/playlists.example.json` to `config/playlists.json`:

```
cp config/playlists.example.json config/playlists.json
```

Edit `config/playlists.json` to define the playlists you want songs sorted into. The more detail you provide in the description, the better Claude will classify.

```json
[
  {
    "name": "Chill",
    "description": "Relaxed, low energy, background listening. Good for studying or winding down.",
    "example_artists": ["Bon Iver", "Novo Amor"],
    "example_songs": ["Skinny Love", "Carry You"]
  }
]
```

---

## Usage

### Fetch songs

Pull all songs from your liked songs and configured playlists:

```
python fetch_songs.py
```

On first run, a browser window will open asking you to log in to Spotify and grant access. After that, your session is cached and future runs are fully automatic.

Songs are saved to `data/songs.json` and deduplicated — running this multiple times won't create duplicates.

---

## Project Structure

```
Sortify/
├── config/
│   ├── sources.json          ← where to pull songs from (gitignored)
│   ├── sources.example.json  ← template
│   ├── playlists.json        ← target playlists for sorting (gitignored)
│   └── playlists.example.json← template
├── data/
│   └── songs.json            ← fetched songs (gitignored, generated on run)
├── fetch_songs.py            ← fetches songs from Spotify
├── .env                      ← your API keys (gitignored)
├── .env.example              ← template
└── requirements.txt
```
