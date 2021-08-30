#----------------------------------------------------------------------------#
# Imports
from flask_migrate import Migrate
import sys

#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

SQLALCHEMY_DATABASE_URI = 'postgresql://wejdan:a@localhost:5432/fyyurapp'


#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String()))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    talent= db.Column(db.Boolean, default=False)
    description = db.Column(db.String(120))
    shows = db.relationship('Show', backref='Venue', lazy='dynamic')
    
    def __repr__(self):
        return f'<Venue {self.id} {self.name}>'


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    state = db.Column(db.String(120))  
    genres = db.Column(db.ARRAY(db.String()))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    venue = db.Column(db.Boolean, default=False)
    description = db.Column(db.String(120))
    shows = db.relationship('Show', backref='Artist', lazy='dynamic')

    def __repr__(self):
        return f'<Artist {self.id} {self.name}>'


class Show(db.Model):

    __tablename__ = 'Show'
    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey(
        'Artist.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f'<Show {self.id}, Artist {self.artist_id}, Venue {self.venue_id}>'
    
#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    venues = Venue.query.all()
    data_venues = []
    areas = set() 
    current_date = datetime.now()
  
    for venue in venues:
      areas.add((venue.city, venue.state))

    for a in areas:
      data_venues.append({
        "city": a[0],
        "state": a[1],
        "venues": []
    })

    for venue in venues:
      number = 0

      shows = Show.query.filter_by(venue_id=venue.id).all()


      for show in shows:
        if show.start_time > current_date:
            number = number + 1 

      for venue_area in data_venues:
        if venue.state == venue_area['state'] and venue.city == venue_area['city']:
          venue_area['venues'].append({
            "id": venue.id,
            "name": venue.name,
            "num_upcoming_shows": number
        })
    return render_template('pages/venues.html', areas=data_venues)

@app.route('/venues/search', methods=['POST'])
def search_venues():
    
    search = request.form.get('search_term', '')
    venues_search = Venue.query.filter(Venue.name.ilike(f'%{search}%'))

    response = {
        "count": venues_search.count(),
        "data": venues_search
    }

     
    return render_template('pages/search_venues.html', results=response, search_term=search)


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
   
    venue = Venue.query.filter_by(id=venue_id).first()
    shows = Show.query.filter_by(venue_id=venue_id).all()
    upcoming_count = 0 
    past_count = 0
    upcoming_show = []  
    past_show = []
    current_date = datetime.now()
  
      
    for show in shows:
            if show.start_time < current_date:
                past_show.append({
                    "artist_id": show.artist_id,
                    "artist_name": Artist.query.filter_by(id=show.artist_id).first().name,
                    "start_time": format_datetime(str(show.start_time)),
                    "artist_image_link": Artist.query.filter_by(id=show.artist_id).first().image_link
                })
                past_count = past_count + 1
        
    for show in shows:
            if show.start_time > current_date:
                upcoming_show.append({
                    "artist_id": show.artist_id,
                    "artist_name": Artist.query.filter_by(id=show.artist_id).first().name,
                    "start_time": format_datetime(str(show.start_time)),
                    "artist_image_link": Artist.query.filter_by(id=show.artist_id).first().image_link
                })
                upcoming_count = upcoming_count + 1 
        
    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website_link": venue.website_link,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.talent,
        "seeking_description": venue.description,
        "image_link": venue.image_link,
        "past_shows": past_show,
        "upcoming_shows": upcoming_show,
        "past_shows_count": past_count,
        "upcoming_shows_count": upcoming_count
    }

    # return template with venue data
    return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
       error = False
       try:
         

        form = VenueForm()
        name = request.form["name"]
        city = form.city.data
        address = form.address.data
        state = form.state.data
        phone = form.phone.data
        genres = form.genres.data
        facebook_link = form.facebook_link.data
        website_link = form.website_link.data
        image_link = form.image_link.data
        talent = True if 'seeking_talent' in request.form else False
        seeking_description = form.seeking_description.data

        venue = Venue(name=name, city=city, state=state, phone=phone,
                        genres=genres, facebook_link=facebook_link,
                        website_link=website_link, image_link=image_link,
                        talent=talent,address=address,
                        description=seeking_description)

        db.session.add(venue)
        db.session.commit()

       except:
        error = True 
        db.session.rollback()
        
       finally:
        db.session.close()
        if error:
            flash('An error occurred. Venue ' +
              request.form['name'] + ' could not be listed.')
        else:
             flash('Venue ' + request.form['name'] + ' was successfully listed!')


        return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
        

        venue = Venue.query.filter(Venue.id == venue_id).first()
        name = venue.name
        db.session.delete(venue)
        db.session.commit() 
        flash('Venue ' + name + ' was successfully deleted.')
  except:
        
        db.session.rollback()

        flash('An error occurred. Venue ' + name + ' could not be deleted.')
  finally:
        
        db.session.close()

    
  return jsonify({'success': True})

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data=[{
    "id": 4,
    "name": "Guns N Petals",
  }, {
    "id": 5,
    "name": "Matt Quevedo",
  }, {
    "id": 6,
    "name": "The Wild Sax Band",
  }]
  return render_template('pages/artists.html', artists=Artist.query.all())

