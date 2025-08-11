from flask import Blueprint, request, jsonify
from src.models.user import db, User
from datetime import datetime

user_bp = Blueprint('user', __name__)

@user_bp.route('/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        
        user = User.query.filter_by(username=username, active=True).first()
        
        if user and user.check_password(password):
            return jsonify({
                'success': True,
                'user': user.to_dict(),
                'message': 'Login successful'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid username or password'
            }), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@user_bp.route('/users', methods=['GET'])
def get_users():
    try:
        users = User.query.filter_by(active=True).all()
        return jsonify([user.to_dict() for user in users])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@user_bp.route('/users', methods=['POST'])
def create_user():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'code', 'password', 'role', 'branch']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Check if username or code already exists
        existing_user = User.query.filter(
            (User.username == data['username']) | (User.code == data['code'])
        ).first()
        
        if existing_user:
            return jsonify({'error': 'Username or code already exists'}), 400
        
        user = User(
            username=data['username'],
            code=data['code'],
            password=data['password'],  # In production, hash this
            role=data['role'],
            branch=data['branch'],
            last_serial=data.get('lastSerial', 1000),
            storage_url=data.get('storageUrl', 'local')
        )
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify(user.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    try:
        user = User.query.get_or_404(user_id)
        return jsonify(user.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        # Update fields
        if 'username' in data:
            # Check if new username already exists
            existing = User.query.filter(User.username == data['username'], User.id != user_id).first()
            if existing:
                return jsonify({'error': 'Username already exists'}), 400
            user.username = data['username']
        
        if 'code' in data:
            # Check if new code already exists
            existing = User.query.filter(User.code == data['code'], User.id != user_id).first()
            if existing:
                return jsonify({'error': 'Code already exists'}), 400
            user.code = data['code']
        
        if 'password' in data:
            user.password = data['password']  # In production, hash this
        if 'role' in data:
            user.role = data['role']
        if 'branch' in data:
            user.branch = data['branch']
        if 'lastSerial' in data:
            user.last_serial = data['lastSerial']
        if 'storageUrl' in data:
            user.storage_url = data['storageUrl']
        if 'active' in data:
            user.active = data['active']
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify(user.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        user = User.query.get_or_404(user_id)
        
        # Soft delete - just mark as inactive
        user.active = False
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'message': 'User deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@user_bp.route('/users/<int:user_id>/serial', methods=['PUT'])
def update_user_serial(user_id):
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        if 'lastSerial' in data:
            user.last_serial = data['lastSerial']
            user.updated_at = datetime.utcnow()
            db.session.commit()
        
        return jsonify(user.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

