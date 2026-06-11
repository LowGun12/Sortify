import os
import json
import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
BATCH_SIZE = 30
MODEL = "claude-opus-4-8"


def load_playlists():
    with open("config/playlists.json", encoding="utf-8") as f:
        return json.load(f)


def load_songs():
    with open("data/songs.json", encoding="utf-8") as f:
        return json.load(f)


def save_songs(songs):
    with open("data/songs.json", "w", encoding="utf-8") as f:
        json.dump(songs, f, indent=2, ensure_ascii=False)


def build_playlist_guide(playlists):
    lines = []
    for p in playlists:
        lines.append(f"- **{p['name']}**: {p['description']}")
        if p.get("example_artists"):
            lines.append(f"  Example artists: {', '.join(p['example_artists'])}")
        if p.get("example_songs"):
            lines.append(f"  Example songs: {', '.join(p['example_songs'])}")
    return "\n".join(lines)


def classify_batch(batch, playlists):
    playlist_names = [p["name"] for p in playlists]
    playlist_guide = build_playlist_guide(playlists)

    songs_list = "\n".join(
        f'{s["id"]} | {s["name"]} — {s["artist"]} | Album: {s["album"]}'
        for s in batch
    )

    prompt = f"""You are classifying songs into playlists based on their artist, title, and album.

## Playlists

{playlist_guide}

## Songs to classify

Each line is: ID | Song — Artist | Album: Album

{songs_list}

## Instructions

For each song, assign it to exactly one playlist from this list:
{json.dumps(playlist_names)}

Pick the single best fit. Consider the artist's known style, the song title, and the album context.

Respond with a JSON object only — no explanation, no markdown. Format:
{{
  "song_id": "Playlist Name",
  "song_id": "Playlist Name",
  ...
}}"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )

    text = response.content[0].text.strip()

    # Strip markdown code fences if present
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        text = text.rsplit("```", 1)[0]

    return json.loads(text)


if __name__ == "__main__":
    playlists = load_playlists()
    songs = load_songs()

    unsorted = [s for s in songs if not s.get("sorted")]
    print(f"{len(unsorted)} songs to classify across {len(playlists)} playlists\n")

    if not unsorted:
        print("Nothing to classify.")
        exit()

    song_index = {s["id"]: s for s in songs}
    total_classified = 0

    for i in range(0, len(unsorted), BATCH_SIZE):
        batch = unsorted[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (len(unsorted) + BATCH_SIZE - 1) // BATCH_SIZE
        print(f"Classifying batch {batch_num}/{total_batches} ({len(batch)} songs)...")

        try:
            results = classify_batch(batch, playlists)

            for song in batch:
                assigned = results.get(song["id"], None)
                song_index[song["id"]]["playlist"] = assigned
                song_index[song["id"]]["sorted"] = True
                total_classified += 1

            save_songs(list(song_index.values()))
            print(f"  Done. {total_classified}/{len(unsorted)} classified so far.")

        except Exception as e:
            print(f"  Error on batch {batch_num}: {e}")
            print("  Skipping batch and continuing...")

    print(f"\nFinished! {total_classified} songs classified.")
    print("Results saved to data/songs.json")
