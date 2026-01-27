from datetime import datetime, timedelta
from flask_cors import CORS
from flask import request, jsonify, render_template
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from plaid.model.country_code import CountryCode
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.products import Products
from sqlalchemy import create_engine
from flask_restful import Resource, marshal_with, reqparse, fields

from itsdangerous import URLSafeTimedSerializer
from sqlalchemy.sql.functions import user

from model import User, Transaction, Activity,Messages, Tasks, app,api,Base,db, BankTransaction, BankAccount

from plaid.api import plaid_api
from plaid.api_client import ApiClient
from plaid.configuration import Configuration

from utils import get_user_task_session, log_activity, generate_token, send_email, confirm_token, admin_required, \
    process_new_transaction

configuration = Configuration(
    host="https://sandbox.plaid.com",
    api_key={
        "clientId": "6904bdc5aa4c2b0023d6da8d",
        "secret": "46b9ceda54767660b4e59e0805c71e"
    }
)
api_client = ApiClient(configuration)
plaid_client = plaid_api.PlaidApi(api_client)




CORS(app,resources={r"/*": {"origins":  ["http://localhost:3000", "http://127.0.0.1:3000"]}},
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
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

user_field={
    'id':fields.Integer,
    'username':fields.String,
    'email':fields.String,
    'password':fields.String,
}

class UserRegister(Resource):
    def post(self):
        try:
            data = request.get_json()
            # user= data['username']
            if User.query.filter((User.username == data['username']) | (User.email == data['email'])).first():
                return {"message": "Username or email already exists"}, 400

            db_name = f"{data['username']}_tasks.db"
            new_user = User(username=data['username'], email=data['email'], db_name=db_name)
            new_user.set_password(data['password'])
            db.session.add(new_user)
            db.session.commit()

            engine = create_engine(f"sqlite:///{db_name}")
            Base.metadata.create_all(engine)


            token = generate_token(data['email'])
            send_email(data['email'], "Verify Your Account", f"Your verification token: {token}")
            log_activity(new_user, "User registered")
            return {"message": "User registered. Check your email for verification token."}, 201

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
            if user and user.check_password(data['password']):
                if user.is_admin:
                    access_token = create_access_token(identity=user.username)
                    log_activity(user, "Admin login")
                    return {
                        "message": "Welcome Admin!",
                        "access_token": access_token
                    }, 200

                access_token = create_access_token(identity=user.username)  # or identity=user.id
                log_activity(user, "User login")
                return {'message': 'User login successfully', 'access_token': access_token}, 200
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
        if not current_user:
            return {"message": "Unauthorized, no identity in token"}, 401
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

        return {'message': 'User login failed'}, 401
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

        current_user = get_jwt_identity()
        user = User.query.filter_by(username=current_user).first()
        if not user:
            return {"message": "User not found"}, 404

        exchange_response = plaid_client.Item.public_token.exchange(public_token)
        user.plaid_access_token = exchange_response['access_token']
        user.plaid_item_id = exchange_response['item_id']
        db.session.commit()
        log_activity(user,"exchange public token")

        return {"message": "Bank account linked successfully ✅"}
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
if __name__ == '__main__':
    app.run(debug=True)