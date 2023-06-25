import json
import os
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import JSONB
load_dotenv()

app = Flask(__name__)
#app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:admin@localhost/pixel_art'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
db = SQLAlchemy(app)

class Artist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(50))
    username = db.Column(db.String(50), default="")
    username_unfinished = db.Column(db.String(50), default="")
    unicode_string = db.Column(db.String(50), default="")

    registration_time = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    pixel_canvas_256 = db.Column(Text, default=json.dumps([0] * 256))

    pixel_arts = db.relationship('PixelArt', backref='artist')

    def __init__(self, ip_address):
        self.ip_address = ip_address

    

class PixelArt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), default="")
    creation_date = db.Column(db.DateTime, default=datetime.utcnow)
    pixel_canvas_256 = db.Column(Text)

    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'))

    def __init__(self, username, pixel_canvas_256, artist_id):
        self.username = username
        self.pixel_canvas_256 = pixel_canvas_256
        self.artist_id = artist_id

    def creation_date_formatted(self):
        return self.creation_date.strftime('%d-%m-%Y')





def remove_ip_addresses():
    time_threshold = datetime.utcnow() - timedelta(minutes=30)
    users_to_update = Artist.query.filter(Artist.last_seen <= time_threshold).all()

    for user in users_to_update:
        user.ip_address = ""
    db.session.commit()

def create_account():
    ip_address = get_ip()
    user = Artist(ip_address)
    db.session.add(user)
    db.session.commit()

def reset_account(user):
    db.session.delete(user)
    db.session.commit()
    create_account()

def get_ip():
    ip_addresses = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')
    ip_address = ip_addresses[0].strip()
    return ip_address

def get_user():
    ip_address = get_ip()
    user = Artist.query.filter_by(ip_address=ip_address).first()
    return user

def get_username_list():
    users = Artist.query.filter(Artist.username != "").order_by(Artist.registration_time.desc()).all()
    username_list = ",".join(user.username for user in users)
    return username_list

def letter_to_name(user, letter):
    user.username_unfinished += letter
    db.session.commit()

def get_info_as_json():
    users = Artist.query.filter(Artist.username != "").order_by(Artist.registration_time.desc()).all()
    usernames = ",".join(user.username for user in users)
    ids = ",".join(str(user.id) for user in users)

    data = {
        "usernames": usernames,
        "ids": ids,
    }

    return jsonify(data)

def unicode_to_name(user):
    unicode_string = user.unicode_string
    if(len(unicode_string) > 3):
        try:
            unicode_value = int(unicode_string, 16)
            unicode_char = str(chr(unicode_value))
            print(unicode_char)
            user.username_unfinished += unicode_char
            user.unicode_string = ""
            db.session.commit()
        except:
            print("ERROR")
            pass

def update_last_seen(user):
    user.last_seen = datetime.utcnow()
    db.session.commit()

def clean_junk(user):
    user.unicode_string = ""
    user.username_unfinished = ""
    db.session.commit()

