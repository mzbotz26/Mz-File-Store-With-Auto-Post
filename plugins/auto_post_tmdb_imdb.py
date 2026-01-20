import re, asyncio, requests
from pyrogram import Client, filters
from config import CHANNEL_ID, POST_CHANNEL, TMDB_API_KEY, OMDB_API_KEY

cache = {}

# ---------------- CLEAN TITLE ----------------

def clean_title(name):
    name = re.sub(r"\.(mkv|mp4|avi|webm)", "", name, flags=re.I)
    name = re.sub(r"@\w+", "", name)
    name = re.sub(r"https?://\S+", "", name)
    name = re.sub(r"\[.*?\]|\(.*?\)", "", name)
    name = re.sub(r"S\d+E\d+|S\d+|E\d+", "", name, flags=re.I)
    name = re.sub(r"480p|720p|1080p|2160p|x264|x265|hevc|webrip|webdl|bluray|hdrip|dual|multi|hindi|tamil|telugu|english|aac|ddp|esub|subs", "", name, flags=re.I)
    name = name.replace(".", " ").replace("_", " ")
    return re.sub(" +", " ", name).strip()

# ---------------- DETECT ----------------

def detect_language(text):
    t = text.lower()
    if "dual" in t or "multi" in t: return "Dual Audio"
    if "hindi" in t: return "Hindi"
    if "tamil" in t: return "Tamil"
    if "telugu" in t: return "Telugu"
    if "english" in t or "eng" in t: return "English"
    return "Hindi"

def detect_resolution(text):
    if "2160" in text: return "2160p"
    if "1080" in text: return "1080p"
    if "720" in text: return "720p"
    if "480" in text: return "480p"
    return "HD"

def detect_codec(text):
    return "x265" if "x265" in text.lower() or "hevc" in text.lower() else "x264"

def detect_source(text):
    t = text.lower()
    if "bluray" in t: return "BLURAY"
    if "webrip" in t: return "WEBRIP"
    if "webdl" in t or "web-dl" in t: return "WEBDL"
    return "WEBDL"

def detect_audio(text):
    t = text.lower()
    if "ddp" in t or "dd+" in t: return "DDP"
    if "aac" in t: return "AAC"
    if "mp3" in t: return "MP3"
    return "AAC"

def detect_episode(text):
    m = re.search(r"S(\d+)[\s\-_.]*E(\d+)", text, re.I)
    return (int(m.group(1)), int(m.group(2))) if m else None

def detect_year(text):
    m = re.search(r"(19\d{2}|20\d{2})", text)
    return m.group(1) if m else None

def size_format(size):
    mb = size/1024/1024
    return f"{round(mb/1024,2)} GB" if mb>1024 else f"{round(mb,2)} MB"

# ---------------- TMDB ----------------

def tmdb_movie(title):
    url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={title}"
    r = requests.get(url).json()
    if r.get("results"):
        m = r["results"][0]
        return {
            "year": m.get("release_date","")[:4],
            "story": m.get("overview","N/A"),
            "rating": m.get("vote_average","N/A"),
            "poster": "https://image.tmdb.org/t/p/w500"+m["poster_path"] if m.get("poster_path") else None
        }
    return None

def tmdb_series(title):
    url = f"https://api.themoviedb.org/3/search/tv?api_key={TMDB_API_KEY}&query={title}"
    r = requests.get(url).json()
    if r.get("results"):
        s = r["results"][0]
        return {
            "id": s["id"],
            "year": s.get("first_air_date","")[:4],
            "story": s.get("overview","N/A"),
            "rating": s.get("vote_average","N/A"),
            "poster": "https://image.tmdb.org/t/p/w500"+s["poster_path"] if s.get("poster_path") else None
        }
    return None

def imdb_fetch(title):
    url = f"https://www.omdbapi.com/?apikey={OMDB_API_KEY}&t={title}"
    r = requests.get(url).json()
    if r.get("Response") == "True":
        return {
            "rating": r.get("imdbRating","N/A"),
            "genre": r.get("Genre","N/A"),
            "year": r.get("Year","N/A")
        }
    return None

# ---------------- AUTO POST ----------------

@Client.on_message(filters.chat(int(CHANNEL_ID)) & (filters.document | filters.video))
async def auto_post(client, message):

    file = message.document or message.video
    name = file.file_name or "Movie"

    title = clean_title(name)
    year = detect_year(name)

    ep = detect_episode(name)

    if ep:
        season, episode = ep
        key = f"{title.lower()}_season_{season}"
    else:
        season = None
        episode = None
        key = title.lower()

    lang = detect_language(name)
    res = detect_resolution(name)
    codec = detect_codec(name)
    source = detect_source(name)
    audio = detect_audio(name)

    quality = f"{lang} {res} {codec} {source} [{audio}]"
    size = size_format(file.file_size)

    bot = await client.get_me()
    link = f"https://t.me/{bot.username}?start=file_{message.id}"

    if key not in cache:
        cache[key] = []

    cache[key].append((quality,size,link,episode))

    await asyncio.sleep(10)

    files = cache.get(key)
    if not files:
        return

    tmdb = tmdb_series(title) if season else tmdb_movie(title)
    imdb = imdb_fetch(title)

    poster = None
    story = "N/A"
    rating = "N/A"
    genre = "N/A"
    year_final = year or "N/A"

    if tmdb:
        story = tmdb["story"]
        poster = tmdb["poster"]
        rating = tmdb["rating"]
        year_final = tmdb["year"] or year_final

    if imdb:
        rating = imdb["rating"]
        genre = imdb["genre"]
        year_final = imdb["year"]

    caption = f"🔖 <b>Title:</b> {title} {year_final}\n\n"
    caption += f"🎬 <b>Genres:</b> {genre}\n⭐️ <b>IMDB Rating:</b> {rating}\n📆 <b>Year:</b> {year_final}\n📕 <b>Story:</b> {story}\n"

    if season:
        caption += f"\n📺 <b>Season:</b> {season}\n"

    for q,s,l,e in files:
        ep_txt = f"E{int(e):02d}" if e else ""
        caption += f"\n📁 ➤ <b>{q} {ep_txt}</b>\n📥 ➪ <a href='{l}'>Get File ({s})</a>\n"

    caption += "\n💪 Powered By : <a href='https://t.me/MzMoviiez'>MzMoviiez</a>"

    if poster:
        await client.send_photo(POST_CHANNEL, poster, caption=caption)
    else:
        await client.send_message(POST_CHANNEL, caption, disable_web_page_preview=True)

    cache.pop(key, None)
