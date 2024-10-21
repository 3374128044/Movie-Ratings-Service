from flask import Flask, request, jsonify
import jwt
import re
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import load_dotenv
load_dotenv()


app = Flask(__name__)
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db' #temporary
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("SQLALCHEMY_DATABASE_URI")
app.config['SECRET_KEY'] = '3zZYv0zSwYG8MaV4'
db = SQLAlchemy(app)
 
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    role = db.Column(db.String(50), default='user')

class Movie(db.Model):
    __tablename__ = 'movies'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)

class Rating(db.Model):
    __tablename__ = 'ratings'
    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)

#initializing database
with app.app_context():
    db.create_all()

#decorator method to make sure endpoints are jwt protected
def token_required(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        token = request.args.get('token')
        if not token:
            return jsonify({'Alert!': "Token missing!"}), 403
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms= ['HS512', 'HS256'])
            current_user = User.query.filter_by(id=payload['user_id']).first()
        except:
            return jsonify({'Alert!': "Invalid token!"}), 403
        return func(current_user, *args, **kwargs)
    return decorated

#decorator method to make sure admin only endpoints are only accessed by admin
def admin_required(func):
    @wraps(func)
    def decorated(current_user, *args, **kwargs):
        if current_user.role != 'admin':
            return jsonify({"message" : "Access denied. Admin privileges only!"}), 403
        return func(current_user, *args, **kwargs)
    return decorated

# Decorator that restricts access to a view function for users only.
def user_only(func):
    @wraps(func)
    def decorated(current_user, *args, **kwargs):
        if current_user.role != 'user':
            return jsonify({"message" : "This is for users only!"}), 403
        return func(current_user, *args, **kwargs)
    return decorated

# Registers a new user in the system.
@app.route('/register', methods=['POST'])
def register_user():
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

    username = request.json.get("username", None)
    password = request.json.get("password", None)
    email = request.json.get("email", None)

    role = request.json.get("role", "user") #user is default role
    if username == None:
        return jsonify({"message" : "Username is required!"}), 404
    elif User.query.filter_by(username=username).first():
        return jsonify({"message" : "Username already exists!"}), 409
    
    if email == None:
        return jsonify({"message" : "Email is required!"}), 404
    elif re.match(email_regex, email) == None:
        return jsonify({"message" : "Invalid email format!"}), 409
    elif User.query.filter_by(email=email).first():
        return jsonify({"message" : "Email already exists!"}), 409
    
    new_user = User(username=username, password=password, email=email, role=role) 
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message" : "User registered successfully!"}), 201

# Authenticates a user and generates a JWT token upon successful login.
@app.route('/login', methods=['POST'])
def login():
    user = User.query.filter_by(username=request.json.get('username', None)).first()
    email = User.query.filter_by(email=request.json.get('email', None)).first()
    if(user and email and user.password == request.json.get('password', None)):
        token = jwt.encode({
            'user_id': user.id,
            'expiration': str(datetime.now(timezone.utc) + timedelta(seconds=120))
        }, app.config['SECRET_KEY'])
        return jsonify({"token" : token}), 200
    else:
        return jsonify({"message" : "Invalid credentials"}), 401

#admins endpoint to add a new movie
@app.route('/movies/add', methods=['POST'])
@token_required
@admin_required
def add_movie(current_user):
    title = request.json.get("title", None)
    description = request.json.get("description", "")

    if not title:
        return jsonify({"message": "Movie title is required!"}), 400

    new_movie = Movie(title=title, description=description)
    db.session.add(new_movie)
    db.session.commit()

    return jsonify({"message": "Movie added successfully!"}), 201

