
import cv2
import numpy as np
import scipy.cluster
import sklearn.cluster
from dotenv import load_dotenv
import os
import requests
import datetime
import base64

from urllib.parse import urlencode
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
import spotipy
from flask import Flask, render_template, request, redirect, session
import psutil
import locale


def get_my_albums():
    sp = spotipy.Spotify(auth=session.get('token'))
    limit = 20  # establece el número máximo de álbumes que se devolverán en una única llamada a la API
    offset = 0  # establece el número de álbumes que se deben omitir antes de comenzar a devolver resultados

    albums = []  # lista para almacenar los álbumes

    # ciclo para obtener los álbumes en bloques de 20
    while True:
        results = sp.current_user_saved_albums(limit=limit, offset=offset)
        if not results['items']:
            # no hay más resultados, se detiene el ciclo
            break
        for item in results['items']:

            item = item['album']

            total_tracks = 0
            try:
                tracks = item['tracks']['items']
                total_tracks = item['total_tracks']
                if total_tracks > 50:
                    tracks = get_all_tracks(item['id'])
            except KeyError:
                tracks = []
                total_tracks = 0

            album = {}
            album['album_id'] = item['id']
            album['album_name'] = item['name']
            album['album_artist'] = item['artists'][0]['name']
            album['album_link'] = item['external_urls']['spotify']
            album['album_art'] = item['images'][0]['url']
            album['album_date'] = get_date(item['release_date'], '')
            album['playtime'] = get_playtime(tracks)
            album['total_tracks'] = item['total_tracks']
            album['album_type'] = item['album_type']
            albums.append(album)
        offset += limit
    return albums

def get_albums(artist):
    sp = get_spotify()

    limit = 20  # establece el número máximo de álbumes que se devolverán en una única llamada a la API
    offset = 0  # establece el número de álbumes que se deben omitir antes de comenzar a devolver resultados

    items = []
    albums = []  # lista para almacenar los álbumes

    try:
        # busca el artista en Spotify
        artist_info = sp.search(q='artist:' + artist, type='artist')
        artist_id = artist_info['artists']['items'][0]['id']
    except (spotipy.SpotifyException, IndexError) as e:
        print(f"No se pudo obtener información del artista {artist}: {e}")
        return []

    # ciclo para obtener los álbumes en bloques de 20
    while True:
        try:
            # obtener los álbumes del artista actual en el offset actual
            results = sp.artist_albums(artist_id, album_type='album,single', country='US', limit=limit, offset=offset)
        except spotipy.SpotifyException as e:
            print(f"No se pudieron obtener los álbumes de {artist}: {e}")
            return albums

        items_results = results['items']
        items.extend(items_results)
        offset += limit  # Avanzar al siguiente conjunto de resultados

        # detener el ciclo si no hay más resultados
        if results['next'] is None:
            break

    # obtener información adicional para cada álbum
    for item in items:
        try:
            album = {}
            album_info = sp.album(item['id'])

            total_tracks = 0
            try:
                tracks = album_info['tracks']['items']
                total_tracks = album_info['total_tracks']
                if total_tracks > 50:
                    tracks = get_all_tracks(album_info['id'])
            except KeyError as e:
                tracks = []
                total_tracks = 0
                print(e)

            album['album_id'] = album_info['id']
            album['album_name'] = album_info['name']
            album['album_artist'] = album_info['artists'][0]['name']
            album['album_link'] = album_info['external_urls']['spotify']
            album['album_art'] = album_info['images'][0]['url']
            album['album_date'] = get_date(album_info['release_date'], '')
            album['playtime'] = get_playtime(tracks)
            album['total_tracks'] = album_info['total_tracks']
            album['album_type'] = album_info['album_type']
            # añadir más campos según tus necesidades
            albums.append(album)

        except spotipy.SpotifyException as e:
            print(f"No se pudo obtener información adicional para el álbum {album['name']}: {e}")

    return albums

def get_artist_albums(artist_name):
    sp = spotipy.Spotify(auth=session.get('token'))
    artist = sp.search(q='artist:' + artist_name, type='artist')
    if not artist['artists']['items']:
        return []
    artist_id = artist['artists']['items'][0]['id']
    albums = []
    results = sp.artist_albums(artist_id, album_type='album,single', country='US')
    albums.extend(results['items'])
    while results['next']:
        results = sp.next(results)
        albums.extend(results['items'])
    return albums


