# MG Holidays — Hotel Management System

A full-stack hotel management application with a **FastAPI** backend (PostgreSQL
via `asyncpg`) and a static **HTML/CSS/JavaScript** frontend. Supports user
sign-up/login, room browsing, bookings, feedback, and an admin panel for
managing rooms and bookings.

🔗 **Live demo:** https://mgholidaysdemo.netlify.app/

## Tech stack

- **Backend:** FastAPI, Uvicorn, asyncpg, Pydantic
- **Database:** PostgreSQL (developed against [Neon](https://neon.tech/))
- **Frontend:** Static HTML, CSS, and vanilla JavaScript (calls the API directly)

## Project structure

```
mg-holidays-hotel-management/
├── backend/
│   ├── main.py            # FastAPI application (all endpoints)
│   ├── API_DOCS.md         # Full API reference & schema notes
│   ├── requirements.txt
│   └── .env.example        # Template for your database connection string
└── frontend/
    ├── Home.html, Rooms.html, Login.html, Sign-Up.html, ...
    ├── Admin-Rooms.html, Admin-Bookings.html, My Bookings.html, ...
    ├── css/
    └── images/
```

## Backend setup

> ⚠️ **Security note:** the database connection string is read from the
> `DATABASE_URL` environment variable — it is **not** hardcoded. Never commit
> your real credentials. Copy `.env.example` to `.env` and fill in your own.

1. **Install dependencies**

   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure the database**

   ```bash
   cp .env.example .env
   # then edit .env and set DATABASE_URL to your PostgreSQL/Neon connection string
   ```

3. **Run the API**

   ```bash
   python main.py
   ```

   The API starts on `http://localhost:8000`.

   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`
   - Health check: `http://localhost:8000/health`

See [`backend/API_DOCS.md`](backend/API_DOCS.md) for the full endpoint reference
and the required database schema.

## Frontend setup

The frontend pages call the API at `http://localhost:8000`. With the backend
running, open the pages with any static server, e.g.:

```bash
cd frontend
python -m http.server 5500
```

Then visit `http://localhost:5500/Home.html`.

> If you deploy the backend elsewhere, update the `API_BASE` / `API_BASE_URL`
> constants inside the HTML files to point at your API URL.

## Key API endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/createuser` | Register a new user |
| POST | `/api/login` | Authenticate |
| GET | `/api/getallrooms` | List rooms |
| GET | `/api/getallroomtypes` | List room types |
| POST | `/api/createbooking` | Create a booking |
| GET | `/api/getmybookings/{user_id}` | A user's bookings |
| GET | `/api/getallbookings` | All bookings (admin) |
| PUT | `/api/updatebookingstatus/{booking_id}` | Update booking status (admin) |
| DELETE | `/api/cancelbooking/{booking_id}` | Cancel a booking |
| POST | `/api/addfeedback` | Submit feedback |

Full list and request/response schemas in [`backend/API_DOCS.md`](backend/API_DOCS.md).

## License

Released under the [MIT License](LICENSE).
