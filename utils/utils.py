
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
from spotipy.oauth2 import SpotifyOAuth
import spotipy
from flask import Flask, render_template, request, redirect, session
import psutil


def get_albums():
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
            album = {}
            album['album_name'] = item['album']['name']
            album['album_artist'] = item['album']['artists'][0]['name']
            album['album_link'] = item['album']['external_urls']['spotify']
            album['album_art'] = item['album']['images'][0]['url']

            albums.append(album)
        offset += limit
    return albums


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
    print(auth_url)
    return auth_url

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
        albums_list.append((album_name, album_artist))

    return albums_list



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

    print(album)
    print(id)

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

    playtime = 0
    for i in r['tracks']['items']:
        playtime += i['duration_ms']

    playtime = str(datetime.timedelta(seconds=playtime//1000))
    if playtime[0] == '0':
        playtime = playtime[2:]
    
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
    data.update({'playtime' : playtime})
    data.update({'tracks' : tracks})
    data.update({'album_art': album_art})
    data.update({'album_type': r['album_type']})
    data.update({'total_tracks': r['total_tracks']})
    data.update({'type': r['type']})
    data.update({'copyright': r['copyrights'][0]['text']})
    try:
        data.update({'release_date' : datetime.datetime.strptime(r['release_date'].replace('-',''), r'%Y%m%d').strftime(r'%B %d, %Y')})
    except ValueError:
        data.update({'release_date' : r['release_date']})
    return data

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
    print(text)
    for i in range(200, 50, -5):
        i = i/100
        textsize = cv2.getTextSize(text, cv2.FONT_HERSHEY_TRIPLEX, i*scale, thickness*scale)
        print(textsize[0][0])
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
