from datetime import datetime, timedelta
from typing import Dict, Any, List

import plaid
from flask import request, jsonify, render_template, current_app
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity

from sqlalchemy import create_engine
from flask_restful import Resource, marshal_with, reqparse, fields

from sqlalchemy.sql.functions import user

from config import plaid_client, configuration, logger, app, api
from model import User, Transaction, Activity, Messages, Tasks, Base, db, BankTransaction, BankAccount, \
    Country, Continent, Language, BankConnection

from plaid.api import plaid_api
from plaid.api_client import ApiClient

from utils import get_user_task_session, log_activity, generate_token, send_email, confirm_token, admin_required, \
    process_new_transaction, ProviderRegistry


# Field definitions
user_field = {
    'id': fields.Integer,
    'username': fields.String,
    'email': fields.String,
    'country_code': fields.String,
    'language_code': fields.String,
    'is_verified': fields.Boolean
}

country_field = {
    'code': fields.String,
    'name': fields.String,
    'continent': fields.String,
    'currency': fields.String,
    'timezone': fields.String,
    'language': fields.String,
    'plaid_supported': fields.Boolean
}

continent_field = {
    'code': fields.String,
    'name': fields.String
}

language_field = {
    'code': fields.String,
    'name': fields.String,
    'native_name': fields.String
}

@app.route('/home')
def home():
    return render_template('index.html')

new_task={
    'id':fields.Integer,
    'task':fields.String,
    'date':fields.DateTime,
    'time':fields.DateTime,
}

class TasksAPI(Resource):
    @jwt_required()
    def post(self):
        try:
            data=request.get_json()
            # user=get_jwt_identity()
            current_identity = get_jwt_identity()
            user = User.query.filter_by(username=current_identity).first()
            task_text = data.get('task')
            date_str = data.get('date')  # Expecting "YYYY-MM-DD"
            time_str = data.get('time')  # Expecting "HH:MM"

            # Combine and parse into datetime objects
            datetime_str = f"{date_str} {time_str}"
            task_datetime = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")

            session = get_user_task_session()
            if not session:
                return jsonify({'message': 'Session creation failed'}), 500

            new_task = Tasks(task=task_text, date=task_datetime, time=task_datetime)
            session.add(new_task)
            session.commit()
            session.close()
            log_activity(user, "task creation")
            return {'message':'Task created!'}
        except Exception as e:
            return {'message': f'failed! {e}'},500
    @jwt_required()
    # @marshal_with(new_task)
    def get(self):
        try:
            session = get_user_task_session()
            # user=User.query.filter_by(id=get_jwt_identity()).first()
            current_identity = get_jwt_identity()
            user = User.query.filter_by(username=current_identity).first()
            tasks = session.query(Tasks).all()
            result = [{
                "id": t.id,
                "task": t.task,
                "date": t.date.isoformat() if t.date else None,
                "time": t.time.isoformat() if t.time else None
            } for t in tasks]
            session.close()
            log_activity(user, "User task view")
            return {"tasks": result}, 200


        except Exception as e:
            return {'message': f'failed! {e}'},500
api.add_resource(TasksAPI, '/tasks')


class UserRegister(Resource):
    def post(self):
        try:
            data = request.get_json()
            # user= data['username']
            if User.query.filter((User.username == data['username']) | (User.email == data['email'])).first():
                return {"message": "Username or email already exists"}, 400

                # Validate country
                country = Country.query.filter_by(code=args['country_code'].upper()).first()
                if not country:
                    return {"message": "Invalid country code"}, 400

                # Validate language
                language = Language.query.filter_by(code=args['language_code'].lower()).first()
                if not language:
                    return {"message": "Invalid language code"}, 400

                # Get continent
                continent = Continent.query.filter_by(code=country.continent).first()

            db_name = f"{data['username']}_tasks.db"
            new_user = User(username=data['username'], email=data['email'], db_name=db_name,
                country_code=country.code,
                continent_code=continent.code if continent else None,
                language_code=language.code,
                timezone=data['timezone'])
            new_user.set_password(data['password'])
            db.session.add(new_user)
            db.session.commit()

            engine = create_engine(f"sqlite:///{db_name}")
            Base.metadata.create_all(engine)


            token = generate_token(data['email'])
            send_email(data['email'], "Verify Your Account", f"Your verification token: {token}")
            log_activity(new_user, "User registered")
            return {"message": "User registered. Check your email for verification token.",
                "user": {
                    "username": new_user.username,
                    "email": new_user.email,
                    "country": country.code,
                    "language": language.code,
                    "timezone": new_user.timezone
                }}, 201

        except Exception as e:
            return jsonify({'message': f'Error: {str(e)}' })
api.add_resource(UserRegister, '/register')

class VerifyAccount(Resource):
    def post(self):
        try:
            data = request.get_json()
            email = confirm_token(data.get('token'))
            if not email:
                return {"message": "Invalid or expired token"}, 400

            user = User.query.filter_by(email=email).first()
            if not user:
                return {"message": "User not found"}, 404

            if user.is_verified:
                return {"message": "Account already verified"}, 200

            user.is_verified = True
            db.session.commit()
            log_activity(user, "Email Verification")
            return {"message": "Account verified successfully"}, 200
        except Exception as e:
            return jsonify({'message': f'Error: {str(e)}' })
api.add_resource(VerifyAccount, '/verify')

class UserLogin(Resource):
    def post(self):
        try:
            data = request.get_json()
            # user = User.query.filter_by(username=data['username']).first()

            user = User.query.filter_by(email=data['email']).first()

            user_data = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "country": user.country_code,
                "language": user.language_code,
                "timezone": user.timezone,
                "is_admin": user.is_admin
            }

            if user and user.check_password(data['password']):
                if user.is_admin:
                    access_token = create_access_token(identity=user.username)
                    log_activity(user, "Admin login")
                    return {
                        "message": "Welcome Admin!",
                        "user": user_data,
                        "access_token": access_token
                    }, 200

                access_token = create_access_token(identity=user.username)  # or identity=user.id
                log_activity(user, "User login")
                return {'message': 'User login successfully','user':user_data, 'access_token': access_token}, 200
            else:
                if user:
                    log_activity(user, "User login failed")
                return {'message': 'User login failed'}, 401

            # if User.query.filter_by(email=data['email']).first():
            #     if user.check_password(data['password']):
            #         access_token = create_access_token(identity=user.username)
            #         log_activity(user, "User login")
            #         return jsonify({'message': 'User login successfully'},{'access_token': access_token})
            #     else:
            #         log_activity(user, "User login failed")
            #         return jsonify({'message': 'User login failed\n username or email is incorrect'})
            # else:
            #     log_activity(user, "User login failed")
            #     return jsonify({'message': 'User login failed\n username or email is incorrect'})
        except Exception as e:

            return jsonify({'message': f'Error: {str(e)}' })
api.add_resource(UserLogin, '/login')


