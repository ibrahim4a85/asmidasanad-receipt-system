from src.models.user import db
from datetime import datetime
import json

class Receipt(db.Model):
    __tablename__ = 'receipts'
    
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, unique=True, nullable=False)
    client_id = db.Column(db.String(50))
    client_name = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    bank_amount = db.Column(db.Float)  # المبلغ في البنك
    tafqeet = db.Column(db.Text)
    method = db.Column(db.String(100), nullable=False)
    bank = db.Column(db.String(100), nullable=False)
    reason = db.Column(db.String(200), nullable=False)
    branch = db.Column(db.String(100), nullable=False)
    invoices = db.Column(db.Text)  # JSON string for invoice details
    created_by = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    attachment = db.Column(db.Text)  # Base64 or URL
    approved = db.Column(db.Boolean, default=False)
    approved_by = db.Column(db.String(100))
    approved_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'number': self.number,
            'clientId': self.client_id,
            'clientName': self.client_name,
            'amount': self.amount,
            'bankAmount': self.bank_amount,
            'tafqeet': self.tafqeet,
            'method': self.method,
            'bank': self.bank,
            'reason': self.reason,
            'branch': self.branch,
            'invoices': json.loads(self.invoices) if self.invoices else [],
            'createdBy': self.created_by,
            'date': self.date.isoformat() if self.date else None,
            'attachment': self.attachment,
            'approved': self.approved,
            'approvedBy': self.approved_by,
            'approvedAt': self.approved_at.isoformat() if self.approved_at else None,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data):
        receipt = cls()
        receipt.number = data.get('number')
        receipt.client_id = data.get('clientId')
        receipt.client_name = data.get('clientName')
        receipt.amount = data.get('amount')
        receipt.bank_amount = data.get('bankAmount', data.get('amount'))
        receipt.tafqeet = data.get('tafqeet')
        receipt.method = data.get('method')
        receipt.bank = data.get('bank')
        receipt.reason = data.get('reason')
        receipt.branch = data.get('branch')
        receipt.invoices = json.dumps(data.get('invoices', []))
        receipt.created_by = data.get('createdBy')
        receipt.date = datetime.fromisoformat(data.get('date')) if data.get('date') else datetime.now().date()
        receipt.attachment = data.get('attachment')
        receipt.approved = data.get('approved', False)
        receipt.approved_by = data.get('approvedBy')
        if data.get('approvedAt'):
            receipt.approved_at = datetime.fromisoformat(data.get('approvedAt'))
        return receipt


class Client(db.Model):
    __tablename__ = 'clients'
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    address = db.Column(db.Text)
    branch = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'clientId': self.client_id,
            'name': self.name,
            'phone': self.phone,
            'email': self.email,
            'address': self.address,
            'branch': self.branch,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None
        }


class Company(db.Model):
    __tablename__ = 'company'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    logo = db.Column(db.Text)  # Base64 encoded image
    header = db.Column(db.Text)  # Base64 encoded image
    footer = db.Column(db.Text)  # Base64 encoded image
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'logo': self.logo,
            'header': self.header,
            'footer': self.footer,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None
        }


class SystemLists(db.Model):
    __tablename__ = 'system_lists'
    
    id = db.Column(db.Integer, primary_key=True)
    list_type = db.Column(db.String(50), nullable=False)  # branches, methods, banks, reasons
    items = db.Column(db.Text, nullable=False)  # JSON array
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'listType': self.list_type,
            'items': json.loads(self.items) if self.items else [],
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None
        }

