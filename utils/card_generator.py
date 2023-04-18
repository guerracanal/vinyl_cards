import numpy as np
from PIL import Image, ImageFont, ImageDraw, ImageOps
import cv2
from skimage import io as skio
from utils.utils import *
import requests
from unidecode import unidecode
import tempfile
import time
import psutil
from io import BytesIO


card = None

def generator(album, resolution, icon):
    global card  # declare card as a global variable

    data = spotify_data_pull(album)
    
    # spacing: Píxeles de separación entre los diferentes elementos que se van a colocar en la carta
    spacing = 100
    # y_position: La posición vertical actual en la que estamos situando los diferentes elementos en el cartel
    y_position = 2*spacing

    # crea una matriz con la resolución indicada
    card = np.ones(resolution, np.uint8)
    card = card*255

    if icon is not None:
        print(icon)
        icon_image = add_icon_key(icon, resolution, spacing)
    else:
        icon_image = None
        
    # Crear y posicionar el arte del album
    album_art = pil_process_album_art(data, resolution, spacing)
    add_album_art_to_card(album_art, resolution, spacing)
    
    # update y position for next element
    y_position += album_art.shape[0] + 3*spacing
    
    print('y_position: ' + str(y_position))
    
    text_box_position = 4000
    add_horizontal_line(album_art.shape[0], text_box_position - 4*spacing, album_art)

    y_position = text_box_position

    album_name = process_text(data['album_name'])
    print(album_name)
    add_title_to_card(album_name, resolution, y_position, spacing)
    
    # update y position for next element
    y_position += 3*spacing
    
    text = data['album_artist']
    add_subtitle_to_card(text, resolution, y_position, spacing)

    # update y position for next element
    y_position += 2*spacing
    
    text =  data['release_date'] + ' - ' + str(data['total_tracks']) + ' tracks  (' +  data['playtime'] + ')'
    add_details_to_card(text, resolution, y_position, spacing)
    
    # update y position for next element
    y_position += spacing
    
    # add border to card with colors of album art
    add_border_to_card(album_art)
    
    # update y position for next element
    y_position += 1*spacing
    
    #add_tracks_album_to_card(card, resolution, y_position, spacing)
    #logo = add_spotify_logo(card, resolution, spacing)
    spotify_code = add_spotify_code(album, resolution, spacing)
    
    #add_label(data['record'] + ' - ' + data['album_type'] + ' ', (spacing, resolution[0]-163))
    #add_label(data['release_date'] + ' (' + data['copyright'] + ')' , (spacing, resolution[0]-spacing))
    
    card = cv2.cvtColor(card, cv2.COLOR_BGR2RGB)

    return(card, album_name)

def pil_process_album_art(data, resolution, spacing):
    global card  # declare card as a global variable
    
    # Download the image directly to memory using BytesIO
    response = requests.get(data['album_art'])
    image = Image.open(BytesIO(response.content))

    # Convert to OpenCV format
    album_art = np.array(image.convert('RGB'))
    album_art = cv2.cvtColor(album_art, cv2.COLOR_RGB2BGR)

    scale_factor = 5.4  # reduce image size by 50%
    album_art = cv2.resize(album_art, (0,0), fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_AREA)

    mask = np.zeros((album_art.shape[0], album_art.shape[1]), np.uint8)
    mask = rounded_rectangle(mask, (0,0), (album_art.shape[0], album_art.shape[1]), 0, color=(255,255,255), thickness=-1)

    art_inv = cv2.bitwise_not(album_art)
    album_art = cv2.bitwise_not(cv2.bitwise_and(art_inv, art_inv, mask=mask))

    return album_art

