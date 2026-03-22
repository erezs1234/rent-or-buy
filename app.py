import streamlit as st
import sqlite3
import pandas as pd

# Page config
st.set_page_config(page_title="מחשבון משכירות למשכנתא | Rent or Buy", page_icon="🏠", layout="centered")

# Custom RTL and Mobile-friendly CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;500;700;900&display=swap');
    
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        direction: rtl;
        text-align: right;
        font-family: 'Heebo', sans-serif;
    }
    
    /* Global alignment for all Streamlit elements */
    .stMarkdown, .stSubheader, .stTitle, .stCaption, div[data-testid="stNumberInput"] {
        direction: rtl;
        text-align: right !important;
    }

    .main-header {
        font-size: clamp(1.8rem, 5vw, 2.5rem);
        font-weight: 900;
        background: linear-gradient(135deg, #0c3d6b 30%, #059669 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        color: transparent;
        text-align: center;
        margin-bottom: 2rem;
        line-height: 1.2;
    }

    .centered-header {
        text-align: center !important;
        width: 100%;
        margin-top: 15px;
        margin-bottom: 25px;
        font-weight: 700;
        font-size: 1.8rem;
    }

    /* Metric alignment */
    div[data-testid="stMetricValue"] {
        text-align: center !important;
        justify-content: center !important;
        display: flex;
    }
    div[data-testid="stMetricLabel"] {
        text-align: center !important;
        justify-content: center !important;
        display: flex;
    }

    /* Container boxes */
    .scenario-box {
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        text-align: right;
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
    }
    .highlight-blue { border-right: 5px solid #0c3d6b; }
    .highlight-green { border-right: 5px solid #059669; background-color: #f0fdf4; }

    /* Fix column layout on mobile to stay in rows */
    [data-testid="column"] {
        width: calc(50% - 1rem) !important;
        flex: 1 1 calc(50% - 1rem) !important;
        min-width: calc(50% - 1rem) !important;
    }
</style>
""", unsafe_allow_html=True)

# Helper functions
def fmt(n):
    return f"₪{int(n):,.0f}"

def calc_max_loan(mp):
    annual_rate = 0.045 # Average rate
    monthly_rate = annual_rate / 12
    total_months = 30 * 12
    if mp <= 0: return 0
    # Mortgage calculation formula (standard)
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

# Main UI
st.markdown('<h1 class="main-header">הפסיקו לשלם לשכירות</h1>', unsafe_allow_html=True)

# Input Section
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        rent = st.number_input("💰 שכר דירה נוכחי", min_value=0, value=5000, step=100)
    with col2:
        equity = st.number_input("🏦 הון עצמי זמין", min_value=0, value=300000, step=10000)
    
    col3, col4 = st.columns(2)
    with col3:
        income = st.number_input("💵 הכנסה משותפת נטו", min_value=0, value=18000, step=500)
    with col4:
        loans = st.number_input("💳 החזר הלוואות", min_value=0, value=0, step=100)

# Calculations
disposable_income = max(income - loans, 0)
max_allowed_repayment = int(disposable_income * 0.35)

# Scenario 1: Same as Rent
mortgage_at_rent = calc_max_loan(rent)
property_at_rent = mortgage_at_rent + equity

# Scenario 2: Max Allowed (35%)
mortgage_at_max = calc_max_loan(max_allowed_repayment)
property_at_max = mortgage_at_max + equity

st.divider()

# Results Section
st.markdown('<h2 class="centered-header">תוצאות החישוב</h2>', unsafe_allow_html=True)

# --- Scenario 1 Section ---
st.markdown(f"""
<div class="scenario-box highlight-blue">
    <h3 style="margin-top:0;">🏠 קנייה בהחזר זהה לשכירות</h3>
    <p>אם תשתמשו ב-<b>{fmt(rent)}</b> שאתם משלמים היום לטובת משכנתא:</p>
    <div style="display:flex; justify-content:space-around; text-align:center;">
        <div><b>סכום המשכנתא</b><br>{fmt(mortgage_at_rent)}</div>
        <div><b>שווי דירה אפשרית</b><br><span style="font-size:1.2rem; color:#0c3d6b; font-weight:700;">{fmt(property_at_rent)}</span></div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- Scenario 2 Section (Only if income allows more) ---
if max_allowed_repayment > rent:
    st.markdown(f"""
    <div class="scenario-box highlight-green">
        <h3 style="margin-top:0;">🚀 השתדרגות בהתאם ליכולת ההחזר</h3>
        <p>בנק ישראל מאפשר לכם החזר של עד <b>{fmt(max_allowed_repayment)}</b> (35% מההכנסה הפנויה).</p>
        <div style="display:flex; justify-content:space-around; text-align:center;">
            <div><b>סכום המשכנתא</b><br>{fmt(mortgage_at_max)}</div>
            <div><b>שווי דירה מקסימלי</b><br><span style="font-size:1.4rem; color:#059669; font-weight:900;">{fmt(property_at_max)}</span></div>
        </div>
        <p style="margin-top:10px; font-size:0.9rem;"><i>* הכנסה פנויה: {fmt(disposable_income)} (הכנסות פחות הלוואות)</i></p>
    </div>
    """, unsafe_allow_html=True)
elif max_allowed_repayment < rent:
    st.markdown(f"""
    <div class="scenario-box" style="border-right: 5px solid #991b1b; background-color: #fef2f2; color:#991b1b;">
        <b>⚠️ שימו לב:</b> שכר הדירה הנוכחי שלכם ({fmt(rent)}) גבוה מהחזר המשכנתא המקסימלי שהבנק יאפשר לכם ({fmt(max_allowed_repayment)}) בהתאם להכנסות.
    </div>
    """, unsafe_allow_html=True)

# Summary Message
st.info(f"בעוד 5 שנים, תצברו הון מוערך של כ-{fmt(property_at_rent * 0.15)} רק מעליית ערך הנכס (15%), במקום לאבד {fmt(rent * 60)} על שכר דירה.")

# Lead Form
st.divider()
st.subheader("📩 קבלו תוכנית מותאמת אישית")
with st.form("lead_form"):
    name = st.text_input("שם מלא", placeholder="ישראל ישראלי")
    phone = st.text_input("מספר טלפון", placeholder="050-0000000")
    submitted = st.form_submit_button("שלחו לי תוכנית לרכישת הנכס ←", use_container_width=True)
    
    if submitted:
        if name and phone:
            conn = sqlite3.connect("leads.db")
            c = conn.cursor()
            c.execute("INSERT INTO leads (name, phone, property_value, shared_income, loan_repayments, rent) VALUES (?, ?, ?, ?, ?, ?)",
                      (name, phone, float(property_at_max), float(income), float(loans), float(rent)))
            conn.commit()
            conn.close()
            st.success(f"תודה {name}! הפרטים נשמרו. נחזור אליך תוך 24 שעות.")
        else:
            st.warning("אנא מלאו שם וטלפון")

# Footer
st.markdown("---")
st.caption("© Even Sapir - Rent or Buy · המחשבון מהווה הערכה בלבד ותואם את תקנות בנק ישראל")