class ProfileResource(Resource):
    # @marshal_with(new_task)
    def options(self):
        return {}
    @jwt_required()
    def get(self):
        current_user=get_jwt_identity()
        user = User.query.filter_by(username=current_user).first()
        if not current_user:
            return {"message": "Unauthorized, no identity in token"}, 401

            # Get user's country and language details
        country = Country.query.filter_by(code=user.country_code).first() if user.country_code else None
        language = Language.query.filter_by(code=user.language_code).first() if user.language_code else None



        # user=User.query.filter_by(username=current_user).first()
        current_identity = get_jwt_identity()
        user = User.query.filter_by(username=current_identity).first()
        session = get_user_task_session()
        if session:
            tasks =  session.query(Tasks).all()
            result = [{
                "id": t.id,
                "task": t.task,
                "date": t.date.isoformat() if t.date else None,
                "time": t.time.isoformat() if t.time else None
            } for t in tasks]
            session.close()
            log_activity(user, "Task Log")
            return {"user": user.username, "tasks": result}, 200

        return jsonify({
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "country": {
                    "code": user.country_code,
                    "name": country.name if country else None,
                    "currency": country.currency if country else None
                } if country else None,
                "language": {
                    "code": user.language_code,
                    "name": language.name if language else None
                } if language else None,
                "timezone": user.timezone,
                "is_verified": user.is_verified,
                "is_admin": user.is_admin
            }
        }), 200
    @jwt_required()
    def post(self):
        try:
            data = request.get_json()
            # user= User.query.filter_by(username=data['username']).first()
            current_identity = get_jwt_identity()
            user = User.query.filter_by(username=current_identity).first()
            task_text = data.get('task')
            date_str = data.get('date')
            time_str = data.get('time')

            datetime_str = f"{date_str} {time_str}"
            task_datetime = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")

            session = get_user_task_session()
            if session:
                new_task = Tasks(task=task_text, date=task_datetime, time=task_datetime)
                session.add(new_task)
                session.commit()
                log_activity(user, "Task added")
                return {'message': 'Task created!'}
            else:
                return {'message': 'User login failed'}, 401
        except Exception as e:
            return {'message': f'Error: {str(e)}' }
api.add_resource(ProfileResource, '/profile')

class Users(Resource):
    @marshal_with(user_field)
    # @admin_required
    def get(self):
        users=User.query.all()
        return users, 200
api.add_resource(Users, '/')

class PasswordResetResource(Resource):
    @jwt_required()
    def post(self):
        email = request.json.get('email')
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"message": "User not found"}), 404

        token = generate_token(user.email)
        log_activity(user, "Requested password reset")
        # reset_url = f"http://localhost:5000/reset-password/{token}"
        send_email(user.email, "Password Reset", f"Your password reset token: {token}")

        return {"message": "Check your email for password reset link"}, 200
    def put(self):
        try:
            data = request.get_json()
            new_password = data.get('password')
            token = data.get('token')
            email = confirm_token(token)
            if not email:
                return jsonify({"message": "Reset link is invalid or expired"}), 400
            current_user = get_jwt_identity()
            user = User.query.filter_by(username=current_user).first()

            if not user:
                return {"message": "User not found"}, 404
            if not new_password:
                return jsonify({"message": "New password is required"}), 400

            user.set_password(new_password)
            db.session.commit()
            log_activity(user, "Password updated")
            return {"message": "Password updated successfully"}, 200

        except Exception as e:
            return {"message": f"Error: {str(e)}"}, 500
api.add_resource(PasswordResetResource, '/password-reset')

class ActivityLogList(Resource):
    @admin_required # only allow logged-in users or admins
    def get(self):
        current_identity = get_jwt_identity()
        user = User.query.filter_by(username=current_identity).first()
        #
        # if not user:
        #     return {"message": "User not found"}, 404

        logs = Activity.query.order_by(Activity.timestamp.asc()).all()
        log_activity(user, "Activity Log")
        # logs = Activity.query.filter_by(user_id=user.id).all()

        return [
            {
                "id": l.id,
                "user_id": l.user_id,
                "action": l.action,
                "timestamp": l.timestamp.isoformat(),
                "ip_address": l.ip_address,
                "user_agent": l.user_agent,
                "email": l.user.email,
                "user":l.user.username if l.user else None
            }
            for l in logs
        ], 200

        # current_user = get_jwt_identity()
        # logs = Activity.query.filter_by(user_id=current_user['id']).all()
        # logs = Activity.query.filter_by(user_id=current_user).all()
        #
        # return [{"action": l.action, "timestamp": l.timestamp.isoformat()} for l in logs]

    # def post(self):
    #     email = request.json.get('email')
    #     user = User.query.filter_by(email=email).first()
    #     if not user:
    #         return {"message": "User not found"}, 404
    #
    #     token = generate_token(user.email)
    #     send_email(user.email, "Password Reset", f"Your password reset token: {token}")
    #
    #     # Log this activity
    #     log_activity(user, "Requested password reset")
    #
    #     return {"message": "Check your email for password reset link"}, 200
api.add_resource(ActivityLogList, '/activity-logs')

class ViewMessages(Resource):
    @admin_required
    def get(self):
        messages = Messages.query.order_by(Messages.timestamp.desc()).all()
        log_activity(user, "View Messages")

        return jsonify([
            {
                'id': msg.id,
                'sender': msg.sender_id,
                'receiver': msg.receiver_id,
                'content': msg.content,
                'timestamp': msg.timestamp
            } for msg in messages
        ])
    def delete(self,message_id):
        message = Messages.query.get(message_id)
        if not message:
            return {'message': 'Message not found'}, 404

        db.session.delete(message)
        db.session.commit()
        log_activity(user, "Message deleted")
        return {'message': f'Message {message_id} deleted successfully'}, 200
api.add_resource(ViewMessages, '/admin/messages')

class SendMessage(Resource):
    @jwt_required()
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('receiver_id', type=str, required=True, help="Receiver ID is required")
        parser.add_argument('content', type=str, required=True, help="Message content is required")
        args = parser.parse_args()

        current_identity = get_jwt_identity()
        user = User.query.filter_by(username=current_identity).first()
        log_activity(user, "Sending message")

        sender_username = get_jwt_identity()
        sender = User.query.filter_by(username=sender_username).first()
        receiver = User.query.filter_by(username=args['receiver_id']).first()


        if not receiver:
            return {"message": "Receiver not found"}, 404

        message = Messages(sender_id=sender.id, receiver_id=receiver.id, content=args['content'])
        db.session.add(message)
        db.session.commit()
        log_activity(user, "Message sent successfully")
        return {"message": "Message sent successfully ✅"}, 201
api.add_resource(SendMessage, '/messages/send')

class GetMessages(Resource):
    @jwt_required()
    def get(self):
        current_user = User.query.filter_by(username=get_jwt_identity()).first()

        current_identity = get_jwt_identity()
        user = User.query.filter_by(username=current_identity).first()
        log_activity(user, "Get Messages")

        # Fetch all messages where user is sender or receiver


        messages = Messages.query.filter(
            (Messages.sender_id == current_user.id) | (Messages.receiver_id == current_user.id)
        ).order_by(Messages.timestamp.desc()).all()

        return [
            {
                "id": m.id,
                "sender": m.sender.username,
                "receiver": m.receiver.username,
                "content": m.content,
                "timestamp": m.timestamp.isoformat(),
            }
            for m in messages
        ], 200

api.add_resource(GetMessages, '/messages')

class MarkMessageRead(Resource):
    @jwt_required()
    def put(self, message_id):
        current_user = get_jwt_identity()
        user = User.query.filter_by(username=current_user).first()

        message = Messages.query.get(message_id)
        if not message:
            return {'message': 'Message not found'}, 404

        if message.receiver_id != user.id:
            return {'message': 'You can only mark your own received messages as read'}, 403

        message.is_read = True
        db.session.commit()
        log_activity(user, f"Marked message {message_id} as read")

        return {'message': f'Message {message_id} marked as read ✅'}, 200

api.add_resource(MarkMessageRead, '/messages/<int:message_id>/read')