# Submits a rating for a specified movie by the authenticated user.
@app.route('/movies/ratings/submit/<int:movie_id>', methods=['POST'])
@token_required
@user_only
def submit_rating(current_user, movie_id):
    movie = Movie.query.filter_by(id=movie_id).first()
    if not movie:
        return jsonify({"message" : "Unable find movie with movie id: %s!" %movie_id}), 409
    rating = Rating.query.filter_by(movie_id=movie.id, user_id=current_user.id).first()
    if rating:
        return jsonify({"message" : "You have already submit a rating for this movie!"}), 400
    rating_score = request.json.get("rating", None)
    if rating_score == None or not isinstance(rating_score, (int, float)):
        return jsonify({"message" : "Please input a valid rating!"}), 404
    new_rating = Rating(movie_id=movie_id, user_id=current_user.id, rating=rating_score)
    db.session.add(new_rating)
    db.session.commit()
    return jsonify({"message": "Successfully submitted rating for %s" %movie.title})

# Retrieves a list of movies along with their average ratings.
@app.route('/movies/ratings', methods=['GET'])
def get_movie_ratings():
    # Query to retrieve movie IDs, titles, descriptions, and their average ratings
    ratings = db.session.query(
        Movie.id,  # Include movie ID
        Movie.title,
        Movie.description,
        db.func.avg(Rating.rating).label('average_rating')  # Calculate average rating
    ).join(Rating, Movie.id == Rating.movie_id).group_by(Movie.id).all()  # Group by Movie.id 

    response = [
        {
            'id': movie_id,  # Add movie ID to the response
            'movie': movie_title,
            'plot': movie_description,
            'overall_rating': round(average_rating, 1)  # Round average rating to 1 decimal point
        }
        for movie_id, movie_title, movie_description, average_rating in ratings
    ]
    return jsonify(response)

# Retrieves the details of a specific movie by its ID.
@app.route('/movies/<movie_id>', methods=['GET'])
def get_movie_details(movie_id):
    # Fetch the movie details
    movie = Movie.query.get(movie_id)
    if not movie:
        return jsonify({'error': 'Movie not found'}), 404   # Error handling

    # Fetch the ratings for this movie
    ratings = Rating.query.filter_by(movie_id=movie.id).all()
    user_ratings = [{'user_id': rating.user_id, 'rating': rating.rating} for rating in ratings]

    response = {
        'id': movie.id,
        'movie': movie.title,
        'plot': movie.description,
        'ratings': user_ratings
    }
    return jsonify(response), 200

# Users update their own existing ratings based on the rating ID.
@app.route('/movies/ratings/update/<int:rating_id>', methods=['PUT'])
@token_required
@user_only
def update_rating(current_user, rating_id):
    rating_to_update = Rating.query.get(rating_id)  # Fetch the rating by its ID
    if rating_to_update and rating_to_update.user_id == current_user.id:  # Check if the rating belongs to the current user
        new_rating = request.json.get("rating", None)
        if new_rating is None or not isinstance(new_rating, (int, float)):
            return jsonify({"message": "Please input a valid rating!"}), 400
        rating_to_update.rating = new_rating
        db.session.commit()
        return jsonify({"message": "Successfully updated rating!"}), 200
    else:
        return jsonify({"message": "Unable to find rating!"}), 404

# Admin deletes a specified rating from the database by rating ID.
@app.route('/movies/ratings/admin-delete/<int:rating_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_rating_admin_only(current_user,rating_id):
    rating = Rating.query.filter_by(id=rating_id).first()
    if rating:
        db.session.delete(rating)
        db.session.commit()
        return jsonify({"message": "Rating deleted successfully!"}), 200
    else:
        return jsonify({"message": "Unable find rating!"}), 404

# Users delete their own ratings by rating ID.
@app.route('/movies/ratings/user-delete/<int:rating_id>', methods=['DELETE'])
@token_required
@user_only
def delete_rating_user_only(current_user, rating_id):
    rating = Rating.query.get(rating_id)  # Fetch the rating by its ID
    if rating and rating.user_id == current_user.id:  # Check if the rating belongs to the current user
        db.session.delete(rating)
        db.session.commit()
        return jsonify({"message": "Your rating has been deleted!"}), 200
    else:
        return jsonify({"message": "Unable to find rating!"}), 404

if __name__ == '__main__':
    app.run(debug=True)

