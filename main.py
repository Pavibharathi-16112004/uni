import os
import secrets
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import mysql.connector
from passlib.context import CryptContext
from authlib.integrations.starlette_client import OAuth
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Allow frontend (opened in Chrome) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Needed for Google OAuth (stores temporary login state)
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET_KEY", "dev-secret"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ---- Google OAuth setup ----
oauth = OAuth()
oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

# Where the frontend should land after Google login succeeds
FRONTEND_SUCCESS_URL = "http://127.0.0.1:5500/simple-login-project/frontend/dashboard.html"

# Where the reset-password link in the email should point to
FRONTEND_RESET_URL = "http://127.0.0.1:5500/simple-login-project/frontend/reset-password.html"


def send_reset_email(to_email: str, reset_link: str):
    sender = os.getenv("EMAIL_ADDRESS")
    app_password = os.getenv("EMAIL_APP_PASSWORD")

    body = f"""Hi,

We received a request to reset your UniJourney password.
Click the link below to set a new password (valid for 30 minutes):

{reset_link}

If you didn't request this, you can ignore this email.
"""

    msg = MIMEText(body)
    msg["Subject"] = "Reset your UniJourney password"
    msg["From"] = sender
    msg["To"] = to_email

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender, app_password)
        server.sendmail(sender, to_email, msg.as_string())


# ---- MySQL connection ----
def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root@123",   # <-- change this
        database="simple_login_db"
    )

# ---- Request models ----
class SignupRequest(BaseModel):
    name: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@app.post("/api/signup")
def signup(user: SignupRequest):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users WHERE email = %s", (user.email,))
    existing = cursor.fetchone()
    if existing:
        cursor.close()
        db.close()
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = pwd_context.hash(user.password)
    cursor.execute(
        "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
        (user.name, user.email, hashed_password)
    )
    db.commit()
    cursor.close()
    db.close()
    return {"message": "Signup successful"}


@app.post("/api/login")
def login(user: LoginRequest):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users WHERE email = %s", (user.email,))
    db_user = cursor.fetchone()
    cursor.close()
    db.close()

    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not pwd_context.verify(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return {"message": "Login successful", "name": db_user["name"], "email": db_user["email"]}


@app.post("/api/forgot-password")
def forgot_password(req: ForgotPasswordRequest):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users WHERE email = %s", (req.email,))
    user = cursor.fetchone()

    if not user:
        cursor.close()
        db.close()
        # Same message whether or not the email exists (avoids leaking which emails are registered)
        return {"message": "If that email is registered, a reset link has been sent."}

    token = secrets.token_urlsafe(32)
    expiry = datetime.utcnow() + timedelta(minutes=30)

    cursor.execute(
        "UPDATE users SET reset_token = %s, reset_token_expiry = %s WHERE email = %s",
        (token, expiry, req.email)
    )
    db.commit()
    cursor.close()
    db.close()

    reset_link = f"{FRONTEND_RESET_URL}?token={token}"
    send_reset_email(req.email, reset_link)

    return {"message": "If that email is registered, a reset link has been sent."}


@app.post("/api/reset-password")
def reset_password(req: ResetPasswordRequest):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users WHERE reset_token = %s", (req.token,))
    user = cursor.fetchone()

    if not user:
        cursor.close()
        db.close()
        raise HTTPException(status_code=400, detail="Invalid or expired reset link")

    if user["reset_token_expiry"] is None or user["reset_token_expiry"] < datetime.utcnow():
        cursor.close()
        db.close()
        raise HTTPException(status_code=400, detail="Reset link has expired. Please request a new one.")

    hashed_password = pwd_context.hash(req.new_password)
    cursor.execute(
        "UPDATE users SET password = %s, reset_token = NULL, reset_token_expiry = NULL WHERE id = %s",
        (hashed_password, user["id"])
    )
    db.commit()
    cursor.close()
    db.close()

    return {"message": "Password reset successful. You can now sign in."}


# ---- Google OAuth routes ----
@app.get("/api/auth/google")
async def google_login(request: Request):
    redirect_uri = "http://127.0.0.1:8000/api/auth/google/callback"
    return await oauth.google.authorize_redirect(request, redirect_uri)


@app.get("/api/auth/google/callback")
async def google_callback(request: Request):
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get("userinfo")

    if not user_info:
        raise HTTPException(status_code=400, detail="Could not fetch user info from Google")

    name = user_info.get("name")
    email = user_info.get("email")

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    existing = cursor.fetchone()

    if not existing:
        # Create an account automatically for first-time Google sign-ins.
        # No usable password for Google accounts, so store a random hash.
        placeholder_password = pwd_context.hash(os.urandom(16).hex())
        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
            (name, email, placeholder_password)
        )
        db.commit()

    cursor.close()
    db.close()

    # Redirect back to frontend with basic info in the URL (simple demo approach)
    return RedirectResponse(url=f"{FRONTEND_SUCCESS_URL}?name={name}&email={email}")


@app.get("/")
def root():
    return {"status": "Backend is running"}