#ML
class TransactionAPI(Resource):
    @jwt_required()
    def post(self):
        data = request.get_json()
        current_identity = get_jwt_identity()
        user = User.query.filter_by(username=current_identity).first()
        if not user:
            return {"message": "User not found"}, 404

        description = data.get("description")
        amount = data.get("amount")
        date_str = data.get("date")  # optional "YYYY-MM-DD"
        date = datetime.strptime(date_str, "%Y-%m-%d") if date_str else None

        result = process_new_transaction(user, description, amount, date)
        log_activity(user, "Transaction created")
        return result, 201

    @jwt_required()
    def get(self):
        current_identity = get_jwt_identity()
        user = User.query.filter_by(username=current_identity).first()
        if not user:
            return {"message": "User not found"}, 404

        transactions = Transaction.query.filter_by(user_id=user.id).all()
        if user.plaid_access_token:
            self._fetch_bank_transactions(user)

        log_activity(user, "Get Transactions")

        return [
            {
                "id": t.id,
                "description": t.description,
                "amount": t.amount,
                "date": t.date.isoformat() if t.date else None,
                "category": t.category,
                "ml_confidence": t.ml_confidence
            } for t in transactions
        ], 200

    def _fetch_bank_transactions(self, user):
        """
        Internal method to fetch bank transactions and process them
        """


        # Example: fetch transactions for the last 30 days
        start_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
        end_date = datetime.utcnow().strftime("%Y-%m-%d")

        try:
            response = plaid_client.Transactions.get(
                access_token=user.plaid_access_token,
                start_date=start_date,
                end_date=end_date
            )
            transactions = response['transactions']
            for t in transactions:
                # Process each transaction via your ML pipeline
                process_new_transaction(
                    user=user,
                    description=t['name'],
                    amount=t['amount'],
                    date=datetime.strptime(t['date'], "%Y-%m-%d")
                )
                log_activity(user, f"Fetched transaction {t['description']}")
        except Exception as e:
            print(f"⚠️ Failed to fetch bank transactions for {user.username}: {e}")

api.add_resource(TransactionAPI, "/transactions")

#ML
class TransactionResource(Resource):
    @jwt_required()
    def post(self):
        try:
            data = request.get_json()
            description = data.get('description')
            amount = data.get('amount')
            date_str = data.get('date')  # Optional, format "YYYY-MM-DD HH:MM"

            # Get current user
            current_identity = get_jwt_identity()
            user = User.query.filter_by(username=current_identity).first()
            if not user:
                return {"message": "User not found"}, 404

            # Convert date string to datetime if provided
            from datetime import datetime
            date = datetime.strptime(date_str, "%Y-%m-%d %H:%M") if date_str else None

            # Process the transaction via AI module
            result = process_new_transaction(user, description, amount, date)
            log_activity(user, f"Marked transaction {result}")

            return {
                "message": "Transaction added successfully ✅",
                "transaction_category": result['transaction_category'],
                "transaction_confidence": result['transaction_confidence'],
                "insights": result['insights']
            }, 201

        except Exception as e:
            return {"message": f"Error: {str(e)}"}, 500
api.add_resource(TransactionResource, '/transactions/add')

# class CreateLinkToken(Resource):
#     def options(self):
#         return {}, 200
#
#     @jwt_required()
#     def get(self):
#         current_user = get_jwt_identity()
#         user = User.query.filter_by(username=current_user).first()
#         if not user:
#             return {"message": "User not found"}, 404
#         response = plaid_client.link_token_create({
#             'user': {'client_user_id': str(user.id)},
#             'client_name': 'FinanceTracker AI',
#             'products': ['transactions'],
#             'country_codes': ['US'],
#             'language': 'en'
#         })
#         return jsonify(response.to_dict()), 200

class CreateLinkToken(Resource):
    # @jwt_required()
    def options(self):
        # current_identity = get_jwt_identity()
        # user = User.query.filter_by(username=current_identity).first()
        # log_activity(user, "Created new link token (OPTION)")
        return {}, 200

    @jwt_required()
    def get(self):
        current_user = get_jwt_identity()
        user = User.query.filter_by(username=current_user).first()
        if not user:
            return {"message": "User not found"}, 404

        if not user.country_code:
            return {"message": "User country not set"}, 400

         # Check if Plaid supports user's country
        country = Country.query.filter_by(code=user.country_code).first()
        if not country or not country.plaid_supported:
            return {
                "message": f"Plaid not available in {user.country_code}. Please use alternative banking method."}, 400

        api_client = ApiClient(configuration)
        plaid_client = plaid_api.PlaidApi(api_client)

        try:
            response = plaid_client.link_token_create({
                'user': {'client_user_id': str(user.id)},
                'client_name': 'FinanceTracker AI (Ohmatt)',
                'products': ['transactions'],
                'country_codes': ['US'],
                'language': 'en'
            })
            log_activity(user, "Requested Plaid link token")
            return jsonify(response.to_dict())  # ✅ Convert to dict for JSON
        except Exception as e:
            return {"message": f"Error creating link token: {str(e)}"}, 500


api.add_resource(CreateLinkToken, '/bank/link-token')

class ExchangePublicToken(Resource):
    @jwt_required()
    def post(self):
        data = request.get_json()
        public_token = data.get('public_token')

        if not public_token:
            return {"message": "Public token is required"}, 400

        current_user = get_jwt_identity()
        user = User.query.filter_by(username=current_user).first()
        if not user:
            return {"message": "User not found"}, 404

        if not user.country_code:
            return {"message": "User country not set"}, 400

        country = Country.query.filter_by(code=user.country_code).first()
        user_currency = country.currency if country else None

        exchange_response = plaid_client.Item.public_token.exchange(public_token)
        user.plaid_access_token = exchange_response['access_token']
        user.plaid_item_id = exchange_response['item_id']
        db.session.commit()
        log_activity(user,"exchange public token")

        try:

            access_token = exchange_response.access_token
            item_id = exchange_response.item_id

            # Get institution info
            item_response = plaid_client.item_get(
                plaid.ItemGetRequest(access_token=access_token)
            )

            institution_id = item_response.item.institution_id

            # Get accounts
            accounts_response = plaid_client.accounts_get(
                plaid.AccountsGetRequest(access_token=access_token)
            )

            # Store accounts with proper currency
            for account in accounts_response.accounts:
                # Use account's currency or fallback to user's country currency
                account_currency = account.balances.iso_currency_code or user_currency

                bank_account = BankAccount(
                    user_id=user.id,
                    institution_name=item_response.item.institution_name or "Unknown",
                    account_name=account.name,
                    account_type=account.type,
                    account_id=account.account_id,
                    balance_available=account.balances.available,
                    balance_current=account.balances.current,
                    currency=account_currency,
                    country_code=user.country_code
                )
                db.session.add(bank_account)

            # Update user's plaid token (for backward compatibility)
            user.plaid_access_token = access_token
            user.plaid_item_id = item_id
            db.session.commit()

            log_activity(user, "Bank account linked")

            return {
                "message": "Bank account linked successfully",
                "accounts_count": len(accounts_response.accounts),
                "institution": item_response.item.institution_name,
                "currency": user_currency
            }, 201

        except Exception as e:
            return {"message": f"Error linking bank account: {str(e)}"}, 500




        # return {"message": "Bank account linked successfully ✅"}


api.add_resource(ExchangePublicToken, '/bank/exchange-token')

class FetchTransactions(Resource):
    @jwt_required()
    def post(self):
        current_user = get_jwt_identity()
        user = User.query.filter_by(username=current_user).first()
        if not user:
            return {"message": "User not found"}, 404
        if not user.plaid_access_token:
            return {"message": "Bank account not linked"}, 400

        response = plaid_client.Transactions.get(
            access_token=user.plaid_access_token,
            start_date="2025-10-01",  # customize date range
            end_date="2025-10-31"
        )

        transactions = response['transactions']
        for t in transactions:
            process_new_transaction(
                user=user,
                description=t['name'],
                amount=t['amount'],
                date=datetime.strptime(t['date'], "%Y-%m-%d")
            )
        log_activity(user,"Fetched transactions")

        return {"fetched": len(transactions)}
api.add_resource(FetchTransactions, '/bank/fetch-transactions')


class SimpleTasksAPI(Resource):
    @jwt_required()
    def get(self):
        """Simple tasks endpoint that returns empty array"""
        try:
            current_user = get_jwt_identity()
            user = User.query.filter_by(username=current_user).first()
            log_activity(user,"fetch tasks")
            return {"tasks": []}, 200
        except Exception as e:
            return {"message": f"Error: {str(e)}"}, 500

    @jwt_required()
    def post(self):
        """Simple task creation that just logs"""
        try:
            data = request.get_json()
            current_identity = get_jwt_identity()
            user = User.query.filter_by(username=current_identity).first()

            print(f"Task created: {data.get('task')}")
            log_activity(user, "task creation (simple)")
            return {"message": "Task created successfully!"}, 201

        except Exception as e:
            return {"message": f"Error: {str(e)}"}, 500