def process_album_art(data, resolution, spacing):
    global card  # declare card as a global variable

    with tempfile.NamedTemporaryFile(delete=False) as f:
        response = requests.get(data['album_art'])
        f.write(response.content)
        temp_file_name = f.name

    f = open(temp_file_name, 'wb')
    f.write(response.content)
    f.close()

    # Cambiar el nombre del archivo temporal
    os.rename(temp_file_name, temp_file_name + '.png')

    album_art = io.imread(temp_file_name + '.png')

    scale_factor = 5.4  # reduce image size by 50%
    album_art = cv2.resize(album_art, (0,0), fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_AREA)
    album_art = cv2.cvtColor(album_art, cv2.COLOR_RGB2BGR)

    mask = np.zeros((album_art.shape[0], album_art.shape[1]), np.uint8)
    mask = rounded_rectangle(mask, (0,0), (album_art.shape[0], album_art.shape[1]), 0, color=(255,255,255), thickness=-1)

    art_inv = cv2.bitwise_not(album_art)
    album_art = cv2.bitwise_not(cv2.bitwise_and(art_inv, art_inv, mask=mask))


    # Eliminar archivo temporal
    os.unlink(temp_file_name + '.png')

    # Cerrar archivo
    f.close()

    return album_art

def add_album_art_to_card(album_art, resolution, spacing):
    global card  # declare card as a global variable

    # calculate x offset to center image horizontally
    x_offset = int((resolution[1] - album_art.shape[1]) / 2)
    y_offset = spacing
    # set image in card
    card[y_offset:y_offset+album_art.shape[0], x_offset:x_offset+album_art.shape[1]] = album_art

def get_font_scale(text, resolution, spacing, font_scale_factor, thickness):
    
    for i in range(2*spacing, 50, -5):
        i = i/100
        textsize = cv2.getTextSize(text, cv2.FONT_HERSHEY_COMPLEX, i*font_scale_factor, thickness)
        if textsize[0][0] <= (resolution[1]-2*spacing):
            font_scale = i*font_scale_factor
            return (font_scale, textsize)
    return (0, ((0, 0), 0))

def add_title_to_card(text, resolution, y_position, spacing):
    global card  # declare card as a global variable
    font_scale = 0
    font_scale_factor = 5
    thickness = 15
    font_scale, textsize = get_font_scale(text, resolution, spacing, font_scale_factor, thickness)

    print('title:' + str(font_scale))    
    # Calculate x position to center text horizontally
    text_width = textsize[0][0]
    x_position = int((resolution[1] - text_width) / 2)

    cv2.putText(card, text, (x_position, y_position), cv2.FONT_HERSHEY_COMPLEX, font_scale, (0,0,0), thickness)

def add_subtitle_to_card(text, resolution, y_position, spacing):
    global card  # declare card as a global variable
    font_scale = 0
    font_scale_factor = 3
    thickness = 10

    font_scale, textsize = get_font_scale(text, resolution, spacing, font_scale_factor, thickness)

    print('subtitle:' + str(font_scale))
    # Calculate x position to center text horizontally
    text_width = textsize[0][0]
    x_position = int((resolution[1] - text_width) / 2)          

    cv2.putText(card, text, (x_position, y_position), cv2.FONT_HERSHEY_COMPLEX, font_scale, (0,0,0), thickness)

def add_details_to_card(text, resolution, y_position, spacing):
    global card  # declare card as a global variable
    font_scale = 0
    font_scale_factor = 5
    thickness = 2

    font_scale, textsize = get_font_scale(text, resolution, spacing, font_scale_factor, thickness)

    print('details:' + str(font_scale))

    text_width = textsize[0][0]
    x_position = int((resolution[1] - text_width) / 2)  # calculate x position to center text horizontally

    cv2.putText(card, text, (x_position, y_position), cv2.FONT_HERSHEY_COMPLEX, font_scale, (0,0,0), thickness)


