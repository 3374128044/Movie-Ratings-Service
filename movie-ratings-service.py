from flask import Flask, request, jsonify
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'
app.config['SECRET_KEY'] = '3zZYv0zSwYG8MaV4'
db = SQLAlchemy(app)
 
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
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

def token_required(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        token = request/args.get('token')
        if not token:
            return jsonify({'Alert!': "Token missing!"}), 401
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'])
            current_user = User.query.filter_by(id=payload['user_id']).first()
        except:
            return jsonify({'Alert!': "Invalid token!"}), 401
        return func(current_user, *args, **kwargs)
    return decorated

def admin_required(func):
    @wraps(func)
    def decorated(current_user, *args, **kwargs):
        if current_user.role != 'admin':
            return jsonify({"message" : "Access denied. Admin privileges only!"}), 403
        return func(current_user, *args, **kwargs)
    return decorated

@app.route('/register', methods=['POST'])
def register_user():
    username = request.json.get("username", None)
    password = request.json.get("password", None)
    if username == None:
        return jsonify({"message" : "Username is required!"}), 404
    new_user = User(username=username, password=password, role=request.json.get('role', 'user')) #user is default role
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message" : "User registered successfully!"}), 201

@app.route('/login', methods=['POST'])
def login():
    user = User.query.filter_by(username=request.json.get('username', None)).first()
    if(user and user.password == request.json.get('password', None)):
        token = jwt.encode({
            'user_id': user.id,
            'expiration': str(datetime.utcnow() + timedelta(seconds=120))
        }, app.config['SECRET_KEY'])
        return jsonify({"token" : token}), 200
    else:
        return jsonify({"message" : "Username or password was incorrect."}), 401

if __name__ == '__main__':
    app.run(debug=True)

