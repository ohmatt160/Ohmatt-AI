from datetime import datetime
from functools import wraps
from sqlalchemy.orm import sessionmaker
from ai_module import categorize_transaction, analyze_spending
from model import User, serializer, mail, Activity, app, db, Transaction
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import create_engine
from flask_mail import Message
from flask import request, jsonify

def get_user_task_session():
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user).first()
    if user:
        engine = create_engine(f"sqlite:///{user.db_name}")
        Session = sessionmaker(bind=engine)
        return Session()
    return None

def generate_token(email):
    return serializer.dumps(email, salt="email-confirm-salt")

def confirm_token(token, expiration=3600):
    try:
        email = serializer.loads(token, salt="email-confirm-salt", max_age=expiration)
    except Exception:
        return None
    return email

def send_email(to, subject, template):
    msg = Message(subject, recipients=[to], html=template, sender=app.config['MAIL_USERNAME'])
    mail.send(msg)

# def log_activity(user, action):
#     log = Activity(
#         user_id=user.id if user else None,
#         action=action,
#         ip_address=request.remote_addr,
#         user_agent=request.headers.get('User-Agent')
#     )
#     db.session.add(log)
#     db.session.commit()
def log_activity(user, action):

    """
    Accepts:
      - user: User instance OR username/email string OR integer user id OR None
      - action: string
    This function resolves the user id when needed, handles errors, and
    never lets exceptions silently prevent logging.
    """
    try:
        # Resolve user id
        user_id = None
        if user is None:
            user_id = None
        elif isinstance(user, int):
            user_id = user
        elif isinstance(user, str):
            # try username then email
            u = User.query.filter_by(username=user).first()
            if not u:
                u = User.query.filter_by(email=user).first()
            user_id = u.id if u else None
        else:
            # assume it's a User instance
            user_id = getattr(user, "id", None)

        log = Activity(
            user_id=user_id,
            action=action,
            ip_address=request.remote_addr if request else None,
            user_agent=request.headers.get('User-Agent') if request else None
        )
        db.session.add(log)
        db.session.commit()
        # optional debug
        print(f"✅ Activity logged: user_id={user_id}, action={action}")
    except Exception as e:
        # rollback to keep session clean & print error for debugging
        db.session.rollback()
        print(f"❌ Failed to log activity: {e}")

def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        current_identity = get_jwt_identity()
        user = User.query.filter_by(username=current_identity).first()

        if not user or not user.is_admin:
            return jsonify({"message": "Access denied: Admins only"}), 403

        return fn(*args, **kwargs)
    return wrapper

#ML
def process_new_transaction(user, description, amount, date=None):
    date = date or datetime.utcnow()
    category, confidence = categorize_transaction(description)

    transaction = Transaction(
        user_id=user.id,
        description=description,
        amount=amount,
        date=date,
        category=category,
        ml_confidence=confidence
    )
    db.session.add(transaction)
    db.session.commit()

    user_transactions = Transaction.query.filter_by(user_id=user.id).all()
    insights = analyze_spending(user_transactions)

    if not description:
        insights.insert(0, "⚠️ Transaction missing description!")

    return {
        "transaction_category": category,
        "transaction_confidence": confidence,
        "insights": insights
    }