# Add this route
api.add_resource(SimpleTasksAPI, '/simple-tasks')

# Register the new API routes
class BankConnectAPI(Resource):
    @jwt_required()
    def get(self):
        """Get Plaid link token"""
        try:
            current_user = get_jwt_identity()
            user = User.query.filter_by(username=current_user).first()
            if not user:
                return {"message": "User not found"}, 404

            response = plaid_client.link_token_create({
                'user': {
                    'client_user_id': str(user.id)
                },
                'client_name': "FinanceTracker AI(Ohmatt)",
                'products': ['transactions', 'auth'],
                'country_codes': ['US'],
                'language': 'en',
                'webhook': 'https://your-webhook-url.com/plaid',  # Optional
                'account_filters': {
                    'depository': {
                        'account_subtypes': ['checking', 'savings']
                    }
                }
            })
            log_activity(user, "creating link token")

            return jsonify(response.to_dict())

        except Exception as e:
            return {"message": f"Error creating link token: {str(e)}"}, 500

    @jwt_required()
    def post(self):
        """Exchange public token for access token"""
        try:
            data = request.get_json()
            public_token = data.get('public_token')

            current_user = get_jwt_identity()
            user = User.query.filter_by(username=current_user).first()
            if not user:
                return {"message": "User not found"}, 404

            # Exchange public token for access token
            exchange_response = plaid_client.item_public_token_exchange({
                'public_token': public_token
            })
            access_token = exchange_response['access_token']
            item_id = exchange_response['item_id']

            # Get account information
            accounts_response = plaid_client.accounts_get({
                'access_token': access_token
            })

            # Store bank accounts
            for account in accounts_response['accounts']:
                if account['type'] in ['depository', 'credit']:  # Only store checking/savings/credit accounts
                    bank_account = BankAccount(
                        user_id=user.id,
                        institution_name=accounts_response['item']['institution_name'],
                        account_name=account['name'],
                        account_type=account['type'],
                        account_id=account['account_id'],
                        balance_available=account['balances'].get('available', 0),
                        balance_current=account['balances'].get('current', 0),
                        currency=account['balances'].get('iso_currency_code', 'USD')
                    )
                    db.session.add(bank_account)

            db.session.commit()

            # Fetch initial transactions
            fetch_transactions(user.id, access_token)
            log_activity(user, "Bank account connection")

            return {"message": "Bank account connected successfully!"}, 201

        except Exception as e:
            return {"message": f"Error connecting bank account: {str(e)}"}, 500
api.add_resource(BankConnectAPI, '/bank/connect')

class BankAccountsAPI(Resource):
    @jwt_required()
    def get(self):
        """Get user's connected bank accounts"""
        try:
            current_user = get_jwt_identity()
            user = User.query.filter_by(username=current_user).first()
            if not user:
                return {"message": "User not found"}, 404

            accounts = BankAccount.query.filter_by(user_id=user.id, is_active=True).all()

            log_activity(user, "bank account fetch")

            return jsonify([{
                'id': acc.id,
                'institution_name': acc.institution_name,
                'account_name': acc.account_name,
                'account_type': acc.account_type,
                'balance_available': acc.balance_available,
                'balance_current': acc.balance_current,
                'currency': acc.currency
            } for acc in accounts])

        except Exception as e:
            return {"message": f"Error fetching accounts: {str(e)}"}, 500
api.add_resource(BankAccountsAPI, '/bank/accounts')

class BankTransactionsAPI(Resource):
    @jwt_required()
    def get(self):
        """Get bank transactions with optional filtering"""
        try:
            current_user = get_jwt_identity()
            user = User.query.filter_by(username=current_user).first()
            if not user:
                return {"message": "User not found"}, 404

            # Get query parameters
            days = request.args.get('days', 30, type=int)
            account_id = request.args.get('account_id')

            start_date = (datetime.utcnow() - timedelta(days=days)).strftime('%Y-%m-%d')
            end_date = datetime.utcnow().strftime('%Y-%m-%d')

            # Fetch from database
            query = BankTransaction.query.filter_by(user_id=user.id)
            if account_id:
                query = query.filter_by(bank_account_id=account_id)

            transactions = query.filter(
                BankTransaction.date >= start_date
            ).order_by(BankTransaction.date.desc()).all()
            log_activity(user, "fetching bank transactions")

            return jsonify([{
                'id': txn.id,
                'description': txn.description,
                'amount': txn.amount,
                'date': txn.date.isoformat(),
                'category': txn.category,
                'merchant_name': txn.merchant_name,
                'pending': txn.pending,
                'account_name': txn.bank_account.account_name if txn.bank_account else 'Unknown'
            } for txn in transactions])


        except Exception as e:
            return {"message": f"Error fetching transactions: {str(e)}"}, 500
api.add_resource(BankTransactionsAPI, '/bank/transactions')

class SyncBankDataAPI(Resource):
    @jwt_required()
    def post(self):
        """Sync bank data (balances and transactions)"""
        try:
            current_user = get_jwt_identity()
            user = User.query.filter_by(username=current_user).first()
            if not user:
                return {"message": "User not found"}, 404

            # Get all user's bank accounts
            accounts = BankAccount.query.filter_by(user_id=user.id, is_active=True).all()

            for account in accounts:
                # Get access token (you'll need to store this securely)
                # For now, we'll use the user's main access token
                if user.plaid_access_token:
                    # Update balances
                    accounts_response = plaid_client.accounts_get({
                        'access_token': user.plaid_access_token
                    })

                    for plaid_account in accounts_response['accounts']:
                        if plaid_account['account_id'] == account.account_id:
                            account.balance_available = plaid_account['balances'].get('available', 0)
                            account.balance_current = plaid_account['balances'].get('current', 0)
                            break

                    # Fetch new transactions
                    fetch_transactions(user.id, user.plaid_access_token)

            db.session.commit()
            log_activity(user,"Sync Bank Data")

            return {"message": "Bank data synced successfully!"}, 200

        except Exception as e:
            return {"message": f"Error syncing bank data: {str(e)}"}, 500


# Helper function to fetch transactions
def fetch_transactions(user_id, access_token, days=30):
    """Fetch transactions from Plaid and store in database"""
    try:
        # current_identity = get_jwt_identity()
        # user = User.query.filter_by(username=current_identity).first()
        start_date = (datetime.utcnow() - timedelta(days=days)).strftime('%Y-%m-%d')
        end_date = datetime.utcnow().strftime('%Y-%m-%d')

        transactions_response = plaid_client.transactions_get({
            'access_token': access_token,
            'start_date': start_date,
            'end_date': end_date
        })

        for txn in transactions_response['transactions']:
            # Check if transaction already exists
            existing_txn = BankTransaction.query.filter_by(
                transaction_id=txn['transaction_id']
            ).first()

            if not existing_txn:
                # Find the bank account
                bank_account = BankAccount.query.filter_by(
                    account_id=txn['account_id']
                ).first()

                if bank_account:
                    bank_txn = BankTransaction(
                        user_id=user_id,
                        bank_account_id=bank_account.id,
                        transaction_id=txn['transaction_id'],
                        description=txn['name'],
                        amount=txn['amount'],
                        date=datetime.strptime(txn['date'], '%Y-%m-%d'),
                        category=', '.join(txn.get('category', [])),
                        pending=txn['pending'],
                        merchant_name=txn.get('merchant_name')
                    )
                    db.session.add(bank_txn)

        db.session.commit()
        log_activity(user, "fetch transactions")

    except Exception as e:
        print(f"Error fetching transactions: {e}")
api.add_resource(SyncBankDataAPI, '/bank/sync')



