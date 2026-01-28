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

# class User(db.Model):
#     id=db.Column(db.Integer,primary_key=True)
#     username=db.Column(db.String(50),unique=True, nullable=False)
#     email=db.Column(db.String(50),unique=True, nullable=False)
#     password=db.Column(db.String(50),nullable=False)
#     db_name = db.Column(db.String(100), unique=True)
#     is_admin = db.Column(db.Boolean, default=False)
#     is_verified = db.Column(db.Boolean, default=False)  # NEW
#     plaid_access_token = db.Column(db.String(255), nullable=True)
#     plaid_item_id = db.Column(db.String(255), nullable=True)
#
#     def set_password(self,password):
#         self.password=generate_password_hash(password,method='pbkdf2:sha256')
#     def check_password(self,password):
#         return check_password_hash(self.password,password)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    db_name = db.Column(db.String(100), unique=True)

    # Location and language preferences
    country_id = db.Column(db.Integer, db.ForeignKey('countries.id'))
    continent_id = db.Column(db.Integer, db.ForeignKey('continents.id'))
    language_id = db.Column(db.Integer, db.ForeignKey('languages.id'))
    timezone = db.Column(db.String(50), default='UTC')

    # User settings
    is_admin = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean, default=False)
    preferences = db.Column(db.JSON, default=lambda: {
        'currency': 'USD',
        'date_format': 'YYYY-MM-DD',
        'notifications': True
    })

    # Relationships
    country = db.relationship('Country', backref='users')
    continent = db.relationship('Continent', backref='users')
    language = db.relationship('Language', backref='users')

    # Financial connections
    bank_connections = db.relationship('BankConnection', backref='user', lazy=True)

    def set_password(self, password):
        self.password = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password, password)
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


    country = db.Column(db.String(50))
    # user = db.relationship('User', backref=db.backref('activities', lazy=True))

class Blacklist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(120), nullable=False)

class Messages(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # sender_id = db.Column(db.String, db.ForeignKey('user.id'), nullable=False)
    # receiver_id = db.Column(db.String, db.ForeignKey('user.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')



    language = db.Column(db.String(5), default='en')



# Ml
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float)
    date = db.Column(db.DateTime)
    ml_confidence = db.Column(db.Float, default=0.0)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('bank_account.id'))

    # Transaction details
    transaction_id = db.Column(db.String(100), unique=True)
    # amount = db.Column(db.Numeric(15, 2), nullable=False)
    currency = db.Column(db.String(3), default='USD')
    # date = db.Column(db.Date, nullable=False)
    datetime = db.Column(db.DateTime)
    description = db.Column(db.String(500))
    merchant_name = db.Column(db.String(200))

    # Categorization
    category = db.Column(db.String(100))
    subcategory = db.Column(db.String(100))

    # Status
    pending = db.Column(db.Boolean, default=False)
    is_transfer = db.Column(db.Boolean, default=False)

    # Relationships
    user = db.relationship('User', backref='transactions')
    account = db.relationship('BankAccount', backref='transactions')


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
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('bank_accounts', lazy=True))

    connection_id = db.Column(db.Integer, db.ForeignKey('bank_connection.id'), nullable=False)
    name = db.Column(db.String(200))
    official_name = db.Column(db.String(200))
    type = db.Column(db.String(50))  # checking, savings, credit, etc.
    subtype = db.Column(db.String(50))

    # Balance information

    balance_limit = db.Column(db.Numeric(15, 2))
    currency = db.Column(db.String(10))

    # Metadata
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)


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

# from datetime import datetime
# from flask_sqlalchemy import SQLAlchemy
# from werkzeug.security import generate_password_hash, check_password_hash
#
# db = SQLAlchemy()


class Country(db.Model):
    __tablename__ = 'countries'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(2), unique=True, nullable=False)  # ISO 3166-1 alpha-2
    name = db.Column(db.String(100), nullable=False)
    continent = db.Column(db.String(50), nullable=False)
    currency = db.Column(db.String(3), nullable=False)  # ISO 4217
    timezone = db.Column(db.String(50), nullable=False)
    language = db.Column(db.String(5), nullable=False)  # ISO 639-1
    plaid_supported = db.Column(db.Boolean, default=False)
    plaid_country_code = db.Column(db.String(2))  # Plaid's country code
    other_provider = db.Column(db.String(50))  # Alternative provider name


class Continent(db.Model):
    __tablename__ = 'continents'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(2), unique=True, nullable=False)  # AF, AS, EU, NA, SA, OC, AN
    name = db.Column(db.String(50), nullable=False)


class Language(db.Model):
    __tablename__ = 'languages'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(5), unique=True, nullable=False)  # ISO 639-1
    name = db.Column(db.String(50), nullable=False)
    native_name = db.Column(db.String(50), nullable=False)


class BankProvider(db.Model):
    __tablename__ = 'bank_providers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    api_name = db.Column(db.String(50), nullable=False)  # plaid, truelayer, etc.
    country_codes = db.Column(db.String(500))  # Comma-separated country codes
    continent_codes = db.Column(db.String(100))  # Comma-separated continent codes
    is_active = db.Column(db.Boolean, default=True)
    api_config = db.Column(db.JSON)  # Store provider-specific config



class BankConnection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    provider_id = db.Column(db.Integer, db.ForeignKey('bank_providers.id'), nullable=False)

    # Provider-specific data
    access_token = db.Column(db.String(500))
    item_id = db.Column(db.String(200))
    institution_id = db.Column(db.String(100))
    institution_name = db.Column(db.String(200))

    # Connection metadata
    is_active = db.Column(db.Boolean, default=True)
    last_sync = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    provider = db.relationship('BankProvider', backref='connections')
    accounts = db.relationship('BankAccount', backref='connection', lazy=True)


# class BankAccount(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     connection_id = db.Column(db.Integer, db.ForeignKey('bank_connection.id'), nullable=False)
#     account_id = db.Column(db.String(100), nullable=False)  # Provider's account ID
#     name = db.Column(db.String(200))
#     official_name = db.Column(db.String(200))
#     type = db.Column(db.String(50))  # checking, savings, credit, etc.
#     subtype = db.Column(db.String(50))
#
#     # Balance information
#     balance_available = db.Column(db.Numeric(15, 2))
#     balance_current = db.Column(db.Numeric(15, 2))
#     balance_limit = db.Column(db.Numeric(15, 2))
#     currency = db.Column(db.String(3))
#
#     # Metadata
#     is_active = db.Column(db.Boolean, default=True)
#     last_updated = db.Column(db.DateTime, default=datetime.utcnow)


