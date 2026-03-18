from fastapi import FastAPI, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
import sqlite3
import os
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

# Database setup
DB_PATH = "leads.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Check if table exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leads'")
    if not c.fetchone():
        c.execute('''CREATE TABLE leads
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      name TEXT,
                      phone TEXT,
                      property_value REAL,
                      shared_income REAL,
                      loan_repayments REAL,
                      rent REAL,
                      created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    else:
        # Add columns if they don't exist (migration)
        c.execute("PRAGMA table_info(leads)")
        columns = [column[1] for column in c.fetchall()]
        if "shared_income" not in columns:
            c.execute("ALTER TABLE leads ADD COLUMN shared_income REAL")
        if "loan_repayments" not in columns:
            c.execute("ALTER TABLE leads ADD COLUMN loan_repayments REAL")
        if "rent" not in columns:
            c.execute("ALTER TABLE leads ADD COLUMN rent REAL")
    conn.commit()
    conn.close()

init_db()

class Lead(BaseModel):
    name: str
    phone: str
    property_value: float
    shared_income: Optional[float] = 0
    loan_repayments: Optional[float] = 0
    rent: Optional[float] = 0

@app.post("/api/submit-lead")
async def submit_lead(lead: Lead):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO leads (name, phone, property_value, shared_income, loan_repayments, rent) VALUES (?, ?, ?, ?, ?, ?)",
                  (lead.name, lead.phone, lead.property_value, lead.shared_income, lead.loan_repayments, lead.rent))
        conn.commit()
        conn.close()
        return JSONResponse(content={"status": "success", "message": "Lead saved successfully"})
    except Exception as e:
        print(f"Error: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

# Serve static files
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