def add_horizontal_line(y_start, y_end, album_art):
    global card  # declare card as a global variable
    
    palette = dominant_colors(album_art)
    num_colors = len(palette)
    # add horizontal line to card
    line_height = y_end - y_start
    horizontal_line = np.zeros((line_height, card.shape[1], 3), np.uint8)
    #cv2.rectangle(horizontal_line, (0, 0), (card.shape[1], thickness), color, -1)
    for i in range(num_colors):

        section_width = int(card.shape[1] / num_colors)
        x_start = section_width * i
        x_end = x_start + section_width
        cv2.rectangle(horizontal_line, (x_start, 0), (x_end, line_height), palette[i], -1)
    
    alpha = 0.3  # define alpha value between 0 (fully transparent) and 1 (fully opaque)
    beta = 1 - alpha  # calculate beta value

    # modify opacity of the rectangle
    horizontal_line = cv2.addWeighted(horizontal_line, alpha, np.ones(horizontal_line.shape, dtype=np.uint8) * 255, beta, 0, horizontal_line)

    card[y_start:y_end, :] = horizontal_line


def add_border_to_card(album_art):
    global card  # declare card as a global variable
    palette = dominant_colors(album_art)

    num_colors = len(palette)
    color_palette = np.ones((5, num_colors*100, 3), np.uint8)
    for i in range(num_colors):
        section = 100*(i+1)
        cv2.rectangle(color_palette, (section-100,0), (section, 100), palette[i], -1)

    # add color border to card
    border_width = 100
    border_height = card.shape[0] - 2 * border_width

    # left border
    left_border = np.zeros((border_height, border_width, 3), np.uint8)
    for i in range(num_colors):
        section = int(border_height / num_colors) * i
        cv2.rectangle(left_border, (0, section), (border_width, section + int(border_height / num_colors)), palette[i], -1)

    # right border
    right_border = np.zeros((border_height, border_width, 3), np.uint8)
    for i in range(num_colors):
        section = int(border_height / num_colors) * i
        cv2.rectangle(right_border, (0, section), (border_width, section + int(border_height / num_colors)), palette[i], -1)

    # top border
    top_border = np.zeros((border_width, card.shape[1], 3), np.uint8)
    for i in range(num_colors):
        section = int(card.shape[1] / num_colors) * i
        cv2.rectangle(top_border, (section, 0), (section + int(card.shape[1] / num_colors), border_width), palette[i], -1)

    # bottom border
    bottom_border = np.zeros((border_width, card.shape[1], 3), np.uint8)
    for i in range(num_colors):
        section = int(card.shape[1] / num_colors) * i
        cv2.rectangle(bottom_border, (section, 0), (section + int(card.shape[1] / num_colors), border_width), palette[i], -1)

    # add borders to card
    card[border_width:card.shape[0]-border_width, 0:border_width] = left_border
    card[border_width:card.shape[0]-border_width, card.shape[1]-border_width:card.shape[1]] = right_border
    card[0:border_width, :] = top_border
    card[card.shape[0]-border_width:card.shape[0], :] = bottom_border

def add_spotify_code(album, resolution, spacing):
    global card  # declare card as a global variable

    album_url_base = r'https://open.spotify.com/album/'
    if "?" in album:
        album = album[:album.find('?')]
    id = album[album.find(album_url_base)+len(album_url_base):]

    # https://scannables.scdn.co/uri/plain/[format]/[background-color-in-hex]/[code-color-in-text]/[size]/[spotify-URI]
    url = 'https://scannables.scdn.co/uri/plain/png/ffffff/black/640/spotify:album:' + id

    response = requests.get(url)
    img_array = np.array(bytearray(response.content), dtype=np.uint8)

    creditslogo = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    height, width, channels = creditslogo.shape
    scale = 2.5
    new_width = int(width * scale)
    new_height = int(height * scale)

    creditslogo = cv2.resize(creditslogo, (new_width, new_height), fx=scale, fy=scale)
    #logo_x = resolution[1] - spacing - creditslogo.shape[1] # left position
    logo_x = resolution[1] - spacing - creditslogo.shape[1] - int((resolution[1] - 2*spacing - creditslogo.shape[1])/2) # center position

    card[resolution[0]-spacing-creditslogo.shape[0]:resolution[0]-spacing, logo_x:logo_x+creditslogo.shape[1]] = creditslogo
    
    return logo_x
    
