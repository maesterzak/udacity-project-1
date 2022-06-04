# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#
import datetime
import logging
from logging import Formatter, FileHandler

import babel
import dateutil.parser
from flask import Flask, render_template, request, flash, redirect, url_for
from flask_migrate import Migrate
from flask_moment import Moment
from werkzeug.exceptions import abort

from forms import *
from models import db, Artist, Venue, Show

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

# migrate = Migrate(app, db)
app = Flask(__name__)
app.config.from_object('config')
moment = Moment(app)
db.init_app(app)
migrate = Migrate(app, db)


# TODO: connect to a local postgresql database

# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    if isinstance(value, str):
        date = dateutil.parser.parse(value)
    else:
        date = value
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"

    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#

@app.route('/')
def index():
    recently_listed_artists = Artist.query.order_by(Artist.id.desc()).limit(10).all()
    recently_listed_venues = Venue.query.order_by(Venue.id.desc()).limit(10).all()
    data = {
        'recently_listed_artists':recently_listed_artists,
        'recently_listed_venues':recently_listed_venues
    }

    return render_template('pages/home.html', data=data)


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    # TODO: replace with real venues data.
    # get unique venues based on city and state
    unique_loc = Venue.query.distinct(Venue.city, Venue.state).all()

    # create empty array and assign to data
    data = []
    # map through unique venues
    for d in unique_loc:
        # filter Venue based on unique city and state values
        x = Venue.query.filter_by(city = d.city, state = d.state ).all()
        # create an empty venue_list array
        venue_list = []
        for a in x:

            upcoming_shows=Show.query.filter(Show.venue.has(id=a.id), Show.start_time > datetime.now()).all()
            upcoming_shows_count = len(upcoming_shows)

            venue_dict = {
                'id': a.id,
                'name':a.name,
                "num_upcoming_shows": upcoming_shows_count,
            }
            venue_list.append(venue_dict)

        d = {
            'city': d.city,
            'state': d.state,
            'venues': venue_list
        }

        data.append(d)



    #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
    # data=[{
    #   "city": "San Francisco",
    #   "state": "CA",
    #   "venues": [{
    #     "id": 1,
    #     "name": "The Musical Hop",
    #     "num_upcoming_shows": 0,
    #   }, {
    #     "id": 3,
    #     "name": "Park Square Live Music & Coffee",
    #     "num_upcoming_shows": 1,
    #   }]
    # }, {
    #   "city": "New York",
    #   "state": "NY",
    #   "venues": [{
    #     "id": 2,
    #     "name": "The Dueling Pianos Bar",
    #     "num_upcoming_shows": 0,
    #   }]
    # }]
    return render_template('pages/venues.html', areas=data);


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    search = request.form.get('search_term', None)
    venue_list = Venue.query.filter(
        Venue.name.ilike("%{}%".format(search))
    ).all()
    venue_count = len(venue_list)
    response ={
        "count": venue_count,
        "data":venue_list
    }

    return render_template('pages/search_venues.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    venue = Venue.query.get(venue_id)
    if venue is None:
        abort(404)
    upcoming_shows=Show.query.filter(Show.venue.has(id=venue_id), Show.start_time > datetime.now()).all()
    past_shows = Show.query.filter(Show.venue.has(id=venue_id), Show.start_time < datetime.now()).all()
    upcoming_shows_count = len(upcoming_shows)
    past_shows_count = len(past_shows)

    data = {
        'id':venue.id,
        'name':venue.name,
        'genres':venue.genres,
        'city':venue.city,
        'state':venue.state,
        'address':venue.address,
        'phone':venue.phone,
        'website':venue.website_link,
        'image_link':venue.image_link,
        'facebook_link':venue.facebook_link,
        'seeking_talent':venue.seeking_talent,
        'seeking_description':venue.seeking_description,
        'upcoming_shows': upcoming_shows,
        'past_shows': past_shows,
        'upcoming_shows_count':upcoming_shows_count,
        'past_shows_count':past_shows_count

    }

    # TODO: replace with real venue data from the venues table, using venue_id

    return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    form = VenueForm(request.form)
    data ={}
    if form.validate():

        try:
            form_venue = Venue()
            form.populate_obj(form_venue)
            db.session.add(form_venue)
            db.session.commit()
            data['name'] = request.form['name']
            flash('Venue ' + request.form['name'] + ' was successfully listed!')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Venue ' + data['name'] + '   could not be listed.')

        finally:
            db.session.close()

    else:
        flash('Invalid or incomplete details')

    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion

    return redirect(url_for('index'))


@app.route('/venues/delete/<venue_id>', methods=['POST'])
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using

    try:
        venue = Venue.query.get(venue_id)

        db.session.delete(venue)
        db.session.commit()
        flash( venue.name + '   was deleted successfully')
        return redirect(url_for('index'))
    except Exception as e:
        db.session.close()
        abort(404)
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    return None


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    data = Artist.query.all()
    if data is None:
        abort(404)
    # TODO: replace with real data returned from querying the database
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    search = request.form.get('search_term', None)
    artist_list = Artist.query.filter(
        Artist.name.ilike("%{}%".format(search))
    ).all()
    artist_count = len(artist_list)
    response ={
        "count": artist_count,
        "data":artist_list
    }

    return render_template('pages/search_artists.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id

    # TODO: replace with real artist data from the artist table, using artist_id
    artist = Artist.query.get(artist_id)
    if artist is None:
        abort(404)

    upcoming_shows=Show.query.filter(Show.artist.has(id=artist_id), Show.start_time > datetime.now()).all()
    past_shows = Show.query.filter(Show.artist.has(id=artist_id), Show.start_time < datetime.now()).all()
    upcoming_shows_count = len(upcoming_shows)
    past_shows_count = len(past_shows)

    data = {
        'id':artist.id,
        'name':artist.name,
        'city':artist.city,
        'state':artist.state,
        'phone':artist.phone,
        'website':artist.website_link,
        'genres':artist.genres,
        'image_link':artist.image_link,
        'facebook_link':artist.facebook_link,
        'seeking_venue':artist.seeking_venue,
        'upcoming_shows': upcoming_shows,
        'past_shows': past_shows,
        'upcoming_shows_count':upcoming_shows_count,
        'past_shows_count':past_shows_count

    }

    return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.get(artist_id)

    # TODO: populate form with fields from artist with ID <artist_id>
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    form = ArtistForm(request.form)
    data = {}
    if form.validate():

        try:
            form_artist = Artist.query.get(artist_id)
            form.populate_obj(form_artist)
            data['name'] = request.form['name']
            db.session.add(form_artist)
            db.session.commit()
            flash('Artist ' + request.form['name'] + ' was successfully updated!')
        except Exception as e:
            db.session.rollback()

            flash('An error occurred. Artist ' + data['name'] + '   could not be updated.')
        finally:
            db.session.close()
    else:
        flash('Invalid or incomplete details')

    # artist record with ID <artist_id> using the new attributes

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.get(venue_id)
    if venue is None:
        abort(404)

    # TODO: populate form with values from venue with ID <venue_id>
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    form = VenueForm(request.form)
    data ={}
    if form.validate():
        try:
            form_venue = Venue.query.get(venue_id)
            form.populate_obj(form_venue)
            data['name'] = request.form['name']
            db.session.add(form_venue)
            db.session.commit()
            flash('Venue ' + request.form['name'] + ' was successfully updated!')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Venue ' + data['name'] + '   could not be updated.')
        finally:
            db.session.close()
    else:
        flash('Invalid or incomplete details')

    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    form = ArtistForm(request.form)

    if form.validate():
        data = {}
        try:
            form_artist = Artist()
            form.populate_obj(form_artist)
            data['name'] = request.form['name']
            db.session.add(form_artist)
            db.session.commit()
            flash('Artist ' + request.form['name'] + ' was successfully listed!')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Artist ' + data['name'] + '   could not be listed.')
        finally:
            db.session.close()
    else:
        flash('Invalid or incomplete details')

    return redirect(url_for('index'))


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    data = Show.query.all()


    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    form = VenueForm(request.form)

    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead
    form = ShowForm(request.form)

    if form.validate():

        try:
            form_show = Show()
            form.populate_obj(form_show)

            db.session.add(form_show)
            db.session.commit()
            flash('Show was successfully listed!')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Show could not be listed.')
        finally:
            db.session.close()

    return redirect(url_for('index'))


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

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