# Request parsers for filtering
countries_parser = reqparse.RequestParser()
countries_parser.add_argument('continent', type=str, location='args', help='Filter by continent code')
countries_parser.add_argument('language', type=str, location='args', help='Filter by language code')
countries_parser.add_argument('plaid_supported', type=lambda x: x.lower() == 'true', location='args',
                              help='Filter by Plaid support')


class CountriesResource(Resource):
    def get(self):
        """Get all countries with optional filtering"""
        try:
            args = countries_parser.parse_args()

            query = Country.query

            if args['continent']:
                query = query.filter_by(continent=args['continent'].upper())
            if args['language']:
                query = query.filter_by(language=args['language'].lower())
            if args['plaid_supported'] is not None:
                query = query.filter_by(plaid_supported=args['plaid_supported'])

            countries = query.order_by(Country.name.asc()).all()

            return {
                'success': True,
                'count': len(countries),
                'countries': [{
                    'code': c.code,
                    'name': c.name,
                    'continent': c.continent,
                    'currency': c.currency,
                    'timezone': c.timezone,
                    'language': c.language,
                    'plaid_supported': c.plaid_supported,
                    'other_provider': c.other_provider
                } for c in countries]
            }, 200

        except Exception as e:
            return {
                'success': False,
                'message': f'Error fetching countries: {str(e)}'
            }, 500


class CountryDetailResource(Resource):
    def get(self, country_code):
        """Get details for a specific country"""
        try:
            country = Country.query.filter_by(code=country_code.upper()).first()

            if not country:
                return {
                    'success': False,
                    'message': f'Country with code {country_code} not found'
                }, 404

            return {
                'success': True,
                'country': {
                    'code': country.code,
                    'name': country.name,
                    'continent': country.continent,
                    'currency': country.currency,
                    'timezone': country.timezone,
                    'language': country.language,
                    'plaid_supported': country.plaid_supported,
                    'other_provider': country.other_provider,
                    'plaid_country_code': country.plaid_country_code
                }
            }, 200

        except Exception as e:
            return {
                'success': False,
                'message': f'Error fetching country: {str(e)}'
            }, 500


class ContinentsResource(Resource):
    def get(self):
        """Get all continents"""
        try:
            continents = Continent.query.order_by(Continent.name.asc()).all()

            return {
                'success': True,
                'count': len(continents),
                'continents': [{
                    'code': c.code,
                    'name': c.name
                } for c in continents]
            }, 200

        except Exception as e:
            return {
                'success': False,
                'message': f'Error fetching continents: {str(e)}'
            }, 500


class ContinentCountriesResource(Resource):
    def get(self, continent_code):
        """Get all countries in a specific continent"""
        try:
            continent = Continent.query.filter_by(code=continent_code.upper()).first()

            if not continent:
                return {
                    'success': False,
                    'message': f'Continent with code {continent_code} not found'
                }, 404

            countries = Country.query.filter_by(continent=continent.code).order_by(Country.name.asc()).all()

            return {
                'success': True,
                'continent': {
                    'code': continent.code,
                    'name': continent.name
                },
                'count': len(countries),
                'countries': [{
                    'code': c.code,
                    'name': c.name,
                    'currency': c.currency,
                    'plaid_supported': c.plaid_supported
                } for c in countries]
            }, 200

        except Exception as e:
            return {
                'success': False,
                'message': f'Error fetching continent countries: {str(e)}'
            }, 500


class LanguagesResource(Resource):
    def get(self):
        """Get all languages"""
        try:
            languages = Language.query.order_by(Language.name.asc()).all()

            return {
                'success': True,
                'count': len(languages),
                'languages': [{
                    'code': l.code,
                    'name': l.name,
                    'native_name': l.native_name
                } for l in languages]
            }, 200

        except Exception as e:
            return {
                'success': False,
                'message': f'Error fetching languages: {str(e)}'
            }, 500


class LanguageDetailResource(Resource):
    def get(self, language_code):
        """Get details for a specific language"""
        try:
            language = Language.query.filter_by(code=language_code.lower()).first()

            if not language:
                return {
                    'success': False,
                    'message': f'Language with code {language_code} not found'
                }, 404

            return {
                'success': True,
                'language': {
                    'code': language.code,
                    'name': language.name,
                    'native_name': language.native_name
                }
            }, 200

        except Exception as e:
            return {
                'success': False,
                'message': f'Error fetching language: {str(e)}'
            }, 500


class SupportedBankingCountriesResource(Resource):
    def get(self):
        """Get countries with banking provider support"""
        try:
            # Get all countries with any banking provider
            countries = Country.query.filter(
                (Country.plaid_supported == True) |
                (Country.other_provider.isnot(None))
            ).order_by(Country.name.asc()).all()

            result = []
            for country in countries:
                providers = []
                if country.plaid_supported:
                    providers.append('plaid')
                if country.other_provider:
                    providers.append(country.other_provider)

                result.append({
                    'code': country.code,
                    'name': country.name,
                    'continent': country.continent,
                    'currency': country.currency,
                    'providers': providers,
                    'plaid_supported': country.plaid_supported
                })

            return {
                'success': True,
                'count': len(result),
                'countries': result
            }, 200

        except Exception as e:
            return {
                'success': False,
                'message': f'Error fetching supported countries: {str(e)}'
            }, 500


class DetectLocationResource(Resource):
    def get(self):
        """Detect user's location based on IP"""
        try:
            # Try to import geoip2 if available
            try:
                import geoip2.database
                from geoip2.errors import AddressNotFoundError

                # For production, you'd use a proper GeoIP database
                # This is just a template
                ip_address = request.remote_addr

                # Example structure - you'd need to download GeoLite2 database
                # reader = geoip2.database.Reader('GeoLite2-City.mmdb')
                # response = reader.city(ip_address)

                # For now, return default values
                return {
                    'success': True,
                    'detected': {
                        'ip': ip_address,
                        'country': 'US',  # Default fallback
                        'continent': 'NA',
                        'timezone': 'America/New_York',
                        'method': 'ip_detection'
                    },
                    'note': 'Using default location. Install geoip2 and add GeoLite2 database for accurate detection.'
                }, 200

            except ImportError:
                # Fallback to request headers or defaults
                ip_address = request.remote_addr

                # Check Cloudflare headers (if using Cloudflare)
                country_from_header = request.headers.get('CF-IPCountry')
                timezone_from_header = request.headers.get('CF-Timezone')

                return {
                    'success': True,
                    'detected': {
                        'ip': ip_address,
                        'country': country_from_header or 'US',
                        'continent': self._get_continent_from_country(
                            country_from_header) if country_from_header else 'NA',
                        'timezone': timezone_from_header or 'UTC',
                        'method': 'header_detection' if country_from_header else 'default_fallback'
                    },
                    'note': 'Using headers for location detection. For better accuracy, install geoip2.'
                }, 200

        except Exception as e:
            return {
                'success': False,
                'message': f'Error detecting location: {str(e)}'
            }, 500

    def _get_continent_from_country(self, country_code):
        """Helper to get continent from country code"""
        if not country_code:
            return 'NA'

        country = Country.query.filter_by(code=country_code.upper()).first()
        if country:
            return country.continent

        # Fallback mapping for common countries
        continent_map = {
            'US': 'NA', 'CA': 'NA', 'MX': 'NA',
            'GB': 'EU', 'FR': 'EU', 'DE': 'EU', 'ES': 'EU', 'IT': 'EU',
            'AU': 'OC', 'NZ': 'OC',
            'JP': 'AS', 'CN': 'AS', 'IN': 'AS', 'KR': 'AS',
            'ZA': 'AF', 'NG': 'AF', 'KE': 'AF',
            'BR': 'SA', 'AR': 'SA', 'CL': 'SA'
        }

        return continent_map.get(country_code.upper(), 'NA')


