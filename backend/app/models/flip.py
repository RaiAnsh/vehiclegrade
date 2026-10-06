"""Flip ledger: a vehicle bought privately to resell, with the real money
that went in and out. `predicted` is a frozen snapshot of the Flip Calculator
(services/flip_calculator.py) taken when the flip was logged, so that once it
sells, actual vs predicted can be compared honestly instead of re-running the
calculator with hindsight.
"""

from datetime import date, datetime

from app.extensions import db

VALID_FLIP_STATUSES = ("holding", "sold")
VALID_EXPENSE_CATEGORIES = ("insurance", "fuel", "maintenance", "repair", "inspection_prep", "safety", "other")


class Flip(db.Model):
    __tablename__ = "flips"

    id = db.Column(db.Integer, primary_key=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey("admin_users.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    generation_id = db.Column(db.Integer, db.ForeignKey("generations.id"), nullable=False, index=True)
    make = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    trim = db.Column(db.String(60), nullable=True)
    title_status = db.Column(db.String(20), nullable=False, default="clean")
    condition = db.Column(db.String(20), nullable=False, default="good")

    status = db.Column(db.String(10), nullable=False, default="holding")

    purchase_date = db.Column(db.Date, nullable=False, default=date.today)
    purchase_price = db.Column(db.Float, nullable=False)
    purchase_tax = db.Column(db.Float, nullable=False, default=0)  # actual RST paid
    purchase_fees = db.Column(db.Float, nullable=False, default=0)  # UVIP, transfer, history report
    mileage_at_purchase = db.Column(db.Integer, nullable=False)
    planned_months = db.Column(db.Float, nullable=False, default=3)

    sale_date = db.Column(db.Date, nullable=True)
    sale_price = db.Column(db.Float, nullable=True)
    sale_fees = db.Column(db.Float, nullable=False, default=0)
    mileage_at_sale = db.Column(db.Integer, nullable=True)

    predicted = db.Column(db.JSON, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    generation = db.relationship("Generation")
    expenses = db.relationship("FlipExpense", back_populates="flip", cascade="all, delete-orphan",
                               order_by="FlipExpense.expense_date")


class FlipExpense(db.Model):
    __tablename__ = "flip_expenses"

    id = db.Column(db.Integer, primary_key=True)
    flip_id = db.Column(db.Integer, db.ForeignKey("flips.id"), nullable=False, index=True)
    expense_date = db.Column(db.Date, nullable=False, default=date.today)
    category = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    note = db.Column(db.String(255), nullable=True)

    flip = db.relationship("Flip", back_populates="expenses")