@app.route('/artists/search', methods=['POST'])
def search_artists():
   
    search = request.form.get('search_term', '')
    artists_search = Artist.query.filter(Artist.name.ilike(f'%{search}%'))
    response = {
         "count": artists_search.count(),
         "data": artists_search
    }

    
    
    return render_template('pages/search_artists.html', results=response, search_term=search)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
   
    artist = Artist.query.filter_by(id=artist_id).first()
    shows = Show.query.filter_by(artist_id=artist_id).all()
    upcoming_count = 0 
    past_count = 0
    upcoming_show = []  
    past_show = []
    current_date = datetime.now()


     
       
    for show in shows:
            if show.start_time < current_date:
                past_show.append({
                    "venue_id": show.venue_id,
                    "venue_name": Venue.query.filter_by(id=show.venue_id).first().name,
                    "start_time": format_datetime(str(show.start_time)),
                    "venue_image_link": Venue.query.filter_by(id=show.venue_id).first().image_link

                })
                past_count = past_count + 1

          
    for show in shows:
            if show.start_time > current_date:

                upcoming_show.append({
                    "venue_id": show.venue_id,
                    "venue_name": Venue.query.filter_by(id=show.venue_id).first().name,
                    "start_time": format_datetime(str(show.start_time)),
                    "venue_image_link": Venue.query.filter_by(id=show.venue_id).first().image_link

                })
                upcoming_count = upcoming_count + 1 
          

    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.venue,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website_link,
        "seeking_description": artist.description,
        "image_link": artist.image_link,
        "past_shows": past_show,
        "past_shows_count": past_count,
        "upcoming_shows": upcoming_show,
        "upcoming_shows_count": upcoming_count,
    }

    return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.filter_by(id=artist_id).first() 
  artist = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website_link": artist.website_link,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.venue,
        "seeking_description": artist.description,
        "image_link": artist.image_link
    }

  form.name.process_data(artist['name'])
  form.city.process_data(artist['city'])
  form.phone.process_data(artist['phone'])
  form.website_link.process_data(artist['website_link'])
  form.image_link.process_data(artist['image_link'])
  form.facebook_link.process_data(artist['facebook_link'])
  form.seeking_description.process_data(artist['facebook_link'])
  form.state.process_data(artist['state'])
  form.genres.process_data(artist['genres'])
  form.seeking_venue.process_data(artist['seeking_venue'])
  

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):

    try:
        form = ArtistForm()
        artist = Artist.query.filter_by(id=artist_id).first()
        artist.name = form.name.data
        artist.genres = form.genres.data
        artist.city = form.city.data
        artist.state = form.state.data
        artist.phone = form.phone.data
        artist.facebook_link = form.facebook_link.data
        artist.image_link = form.image_link.data
        artist.website_link = form.website_link.data
        seeking_venue = True if 'seeking_venue' in request.form else False
        artist.description = form.seeking_description.data

        db.session.commit()

        flash('Artist ' + request.form['name'] + ' was successfully updated!')
    
    except:
       

        db.session.rollback()
        flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated.')
    finally:
        
        db.session.close()

    
        return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm() 
  venue = Venue.query.filter_by(id=venue_id).first() 
  venue = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website_link": venue.website_link,
        "facebook_link": venue.facebook_link,
        "talent": venue.talent,
        "description": venue.description,
        "image_link": venue.image_link
    }

  form.name.process_data(venue['name'])
  form.city.process_data(venue['city'])
  form.address.process_data(venue['address'])
  form.phone.process_data(venue['phone'])
  form.website_link.process_data(venue['website_link'])
  form.facebook_link.process_data(venue['facebook_link'])
  form.seeking_description.process_data(venue['description'])
  form.image_link.process_data(venue['image_link'])
  form.state.process_data(venue['state'])
  form.genres.process_data(venue['genres'])
  form.seeking_talent.process_data(venue['talent'])

  return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  
    try:
        form = VenueForm()

        
        venue = Venue.query.filter_by(id=venue_id).first()
        venue.name = form.name.data
        venue.genres = form.genres.data
        venue.city = form.city.data
        venue.state = form.state.data
        venue.address = form.address.data
        venue.phone = form.phone.data
        venue.facebook_link = form.facebook_link.data
        venue.website_link = form.website_link.data
        venue.image_link = form.image_link.data
        venue.talent = True if 'seeking_talent' in request.form else False
        venue.description = form.seeking_description.data

        
        db.session.commit()
        flash('Venue ' + request.form['name'] + ' was successfully updated!')
    
    except:
        
        db.session.rollback()
        flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated.')
    finally:
       
        db.session.close()

    
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
       error = False
       try:
        form = ArtistForm()
        name = form.name.data
        city = form.city.data
        state = form.state.data
        phone = form.phone.data
        genres = form.genres.data
        facebook_link = form.facebook_link.data
        website_link = form.website_link.data
        image_link = form.image_link.data
        seeking_venue = True if 'seeking_venue' in request.form else False
        seeking_description = form.seeking_description.data

        
        artist = Artist(name=name, city=city, state=state, phone=phone,
                        genres=genres, facebook_link=facebook_link,
                        website_link=website_link, image_link=image_link,
                        venue=seeking_venue,
                        description=seeking_description)

       
        db.session.add(artist)
        db.session.commit()

       except:
        
        error = True 
        db.session.rollback()
        
       finally:
        
        db.session.close()
        if error:
            flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
        
        else:
             flash('Artist ' + request.form['name'] + ' was successfully listed!')
    
    
    
        return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    shows = Show.query.order_by(db.asc(Show.start_time))
    data_show = []
    
    for show in shows:
      start_time = format_datetime(str(show.start_time))
      artist_id = show.artist_id
      venue_id =  show.venue_id
      venue_name = Venue.query.filter_by(id=show.venue_id).first().name
      artist_name = Artist.query.filter_by(id=show.artist_id).first().name
      artist_image_link =  Artist.query.filter_by(id=show.artist_id).first().image_link

      data_show.append({
            "venue_name": venue_name,
            "artist_name": artist_name,
            "artist_id": artist_id,
            "venue_id": venue_id,
            "artist_image_link": artist_image_link,
            "start_time": start_time
        })

   
    return render_template('pages/shows.html', shows=data_show)
@app.route('/shows/create')
def create_shows():

  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    try:
        artist = request.form['artist_id']
        venue = request.form['venue_id']
        start_time = request.form['start_time']
        show = Show(artist_id=artist, venue_id=venue, start_time=start_time)
        db.session.add(show)
        db.session.commit()
        flash('Show was successfully listed!')
    except:
        db.session.rollback()
        flash('An error occurred. Show could not be listed.')
    finally:
        db.session.close()

    
    return render_template('pages/home.html')
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
