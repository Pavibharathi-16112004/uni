# UniJourney — Full Project (HTML/CSS/JS + FastAPI + MySQL)

Ithu `uni-journey.vercel.app` site oda replica — Login → Signup → Forgot/Reset Password →
Dashboard → Leads, ellame full ah run aagum maari kudukkirom.

```
simple-login-project/
├── frontend/
│   ├── index.html            → Login page
│   ├── signup.html           → Signup page
│   ├── forgot-password.html  → Forgot password page
│   ├── reset-password.html   → Reset password page
│   ├── dashboard.html        → Dashboard (stat cards + recent leads)
│   ├── leads.html            → Full leads list + filters
│   ├── dashboard.css         → Dashboard/Leads theme (navy #1F3864)
│   ├── style.css             → Login/Signup theme
│   └── script.js             → Login/Signup API calls
└── backend/
    ├── main.py                → FastAPI app (signup/login/forgot/reset/Google OAuth)
    ├── schema.sql              → MySQL database + users table
    ├── requirements.txt
    └── .env                    → Google OAuth + Gmail SMTP secrets
```

---

## STEP 1 — MySQL Database Setup

1. MySQL start pannunga (XAMPP / WAMP / standalone MySQL service, edhu use pannalum irukalam).
2. MySQL Workbench thira, illa terminal la login pannunga:
   ```
   mysql -u root -p
   ```
3. `backend/schema.sql` file ah run pannunga. Idhu `simple_login_db` database um `users` table um create pannum:
   ```
   source /full/path/to/backend/schema.sql;
   ```
   (Workbench na, file open pannitu lightning bolt icon click pannunga.)

---

## STEP 2 — Backend Setup (FastAPI)

1. Terminal la backend folder ku po:
   ```
   cd backend
   ```
2. Virtual environment (optional but recommended):
   ```
   python -m venv venv
   venv\Scripts\activate        (Windows)
   source venv/bin/activate     (Mac/Linux)
   ```
3. Dependencies install pannunga:
   ```
   pip install -r requirements.txt
   ```
4. `main.py` file open pannitu **line 80** la irukra MySQL password ah unga actual password kooda maathunga:
   ```python
   password="YOUR_MYSQL_PASSWORD",   # <-- ithula unga MySQL root password podunga
   ```
5. `.env` file la (Google login + forgot-password email venumna mattum):
   - `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` → Google Cloud Console la create pannina OAuth credentials
   - `EMAIL_ADDRESS` / `EMAIL_APP_PASSWORD` → Gmail App Password (forgot-password mail anuppa)
   - Ivanga illama kooda signup/login/dashboard/leads full ah velai pannum — Google login um forgot-password mail mattum thevai padum.
6. Server start pannunga:
   ```
   uvicorn main:app --reload
   ```
7. Browser la `http://127.0.0.1:8000` open pannunga — `{"status":"Backend is running"}` nu varanum. Idhu vandha backend sari ah irukku nu artham.

---

## STEP 3 — Frontend Run Pannuradhu

**Recommended: VS Code Live Server**
1. VS Code la `frontend` folder open pannunga.
2. "Live Server" extension install pannitu, `index.html` mela right-click → **Open with Live Server**.
3. URL `http://127.0.0.1:5500/.../frontend/index.html` maari varum.

(Live Server illama direct double-click pannitu Chrome la open pannalam kooda — CORS backend la already `allow_origins=["*"]` nu set pannirukom, so andha maadhiri open pannalum velai pannum.)

---

## STEP 4 — Full Flow Test

1. **Signup** → `signup.html` la name/email/password kudutu account create pannunga.
2. **Login** → `index.html` ku po, andha email/password kudunga → "Login successful" message varum → automatic ah **Dashboard** ku redirect aagum.
3. **Dashboard** (`dashboard.html`) → Welcome message, stat cards (Leads/Applications/Universities/Documents), Recent Leads table kaatum. (Ippo idhu demo/sample data — real MySQL data connect pannanumna sollunga, `/api/dashboard-stats` endpoint add panren.)
4. **Leads** (sidebar la "Leads" click pannunga) → Full leads list, stage filter chips (New/Contacted/Applied/Offer/Enrolled) work aagum.
5. **Logout** → sidebar bottom la irukra Logout click pannuna login page ku thirumba varum.
6. **Forgot Password** → `forgot-password.html` la email kudutha, `.env` la Gmail App Password set pannirundha, reset link mail varum.
7. **Google Login** → index.html la "Continue with Google" button, `.env` la Google OAuth credentials set pannirundha velai pannum.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| "Could not reach server" | FastAPI terminal la `uvicorn main:app --reload` run aagi irukka nu check pannunga |
| MySQL connection error | MySQL service start aagi irukka + `main.py` la password correct ah irukka check pannunga |
| Login aana udane dashboard varala | Browser console la (F12) error irukka nu paarunga, `script.js` andha zip la irukka nu confirm pannunga |
| Google login velai pannala | `.env` la `GOOGLE_CLIENT_ID` / `SECRET` correct ah irukka, Google Cloud Console la redirect URI `http://127.0.0.1:8000/api/auth/google/callback` add pannirukka check pannunga |
| Forgot-password mail varala | Gmail App Password correct ah irukka (16 characters, spaces illama), 2FA Gmail account la on ah irukka check pannunga |