def get_date(date_input, lang):
    try:
        locale.setlocale(locale.LC_TIME, lang)
        date = datetime.datetime.strptime(date_input.replace('-',''), r'%Y%m%d')
        #month = date.strftime("%b").capitalize()
        day = date.strftime("%d").lstrip('0')
        month = date.strftime("%d").lstrip('0')
        #date_format =  date.strftime(r'%d de {} de %Y').lstrip('0').format(month)
        date_format = date.strftime(r'{}/{}/%Y').lstrip('0').format(day, month)
    except ValueError:
        return date_input
    return date_format

def ms_to_hhmm(duration_ms):
    duration_seconds = duration_ms // 1000
    duration = datetime.timedelta(seconds=duration_seconds)
    hhmm = str(duration).split('.')[0]  # extract the hh:mm part
    return hhmm


def get_playtime_old(tracks):

    playtime = 0
    for i in tracks:
        playtime += i['duration_ms']

    playtime = str(datetime.timedelta(seconds=playtime//1000))
    if playtime[0] == '0':
        playtime = playtime[2:]
    return playtime

def get_playtime(tracks):
    
    playtime = 0
    for i in tracks:
        playtime += i['duration_ms']

    playtime_seconds = playtime // 1000
    minutes, seconds = divmod(playtime_seconds, 60)
    hours, minutes = divmod(minutes, 60)

    if hours == 0:
        return f"{minutes} min"
    else:
        return f"{hours} h {minutes} min"
    
def get_playtime_pro(tracks):
    sp = spotipy.Spotify(auth=session.get('token'))
    playtime_ms = 0
    total_tracks = len(tracks)
    
    # handle playlists with more than 50 tracks
    if total_tracks > 50:
        #sp = spotipy.Spotify(auth=token)
        offset = 0
        while offset < total_tracks:
            results = sp.tracks(tracks[offset:offset+50])
            for track in results['tracks']:
                playtime_ms += track['duration_ms']
            offset += 50
    else:
        for track in tracks:
            playtime_ms += track['duration_ms']
    
    playtime_seconds = playtime_ms // 1000
    minutes, seconds = divmod(playtime_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    
    if hours == 0:
        return f"{minutes} min"
    else:
        return f"{hours} h {minutes} min"



def get_user_spotify():

    session.clear()

    code = request.args.get('code')
    token = get_access_token(code)

    session['token'] = token

    sp = spotipy.Spotify(auth=token)
    user = sp.current_user()
    return user['display_name']

def get_access_token(code):
    sp_oauth = SpotifyOAuth(
        client_id=os.getenv('SPOTIFY_ID'),
        client_secret=os.getenv('SPOTIFY_SECRET'),
        redirect_uri=os.getenv('SPOTIFY_REDIRECT_URI'),
        scope='user-library-read'
    )
    token_info = sp_oauth.get_access_token(code)
    return token_info['access_token']

def login_spotify():
    load_dotenv()
    sp_oauth = SpotifyOAuth(client_id=os.getenv('SPOTIFY_ID'), client_secret=os.getenv('SPOTIFY_SECRET'),
                            redirect_uri=os.getenv('SPOTIFY_REDIRECT_URI'), scope='user-library-read')
    auth_url = sp_oauth.get_authorize_url()
    return auth_url

def get_spotify():
    load_dotenv()
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=os.getenv('SPOTIFY_ID'),
        client_secret=os.getenv('SPOTIFY_SECRET'),
        redirect_uri=os.getenv('SPOTIFY_REDIRECT_URI'),
        scope='user-library-read'))
    return sp

def get_auth_url():
    load_dotenv()
    AUTH_URL = 'https://accounts.spotify.com/authorize'
    params = urlencode({
        'client_id': os.getenv('SPOTIFY_ID'),
        'response_type': 'code',
        'redirect_uri': 'http://localhost:8000/callback',
        'scope': 'user-library-read'
    })
    return f"{AUTH_URL}?{params}"


def get_access_token_2():
    load_dotenv()
    client_id = os.getenv('SPOTIFY_ID')
    client_secret = os.getenv('SPOTIFY_SECRET')
    auth_url = 'https://accounts.spotify.com/api/token'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    # Encode client ID and secret into base64 string
    credentials = f"{client_id}:{client_secret}"
    credentials_b64 = base64.b64encode(credentials.encode()).decode()

    # Request access token
    response = requests.post(auth_url,
                             headers=headers,
                             data={'grant_type': 'client_credentials'},
                             auth=(client_id, client_secret))

    if response.status_code == 200:
        token = response.json()['access_token']
        return token
    else:
        raise Exception("Failed to get access token")

def get_saved_albums():
    load_dotenv()
    SPOTIFY_SECRET = os.getenv('SPOTIFY_SECRET')
    SPOTIFY_ID = os.getenv('SPOTIFY_ID')
    AUTH_URL = r'https://accounts.spotify.com/api/token'
    saved_albums_url = f"https://api.spotify.com/v1/users/me/albums"
    album_url_base = r'https://open.spotify.com/album/'
    USER_PROFILE_URL = r'https://api.spotify.com/v1/me'

    access_token = get_access_token_2()


    headers = {
        'Authorization': 'Bearer {token}'.format(token=access_token)
    }

    r = requests.get(USER_PROFILE_URL, headers=headers)

    saved_albums_response = requests.get(saved_albums_url, headers=headers)
    saved_albums_data = saved_albums_response.json()

    albums_list = []
    for item in saved_albums_data['items']:
        album_name = item['album']['name']
        album_artist = item['album']['artists'][0]['name']
        album_date = item['release_date']
        albums_list.append((album_name, album_artist, album_date))

    return albums_list



def spotify_data_pull_old(album):
    get_auth_url()

    load_dotenv()
    SPOTIFY_SECRET = os.getenv('SPOTIFY_SECRET')
    SPOTIFY_ID = os.getenv('SPOTIFY_ID')
    album_url_base = r'https://open.spotify.com/album/'
    AUTH_URL = r'https://accounts.spotify.com/api/token'
    album_get = 'https://api.spotify.com/v1/albums/{id}'

    if "?" in album:
        album = album[:album.find('?')]
    id = album[album.find(album_url_base)+len(album_url_base):]

    auth_response = requests.post(AUTH_URL, {
    'grant_type': 'client_credentials',
    'client_id': SPOTIFY_ID,
    'client_secret': SPOTIFY_SECRET,
    })

    auth_response_data = auth_response.json()
    access_token = auth_response_data['access_token']
    headers = {
        'Authorization': 'Bearer {token}'.format(token=access_token)
    }

    r = requests.get(album_get.format(id=id), headers=headers)
    r = r.json()
        
    tracks = []
    for i, track in enumerate(r['tracks']['items']):
        if i == 30:
            tracks.append("and more...")
            break
        tracks.append(track['name'])
    
    album_art = r['images'][0]['url']

    data = {}
    
    data.update({'album_name': r['name']})
    data.update({'album_artist': r['artists'][0]['name']})
    data.update({'record' : r['label']})
    data.update({'playtime' : get_playtime(r['tracks']['items'])})
    data.update({'tracks' : tracks})
    data.update({'album_art': album_art})
    data.update({'album_type': r['album_type']})
    data.update({'total_tracks': r['total_tracks']})
    data.update({'label_tracks': 'canciones'})
    data.update({'type': r['type']})
    data.update({'copyright': r['copyrights'][0]['text']})
    data.update({'release_date' : get_date(r['release_date'], '')})
        
    return data

def spotify_data_pull(album):
    get_auth_url()

    load_dotenv()
    SPOTIFY_SECRET = os.getenv('SPOTIFY_SECRET')
    SPOTIFY_ID = os.getenv('SPOTIFY_ID')
    album_url_base = r'https://open.spotify.com/album/'
    AUTH_URL = r'https://accounts.spotify.com/api/token'
    album_get = 'https://api.spotify.com/v1/albums/{id}'

    if "?" in album:
        album = album[:album.find('?')]
    id = album[album.find(album_url_base)+len(album_url_base):]

    auth_response = requests.post(AUTH_URL, {
    'grant_type': 'client_credentials',
    'client_id': SPOTIFY_ID,
    'client_secret': SPOTIFY_SECRET,
    })

    auth_response_data = auth_response.json()
    access_token = auth_response_data['access_token']
    headers = {
        'Authorization': 'Bearer {token}'.format(token=access_token)
    }

    r = requests.get(album_get.format(id=id), headers=headers)
    r = r.json()
    
    tracks = r['tracks']['items']
    total_tracks = r['total_tracks']
    if total_tracks > 50:
        tracks = get_all_tracks(id)

    tracks_info = []
    for i, track in enumerate(r['tracks']['items']):
        if i == 30:
            tracks_info.append("and more...")
            break
        tracks_info.append(track['name'])
    
    album_art = r['images'][0]['url']

    data = {}
    data.update({'album_name': r['name']})
    data.update({'album_artist': r['artists'][0]['name']})
    data.update({'record' : r['label']})
    data.update({'playtime' : get_playtime(tracks)})
    data.update({'tracks' : tracks_info})
    data.update({'album_art': album_art})
    data.update({'album_type': r['album_type']})
    data.update({'total_tracks': total_tracks})
    data.update({'label_tracks': 'canciones'})
    data.update({'type': r['type']})
    #data.update({'copyright': r['copyrights'][0]['text']})
    data.update({'release_date' : get_date(r['release_date'], '')})
        
    return data

def get_all_tracks(album_id):
    sp = spotipy.Spotify(auth=session.get('token'))

    results = sp.album_tracks(album_id, limit=50)
    tracks = results['items']

    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])

    return tracks




