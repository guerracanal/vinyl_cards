from utils.card_generator import generator
from utils.user import login_user, get_user, print_saved_albums, get_my_albums, get_artist_albums, get_albums
from PIL import Image
import io
from base64 import b64encode
from dotenv import load_dotenv
import os
from flask import Flask, render_template, request, redirect, session, send_file
import sys

load_dotenv()

app = Flask(__name__, instance_relative_config=True)
app.config["SECRET_KEY"]=os.getenv('FLASK_SECRET')

@app.route('/')
def index():
        return render_template('mainpage.html', PageTitle="Vinyl Card Generator")


@app.route('/card', methods = ['POST', 'GET'])
def card_result():
    if request.method == 'GET':
        album_link = request.args.get('link')
        icon = request.args.get('icon')
        album = request.args.get('album')

        if album:
            album_link = r'https://open.spotify.com/album/' + album

        resolution = (5040, 3600, 3)
        card, album_name = generator(album_link, resolution, icon)
        card = Image.fromarray(card)

        card = card.resize((int(6.3/2.54*300), int(8.8/2.54*300)), resample=Image.LANCZOS)

        card_bytes = io.BytesIO()
        card.save(card_bytes, "png")
        card_bytes.seek(0)
    
        return send_file(            card_bytes,
            mimetype='image/png',
            download_name="{}_card.jpg".format(album_name),
            as_attachment=True
        )

@app.route('/login', methods = ['POST', 'GET'])
def login():
    if request.method == 'POST':
        return redirect(login_user())

@app.route('/user')
def user():
    nombre_usuario = ''
    get_user()
    if 'token' in session:
        nombre_usuario = get_user()
    return render_template('user.html', nombre_usuario=nombre_usuario)

@app.route('/my-albums', methods=['POST', 'GET'])
def my_albums():
    nombre_usuario = ''
    get_user()
    if 'token' in session:
        nombre_usuario = get_user()

    if request.method == 'GET':
        saved_albums = print_saved_albums()
        albums = []
        for album in saved_albums:
            album_dict = {}
            album_dict['album_name'] = album['album_name']
            album_dict['album_artist'] = album['album_artist']
            album_dict['album_art'] = album['album_art']
            album_dict['album_link'] = album['album_id']
            album_dict['album_date'] = album['album_date']
            album_dict['total_tracks'] = album['total_tracks']
            album_dict['playtime'] = album['playtime']
            album_dict['album_type'] = album['album_type']
            albums.append(album_dict)

        type = request.args.get('type')
        if type:
            albums = [album for album in albums if album['album_type'] == type]

        artist = request.args.get('artist')
        if artist:
            albums = [album for album in albums if album['album_artist'].lower() == artist.lower()]

        return render_template('albums.html', albums=albums, nombre_usuario=nombre_usuario)
    return render_template('albums.html')


@app.route('/<string:artist>', methods=['POST', 'GET'])
def albums_artist(artist):
    if request.method == 'GET':
        albums_result = get_albums(artist)  # variable para almacenar los resultados de get_albums()
        albums = []  # variable para almacenar los diccionarios creados dentro del bucle for
        for album in albums_result:
                       
            album_dict = {}
            album_dict['album_name'] = album['album_name']
            album_dict['album_artist'] = album['album_artist']
            album_dict['album_art'] = album['album_art']
            album_dict['album_link'] = album['album_id']
            album_dict['album_date'] = album['album_date']
            album_dict['total_tracks'] = album['total_tracks']
            album_dict['playtime'] = album['playtime']
            album_dict['album_type'] = album['album_type']
            albums.append(album_dict)
     
        type = request.args.get('type')
        if type:
            albums = [album for album in albums if album['album_type'] == type]

    return render_template('albums.html', albums=albums)



if __name__ == '__main__':
    app.run()

