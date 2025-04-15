#****************** Packages/libraries required*****************************
from flask import Flask, flash, render_template, url_for,session, request, redirect, after_this_request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
import datetime
from functools import wraps
import numpy as np
import matplotlib.pyplot as plt
import mpld3
import os
from sqlalchemy import func
from sqlalchemy import desc
import json, random
import re

#******************flask application setting********************************
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test1.sqlite3"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["SECRET_KEY"] = "superstrongkey"
db = SQLAlchemy()
#***************************Databases***************************************
#************************User class database********************************
class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable =True)
    username = db.Column(db.String(80), nullable=False)
    password_hash = db.Column(db.String(600), nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    is_creator = db.Column(db.Boolean, nullable=True)
    
    

    @property
    def password(self):
        raise AttributeError("hashed password can't be read!")
    
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def validcheck(self, password):
        return check_password_hash(self.password_hash, password)
    
#************************class Song******************************************
class Song(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(120), nullable = False)
    lyric = db.Column(db.String(1028), nullable = False)
    artist_name = db.Column(db.String(300), nullable = False)
    duration = db.Column(db.String(8), nullable = False)
    created_date = db.Column(db.DateTime, nullable = False, default=datetime.datetime.utcnow())
    album_id = db.Column(db.Integer, db.ForeignKey('album.id'))
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    genre_id = db.Column(db.Integer, db.ForeignKey('genre.id'))
    rated_value = db.Column(db.Integer, db.ForeignKey('rating.id'))
    flagged = db.Column(db.Boolean, default=False)
    
        
#*************************Class Rating*********************************************
class Rating(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    rating_given = db.Column(db.Integer, nullable = True)
    rated_song = db.Column(db.Integer, db.ForeignKey('song.id'), nullable = False)
    rated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable = False)

    # Define the relationships
    # songs = db.relationship("Song", backref="rating", lazy=True)
    # users = db.relationship("Users", backref="rating", lazy=True)

#*************************Class Artist********************************************
class Artist(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    artist_name = db.Column(db.String(80), nullable = False)
    
#*************************Class Genre*********************************************
class Genre(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable = False)
    genre_name = db.Column(db.String(60), nullable=False)
    made_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable = False)
    
    # Define the relationships
    users = db.relationship("Users", backref="genre", lazy=True)

#*************************Class GenreSong****************************************
class GenreSong(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey('song.id'), nullable=False, unique=True)
    genre_id = db.Column(db.Integer, db.ForeignKey('genre.id'), nullable=False)

    # Define the relationships
    songs = db.relationship("Song", backref="genresong", lazy=True)
    genres = db.relationship("Genre", backref="genresong", lazy=True)

#*************************Class Playlist*****************************************
class Playlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title=db.Column(db.String(80), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Define the relationship with User
    users = db.relationship("Users", backref="playlist", lazy=True)

#*************************Class PlaylistSong*****************************************
class PlaylistSong(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey('song.id'), nullable=False, unique=True)
    playlist_id = db.Column(db.Integer, db.ForeignKey('playlist.id'), nullable=False)

    # Define the relationships with Song and Playlist
    songs = db.relationship("Song", backref="playlistsong", lazy=True)
    playlists = db.relationship("Playlist", backref="playlistsong",lazy=True)

#*************************Class Album*****************************************
class Album(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable = False)
    album_title = db.Column(db.String(128), nullable=False)
    creator = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    release_date = db.Column(db.Date, nullable = False, default=datetime.datetime.utcnow())
    flagged = db.Column(db.Boolean, default=False)

    # Define the relationships
    users = db.relationship("Users", backref="album", lazy=True)
        
#*************************Class AlbumSong*****************************************
class AlbumSong(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable = False)
    song_id = db.Column(db.Integer, db.ForeignKey('song.id'), nullable = False, unique=True)
    album_id = db.Column(db.Integer, db.ForeignKey('album.id'), nullable=False)

    # Define the relationships with Song and album
    songs = db.relationship("Song", backref="albumsong", lazy=True)
    albums = db.relationship("Album", backref="albumsong",lazy=True)

#************************Creating App Context*******************************
db.init_app(app)
with app.app_context():
    db.create_all()
    admin = Users.query.filter_by(is_admin=True).first()
    if not admin:
        admin = Users(name='Administrator', username='admin', password='admin', is_admin=True, is_creator=False)
        db.session.add(admin)
        db.session.commit()

#************************User Authentication********************************
def user_auth(func):
    @wraps(func)
    def inner(*args, **kwrags):
        if 'user_id' not in session:
            return redirect(url_for('musicapp'))            
        return func(*args, **kwrags)
    return inner

#************************Creator Authentication********************************
def creator_auth(func):
    @wraps(func)
    def inner(*args, **kwrags):
        user = Users.query.get(session['user_id'])
        if 'user_id' not in session:
            flash('You are not registered, Please register first!', 'info')
            return redirect(url_for('userlogin'))
        if not user.is_creator and not user.is_admin:
            flash('You are not permitted for this login !', 'warning')
            return redirect(url_for('musicapp'))
        return func(*args, **kwrags)
    return inner

#************************Admin Authentication*******************************
def admin_auth(func):
    @wraps(func)
    def inner(*args, **kwrags):
        user = Users.query.get(session['user_id'])
        if 'user_id' not in session:
            flash('You are not registered, Please register first!', 'info')
            return redirect(url_for('apmlogin'))
        if not user.is_creator and not user.is_admin:
            flash('You are not permitted for this login !', 'warning')
            return redirect(url_for('musicapp'))
        return func(*args, **kwrags)
    return inner

#************************Setting routes*************************************
#***************************************************************************
#************************Song Search option for User************************
@app.route('/')
@user_auth
def index():
    user=Users.query.get(session['user_id'])
    songs = Song.query.filter_by(flagged=False).order_by(desc(Song.rated_value)).all()
    albums = Album.query.filter_by(flagged=False).all()
    rounded_ratings = [round(song.rated_value, 1) if song.rated_value is not None else None for song in songs]
    ratings=rounded_ratings
    if 'user_id' not in session:    
        return redirect(url_for('musicapp'))
    # session['user_id']=user.id
    if user.is_admin:
        return redirect(url_for('appmanager'))
    # if user.is_creator:
    #     return redirect(url_for('creator_dash')) 
    # Else will render to UserInterface   
    lookingfor = request.args.get('lookingfor')
    searchquery = request.args.get('searchquery')
    lookingfors = {
        'song' : 'Song Title',
        'album' : 'Album Name',
        'genre' : 'Genre Name',
        'playlist' : 'Playlist Name'
    }
    if not lookingfor or not searchquery:
        songs = Song.query.filter_by(flagged=False).order_by(desc(Song.rated_value)).all()
        albums = Album.query.filter_by(flagged=False).all()
        genres = Genre.query.all()
        playlists = Playlist.query.all()
        playlistsong = PlaylistSong.query.all()
        return render_template('index.html', user=user, genres=genres,
                               songs=songs,albums=albums, playlists=playlists,
                                 lookingfors=lookingfors, playlistsong=playlistsong,ratings=ratings)
    
    if lookingfor == 'song':
        songs = Song.query.filter(Song.title.ilike('%'+searchquery+'%')).all()
        if len(songs) > 0:
            flash('Matched songs are here', 'success')
            return render_template('index.html', user=user,
                                    songs=songs,lookingfor=lookingfor,
                                    searchquery=searchquery, lookingfors=lookingfors,ratings=ratings)
        else:
            flash(f"Oh! No song found", 'danger')
            return render_template('index.html', user=user, songs=songs,
                                   lookingfor=lookingfor, searchquery=searchquery,
                                   lookingfors=lookingfors)
    if lookingfor == 'album':
        albums = Album.query.filter(Album.album_title.ilike('%'+searchquery+'%')).all()
        if len(albums) > 0:
            flash('Matched albums are here', 'success')
            return render_template('index.html', user=user,albums=albums,
                                   lookingfor=lookingfor, searchquery=searchquery,
                                   lookingfors=lookingfors)
        else:
            flash(f"Oh! No album found", 'danger')
            return render_template('index.html', user=user, albums=albums,
                                   lookingfor=lookingfor, searchquery=searchquery,
                                   lookingfors=lookingfors)
    if lookingfor == 'playlist':
        playlists = Playlist.query.filter(Playlist.title.ilike('%'+searchquery+'%')).all()
        if len(playlists) > 0:
            flash('Matched playlists are here', 'success')
            return render_template('index.html', user=user, playlists=playlists,
                                   lookingfor=lookingfor, searchquery=searchquery,
                                     lookingfors=lookingfors)
        else:
            flash(f"Oh! No playlist found", 'danger')
            return render_template('index.html', user=user, playlists=playlists,
                                   lookingfor=lookingfor, searchquery=searchquery, 
                                   lookingfors=lookingfors)
    if lookingfor == 'genre':
        genres = Genre.query.filter(Genre.genre_name.ilike('%'+searchquery+'%')).all()
        if len(genres) > 0:
            flash('Matched genres are here', 'success')
            return render_template('index.html', user=user,genres=genres, lookingfor=lookingfor, 
                                   searchquery=searchquery, lookingfors=lookingfors)
        else:
            flash(f"Oh! No genre found", 'danger')
            return render_template('index.html', user=user, genres=genres,
                                   lookingfor=lookingfor, searchquery=searchquery, 
                                   lookingfors=lookingfors)

    genres = Genre.query.all()
    songs = Song.query.all()
    albums = Album.query.all()
    playlists = Playlist.query.all()
    return render_template('index.html', user=user,genres=genres, songs=songs,
                            playlists=playlists,albums=albums, lookingfors=lookingfors,ratings=ratings)

#************************New User Registration******************************
@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name=request.form.get("name")
        username=request.form.get("username")
        password=request.form.get("password")
        # is_creator=request.form.get("is_creator")
        if username=='' or password == '':
            flash("Username and Password can not be empty", 'info')
            return redirect(url_for('register'))
        user = Users.query.filter_by(username=username).first()
        if user:
            flash(f"'{username}' Username exists, Choose different one !", 'warning')
            return redirect(url_for('register'))
        user = Users(name=name, username=username, password=password, is_creator=False)
        db.session.add(user)
        db.session.commit()
        flash(f'Congratulations {name}! you have been registered successfully!', 'success')
        return redirect(url_for("musicapp"))
    else:
        return render_template("/user/register.html")
    
#************************Login Route***************************************
@app.route("/musicapp", methods=["GET", "POST"])
def musicapp():
    return render_template("musicapp.html")

@app.route("/login/user", methods=["GET", "POST"])
def userlogin():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = Users.query.filter_by(username=username).first()
        if not user:
            flash("Username doesn't exists! Please check username", 'warning')
            return redirect(url_for('userlogin'))
        if user.is_admin :
            flash("Ohh! You are login at normal user login", 'info')
            return redirect(url_for('userlogin'))
        if not user.validcheck(password):
            flash("Wrong Password!")
            return redirect(url_for('userlogin'))
        session['user_id'] = user.id
        return redirect(url_for('index'))
    else:
        return render_template("/user/userlogin.html")

#********************access of admin section********************************
@app.route("/login/admin", methods=["GET", "POST"])
def apmlogin():
    #=================user credential authentication===================================
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = Users.query.filter_by(username=username).first()
        #==============if not an user=================================================
        if not user:
            flash("Username doesn't exist! Please check username", 'warning')
            return redirect(url_for('apmlogin'))
        #=============validating password authentication==============================
        if not user.validcheck(password):
            flash("Please check password credentials!")
            return redirect(url_for("apmlogin"))
        flash(f'{user.name} Logged! successfully!', 'success')
        #=============storing user login in session==================================
        session['user_id'] = user.id
        return redirect(url_for('appmanager',user=user))
    else:
        return render_template("/admin/apmlogin.html")

@app.route('/appmanager', methods=['GET', 'POST'])
@admin_auth
def appmanager():
    user=Users.query.get(session['user_id'])
    # tc=total_creators
    # tnu=total normal user
    tc = Users.query.filter_by(is_admin=False, is_creator=True).count()
    tnu = Users.query.filter_by(is_admin=False, is_creator=False).count()
    tsu = Song.query.count()
    tam = Album.query.count()
    tgm = Genre.query.count()
    if not user.is_admin:
        flash(f"{user.name}, you are not authorize for this section.", 'danger')
        return redirect(url_for('index'))
    else:
        return render_template('/admin/appmanager.html', user = user, tnu=tnu, tc=tc, tam=tam, tgm=tgm, tsu=tsu)
    

@app.route('/apm_track', methods=['GET', 'POST'])
@admin_auth
def apm_track():
    user=Users.query.get(session['user_id'])
    songs = Song.query.all()
    # albums = Album.query.all()
    if 'user_id' not in session:
        flash('You are not registered, Please register first!', 'info')
        return redirect(url_for('musicapp'))

    lookingfor = request.args.get('lookingfor')
    searchquery = request.args.get('searchquery')
    lookingfors = {
        'song' : 'Song Title'
    }
    if not lookingfor or not searchquery:
        songs = Song.query.all()
        return render_template('/admin/apm_track.html', user=user, songs=songs, lookingfors=lookingfors)
    
    if lookingfor == 'song':
        songs = Song.query.filter(Song.title.ilike('%'+searchquery+'%')).all()
        if len(songs) > 0:
            flash('Matched songs are here', 'success')
            return render_template('/admin/apm_track.html', user=user,
                                    songs=songs,lookingfor=lookingfor,
                                    searchquery=searchquery, lookingfors=lookingfors)
        else:
            flash(f"Oh! No song found", 'danger')
            return render_template('/admin/apm_track.html', user=user, songs=songs,
                                   lookingfor=lookingfor, searchquery=searchquery,
                                   lookingfors=lookingfors)
    return render_template('/admin/apm_track.html', user=user, songs=songs, lookingfors=lookingfors)


@app.route('/apm_album', methods=['GET', 'POST'])
@admin_auth
def apm_album():
    user=Users.query.get(session['user_id'])
    albums = Album.query.all()
    if 'user_id' not in session:
        flash('You are not registered, Please register first!', 'info')
        return redirect(url_for('musicapp'))

    lookingfor = request.args.get('lookingfor')
    searchquery = request.args.get('searchquery')
    lookingfors = {
        'album' : 'Album Name'
    }
    if not lookingfor or not searchquery:
        albums = Album.query.all()
        return render_template('/admin/apm_album.html', user=user, albums=albums, lookingfors=lookingfors)
    
    if lookingfor == 'album':
        albums = Album.query.filter(Album.album_title.ilike('%'+searchquery+'%')).all()
        if len(albums) > 0:
            flash('Matched albums are here', 'success')
            return render_template('/admin/apm_album.html', user=user,albums=albums,
                                   lookingfor=lookingfor, searchquery=searchquery,
                                   lookingfors=lookingfors)
        else:
            flash(f"Oh! No album found", 'danger')
            return render_template('/admin/apm_album.html', user=user, albums=albums,
                                   lookingfor=lookingfor, searchquery=searchquery,
                                   lookingfors=lookingfors)

    albums = Album.query.all()
    return render_template('/admin/apm_album.html', user=user,albums=albums, lookingfors=lookingfors)
    
#********************Bar graph section******************************
@app.route('/appmanager/chart')
@admin_auth
def chart():
    import numpy as np
    import io
    import base64
    user=Users.query.get(session['user_id'])
    songs = Song.query.all()
    song_titles = [song.title for song in songs]
    print(songs)
    ratings = [song.rated_value or 0 for song in songs]  # Replace 'or 0' with a default value if needed
    print(ratings)
    song_t = np.array(song_titles)
    ratings=np.array(ratings)
    plt.bar(song_t, ratings, color='orange', alpha=0.7)
    plt.xlabel('Song Title')
    plt.ylabel('Rating')
    plt.title('Song Ratings')
    plt.ylim(0, 5)
    static_folder = 'static'
    png_filepath = os.path.join(static_folder, 'song_ratings_plot.png')
    plt.savefig(png_filepath)
    if os.path.exists(static_folder):
        os.remove(png_filepath)
    plt.savefig(png_filepath)
    plt.show()
    tc = Users.query.filter_by(is_admin=False, is_creator=True).count()
    tnu = Users.query.filter_by(is_admin=False, is_creator=False).count()
    tsu = Song.query.count()
    tam = Album.query.count()
    tgm = Genre.query.count()
    if not user.is_admin:
        flash(f"{user.name}, you are not authorize for this section.", 'danger')
        return redirect(url_for('index'))
    else:
        return render_template('/admin/appmanager.html', user = user, tnu=tnu, tc=tc, tam=tam, tgm=tgm, tsu=tsu)

#********************access of profile section******************************
@app.route('/profile', methods=['GET','POST'])
@user_auth
def profile():
    user = Users.query.get(session['user_id'])
    if request.method == 'POST':
        name = request.form.get('name')
        username = request.form.get('username')
        password = request.form.get('password')
        current_pass = request.form.get('current_pass')

#***************Check username or password input is not blank***************
        if username == '' or password == '' or current_pass == '':
            flash("Username or Password can not be empty", 'warning')
            return redirect(url_for('profile'))

#***************Check username exists in database or not********************
        if Users.query.filter_by(username=username).first() and username != user.username:
            flash(f"'{username}' Username already/not exists, please choose different", 'warning')
            return redirect(url_for('profile'))
        
#*********************Password authentication******************************
        if not user.validcheck(current_pass):
            flash(f"{name}! You enter incorrect current password!", 'warning')
            return redirect(url_for('profile'))
        
#***************If valid check OK, update the profile**********************
        user.name=name
        user.username=username
        user.password=password
        db.session.commit()
        flash('Your profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    
#***************Otherwise render existing profile**************************
    else:
        return render_template('/user/profile.html', user = Users.query.get(session['user_id']))
  
#********************Access to Creator**************************************
@app.route('/creator', methods=['GET','POST'])
@user_auth
def creator():
    user=Users.query.get(session['user_id'])
    if request.method == 'POST':
        choice = request.form.get("choice")
        if 'user_id' not in session:
            flash('You are not registered, Please register first!', 'info')
            return redirect(url_for('musicapp'))
        if choice == 'YES':
            user.is_creator=True
            db.session.commit()
            flash('Great , Now you are a creator !', 'info')
            return redirect(url_for('index'))
        else:
            flash('Great to see you here , Please come again to be creator !', 'info')
            return redirect(url_for('index'))   
    return render_template('/creator/creator_register.html', user=user)

@app.route('/creator_dash', methods=['GET','POST'])
@creator_auth
def creator_dash():
    user=Users.query.get(session['user_id'])
    songs = Song.query.filter_by(created_by=session['user_id']).filter_by(flagged=False).all()
    tsu = Song.query.filter_by(created_by=session['user_id']).count()
    tam = Album.query.filter_by(creator=session['user_id']).count()
    tgm = Genre.query.filter_by(made_by=session['user_id']).count()
    ratings = Song.query.filter_by(created_by=session['user_id']).values(Song.rated_value)
    valid_ratings = [rating[0] for rating in ratings if rating[0] is not None]
    if valid_ratings:
        a_rat = sum(valid_ratings) / len(valid_ratings)
        a_rating = round(a_rat, 2)
    else:
        a_rating = None
    genres = Genre.query.all()
    albums = Album.query.filter_by(flagged=False).all()
    artists=Artist.query.all()
    return render_template('/creator/creator_dash.html',a_rating=a_rating, user = user,tam=tam , tgm=tgm, tsu=tsu, songs=songs, genres=genres, albums=albums, artists=artists)

@app.route('/creator_dash/upload_song', methods=['GET','POST'])
@creator_auth
def upload_song():
    user=Users.query.get(session['user_id'])
    genres = Genre.query.all()
    albums = Album.query.all()
    artists=Artist.query.all()
    if request.method == "POST":
        title=request.form.get("title")
        artist_id=request.form.get("singer")
        duration=request.form.get("duration")
        lyric=request.form.get("lyric")
        song = Song.query.filter_by(title=title).first()
        if title=='' or artist_id == '' or lyric == '' or duration == '':
            flash("Please fill all the required field", 'info')
            return redirect(url_for('creator_dash'))
        if song:
            flash(f"'{title}' Title exists, Choose different one !", 'warning')
            return redirect(url_for('creator_dash')) 
        else:
            songartist = Artist.query.filter_by(id=int(artist_id)).first()
            # print(songartist)
            song = Song(title=title, artist_name=songartist.artist_name, lyric=lyric, duration=duration, artist_id=int(artist_id), created_by=session['user_id'])
            db.session.add(song)
            db.session.commit()
            flash(f'Congratulations Song {title}! added successfully!', 'success')
            return redirect(url_for("creator_dash"))
    else:
        return render_template("/creator/creator_song_upload.html",user=user,genres=genres,albums=albums,artists=artists)


@app.route('/song/<int:id>/view_lyric', methods=['GET','POST'])
def view_lyric(id):
    user=Users.query.get(session['user_id'])
    song = Song.query.get(id)
    return render_template('view_lyric.html', user = user, song=song)
    
#********************Edit Song**********************************************
@app.route('/song/edit_song/<int:id>', methods=['GET','POST'])
@creator_auth
def edit_song(id):
    user=Users.query.get(session['user_id'])
    songs = Song.query.get(id)
    genres = Genre.query.all()
    albums = Album.query.all()
    artists=Artist.query.all()
    album_id = Album.query.filter_by(id=songs.album_id).first()
    artist_id = Artist.query.filter_by(id=songs.artist_id).first()
    # print(artist_id, songs.album_id)
    genre_id = Song.query.filter_by(id=songs.genre_id).first()
    if not user.is_creator:
        flash(f"{user.name}, You are not authorize for this section.", 'danger')
        return redirect(url_for('index'))
    if request.method == 'POST':
        # all variables
        title = request.form.get('title') #songtitle
        lyric = request.form.get('lyric') #songlyric
        duration = request.form.get('duration') #songduration
        # created_date= request.form.get('created_date')
        #albumclass vairable
        album_id = request.form.get('album')
        #artistclass variable
        artist_id = request.form.get('singer')
        artists=Artist.query.filter_by(id=int(artist_id)).first()
        artist_name=artists.artist_name
        # artist_name = Artist.query.filter_by(id.artist_name=artist_id.artist_name).first()
        #genreclass variable
        genre_id = request.form.get('genre')
        #common conditional formatting for check empty value
        if title=='' or artist_name == '' or lyric == '' or duration == '':
            flash("Please fill all the required field", 'info')
            return redirect(url_for('creator_dash'))
        choice = request.form.get('choice')
        if choice == 'YES':
            songs.title = title
            songs.lyric = lyric
            songs.artist_name = artist_name
            songs.duration = duration
            songs.album_id = int(album_id)
            songs.artist_id = int(artist_id)
            songs.created_by = session['user_id']
            songs.genre_id = int(genre_id)
            db.session.add(songs)
            db.session.commit()
            flash(f'Congratulations Song {title}! updated successfully!', 'success')
            return redirect(url_for("creator_dash"))
        else:
            flash("Song not updated in database.", 'info')
            return redirect(url_for('creator_dash'))
    return render_template('/songaction/edit_song.html', user = user,songs=songs,genres=genres,albums=albums,artists=artists,album_id=album_id,artist_id=artist_id,genre_id=genre_id)

@app.route('/song/<int:id>/delete_song', methods=['GET','POST'])
@creator_auth
@admin_auth
def delete_song(id):
    user=Users.query.get(session['user_id'])
    song = Song.query.get(id)
    if request.method == 'POST':
        if not song:
            flash(f"Song doesn't exist.", 'warning')
            return redirect(url_for('creator_dash'))
        choice = request.form.get('choice')
        if choice == 'YES':
            try:         
                db.session.delete(song)
                db.session.commit()
                if user.is_admin:
                    flash("Song deleted from database.", 'success')
                    return redirect(url_for('apm_track'))
                else:
                    flash("Song deleted from database.", 'success')
                    return redirect(url_for('creator_dash'))
            except Exception as e:
                db.session.rollback()
                if user.is_admin:
                    flash(f"Song con't be deleted {e} from database.", 'success')
                    return redirect(url_for('apm_track'))
                else:
                    flash(f"Song con't be deleted {e} from database.", 'success')
                    return redirect(url_for('creator_dash'))
        else:
            if user.is_admin:
                flash("Song not deleted from database.", 'info')
                return redirect(url_for('apm_track'))
            else:
                flash("Song not deleted from database.", 'info')
                return redirect(url_for('creator_dash'))
    else:
        return render_template('/songaction/delete_song.html', user=user, song=song)

#********************Action for artist***************************************
@app.route('/artist/update_artist', methods=['GET','POST'])
@creator_auth
def update_artist():
    user=Users.query.get(session['user_id'])
    artists=Artist.query.all()
    return render_template('/artist/update_artist.html', user=user, artists=artists)

@app.route('/artist/add_artist', methods=['GET','POST'])
@creator_auth
def add_artist():
    user=Users.query.get(session['user_id'])
    artists=Artist.query.all()
    if not user.is_creator:
        flash(f"{user.name}, You are not authorize for this section.", 'danger')
        return redirect(url_for('index'))
    if request.method == 'POST':
        # all variables
        #artist class variable
        artist_name = request.form.get('singer')
        #common conditional formatting for check empty value
        if artist_name == '':
            flash("Attributes filed can't be empty.", 'warning')
            return redirect(url_for('creator_dash'))
        if Artist.query.filter_by(artist_name=artist_name).first():
            flash(f"{artist_name} name already exist, please try again", 'warning')
            return redirect(url_for('add_artist'))        
        artist = Artist(artist_name=artist_name)
        db.session.add(artist)
        db.session.commit()
        flash(f"{artist.artist_name} added successfully!", 'success')
        return redirect(url_for('update_artist'))
    return render_template('/artist/add_artist.html', user=user, artists=artists)

@app.route('/artist/edit_artist/<int:id>', methods=['GET','POST'])
@creator_auth
def edit_artist(id):
    user=Users.query.get(session['user_id'])
    artist = Artist.query.get(id)
    return "<h1>You are in edit artist data</h1>"

@app.route('/artist/delete_artist/<int:id>', methods=['GET','POST'])
@creator_auth
def delete_artist(id):
    user=Users.query.get(session['user_id'])
    artist = Artist.query.get(id)
    if request.method == 'POST':
        if not artist:
            flash(f"Artist doesn't exist.", 'warning')
            return redirect(url_for('creator_dash'))
        choice = request.form.get('choice')
        if choice == 'YES':
            db.session.delete(artist)
            db.session.commit()
            flash("Artist delete from database.", 'success')
            return redirect(url_for('creator_dash'))
        else:
            flash("Artist not deleted from database.", 'info')
            return redirect(url_for('creator_dash'))
    else:
        if not artist:
            flash(f"Artist doesn't exist.", 'warning')
            return redirect(url_for('creator_dash'))
        return render_template('/artist/delete_artist.html', user=user, artist=artist)

#********************Action for genre****************************************
@app.route('/genre/update_genre', methods=['GET','POST'])
@creator_auth
def update_genre():
    user=Users.query.get(session['user_id'])
    genres=Genre.query.all()
    return render_template('/genre/update_genre.html', user=user, genres=genres)

@app.route('/genre/add_genre', methods=['GET','POST'])
@creator_auth
def add_genre():
    user=Users.query.get(session['user_id'])
    genres=Genre.query.all()
    if not user.is_creator:
        flash(f"{user.name}, You are not authorize for this section.", 'danger')
        return redirect(url_for('index'))
    if request.method == 'POST':
        # all variables
        #album class variable
        genre_name = request.form.get('name')
        #common conditional formatting for check empty value
        if genre_name == '':
                flash("Attributes filed can't be empty.", 'warning')
                return redirect(url_for('creator_dash'))
        if Genre.query.filter_by(genre_name=genre_name).first():
                flash(f"{genre_name} name already exist, please try again", 'warning')
                return redirect(url_for('add_genre'))
        genre = Genre(genre_name=genre_name, made_by=session['user_id'])
        db.session.add(genre)
        db.session.commit()
        flash(f"{genre.genre_name} added successfully!", 'success')
        return redirect(url_for('add_genre'))       
    return render_template('/genre/add_genre.html', user=user, genres=genres)


@app.route('/genre/add_to_genre', methods=['GET','POST'])
@creator_auth
def add_to_genre():
    user=Users.query.get(session['user_id'])
    songs=Song.query.all()
    genres = Genre.query.filter_by(made_by=session['user_id']).all()
    if not user.is_creator:
        flash(f"{user.name}, You are not authorize for this section.", 'danger')
        return redirect(url_for('index'))
    if request.method == 'POST':
        selected_genre_id=int(request.form.get("selected_genre"))
        selected_songs_ids = [int(song_id) for song_id in request.form.getlist('selected_songs')]
        if not selected_songs_ids:
            flash("Please select at least one song.", 'info')
            return redirect(url_for('add_to_genre'))
        if not selected_genre_id:
            flash("Please select at least one genre.", 'info')
            return redirect(url_for('add_to_genre'))
        try:
            for song_id in selected_songs_ids:
                song = Song.query.get(song_id)
                if song.genre_id==selected_genre_id:
                    flash(f"{song.title} already in {selected_genre_id}", 'info')
                else:
                    genre_song = GenreSong(genre_id=selected_genre_id, song_id=song.id)
                    song.genre_id=selected_genre_id
                    db.session.add(genre_song)
                    db.session.commit()
                    flash("Songs added to genre successfully!", 'success')
        except Exception as e:
            flash(f"Songs not added to genre due to {e} !", 'danger')
            return redirect(url_for('add_to_genre'))
    return render_template('/genre/add_to_genre.html', user=user, genres=genres, songs=songs)

@app.route('/genre/<int:id>/edit_genre', methods=['GET','POST'])
@creator_auth
def edit_genre(id):
    user=Users.query.get(session['user_id'])
    return "<h1>You are in edit genre page</h1>"

@app.route('/genre/<int:id>/delete_genre', methods=['GET','POST'])
@creator_auth
def delete_genre(id):
    user=Users.query.get(session['user_id'])
    genre = Genre.query.get(id)
    if request.method == 'POST':
        if not genre:
            flash(f"Genre doesn't exist.", 'warning')
            return redirect(url_for('creator_dash'))
        choice = request.form.get('choice')
        if choice == 'YES':
            db.session.delete(genre)
            db.session.commit()
            flash("Genre deleted from database.", 'success')
            return redirect(url_for('creator_dash'))
        else:
            flash("Genre not deleted from database.", 'info')
            return redirect(url_for('creator_dash'))
    else:
        return render_template('/genre/delete_genre.html', user=user, genre=genre)
    

@app.route('/genre/<int:id>/viewgenre', methods=['GET','POST'])
@user_auth
def viewgenre(id):
    user=Users.query.get(session['user_id'])
    genresong=GenreSong.query.get(id)
    try:
        if genresong.genre_id is None:
            flash("Genre not found", 'info')
            return redirect(url_for('index'))
        genre_id = genresong.genre_id
        genre = Genre.query.get(id)
        genre_songs = GenreSong.query.filter_by(genre_id=genre_id).all()
        song_ids = [ps.song_id for ps in genre_songs]
        songs = Song.query.join(GenreSong).filter(GenreSong.genre_id == id).all()
        return render_template('/genre/viewgenre.html', user=user, genre=genre, song_ids=song_ids, songs=songs)
    except Exception as e:
        flash("No song assigned for genre contact creator for update database", 'info')
        return redirect(url_for('index'))
  
#********************Action for album****************************************
@app.route('/album/add_album', methods=['GET','POST'])
@creator_auth
def add_album():
    user=Users.query.get(session['user_id'])
    albums=Album.query.all()
    if not user.is_creator:
        flash(f"{user.name}, You are not authorize for this section.", 'danger')
        return redirect(url_for('index'))
    if request.method == 'POST':
        # all variables
        #album class variable
        album_title = request.form.get('title')
        #common conditional formatting for check empty value
        if album_title == '':
                flash("Attributes filed can't be empty.", 'warning')
                return redirect(url_for('creator_dash'))
        if Album.query.filter_by(album_title=album_title).first():
                flash(f"{album_title} name already exist, please try again", 'warning')
                return redirect(url_for('add_album')) 
        album = Album(album_title=album_title, creator=session['user_id'])
        db.session.add(album)
        db.session.commit()
        flash(f"{album.album_title} added successfully!", 'success')
        return redirect(url_for('add_album'))       
    return render_template('/album/add_album.html', user=user, albums=albums)

@app.route('/album/add_to_album', methods=['GET','POST'])
@creator_auth
def add_to_album():
    user=Users.query.get(session['user_id'])
    song=Song.query.all()
    albums = Album.query.filter_by(creator=session['user_id']).all()
    if not user.is_creator:
        flash(f"{user.name}, You are not authorize for this section.", 'danger')
        return redirect(url_for('index'))
    if request.method == 'POST':
        selected_album_id=int(request.form.get("selected_album"))
        selected_songs_ids = [int(song_id) for song_id in request.form.getlist('selected_songs')]
        if not selected_songs_ids:
            flash("Please select at least one song.", 'info')
            return redirect(url_for('add_to_album'))
        if not selected_album_id:
            flash("Please select at least one playlist.", 'info')
            return redirect(url_for('add_to_album'))
        try:
            for song_id in selected_songs_ids:
                # print(song_id, type(song_id))
                song = Song.query.get(song_id)
                if song.album_id==selected_album_id:
                    flash(f"{song.title} already in {selected_album_id}", 'info')
                else:
                    album_song = AlbumSong(album_id=selected_album_id, song_id=song.id)
                    song.album_id=selected_album_id
                    db.session.add(album_song)
            db.session.commit()
            flash("Songs added to album successfully!", 'success')
        except Exception as e:
            flash(f"Songs not added to album due to {e} !", 'danger')
        return redirect(url_for('add_to_album'))
        # except Exception as e:
        #     flash(f"{e} during updating database",'info')
    return render_template('/album/add_to_album.html', user=user, albums=albums, song=song) 


@app.route('/album/<int:id>/edit_album', methods=['GET','POST'])
@creator_auth
def edit_album(id):
    user=Users.query.get(session['user_id'])
    return "<h1>You are in edit album page</h1>"

@app.route('/album/<int:id>/delete_album', methods=['GET','POST'])
@creator_auth
def delete_album(id):
    user=Users.query.get(session['user_id'])
    album = Album.query.get(id)
    if request.method == 'POST':
        if not album:
            flash(f"Album doesn't exist.", 'warning')
            return redirect(url_for('creator_dash'))
        choice = request.form.get('choice')
        if choice == 'YES':
            db.session.delete(album)
            db.session.commit()
            if user.is_admin:
                flash("Album deleted from database.", 'success')
                return redirect(url_for('apm_track'))
            else:
                flash("Album deleted from database.", 'success')
                return redirect(url_for('creator_dash'))
        else:
            if user.is_admin:
                flash("Album not deleted from database.", 'info')
                return redirect(url_for('apm_track'))
            else:
                flash("Album not deleted from database.", 'info')
                return redirect(url_for('creator_dash'))
    else:
        return render_template('/album/delete_album.html', user=user, album=album)
    
@app.route('/album/update_album', methods=['GET','POST'])
@creator_auth
def update_album():
    user=Users.query.get(session['user_id'])
    albums=Album.query.all()
    return render_template('/album/update_album.html', user=user, albums=albums)

@app.route('/album/<int:id>/viewalbum', methods=['GET','POST'])
@user_auth
def viewalbum(id):
    user=Users.query.get(session['user_id'])
    albumsong=AlbumSong.query.get(id)
    try:
        if albumsong.album_id is None:
            flash("Album not found", 'info')
            return redirect(url_for('index'))
        album_id = albumsong.album_id
        album_s=Album.query.filter_by(id=album_id).first()
        if album_s is None:
            flash("Album not found", 'info')
            return redirect(url_for('index'))
        album = Album.query.get(id)
        album_songs = AlbumSong.query.filter_by(album_id=album_id).all()
        song_ids = [ps.song_id for ps in album_songs]
        songs = Song.query.join(AlbumSong).filter(AlbumSong.album_id == id).all()
        return render_template('/album/viewalbum.html', user=user, album=album, song_ids=song_ids, songs=songs)
    except Exception as e:
        flash("No song assigned for album contact creator for update database", 'info')
        return redirect(url_for('index'))

#************************Add to Playlist************************************
@app.route('/user/add_playlist', methods=['GET','POST'])
@user_auth
def add_playlist():
    user=Users.query.get(session['user_id'])
    
    if not user:
        flash(f"{user.name}, Please do register first !", 'danger')
        return redirect(url_for('index'))   
    if request.method == 'POST':
        # all variables
        #album class variable
        title = request.form.get('title')
        playlist=Playlist.query.filter_by(title=title).first()
        #common conditional formatting for check empty value
        if title == '':
                flash("Attributes filed can't be empty.", 'warning')
                return redirect(url_for('add_playlist'))
        
        if playlist:
                flash(f"Title {title} already exist, please choose different !", 'warning')
                return redirect(url_for('add_playlist')) 
        else:
            playlist=Playlist(title=title, user_id=session['user_id'])
            db.session.add(playlist)
            db.session.commit()
            flash(f"Playlist {title} added successfully!", 'success')
            return redirect(url_for('add_playlist')) 
    playlists = Playlist.query.filter_by(user_id=session['user_id']).all()
    return render_template('/user/add_playlist.html', user=user, playlists=playlists)


@app.route('/playlist/add_to_playlist', methods=['GET','POST'])
@user_auth
def add_to_playlist():
    user=Users.query.get(session['user_id'])
    song=Song.query.all()
    playlists = Playlist.query.filter_by(user_id=session['user_id']).all()
    if request.method == 'POST':
        selected_playlist_id=request.form.get("selected_playlist")
        selected_songs_ids = [int(song_id) for song_id in request.form.getlist('selected_songs')]
        if not selected_songs_ids:
            flash("Please select at least one song.", 'info')
            return redirect(url_for('add_to_playlist'))
        if not selected_playlist_id:
            flash("Please select at least one playlist.", 'info')
            return redirect(url_for('add_to_playlist'))
        playlist = Playlist.query.get(selected_playlist_id)
        if playlist:
            for song_id in selected_songs_ids:
                song = Song.query.get(song_id)
                if song:
                    playlist_song = PlaylistSong(playlist_id=playlist.id, song_id=song.id)
                    db.session.add(playlist_song)
            db.session.commit()
            flash("Songs added to playlist successfully!", 'success')
            return redirect(url_for('add_to_playlist'))
    return render_template('/user/add_to_playlist.html', user=user, playlists=playlists, song=song)



@app.route('/playlist/<int:id>/tracks', methods=['GET','POST'])
@user_auth
def viewtracks(id):
    user=Users.query.get(session['user_id'])
    playlistsong=PlaylistSong.query.get(id)
    try:
        playlist_id = playlistsong.playlist_id
        playlist_s=Playlist.query.filter_by(id=playlist_id).first()
        if playlist_s is None:
            flash("Playlist not found", 'danger')
            return redirect(url_for('index'))
        playlist_songs = PlaylistSong.query.filter_by(playlist_id=id).all()
        song_ids = [ps.song_id for ps in playlist_songs]
        songs = Song.query.filter(Song.id.in_(song_ids)).all()
        return render_template('/user/viewtracks.html', user=user, playlist_title=playlist_s.title,song_ids=song_ids, songs=songs)
    except Exception as e:
        flash("No song assigned for playlist, first assign songs to playlist", 'info')
        return redirect(url_for('index'))
#************************User Rating****************************************
@app.route('/song_rating/<int:id>', methods=['POST'])
@user_auth
def song_rating(id):
    user=Users.query.get(session['user_id'])
    song=Song.query.get(id)
    try:
        if request.method == 'POST':
            existing_rating = Rating.query.filter_by(rated_song=id, rated_by=user.id).first()
            if existing_rating:
                flash(f"You have already rated this song.", 'warning')
            else:
                user_rating=int(request.form.get('rating'))
                if 0<= user_rating <=5:                
                    ratings = Rating.query.filter_by(rated_song=id).all()
                    total_ratings = len(ratings)
                    # print(type(total_ratings))
                    current_average = song.rated_value or 0
                    new_average = ((current_average * total_ratings) + user_rating) / (total_ratings + 1)
                    song.rated_value = new_average
                    # print(song.rated_value)
                    new_rating = Rating(rating_given=user_rating, rated_song=song.id, rated_by=user.id)
                    db.session.add(new_rating)
                    db.session.commit()
                    flash(f"Rating submitted successfully for {song.title}", 'success')
    except Exception as e:
            flash(f"{e} during updating database",'info')
    return redirect(url_for('view_lyric',id=song.id,user=user,))

#************************Flag****************************************
@app.route('/apm_track/flag/<int:id>', methods=['GET','POST'])
@admin_auth
def flag(id):
    song = Song.query.get(id)
    if request.method == 'POST':
        choice = request.form.get('choice')
        if choice == 'Block':
            song.flagged = True
            db.session.commit()
            flash('Song flagged successfully!', 'success')
        else:
            song.flagged = False
            db.session.commit()
            flash('Song flag removed', 'warning')
        return redirect(url_for('apm_track'))
    return render_template('/admin/apm_flag.html', song=song)

@app.route('/apm_track/flag1/<int:id>', methods=['GET','POST'])
@admin_auth
def flag1(id):
    album = Album.query.get(id)
    if request.method == 'POST':
        choice = request.form.get('choice')
        if choice == 'Block':
            album.flagged = True
            db.session.commit()
            flash('Album flagged successfully!', 'success')
        else:
            album.flagged = False
            db.session.commit()
            flash('Album flag removed !', 'warning')
        return redirect(url_for('apm_album'))
    return render_template('/admin/apm_flag1.html', album=album)


#************************User Logout****************************************
@app.route("/logout")
@user_auth
def logout():
    session.pop('user_id', None)
    flash('Logged out! Login to continue.', 'success')
    return redirect(url_for("musicapp"))
#************************Instance*******************************************
if __name__ == "__main__":
    app.run(debug=True)