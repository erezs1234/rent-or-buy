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
        margin-bottom: 15px;
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

    /* Input boxes - ensuring strict RTL labels */
    div[data-testid="stNumberInput"] label {
        text-align: right !important;
        width: 100%;
        display: block;
    }

    .warning-box, .success-box {
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 20px;
        text-align: right;
        font-size: 0.95rem;
        line-height: 1.6;
    }
    .warning-box {
        background-color: #fef2f2;
        border: 1px solid #fee2e2;
        color: #991b1b;
    }
    .success-box {
        background-color: #f0fdf4;
        border: 1px solid #dcfce7;
        color: #166534;
    }

    /* Improve column layout on mobile to stay in rows */
    [data-testid="column"] {
        width: calc(50% - 1rem) !important;
        flex: 1 1 calc(50% - 1rem) !important;
        min-width: calc(50% - 1rem) !important;
    }
    
    @media (max-width: 640px) {
        /* Optional: adjust font sizes for very small screens */
        .main-header { font-size: 1.6rem; }
    }
</style>
""", unsafe_allow_html=True)

# Helper functions
def fmt(n):
    return f"₪{int(n):,.0f}"

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

# Main UI
st.markdown('<h1 class="main-header">הפסיקו לשלם לשכירות</h1>', unsafe_allow_html=True)

# Input Section - Forced 2-column layout for mobile
with st.container():
    # First Row
    col1, col2 = st.columns(2)
    with col1:
        rent = st.number_input("💰 שכר דירה", min_value=0, value=5000, step=100)
    with col2:
        equity = st.number_input("🏦 הון עצמי", min_value=0, value=300000, step=10000)
    
    # Second Row
    col3, col4 = st.columns(2)
    with col3:
        income = st.number_input("💵 הכנסה נטו", min_value=0, value=18000, step=500)
    with col4:
        loans = st.number_input("💳 החזר הלוואות", min_value=0, value=0, step=100)

# Calculations
disposable_income = max(income - loans, 0)
max_allowed_repayment = int(disposable_income * 0.35)
over_ratio = rent > max_allowed_repayment
remaining_allowance = max(max_allowed_repayment - rent, 0)

max_loan = calc_max_loan(rent)
property_value = max_loan + equity
ratio = (rent / disposable_income * 100) if disposable_income > 0 else 0

st.divider()

# Results Header Centered
st.markdown('<h2 class="centered-header">תוצאות החישוב</h2>', unsafe_allow_html=True)

# Results Row 1
res_col1, res_col2 = st.columns(2)
res_col1.metric("שווי נכס אפשרי", fmt(property_value))
res_col2.metric("יחס החזר", f"{ratio:.0f}%")

# Results Row 2 (Full Width)
st.metric("החזר מרבי מותר (35% מהפנויה)", fmt(max_allowed_repayment))

if over_ratio:
    st.markdown(f"""
    <div class="warning-box">
        <b>🛑 חריגה ממגבלת בנק ישראל</b><br>
        הכנסה פנויה: {fmt(disposable_income)} (הכנסות פחות הלוואות)<br>
        ההחזר המרבי המותר (35%) הוא <b>{fmt(max_allowed_repayment)}</b>.<br>
        שכר הדירה הנוכחי ({fmt(rent)}) חורג מהמגבלה.
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div class="success-box">
        <b>✅ תואם מגבלות בנק ישראל</b><br>
        הכנסה פנויה: {fmt(disposable_income)} (הכנסות פחות הלוואות)<br>
        הבנק מאפשר החזר של עד <b>{fmt(max_allowed_repayment)}</b>.<br>
        יש לכם "מרווח" של <b>{fmt(remaining_allowance)}</b> מעבר לשכירות.
    </div>
    """, unsafe_allow_html=True)

# Equity Forecast
st.subheader("📈 תחזית ל-5 שנים")
rent_lost = rent * 60
appreciation = int(property_value * 0.15)
st.info(f"בעוד 5 שנים, תצברו הון מוערך של {fmt(appreciation)} רק מעליית ערך הנכס (15%), במקום לאבד {fmt(rent_lost)} על שכר דירה.")

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
                      (name, phone, float(property_value), float(income), float(loans), float(rent)))
            conn.commit()
            conn.close()
            st.success(f"תודה {name}! הפרטים נשמרו. נחזור אליך תוך 24 שעות.")
        else:
            st.warning("אנא מלאו שם וטלפון")

# Footer
st.markdown("---")
st.caption("© Even Sapir - Rent or Buy · המחשבון מהווה הערכה בלבד ותואם את תקנות בנק ישראל")