def rounded_rectangle(src, top_left, bottom_right, radius=1, color=255, thickness=1, line_type=cv2.LINE_AA):

    #  corners:
    #  p1 - p2
    #  |     |
    #  p4 - p3

    p1 = top_left
    p2 = (bottom_right[1], top_left[1])
    p3 = (bottom_right[1], bottom_right[0])
    p4 = (top_left[0], bottom_right[0])

    height = abs(bottom_right[0] - top_left[1])

    if radius > 1:
        radius = 1

    corner_radius = int(radius * (height/2))

    if thickness < 0:

        #big rect
        top_left_main_rect = (int(p1[0] + corner_radius), int(p1[1]))
        bottom_right_main_rect = (int(p3[0] - corner_radius), int(p3[1]))

        top_left_rect_left = (p1[0], p1[1] + corner_radius)
        bottom_right_rect_left = (p4[0] + corner_radius, p4[1] - corner_radius)

        top_left_rect_right = (p2[0] - corner_radius, p2[1] + corner_radius)
        bottom_right_rect_right = (p3[0], p3[1] - corner_radius)

        all_rects = [
        [top_left_main_rect, bottom_right_main_rect], 
        [top_left_rect_left, bottom_right_rect_left], 
        [top_left_rect_right, bottom_right_rect_right]]

        [cv2.rectangle(src, rect[0], rect[1], color, thickness) for rect in all_rects]

    # draw straight lines
    cv2.line(src, (p1[0] + corner_radius, p1[1]), (p2[0] - corner_radius, p2[1]), color, abs(thickness), line_type)
    cv2.line(src, (p2[0], p2[1] + corner_radius), (p3[0], p3[1] - corner_radius), color, abs(thickness), line_type)
    cv2.line(src, (p3[0] - corner_radius, p4[1]), (p4[0] + corner_radius, p3[1]), color, abs(thickness), line_type)
    cv2.line(src, (p4[0], p4[1] - corner_radius), (p1[0], p1[1] + corner_radius), color, abs(thickness), line_type)

    # draw arcs
    cv2.ellipse(src, (p1[0] + corner_radius, p1[1] + corner_radius), (corner_radius, corner_radius), 180.0, 0, 90, color ,thickness, line_type)
    cv2.ellipse(src, (p2[0] - corner_radius, p2[1] + corner_radius), (corner_radius, corner_radius), 270.0, 0, 90, color , thickness, line_type)
    cv2.ellipse(src, (p3[0] - corner_radius, p3[1] - corner_radius), (corner_radius, corner_radius), 0.0, 0, 90,   color , thickness, line_type)
    cv2.ellipse(src, (p4[0] + corner_radius, p4[1] - corner_radius), (corner_radius, corner_radius), 90.0, 0, 90,  color , thickness, line_type)

    return src


def font_scale_finder(text, scale, limit, thickness):
    for i in range(200, 50, -5):
        i = i/100
        textsize = cv2.getTextSize(text, cv2.FONT_HERSHEY_TRIPLEX, i*scale, thickness*scale)
        if textsize[0][0] <= limit*scale:
            return i

def dominant_colors(image):

    image = np.resize(image, (3*(image.shape[0])//4, 3*(image.shape[1])//4, image.shape[2]))
    ar = np.asarray(image)
    shape = ar.shape
    ar = ar.reshape(np.product(shape[:2]), shape[2]).astype(float)

    kmeans = sklearn.cluster.MiniBatchKMeans(
        n_clusters=10,
        init="k-means++",
        max_iter=20,
        random_state=1000
    ).fit(ar)
    codes = kmeans.cluster_centers_

    vecs, _dist = scipy.cluster.vq.vq(ar, codes)         # assign codes
    counts, _bins = np.histogram(vecs, len(codes))    # count occurrences

    colors = []
    for index in np.argsort(counts)[::-1]:
        colors.append([int(code) for code in codes[index]])
    return colors                    # returns colors in order of dominance


def find_process_using_file(filename):
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            for file in proc.open_files():
                if file.path == filename:
                    return proc
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            pass
    return None
