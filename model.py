from datetime import datetime, time
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import  JWTManager

from sqlalchemy import Column, DateTime, Integer, Text
from sqlalchemy.ext.declarative import declarative_base

from werkzeug.security import generate_password_hash, check_password_hash
from flask_restful import  Api, reqparse
from flask_mail import Mail
from itsdangerous import URLSafeTimedSerializer
from flask_migrate import Migrate

Base= declarative_base()

app = Flask(__name__)
api = Api(app)
jwt=JWTManager(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Looking to send emails in production? Check out our Email API/SMTP product!
app.config['MAIL_SERVER']='sandbox.smtp.mailtrap.io'
app.config['MAIL_PORT'] = 2525
app.config['MAIL_USERNAME'] = 'd5c82933204588'
app.config['MAIL_PASSWORD'] = '48a454b81a1e63'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
# set expiration in seconds (example: 24 hours)
app.config['EMAIL_TOKEN_EXPIRATION'] = 24 * 60 * 60  # 86400 seconds
SECRET_KEY = 'your-secret-key'
JWT_SECRET_KEY = 'your-jwt-secret'
app.config['SECRET_KEY'] = SECRET_KEY
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY
db=SQLAlchemy(app)
mail = Mail(app)
migrate=Migrate(app,db)

class User(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(50),unique=True, nullable=False)
    email=db.Column(db.String(50),unique=True, nullable=False)
    password=db.Column(db.String(50),nullable=False)
    db_name = db.Column(db.String(100), unique=True)
    is_admin = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean, default=False)  # NEW
    plaid_access_token = db.Column(db.String(255), nullable=True)
    plaid_item_id = db.Column(db.String(255), nullable=True)

    def set_password(self,password):
        self.password=generate_password_hash(password,method='pbkdf2:sha256')
    def check_password(self,password):
        return check_password_hash(self.password,password)
args=reqparse.RequestParser()
args.add_argument('username',required=True)
args.add_argument('email',required=True)
args.add_argument('password',required=True)

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    action = db.Column(db.String(100))
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('logs', lazy=True))

class Blacklist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(120), nullable=False)

class Messages(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.String, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.String, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')

# Ml
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    description = db.Column(db.String(255))
    amount = db.Column(db.Float)
    date = db.Column(db.DateTime)
    category = db.Column(db.String(50))
    ml_confidence = db.Column(db.Float, default=0.0)


# Add these new models to your existing models
class BankAccount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    institution_name = db.Column(db.String(100), nullable=False)
    account_name = db.Column(db.String(100), nullable=False)
    account_type = db.Column(db.String(50), nullable=False)
    account_id = db.Column(db.String(100), nullable=False)  # Plaid account ID
    balance_available = db.Column(db.Float, default=0.0)
    balance_current = db.Column(db.Float, default=0.0)
    currency = db.Column(db.String(10), default='USD')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('bank_accounts', lazy=True))


class BankTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    bank_account_id = db.Column(db.Integer, db.ForeignKey('bank_account.id'))
    transaction_id = db.Column(db.String(100), unique=True)  # Plaid transaction ID
    description = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    category = db.Column(db.String(100))
    pending = db.Column(db.Boolean, default=False)
    merchant_name = db.Column(db.String(100))

    user = db.relationship('User', backref=db.backref('bank_transactions', lazy=True))
    bank_account = db.relationship('BankAccount', backref=db.backref('transactions', lazy=True))

class Tasks(Base):
    __tablename__='tasks'
    id=Column(Integer,primary_key=True)
    date = Column(DateTime, default=lambda:  datetime.combine(datetime.utcnow().date(), time.min))
    time = Column(DateTime, default=datetime.utcnow)
    task=Column(Text,nullable=False)

    def __repr__(self):
        return '<Task %r>' % self.task
args.add_argument('task',required=True)
args.add_argument('date',required=True)