# Admin Resources (if you want admin-only geo management)
class AdminCountriesResource(Resource):
    @jwt_required()
    def post(self):
        """Add a new country (admin only)"""
        try:

            current_user = get_jwt_identity()
            user = User.query.filter_by(username=current_user).first()

            if not user or not user.is_admin:
                return {
                    'success': False,
                    'message': 'Admin access required'
                }, 403

            data = request.get_json()

            # Validate required fields
            required_fields = ['code', 'name', 'continent', 'currency', 'timezone', 'language']
            for field in required_fields:
                if field not in data:
                    return {
                        'success': False,
                        'message': f'Missing required field: {field}'
                    }, 400

            # Check if country already exists
            if Country.query.filter_by(code=data['code'].upper()).first():
                return {
                    'success': False,
                    'message': f'Country with code {data["code"]} already exists'
                }, 400

            # Create new country
            country = Country(
                code=data['code'].upper(),
                name=data['name'],
                continent=data['continent'].upper(),
                currency=data['currency'].upper(),
                timezone=data['timezone'],
                language=data['language'].lower(),
                plaid_supported=data.get('plaid_supported', False),
                plaid_country_code=data.get('plaid_country_code'),
                other_provider=data.get('other_provider')
            )

            db.session.add(country)
            db.session.commit()

            return {
                'success': True,
                'message': f'Country {country.name} added successfully',
                'country': {
                    'code': country.code,
                    'name': country.name
                }
            }, 201

        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Error adding country: {str(e)}'
            }, 500


# New Resource for getting supported countries
class SupportedCountriesResource(Resource):
    def get(self):
        """Get countries supported by banking providers"""
        plaid_supported = request.args.get('plaid_supported', 'true').lower() == 'true'

        query = Country.query
        if plaid_supported:
            query = query.filter_by(plaid_supported=True)

        countries = query.all()

        result = []
        for country in countries:
            providers = []
            if country.plaid_supported:
                providers.append('plaid')
            if country.other_provider:
                providers.append(country.other_provider)

            result.append({
                'code': country.code,
                'name': country.name,
                'continent': country.continent,
                'currency': country.currency,
                'providers': providers,
                'plaid_supported': country.plaid_supported
            })

        return jsonify(result), 200
api.add_resource(SupportedCountriesResource, '/bank/supported-countries')

# Keep all your existing Resources (TasksAPI, VerifyAccount, PasswordResetResource, etc.)
# with minimal modifications to use the new user model

class UpdateProfileResource(Resource):
    @jwt_required()
    def put(self):
        """Update user profile including country/language"""
        current_identity = get_jwt_identity()
        user = User.query.filter_by(username=current_identity).first()

        if not user:
            return {"message": "User not found"}, 404

        data = request.get_json()

        # Update country if provided
        if 'country_code' in data:
            country = Country.query.filter_by(code=data['country_code'].upper()).first()
            if not country:
                return {"message": "Invalid country code"}, 400
            user.country_code = country.code

            # Update continent based on country
            continent = Continent.query.filter_by(code=country.continent).first()
            if continent:
                user.continent_code = continent.code

        # Update language if provided
        if 'language_code' in data:
            language = Language.query.filter_by(code=data['language_code'].lower()).first()
            if not language:
                return {"message": "Invalid language code"}, 400
            user.language_code = language.code

        # Update timezone if provided
        if 'timezone' in data:
            user.timezone = data['timezone']

        db.session.commit()
        log_activity(user, "Profile updated")

        return {"message": "Profile updated successfully"}, 200
api.add_resource(UpdateProfileResource, '/profile/update')

# Register all resources

api.add_resource(CountriesResource, '/countries')
api.add_resource(CountryDetailResource, '/countries/<string:country_code>')
api.add_resource(ContinentsResource, '/continents')
api.add_resource(ContinentCountriesResource, '/continents/<string:continent_code>/countries')
api.add_resource(LanguagesResource, '/languages')
api.add_resource(LanguageDetailResource, '/languages/<string:language_code>')
api.add_resource(SupportedBankingCountriesResource, '/banking/supported-countries')
api.add_resource(DetectLocationResource, '/location/detect')
api.add_resource(AdminCountriesResource, '/admin/countries')  # Admin only

# Request parsers
bank_connect_parser = reqparse.RequestParser()
bank_connect_parser.add_argument('provider', type=str, required=False,
                                 help='Specific provider to use (optional)')
bank_connect_parser.add_argument('account_number', type=str, required=False)
bank_connect_parser.add_argument('bank_code', type=str, required=False)


class UnifiedBankConnectResource(Resource):
    """Unified banking connection for all providers"""

    @jwt_required()
    def get(self):
        """Get banking connection options for user's country"""
        current_user = get_jwt_identity()
        user = User.query.filter_by(username=current_user).first()

        if not user:
            return {"success": False, "message": "User not found"}, 404

        if not user.country_code:
            return {"success": False, "message": "User country not set"}, 400

        country = Country.query.filter_by(code=user.country_code).first()
        if not country:
            return {"success": False, "message": "Invalid country code"}, 400

        # Get available providers for user's country
        available_providers = ProviderRegistry.get_providers_for_country(user.country_code)

        if not available_providers:
            return {
                "success": False,
                "message": f"No banking providers available for {country.name}",
                "country": user.country_code
            }, 400

        # Get provider details
        providers_info = []
        for provider_name in available_providers:
            # Check if provider is configured
            config_key = f"{provider_name.upper()}_CONFIG"
            provider_config = app.config.get(config_key, {})

            if provider_config.get('enabled', True):
                providers_info.append({
                    'name': provider_name,
                    'display_name': provider_name.title(),
                    'supported_features': self._get_provider_features(provider_name),
                    'requires_account_number': provider_name in ['flutterwave', 'paystack', 'mono']
                })

        return {
            "success": True,
            "country": {
                "code": user.country_code,
                "name": country.name,
                "currency": country.currency
            },
            "available_providers": providers_info,
            "recommended_provider": available_providers[0]  # First is default
        }, 200

    @jwt_required()
    def post(self):
        """Connect to banking provider"""
        args = bank_connect_parser.parse_args()
        current_user = get_jwt_identity()
        user = User.query.filter_by(username=current_user).first()

        if not user:
            return {"success": False, "message": "User not found"}, 404

        # Determine which provider to use
        provider_name = args.get('provider')
        if not provider_name:
            # Use default for user's country
            provider_name = ProviderRegistry.get_default_provider_for_country(user.country_code)
            if not provider_name:
                return {"success": False, "message": "No provider available for your country"}, 400

        # Get provider config
        config_key = f"{provider_name.upper()}_CONFIG"
        provider_config = app.config.get(config_key, {})

        if not provider_config:
            return {"success": False, "message": f"Provider {provider_name} not configured"}, 400

        try:
            # Create provider instance
            provider = ProviderRegistry.create_provider(provider_name, provider_config)

            # Different providers have different connection methods
            if provider_name in ['flutterwave', 'paystack', 'mono']:
                # African providers often use account verification
                account_number = args.get('account_number')
                bank_code = args.get('bank_code')

                if not account_number or not bank_code:
                    return {
                        "success": False,
                        "message": "Account number and bank code required for this provider"
                    }, 400

                # Verify account
                if hasattr(provider, 'verify_bank_account'):
                    result = provider.verify_bank_account(account_number, bank_code, user.country_code)

                    if result.get('success'):
                        # Store connection
                        connection = BankConnection(
                            user_id=user.id,
                            provider_id=provider_name,
                            institution_name=result.get('bank_name', 'Unknown'),
                            account_name=result.get('account_name'),
                            account_number=account_number,
                            bank_code=bank_code,
                            is_active=True
                        )

                        db.session.add(connection)
                        db.session.commit()

                        logger.info(f"User {user.id} connected {provider_name} account")

                        return {
                            "success": True,
                            "message": f"Bank account verified and connected via {provider_name}",
                            "connection_id": connection.id,
                            "account_name": result.get('account_name'),
                            "provider": provider_name
                        }, 201
                    else:
                        return {
                            "success": False,
                            "message": f"Account verification failed: {result.get('error')}"
                        }, 400

            elif provider_name == 'plaid':
                # Plaid uses link tokens (handled by existing PlaidResource)
                return {
                    "success": False,
                    "message": "Use /bank/link-token endpoint for Plaid"
                }, 400

            else:
                # Other providers (OAuth flow)
                link_data = provider.create_link_token(str(user.id), user.country_code)

                return {
                    "success": True,
                    "provider": provider_name,
                    "connection_method": link_data.get('auth_type', 'oauth'),
                    "data": link_data
                }, 200

        except Exception as e:
            logger.error(f"Error connecting to {provider_name}: {str(e)}")
            return {
                "success": False,
                "message": f"Error connecting to {provider_name}: {str(e)}"
            }, 500

    def _get_provider_features(self, provider_name: str) -> List[str]:
        """Get features supported by provider"""
        features_map = {
            'plaid': ['transactions', 'balances', 'accounts', 'auth'],
            'flutterwave': ['account_verification', 'transfers', 'payments', 'balance'],
            'paystack': ['account_verification', 'payments', 'subscriptions'],
            'mono': ['account_linking', 'transactions', 'identity'],
            'stitch': ['payments', 'account_linking'],
            'okra': ['account_linking', 'transactions', 'income'],
            'bloc': ['account_linking', 'transfers']
        }

        return features_map.get(provider_name, ['payments'])


