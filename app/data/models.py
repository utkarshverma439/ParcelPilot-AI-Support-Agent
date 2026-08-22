from sqlalchemy import Column, String, Float, Boolean, Text, DateTime, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

Base = declarative_base()


class Account(Base):
    __tablename__ = "accounts"

    account_id = Column(String, primary_key=True)
    account_name = Column(String, nullable=False)
    plan = Column(String, nullable=False)
    status = Column(String, default="active")
    csm = Column(String)
    contract_file = Column(String)
    premium_support = Column(Boolean, default=False)
    notes = Column(Text)


class Order(Base):
    __tablename__ = "orders"

    order_id = Column(String, primary_key=True)
    account_id = Column(String, nullable=False)
    carrier = Column(String, nullable=False)
    status = Column(String, nullable=False)
    booked_at = Column(String)
    pickup_window_start = Column(String)
    pickup_window_end = Column(String)
    pickup_actual_at = Column(String)
    shipment_fee_inr = Column(Float)
    carrier_fault = Column(Boolean, default=False)
    customer_fault = Column(Boolean, default=False)
    cancellation_requested_at = Column(String)
    notes = Column(Text)


class Ticket(Base):
    __tablename__ = "tickets"

    ticket_id = Column(String, primary_key=True)
    account_id = Column(String, nullable=False)
    created_at = Column(String)
    status = Column(String, default="open")
    subject = Column(String)
    description = Column(Text)
    channel = Column(String)
    assigned_to = Column(String)
    last_customer_message_at = Column(String)
    historical_resolution = Column(Text)


class Action(Base):
    __tablename__ = "actions"

    action_id = Column(String, primary_key=True)
    action_type = Column(String, nullable=False)
    status = Column(String, default="pending")
    requested_by = Column(String)
    account_id = Column(String)
    payload_json = Column(Text)
    created_at = Column(String, default=lambda: datetime.utcnow().isoformat())
    confirmed_at = Column(String)
    executed_at = Column(String)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(String, primary_key=True)
    request_id = Column(String)
    user_id = Column(String)
    account_id = Column(String)
    action = Column(String)
    details = Column(Text)
    timestamp = Column(String, default=lambda: datetime.utcnow().isoformat())


def init_db(database_url: str):
    engine = create_engine(database_url, echo=False)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)