def fill_pixel(canvas_data, width, height, number, target_color, replacement_color):
    stack = [(number % width, number // width)]

    while stack:
        x, y = stack.pop()

        if canvas_data[y * width + x] == target_color:
            canvas_data[y * width + x] = replacement_color

            if x > 0:
                stack.append((x - 1, y))  # Check left pixel
            if x < width - 1:
                stack.append((x + 1, y))  # Check right pixel
            if y > 0:
                stack.append((x, y - 1))  # Check top pixel
            if y < height - 1:
                stack.append((x, y + 1))  # Check bottom pixel

    return canvas_data

def get_pixel_arts_as_json():
    pixel_arts = PixelArt.query.order_by(PixelArt.creation_date.asc()).all()
    canvases = ";".join(json.dumps(pixel_art.pixel_canvas_256) for pixel_art in pixel_arts)
    usernames = ",".join(str(pixel_art.username) for pixel_art in pixel_arts)
    creation_dates = ",".join(str(pixel_art.creation_date_formatted()) for pixel_art in pixel_arts)


    data = {
        "canvases": canvases,
        "usernames": usernames,
        "creation_dates": creation_dates,
    }

    return jsonify(data)

@app.route("/publish_pixel_art")
def route_publish_pixel_art():
    user = get_user()
    if(user is None): return "Not registered"
    pixel_art = PixelArt(username=user.username, pixel_canvas_256=user.pixel_canvas_256, artist_id=user.id)
    user.pixel_arts.append(pixel_art)
    db.session.add(pixel_art)
    user.pixel_canvas_256 = json.dumps([0] * 256)
    db.session.commit()

    return jsonify(pixel_art.pixel_canvas_256)

@app.route("/pixel/fill/<int:number>/<int:color>")
def route_fill_pixel(number, color):
    user = get_user()
    if(user is None): return "Not registered"

    width = 16
    height = 16
    canvas_data = json.loads(user.pixel_canvas_256)

    target_color = canvas_data[number]
    replacement_color = color

    if target_color == replacement_color:
        return jsonify(user.pixel_canvas_256)  # No need to fill if colors are the same

    filled_canvas_data = fill_pixel(canvas_data, width, height, number, target_color, replacement_color)

    user.pixel_canvas_256 = json.dumps(filled_canvas_data)
    db.session.commit()

    return jsonify(user.pixel_canvas_256)


@app.route("/pixel/<int:number>/<int:color>")
def route_change_pixel(number, color):
    user = get_user()
    if(user is None): return "Not registered"

    canvas_data = json.loads(user.pixel_canvas_256)
    canvas_data[number] = color
    user.pixel_canvas_256 = json.dumps(canvas_data)
    db.session.commit()
    return jsonify(user.pixel_canvas_256)


@app.route("/reset_canvas")
def route_reset_canvas():
    user = get_user()
    if(user is None): return "Not registered"

    user.pixel_canvas_256 = json.dumps([0] * 256)
    db.session.commit()
    return  user.pixel_canvas_256


@app.route("/get_my_canvas_data")
def get_my_canvas_data():
    user = get_user()
    if(user is None): return json.dumps([0] * 256)
    return  user.pixel_canvas_256

@app.route("/get_pixel_arts")
def get_pixel_arts():
    return get_pixel_arts_as_json()

@app.route("/get_data")
def get_data():
    remove_ip_addresses()
    user = get_user()
    if(user is not None):
        update_last_seen(user)
    return get_info_as_json()

@app.route("/login_as/<number>")
def login_as(number):
    ip_address = get_ip()
    user = Artist.query.filter(Artist.id == int(number)).first()
    if(user is None): return "Not registered"
    user.ip_address = ip_address
    db.session.commit()
    update_last_seen(user)
    return "Logged in as: " + user.username

@app.route("/login")
def login():
    user = get_user()
    if user is None:
        create_account()
    elif user.username == "":
        reset_account(user)
    else:
        update_last_seen(user)
        clean_junk(user)
        #login


    return get_info_as_json()


@app.route("/unicode/start/<letter>")
def start(letter):
    user = get_user()
    if(user is None): return "Not registered"
    unicode_to_name(user)
    user.unicode_string = letter
    db.session.commit()

    return "Current username: " + user.username_unfinished


@app.route("/unicode/continue/<letter>")
def continue_string(letter):
    user = get_user()
    if(user is None): return "Not registered"

    user.unicode_string += letter
    db.session.commit()

    return "Current string: " + user.unicode_string

@app.route("/letter/<letter>")
def add_letter(letter):
    user = get_user()
    if(user is None): return "Not registered"
    unicode_to_name(user)
    letter_to_name(user, letter)
    return "Current string: " + user.unicode_string


@app.route("/finish_username")
def finish_username():
    user = get_user()
    if(user is None): return "Not registered"
    unicode_to_name(user)
    user.username = user.username_unfinished
    user.username_unfinished = ""
    db.session.commit()
    update_last_seen(user)

    return "Account created: " + user.username


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run()