class BankAccountsResource(Resource):
    """Get user's connected bank accounts across all providers"""

    @jwt_required()
    def get(self):
        current_user = get_jwt_identity()
        user = User.query.filter_by(username=current_user).first()

        if not user:
            return {"success": False, "message": "User not found"}, 404

        connections = BankConnection.query.filter_by(user_id=user.id, is_active=True).all()

        accounts = []
        for conn in connections:
            accounts.append({
                'id': conn.id,
                'provider': conn.provider_id,
                'institution_name': conn.institution_name,
                'account_name': conn.account_name,
                'account_number': conn.account_number,
                'created_at': conn.created_at.isoformat() if conn.created_at else None,
                'last_sync': conn.last_sync.isoformat() if conn.last_sync else None
            })

        return {
            "success": True,
            "count": len(accounts),
            "accounts": accounts
        }, 200


class WebhookResource(Resource):
    """Handle webhooks from various banking providers"""

    def post(self, provider_name: str):
        """Process webhook from banking provider"""
        webhook_data = request.get_json()
        signature = request.headers.get('x-paystack-signature') or \
                    request.headers.get('verif-hash') or \
                    request.headers.get('x-flutterwave-signature')

        # Get provider config
        config_key = f"{provider_name.upper()}_CONFIG"
        provider_config = app.config.get(config_key, {})

        if not provider_config:
            logger.warning(f"Webhook from unconfigured provider: {provider_name}")
            return {"success": False, "message": "Provider not configured"}, 400

        try:
            # Create provider instance
            provider = ProviderRegistry.create_provider(provider_name, provider_config)

            # Verify signature if required
            if hasattr(provider, 'verify_webhook_signature'):
                if not provider.verify_webhook_signature(request.data.decode('utf-8'), signature):
                    logger.warning(f"Invalid webhook signature from {provider_name}")
                    return {"success": False, "message": "Invalid signature"}, 400

            # Process webhook based on provider
            transaction = None
            if provider_name == 'paystack':
                if hasattr(provider, 'process_transaction_webhook'):
                    transaction = provider.process_transaction_webhook(webhook_data)
            elif provider_name == 'flutterwave':
                # Process Flutterwave webhook
                transaction = self._process_flutterwave_webhook(webhook_data)

            # Store transaction in database if applicable
            if transaction:
                self._store_transaction(transaction)
                logger.info(f"Processed {provider_name} webhook: {transaction.get('reference')}")

            return {"success": True, "message": "Webhook processed"}, 200

        except Exception as e:
            logger.error(f"Error processing {provider_name} webhook: {str(e)}")
            return {"success": False, "message": "Webhook processing failed"}, 500

    def _process_flutterwave_webhook(self, data: Dict) -> Dict[str, Any]:
        """Process Flutterwave webhook"""
        event = data.get('event')
        transaction_data = data.get('data', {})

        return {
            'provider': 'flutterwave',
            'event': event,
            'transaction_id': transaction_data.get('id'),
            'tx_ref': transaction_data.get('tx_ref'),
            'amount': transaction_data.get('amount'),
            'currency': transaction_data.get('currency'),
            'status': transaction_data.get('status'),
            'payment_type': transaction_data.get('payment_type'),
            'created_at': transaction_data.get('created_at'),
            'customer': transaction_data.get('customer', {})
        }

    def _store_transaction(self, transaction: Dict):
        """Store transaction from webhook"""


        # Find user by email or reference
        user = None
        if 'customer' in transaction:
            email = transaction['customer'].get('email')
            if email:
                user = User.query.filter_by(email=email).first()

        if user:
            bank_txn = BankTransaction(
                user_id=user.id,
                transaction_id=transaction.get('transaction_id') or transaction.get('reference'),
                description=f"{transaction.get('provider')} transaction",
                amount=transaction.get('amount', 0),
                date=datetime.utcnow(),
                currency=transaction.get('currency', 'NGN'),
                metadata=transaction
            )

            db.session.add(bank_txn)
            db.session.commit()


class GlobalBankConnectResource(Resource):
    """Global banking connection for all providers"""

    @jwt_required()
    def get(self):
        """Get available banking options for user's country"""
        current_user = get_jwt_identity()
        user = User.query.filter_by(username=current_user).first()

        if not user:
            return {"success": False, "message": "User not found"}, 404

        if not user.country_code:
            return {"success": False, "message": "User country not set"}, 400

        country = Country.query.filter_by(code=user.country_code).first()
        if not country:
            return {"success": False, "message": "Invalid country code"}, 400

        # Get available providers
        providers = ProviderRegistry.get_providers_for_country(user.country_code)

        if not providers:
            return {
                "success": False,
                "message": f"No banking providers available for {country.name}",
                "country": user.country_code
            }, 400

        # Get provider details
        providers_info = []
        for provider_name in providers:
            config_key = f"{provider_name.upper()}_CONFIG"
            provider_config = current_app.config.get(config_key, {})

            if provider_config.get('enabled', True):
                try:
                    provider = ProviderRegistry.create_provider(provider_name, provider_config)
                    capabilities = provider.get_capabilities()

                    providers_info.append({
                        'name': provider_name,
                        'display_name': provider_name.title(),
                        'capabilities': capabilities,
                        'method': 'oauth' if provider_name in ['plaid', 'truelayer'] else 'account_verification'
                    })
                except Exception as e:
                    logger.error(f"Error creating provider {provider_name}: {e}")
                    continue

        return {
            "success": True,
            "country": {
                "code": user.country_code,
                "name": country.name,
                "currency": country.currency
            },
            "available_providers": providers_info,
            "recommended": providers[0]
        }, 200
api.add_resource(GlobalBankConnectResource, '/banking/options')