def add_icon(image_file, right_logo, resolution, spacing):
    global card  # declare card as a global variable

    image = cv2.imread(image_file)
    image = cv2.resize(image, (200, 200))  # replace with desired size
    image_x = right_logo - spacing - image.shape[1]
    card[resolution[0]-spacing-image.shape[0]:resolution[0]-spacing, image_x:image_x+image.shape[1]] = image
    
    return image_x

def add_icon_key(image_file, resolution, spacing):
    global card  # declare card as a global variable

    image = cv2.imread("static/images/" + image_file)
    image = cv2.resize(image, (400, 400))  # replace with desired size
    
    image_x = resolution[1] - spacing - image.shape[1]
    image_y = resolution[0] - spacing - image.shape[0]

    # add the image to the bottom right corner of the card
    card[image_y:image_y+image.shape[0], image_x:image_x+image.shape[1]] = image
    
    return image_x
    

def add_label(text, position):
    global card  # declare card as a global variable

    cv2.putText(card, text, position, cv2.FONT_HERSHEY_PLAIN, 3.5, (0,0,0), 5)

import re

def remove_additions(text):
    additions = ["Deluxe Edition", "Deluxe", "Remastered", "\d{4} Remaster", "Super Deluxe", "Collector's Edition", "Anniversary Edition", "Special Edition", "Limited Edition", "Extended Version", "Bonus Tracks", "Live Album", "Original Soundtrack", "Original Motion Picture Soundtrack"]
    regex_list = []
    for addition in additions:
        # Create regex patterns for each possible addition
        regex = re.compile(r"\s*" + addition + r"(?![a-zA-Z0-9])|\s*\(" + addition + r"\)\s*|\s*-" + addition + r"(?![a-zA-Z0-9])\s*|\s*\(\d{4} Version\)\s*|", re.IGNORECASE)
        text = re.sub(regex, '', text)
        regex_list.append(regex)
        
    # Apply regex patterns to remove any matches from the text
    for regex in regex_list:
        text = regex.sub("", text)

    text = bytes(text, 'utf-8').decode('unicode_escape')
    text = remove_special_characters(text)    
    return text

import re

def remove_special_characters(text):
    # Eliminar caracteres especiales con expresiones regulares
    text = unidecode(text)

    pattern = r'[^a-zA-z0-9\s]'
    text = re.sub(pattern, '', text)
    
    return text

def process_text(text):
    print(text)
    text = text.encode('unicode_escape').decode('utf-8')
    text = remove_additions(text)
    print(text)
    if len(text) > 40:
        print(len(text))
        return text[:40] + "..."
    return text

if __name__ == '__main__':

    album = input("Enter Spotify Album link: ")
    if album == '':
        album = 'https://open.spotify.com/album/6D9urpsOWWKtYvF6PaorGE?si=-vOP9zWNQK6Mfq55f3o4kw'
    if album.find('https://open.spotify.com/album/') == -1:
        print("Enter valid Spotify album link.")
        exit(1)

    resolution = ''
    #resolution = input("Enter height, width in pixels: ")
    if resolution == '':
        # resolution = (5100, 3300, 3)
        resolution = (5040, 3600, 3)
    else:
        resolution = list(map(int, resolution.strip().split(',')))
        resolution.append(3)

    card, album_name = generator(album, resolution)

    album_name = remove_special_characters(album_name)

    card = cv2.cvtColor(card, cv2.COLOR_RGB2BGR)

    cv2.imwrite("{}_card.jpg".format(album_name), card)

    Image.open("{}_card.jpg".format(album_name)).show()
 