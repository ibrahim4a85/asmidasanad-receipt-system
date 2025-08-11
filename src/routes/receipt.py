from flask import Blueprint, request, jsonify
from src.models.receipt import db, Receipt, Client, Company, SystemLists
from src.models.user import User
from datetime import datetime, date
import json

receipt_bp = Blueprint('receipt', __name__)

@receipt_bp.route('/receipts', methods=['GET'])
def get_receipts():
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        branch = request.args.get('branch')
        method = request.args.get('method')
        bank = request.args.get('bank')
        reason = request.args.get('reason')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        search = request.args.get('search')
        created_by = request.args.get('created_by')
        
        # Build query
        query = Receipt.query
        
        if branch and branch != 'الكل':
            query = query.filter(Receipt.branch == branch)
        if method and method != 'الكل':
            query = query.filter(Receipt.method == method)
        if bank and bank != 'الكل':
            query = query.filter(Receipt.bank == bank)
        if reason and reason != 'الكل':
            query = query.filter(Receipt.reason == reason)
        if date_from:
            query = query.filter(Receipt.date >= datetime.fromisoformat(date_from).date())
        if date_to:
            query = query.filter(Receipt.date <= datetime.fromisoformat(date_to).date())
        if search:
            query = query.filter(
                db.or_(
                    Receipt.number.like(f'%{search}%'),
                    Receipt.client_id.like(f'%{search}%'),
                    Receipt.client_name.like(f'%{search}%')
                )
            )
        if created_by:
            query = query.filter(Receipt.created_by == created_by)
        
        # Order by date desc
        query = query.order_by(Receipt.date.desc(), Receipt.number.desc())
        
        # Paginate
        receipts = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'receipts': [receipt.to_dict() for receipt in receipts.items],
            'total': receipts.total,
            'pages': receipts.pages,
            'current_page': receipts.page,
            'per_page': receipts.per_page
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@receipt_bp.route('/receipts', methods=['POST'])
def create_receipt():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['number', 'clientName', 'amount', 'method', 'bank', 'reason', 'branch', 'createdBy']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Check if receipt number already exists
        existing = Receipt.query.filter_by(number=data['number']).first()
        if existing:
            return jsonify({'error': 'Receipt number already exists'}), 400
        
        # Create receipt
        receipt = Receipt.from_dict(data)
        db.session.add(receipt)
        
        # Update user's last serial
        user = User.query.filter_by(username=data['createdBy']).first()
        if user:
            user.last_serial = data['number']
        
        db.session.commit()
        
        return jsonify(receipt.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@receipt_bp.route('/receipts/<int:receipt_id>', methods=['GET'])
def get_receipt(receipt_id):
    try:
        receipt = Receipt.query.get_or_404(receipt_id)
        return jsonify(receipt.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@receipt_bp.route('/receipts/<int:receipt_id>', methods=['PUT'])
def update_receipt(receipt_id):
    try:
        receipt = Receipt.query.get_or_404(receipt_id)
        data = request.get_json()
        
        # Update fields
        if 'clientId' in data:
            receipt.client_id = data['clientId']
        if 'clientName' in data:
            receipt.client_name = data['clientName']
        if 'amount' in data:
            receipt.amount = data['amount']
        if 'bankAmount' in data:
            receipt.bank_amount = data['bankAmount']
        if 'tafqeet' in data:
            receipt.tafqeet = data['tafqeet']
        if 'method' in data:
            receipt.method = data['method']
        if 'bank' in data:
            receipt.bank = data['bank']
        if 'reason' in data:
            receipt.reason = data['reason']
        if 'branch' in data:
            receipt.branch = data['branch']
        if 'invoices' in data:
            receipt.invoices = json.dumps(data['invoices'])
        if 'attachment' in data:
            receipt.attachment = data['attachment']
        if 'approved' in data:
            receipt.approved = data['approved']
            if data['approved'] and 'approvedBy' in data:
                receipt.approved_by = data['approvedBy']
                receipt.approved_at = datetime.utcnow()
        
        receipt.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify(receipt.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@receipt_bp.route('/receipts/<int:receipt_id>/approve', methods=['POST'])
def approve_receipt(receipt_id):
    try:
        receipt = Receipt.query.get_or_404(receipt_id)
        data = request.get_json()
        
        receipt.approved = True
        receipt.approved_by = data.get('approvedBy')
        receipt.approved_at = datetime.utcnow()
        
        # Update bank amount if provided
        if 'bankAmount' in data:
            receipt.bank_amount = data['bankAmount']
        
        db.session.commit()
        
        return jsonify(receipt.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@receipt_bp.route('/receipts/<int:receipt_id>', methods=['DELETE'])
def delete_receipt(receipt_id):
    try:
        receipt = Receipt.query.get_or_404(receipt_id)
        db.session.delete(receipt)
        db.session.commit()
        
        return jsonify({'message': 'Receipt deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@receipt_bp.route('/receipts/stats', methods=['GET'])
def get_receipt_stats():
    try:
        branch = request.args.get('branch')
        created_by = request.args.get('created_by')
        
        # Build base query
        query = Receipt.query
        if branch and branch != 'الكل':
            query = query.filter(Receipt.branch == branch)
        if created_by:
            query = query.filter(Receipt.created_by == created_by)
        
        # Calculate stats
        total_receipts = query.count()
        total_amount = db.session.query(db.func.sum(Receipt.bank_amount)).filter(
            query.whereclause if query.whereclause is not None else True
        ).scalar() or 0
        
        # Today's receipts
        today = date.today()
        today_receipts = query.filter(Receipt.date == today).count()
        
        # Pending approval
        pending_approval = query.filter(Receipt.approved == False).count()
        
        # Branch stats
        branch_stats = db.session.query(
            Receipt.branch,
            db.func.sum(Receipt.bank_amount).label('total'),
            db.func.count(Receipt.id).label('count')
        ).group_by(Receipt.branch).all()
        
        # Method stats
        method_stats = db.session.query(
            Receipt.method,
            db.func.sum(Receipt.bank_amount).label('total'),
            db.func.count(Receipt.id).label('count')
        ).group_by(Receipt.method).all()
        
        return jsonify({
            'totalReceipts': total_receipts,
            'totalAmount': float(total_amount),
            'todayReceipts': today_receipts,
            'pendingApproval': pending_approval,
            'branchStats': [{'name': stat[0], 'amount': float(stat[1] or 0), 'count': stat[2]} for stat in branch_stats],
            'methodStats': [{'name': stat[0], 'amount': float(stat[1] or 0), 'count': stat[2]} for stat in method_stats]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Client routes
@receipt_bp.route('/clients', methods=['GET'])
def get_clients():
    try:
        clients = Client.query.all()
        return jsonify([client.to_dict() for client in clients])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@receipt_bp.route('/clients', methods=['POST'])
def create_client():
    try:
        data = request.get_json()
        
        # Check if client ID already exists
        existing = Client.query.filter_by(client_id=data['clientId']).first()
        if existing:
            return jsonify({'error': 'Client ID already exists'}), 400
        
        client = Client(
            client_id=data['clientId'],
            name=data['name'],
            phone=data.get('phone'),
            email=data.get('email'),
            address=data.get('address'),
            branch=data.get('branch')
        )
        
        db.session.add(client)
        db.session.commit()
        
        return jsonify(client.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@receipt_bp.route('/clients/<client_id>', methods=['GET'])
def get_client(client_id):
    try:
        client = Client.query.filter_by(client_id=client_id).first_or_404()
        return jsonify(client.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Company settings
@receipt_bp.route('/company', methods=['GET'])
def get_company():
    try:
        company = Company.query.first()
        if not company:
            # Create default company
            company = Company(name='شركة الأسمدة المتحدة السعودية')
            db.session.add(company)
            db.session.commit()
        
        return jsonify(company.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@receipt_bp.route('/company', methods=['PUT'])
def update_company():
    try:
        company = Company.query.first()
        if not company:
            company = Company()
            db.session.add(company)
        
        data = request.get_json()
        
        if 'name' in data:
            company.name = data['name']
        if 'logo' in data:
            company.logo = data['logo']
        if 'header' in data:
            company.header = data['header']
        if 'footer' in data:
            company.footer = data['footer']
        
        company.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify(company.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# System lists
@receipt_bp.route('/lists', methods=['GET'])
def get_lists():
    try:
        lists = {}
        system_lists = SystemLists.query.all()
        
        for system_list in system_lists:
            lists[system_list.list_type] = json.loads(system_list.items)
        
        # Default lists if not found
        if not lists:
            default_lists = {
                'branches': ['الرياض', 'بريدة', 'الخرج', 'وادي الدواسر', 'جدة', 'تبوك'],
                'methods': ['نقداً', 'شبكة', 'تحويل بنكي', 'إيداع نقدي', 'شيك'],
                'banks': ['الراجحي', 'الأهلي', 'الرياض', 'ساب', 'الاستثمار'],
                'reasons': ['سداد فواتير', 'دفعة من الحساب', 'سداد الرصيد']
            }
            
            for list_type, items in default_lists.items():
                system_list = SystemLists(list_type=list_type, items=json.dumps(items))
                db.session.add(system_list)
            
            db.session.commit()
            lists = default_lists
        
        return jsonify(lists)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@receipt_bp.route('/lists', methods=['PUT'])
def update_lists():
    try:
        data = request.get_json()
        
        for list_type, items in data.items():
            system_list = SystemLists.query.filter_by(list_type=list_type).first()
            if system_list:
                system_list.items = json.dumps(items)
                system_list.updated_at = datetime.utcnow()
            else:
                system_list = SystemLists(list_type=list_type, items=json.dumps(items))
                db.session.add(system_list)
        
        db.session.commit()
        
        return jsonify({'message': 'Lists updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