def seed_geo_data():
    with app.app_context():
        # Messages.__table__.drop(db.engine)
        # Messages.__table__.create(db.engine)

        # Messages.__table__.drop(db.engine)
        # admin = User(username="Ohmatt", email="mattwhingan@gmail.com",  is_admin=True)
        # admin.set_password("160118+Oh")
        # db.session.add(admin)
        # db.session.commit()
        # print("✅ Admin user created")
        me = User.query.filter_by(username="Ohmatt").first()
        if me:
            me.is_admin = True
            db.session.commit()
            print("Admin privileges granted ✅")
        else:
            print("User not found ❌")
        db.create_all()


        # Clear existing data
        db.session.query(Country).delete()
        db.session.query(Continent).delete()
        db.session.query(Language).delete()

        print("Seeding African countries...")

        # Ensure Africa continent exists
        africa = Continent.query.filter_by(code='AF').first()
        if not africa:
            africa = Continent(code='AF', name='Africa')
            db.session.add(africa)
            db.session.commit()

        # Add African countries with banking providers
        african_countries = [
            # Nigeria - multiple providers
            {
                'code': 'NG', 'name': 'Nigeria', 'continent': 'AF',
                'currency': 'NGN', 'timezone': 'Africa/Lagos',
                'language': 'en', 'plaid_supported': False,
                'other_provider': 'flutterwave'  # Primary provider
            },
            # Kenya
            {
                'code': 'KE', 'name': 'Kenya', 'continent': 'AF',
                'currency': 'KES', 'timezone': 'Africa/Nairobi',
                'language': 'en', 'plaid_supported': False,
                'other_provider': 'flutterwave'
            },
            # Ghana
            {
                'code': 'GH', 'name': 'Ghana', 'continent': 'AF',
                'currency': 'GHS', 'timezone': 'Africa/Accra',
                'language': 'en', 'plaid_supported': False,
                'other_provider': 'flutterwave'
            },
            # South Africa
            {
                'code': 'ZA', 'name': 'South Africa', 'continent': 'AF',
                'currency': 'ZAR', 'timezone': 'Africa/Johannesburg',
                'language': 'en', 'plaid_supported': False,
                'other_provider': 'stitch'
            },
            # Rwanda
            {
                'code': 'RW', 'name': 'Rwanda', 'continent': 'AF',
                'currency': 'RWF', 'timezone': 'Africa/Kigali',
                'language': 'en', 'plaid_supported': False,
                'other_provider': 'flutterwave'
            },
            # Uganda
            {
                'code': 'UG', 'name': 'Uganda', 'continent': 'AF',
                'currency': 'UGX', 'timezone': 'Africa/Kampala',
                'language': 'en', 'plaid_supported': False,
                'other_provider': 'flutterwave'
            },
            # Tanzania
            {
                'code': 'TZ', 'name': 'Tanzania', 'continent': 'AF',
                'currency': 'TZS', 'timezone': 'Africa/Dar_es_Salaam',
                'language': 'sw', 'plaid_supported': False,
                'other_provider': 'flutterwave'
            },
            # Egypt
            {
                'code': 'EG', 'name': 'Egypt', 'continent': 'AF',
                'currency': 'EGP', 'timezone': 'Africa/Cairo',
                'language': 'ar', 'plaid_supported': False,
                'other_provider': 'other'  # Need specific Egyptian provider
            },
            # Ethiopia
            {
                'code': 'ET', 'name': 'Ethiopia', 'continent': 'AF',
                'currency': 'ETB', 'timezone': 'Africa/Addis_Ababa',
                'language': 'am', 'plaid_supported': False,
                'other_provider': 'other'
            },
            # Morocco
            {
                'code': 'MA', 'name': 'Morocco', 'continent': 'AF',
                'currency': 'MAD', 'timezone': 'Africa/Casablanca',
                'language': 'ar', 'plaid_supported': False,
                'other_provider': 'other'
            },
        ]

        for data in african_countries:
            country = Country.query.filter_by(code=data['code']).first()
            if not country:
                country = Country(**data)
                db.session.add(country)
                print(f"Added {data['name']} ({data['code']})")
            else:
                # Update existing country
                for key, value in data.items():
                    setattr(country, key, value)
                print(f"Updated {data['name']} ({data['code']})")

        db.session.commit()
        print(f"✅ Seeded {len(african_countries)} African countries")

        # Add continents
        continents = [
            {'code': 'AF', 'name': 'Africa'},
            {'code': 'AS', 'name': 'Asia'},
            {'code': 'EU', 'name': 'Europe'},
            {'code': 'NA', 'name': 'North America'},
            {'code': 'SA', 'name': 'South America'},
            {'code': 'OC', 'name': 'Oceania'},
            {'code': 'AN', 'name': 'Antarctica'}
        ]

        for data in continents:
            continent = Continent(**data)
            db.session.add(continent)

        # Add languages
        languages = [
            {'code': 'en', 'name': 'English', 'native_name': 'English'},
            {'code': 'es', 'name': 'Spanish', 'native_name': 'Español'},
            {'code': 'fr', 'name': 'French', 'native_name': 'Français'},
            {'code': 'de', 'name': 'German', 'native_name': 'Deutsch'},
            {'code': 'pt', 'name': 'Portuguese', 'native_name': 'Português'},
            {'code': 'zh', 'name': 'Chinese', 'native_name': '中文'},
            {'code': 'ar', 'name': 'Arabic', 'native_name': 'العربية'},
            {'code': 'hi', 'name': 'Hindi', 'native_name': 'हिन्दी'},
            {'code': 'ru', 'name': 'Russian', 'native_name': 'Русский'},
            {'code': 'ja', 'name': 'Japanese', 'native_name': '日本語'}
        ]

        for data in languages:
            language = Language(**data)
            db.session.add(language)

        # Add sample countries (focus on Plaid-supported ones)
        countries = [
            {
                'code': 'US', 'name': 'United States', 'continent': 'NA',
                'currency': 'USD', 'timezone': 'America/New_York',
                'language': 'en', 'plaid_supported': True, 'plaid_country_code': 'US'
            },
            {
                'code': 'CA', 'name': 'Canada', 'continent': 'NA',
                'currency': 'CAD', 'timezone': 'America/Toronto',
                'language': 'en', 'plaid_supported': True, 'plaid_country_code': 'CA'
            },
            {
                'code': 'GB', 'name': 'United Kingdom', 'continent': 'EU',
                'currency': 'GBP', 'timezone': 'Europe/London',
                'language': 'en', 'plaid_supported': True, 'plaid_country_code': 'GB'
            },
            {
                'code': 'IE', 'name': 'Ireland', 'continent': 'EU',
                'currency': 'EUR', 'timezone': 'Europe/Dublin',
                'language': 'en', 'plaid_supported': True, 'plaid_country_code': 'IE'
            },
            {
                'code': 'ES', 'name': 'Spain', 'continent': 'EU',
                'currency': 'EUR', 'timezone': 'Europe/Madrid',
                'language': 'es', 'plaid_supported': True, 'plaid_country_code': 'ES'
            },
            {
                'code': 'FR', 'name': 'France', 'continent': 'EU',
                'currency': 'EUR', 'timezone': 'Europe/Paris',
                'language': 'fr', 'plaid_supported': True, 'plaid_country_code': 'FR'
            },
            {
                'code': 'NL', 'name': 'Netherlands', 'continent': 'EU',
                'currency': 'EUR', 'timezone': 'Europe/Amsterdam',
                'language': 'nl', 'plaid_supported': True, 'plaid_country_code': 'NL'
            },
            {
                'code': 'DE', 'name': 'Germany', 'continent': 'EU',
                'currency': 'EUR', 'timezone': 'Europe/Berlin',
                'language': 'de', 'plaid_supported': True, 'plaid_country_code': 'DE'
            },
            # Add more countries as needed
        ]

        for data in countries:
            country = Country(**data)
            db.session.add(country)

        db.session.commit()
        print("✅ Geo data seeded successfully!")

# with app.app_context():
#     # Messages.__table__.drop(db.engine)
#     # Messages.__table__.create(db.engine)
#
#     # Messages.__table__.drop(db.engine)
#     # admin = User(username="Ohmatt", email="mattwhingan@gmail.com",  is_admin=True)
#     # admin.set_password("160118+Oh")
#     # db.session.add(admin)
#     # db.session.commit()
#     # print("✅ Admin user created")
#     me = User.query.filter_by(username="Ohmatt").first()
#     if me:
#         me.is_admin = True
#         db.session.commit()
#         print("Admin privileges granted ✅")
#     else:
#         print("User not found ❌")
#     db.create_all()
if __name__ == '__main__':
    app.run(debug=True)
    seed_geo_data()