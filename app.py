import streamlit as st
import sqlite3
import pandas as pd

# Page config
st.set_page_config(page_title="מחשבון משכירות למשכנתא | Rent or Buy", page_icon="🏠", layout="centered")

# Custom RTL CSS
st.markdown("""
<style>
    .stApp {
        direction: rtl;
        text-align: right;
    }
    div[data-testid="stMetricValue"] > div {
        direction: ltr;
        justify-content: flex-end;
    }
    .main-header {
        font-size: 2.5rem;
        font-weight: 900;
        background: linear-gradient(135deg, #0c3d6b 30%, #059669 100%);
        -webkit-background-clip: text;
        -webkit-text-fill_color: transparent;
        color: transparent;
        text-align: center;
        margin-bottom: 2rem;
    }
    .warning-box {
        background-color: #fef2f2;
        border: 1px solid #fee2e2;
        border-radius: 15px;
        padding: 20px;
        color: #991b1b;
        margin-bottom: 20px;
    }
    .success-box {
        background-color: #f0fdf4;
        border: 1px solid #dcfce7;
        border-radius: 15px;
        padding: 20px;
        color: #166534;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Helper functions
def fmt(n):
    return f"₪{n:,.0f}"

def calc_max_loan(mp):
    annual_rate = 0.045
    monthly_rate = annual_rate / 12
    total_months = 30 * 12
    if mp <= 0: return 0
    return mp * ((1 - (1 + monthly_rate)**-total_months) / monthly_rate)

def init_db():
    conn = sqlite3.connect("leads.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS leads
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT,
                  phone TEXT,
                  property_value REAL,
                  shared_income REAL,
                  loan_repayments REAL,
                  rent REAL,
                  created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

# UI
st.markdown('<h1 class="main-header">הפסיקו לשלם למשכיר שלכם</h1>', unsafe_allow_html=True)

with st.container():
    col1, col2 = st.columns(2)
    with col1:
        rent = st.slider("💰 שכר דירה נוכחי", 2000, 15000, 5000, step=100)
        equity = st.slider("🏦 הון עצמי זמין", 50000, 2000000, 300000, step=10000)
    with col2:
        income = st.slider("משותפת נטו 👛", 8000, 60000, 18000, step=500)
        loans = st.slider("💳 החזר הלוואות שוטפות", 0, 10000, 0, step=100)

# Calculations
disposable_income = max(income - loans, 0)
max_allowed_repayment = int(disposable_income * 0.35)
over_ratio = rent > max_allowed_repayment
remaining_allowance = max(max_allowed_repayment - rent, 0)

max_loan = calc_max_loan(rent)
property_value = max_loan + equity
ratio = (rent / disposable_income * 100) if disposable_income > 0 else 0

st.divider()

# Results Section
st.subheader("תוצאות החישוב")
m1, m2, m3 = st.columns(3)
m1.metric("שווי נכס אפשרי", fmt(property_value))
m2.metric("החזר חודשי מותר (35%)", fmt(max_allowed_repayment))
m3.metric("יחס החזר", f"{ratio:.0f}%")

if over_ratio:
    st.markdown(f"""
    <div class="warning-box">
        <b>🛑 מגבלת תקנות בנק ישראל</b><br>
        בהתאם להכנסות שלכם, ההחזר החודשי <b>לא יכול לעבור {fmt(max_allowed_repayment)}</b>.<br>
        שכר הדירה הנוכחי שלכם ({fmt(rent)}) חורג מהמגבלה הבנקאית.
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div class="success-box">
        <b>✅ אישור עקרוני (יחס החזר)</b><br>
        הבנק מאפשר החזר מקסימלי של <b>{fmt(max_allowed_repayment)}</b>.<br>
        יש לכם "מרווח" של עוד <b>{fmt(remaining_allowance)}</b> מעבר לשכר הדירה.
    </div>
    """, unsafe_allow_html=True)

# Equity Forecast (Simplified version of the chart)
st.subheader("תחזית ל-5 שנים")
rent_lost = rent * 60
appreciation = property_value * 0.15 # Approx 3% annual
st.info(f"ב-5 שנים של בעלות תצברו הון מוערך של {fmt(appreciation)} רק מעליית ערך הנכס, במקום לאבד {fmt(rent_lost)} על שכירות.")

# Lead Form
st.divider()
st.subheader("קבלו תוכנית מותאמת אישית")
with st.form("lead_form"):
    name = st.text_input("שם מלא")
    phone = st.text_input("מספר טלפון")
    submitted = st.form_submit_button("שלחו לי תוכנית לרכישת הנכס ←")
    
    if submitted:
        if name and phone:
            conn = sqlite3.connect("leads.db")
            c = conn.cursor()
            c.execute("INSERT INTO leads (name, phone, property_value, shared_income, loan_repayments, rent) VALUES (?, ?, ?, ?, ?, ?)",
                      (name, phone, property_value, income, loans, rent))
            conn.commit()
            conn.close()
            st.success(f"תודה {name}! הפרטים נשמרו. נחזור אליך תוך 24 שעות.")
        else:
            st.warning("אנא מלאו שם וטלפון")

# Footer
st.markdown("---")
st.caption("© Rent or Buy · המחשבון מהווה הערכה בלבד ותואם את תקנות בנק ישראל")
