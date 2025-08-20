import streamlit as st
import stripe
from urllib.parse import urljoin
from sqlalchemy.orm import Session
from db import Payment, User

def _stripe_setup():
    secret = st.secrets.get("stripe", {}).get("secret_key", "")
    if not secret:
        raise RuntimeError("Stripe secret_key ausente nos secrets.")
    stripe.api_key = secret
    return stripe

def _base_url():
    return st.secrets.get("app", {}).get("base_url", "http://localhost:8501")

def create_checkout_session(db: Session, user: User, quantity: int = 1):
    s = _stripe_setup()
    price_id = st.secrets.get("stripe", {}).get("price_id")
    if not price_id:
        raise RuntimeError("stripe.price_id ausente nos secrets.")

    success_url = urljoin(_base_url(), "/?paid_success=true&session_id={CHECKOUT_SESSION_ID}")
    cancel_url = urljoin(_base_url(), "/?paid_cancel=true")

    checkout = s.checkout.Session.create(
        mode="subscription" if price_id.startswith("price_") else "payment",
        line_items=[{"price": price_id, "quantity": quantity}],
        customer_email=user.email,
        success_url=success_url,
        cancel_url=cancel_url,
        allow_promotion_codes=True,
        metadata={"user_id": user.id},
    )
    p = Payment(
        id=str(checkout.id),
        user_id=user.id,
        status="created",
        amount=0,
        currency="BRL",
        provider="stripe",
        checkout_session_id=checkout.id,
        payment_intent_id=checkout.get("payment_intent") if isinstance(checkout.get("payment_intent"), str) else None
    )
    db.add(p)
    db.commit()
    return checkout.url

def verify_checkout_session(db: Session, session_id: str) -> bool:
    s = _stripe_setup()
    sess = s.checkout.Session.retrieve(session_id, expand=["payment_intent", "subscription"])
    is_paid = False
    if sess.status == "complete" and sess.payment_status == "paid":
        is_paid = True
    p = db.query(Payment).filter(Payment.checkout_session_id == session_id).first()
    if p:
        p.status = "paid" if is_paid else (sess.status or "unknown")
        db.commit()
    return is_paid
