from utils.utils import *

def get_user():
    return get_user_spotify()

def login_user():
    return login_spotify()

def print_saved_albums():
    saved_albums = get_my_albums()       
    return saved_albums
