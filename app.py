from utils.card_generator import generator
from utils.user import login_user, get_user, print_saved_albums
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
        album_link = request.args.get('album')
        icon = request.args.get('icon')

        if icon:
            print("icon: " + icon)
        else:
            print("icon no definido")
            
        if album_link:
            print("album: " + album_link)
        else:
            print("album no definido")


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

@app.route('/albums', methods=['POST', 'GET'])
def albums():
    nombre_usuario = ''
    get_user()
    if 'token' in session:
        nombre_usuario = get_user()
    if request.method == 'POST':
        saved_albums = print_saved_albums()
        albums = []
        for album in saved_albums:
            album_dict = {}
            album_dict['album_name'] = album['album_name']
            album_dict['album_artist'] = album['album_artist']
            album_dict['album_art'] = album['album_art']
            album_dict['album_link'] = album['album_link']
            album_dict['album_date'] = album['album_date']
            albums.append(album_dict)
        return render_template('albums.html', albums=albums, nombre_usuario=nombre_usuario)
    return render_template('albums.html')

if __name__ == '__main__':
    app.run(debug=True)