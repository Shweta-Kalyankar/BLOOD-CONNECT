from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from enum import Enum as pyEnum
from sqlalchemy import CheckConstraint, Index
from sqlalchemy.types import Enum

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    pincode = db.Column(db.String(10), nullable=False, index=True)
    user_type = db.Column(Enum("blood_bank", "hospital", name="user_types"), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    blood_bank_profile = db.relationship("BloodBank", backref="user", uselist=False, cascade="all, delete")
    hospital_profile = db.relationship("Hospital", backref="user", uselist=False, cascade="all, delete")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class BloodBank(db.Model):
    __tablename__ = "blood_banks"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    license_number = db.Column(db.String(50), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    pincode = db.Column(db.String(10), nullable=False, index=True)

    # Relationships
    blood_inventory = db.relationship("BloodInventory", backref="blood_bank", lazy="dynamic", cascade="all, delete")
    blood_requests = db.relationship("BloodRequest", backref="blood_bank", lazy="dynamic", cascade="all, delete")


class Hospital(db.Model):
    __tablename__ = "hospitals"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    license_number = db.Column(db.String(50), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    pincode = db.Column(db.String(10), nullable=False, index=True)

    # Relationships
    blood_requests = db.relationship("BloodRequest", backref="hospital", lazy="dynamic", cascade="all, delete")


class BloodTypeEnum(str, pyEnum):
    A_POS = "A+"
    A_NEG = "A-"
    B_POS = "B+"
    B_NEG = "B-"
    AB_POS = "AB+"
    AB_NEG = "AB-"
    O_POS = "O+"
    O_NEG = "O-"


class BloodInventory(db.Model):
    __tablename__ = "blood_inventory"

    id = db.Column(db.Integer, primary_key=True)
    blood_bank_id = db.Column(db.Integer, db.ForeignKey("blood_banks.id", ondelete="CASCADE"), nullable=False)
    blood_type = db.Column(Enum(*[e.value for e in BloodTypeEnum], name="blood_type_enum"), nullable=False)
    
    quantity_ml = db.Column(db.Integer, nullable=False)
    expiration_date = db.Column(db.DateTime, nullable=False)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("quantity_ml > 0", name="check_quantity_positive"),
    )


class RequestStatusEnum(str, pyEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    FULFILLED = "fulfilled"
    CANCELLED = "cancelled"


class UrgencyLevelEnum(str, pyEnum):
    NORMAL = "normal"
    URGENT = "urgent"
    CRITICAL = "critical"


class BloodRequest(db.Model):
    __tablename__ = "blood_requests"

    id = db.Column(db.Integer, primary_key=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False)
    blood_bank_id = db.Column(db.Integer, db.ForeignKey("blood_banks.id", ondelete="CASCADE"), nullable=False)
    blood_type = db.Column(Enum(*[e.value for e in BloodTypeEnum], name="blood_type_enum"), nullable=False)
    quantity_ml = db.Column(db.Integer, nullable=False)
    request_date = db.Column(db.DateTime, default=datetime.utcnow)
    required_by_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(Enum(*[e.value for e in RequestStatusEnum], name="request_status_enum"), 
                       default=RequestStatusEnum.PENDING.value, 
                       nullable=False)
    urgency_level = db.Column(Enum(*[e.value for e in UrgencyLevelEnum], name="urgency_level_enum"), nullable=False)
    notes = db.Column(db.Text, nullable=True)

    __table_args__ = (
        CheckConstraint("quantity_ml > 0", name="check_request_quantity_positive"),
    )


class TransferStatusEnum(str, pyEnum):
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    FAILED = "failed"


class BloodTransfer(db.Model):
    __tablename__ = "blood_transfers"

    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey("blood_requests.id", ondelete="CASCADE"), nullable=False)
    transfer_date = db.Column(db.DateTime, default=datetime.utcnow)
    quantity_ml = db.Column(db.Integer, nullable=False)
    status = db.Column(Enum(*[e.value for e in TransferStatusEnum], name="transfer_status_enum"), nullable=False)
    notes = db.Column(db.Text, nullable=True)

    __table_args__ = (
        CheckConstraint("quantity_ml > 0", name="check_transfer_quantity_positive"),
    )
from app import db
