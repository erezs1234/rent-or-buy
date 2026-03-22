import streamlit as st
import sqlite3
import pandas as pd
import requests

# Page config
st.set_page_config(page_title="מחשבון משכירות למשכנתא | Rent or Buy", page_icon="🏠", layout="centered")

# --- CONFIGURATION (ActiveTrail) ---
ACTIVETRAIL_API_KEY = "0XB72928E8F989B66EF693CD31E699DC49DFBC14F486021F2A7C9A6D8185E9151EF9F42884A5D149C7BA06F0AE8F93F415"
ACTIVETRAIL_GROUP_NAME = "נרשמים למתנה - מחשבון הון עצמי"

# Initialize Session State
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'data' not in st.session_state:
    st.session_state.data = {}

# Custom RTL and Mobile-friendly CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;500;700;900&display=swap');
    
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        direction: rtl;
        text-align: right;
        font-family: 'Heebo', sans-serif;
    }
    
    .stMarkdown, .stSubheader, .stTitle, .stCaption, div[data-testid="stNumberInput"], div[data-testid="stTextInput"] {
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

    [data-testid="column"] {
        width: calc(50% - 1rem) !important;
        flex: 1 1 calc(50% - 1rem) !important;
        min-width: calc(50% - 1rem) !important;
    }

    .step-indicator {
        text-align: center;
        margin-bottom: 20px;
        color: #64748b;
        font-size: 0.9rem;
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

ACTIVETRAIL_BASE_URL = "https://webapi.mymarketing.co.il/api"

def sync_to_activetrail(name, phone, email):
    """Sync lead data to ActiveTrail API with correct base URL and timeout"""
    headers = {"Authorization": ACTIVETRAIL_API_KEY}
    
    try:
        # 1. Find Group ID by Name
        group_id = None
        groups_resp = requests.get(f"{ACTIVETRAIL_BASE_URL}/groups", headers=headers, timeout=10)
        if groups_resp.status_code == 200:
            groups = groups_resp.json()
            for g in groups:
                if g['name'].strip() == ACTIVETRAIL_GROUP_NAME.strip():
                    group_id = g['id']
                    break
        
        if not group_id:
            return False, f"המערכת לא מצאה קבוצה בשם '{ACTIVETRAIL_GROUP_NAME}'"
        
        # 2. Add Contact directly to Group (Flat Payload)
        # Using the /groups/{id}/members endpoint which handles creation/update and group assignment
        data = {
            "first_name": name,
            "email": email,
            "phone1": phone,      # Primary phone field in ActiveTrail
            "sms_phone": phone,   # For SMS-based automations
            "status": "Subscribe" # Must be 'Subscribe' to trigger automations
        }
        
        resp = requests.post(
            f"{ACTIVETRAIL_BASE_URL}/groups/{group_id}/members", 
            headers=headers, 
            json=data, 
            timeout=10
        )
        
        if resp.status_code in [200, 201]:
            return True, f"הושלם (קבוצה ID: {group_id})"
        else:
            return False, f"שגיאה {resp.status_code}: {resp.text}"
            
    except Exception as e:
        return False, str(e)

def init_db():
    conn = sqlite3.connect("leads.db")
    c = conn.cursor()
    c.execute("PRAGMA table_info(leads)")
    columns = [col[1] for col in c.fetchall()]
    
    if not columns:
        c.execute('''CREATE TABLE leads
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      name TEXT,
                      phone TEXT,
                      email TEXT,
                      property_value REAL,
                      shared_income REAL,
                      loan_repayments REAL,
                      rent REAL,
                      created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    else:
        if 'email' not in columns:
            c.execute("ALTER TABLE leads ADD COLUMN email TEXT")
    
    conn.commit()
    conn.close()

init_db()

# Main UI
st.markdown('<h1 class="main-header">הפסיקו לשלם לשכירות</h1>', unsafe_allow_html=True)

# --- STEP 1: Financial Inputs ---
if st.session_state.step == 1:
    st.markdown('<div class="step-indicator">שלב 1 מתוך 3: נתונים פיננסיים</div>', unsafe_allow_html=True)
    with st.form("financial_form"):
        col1, col2 = st.columns(2)
        with col1:
            rent = st.number_input("💰 שכר דירה נוכחי", min_value=0, value=5000, step=100)
            equity = st.number_input("🏦 הון עצמי זמין", min_value=0, value=300000, step=10000)
        with col2:
            income = st.number_input("💵 הכנסה משותפת נטו", min_value=0, value=18000, step=500)
            loans = st.number_input("💳 החזר הלוואות", min_value=0, value=0, step=100)
        
        submitted = st.form_submit_button("המשך לשלב הבא ←", use_container_width=True)
        if submitted:
            st.session_state.data.update({
                'rent': rent,
                'equity': equity,
                'income': income,
                'loans': loans
            })
            st.session_state.step = 2
            st.rerun()

# --- STEP 2: Lead Details ---
elif st.session_state.step == 2:
    st.markdown('<div class="step-indicator">שלב 2 מתוך 3: פרטי יצירת קשר</div>', unsafe_allow_html=True)
    st.info("כדי להציג את החישוב המדויק עבורכם, אנא מלאו את הפרטים:")
    with st.form("contact_form"):
        name = st.text_input("שם מלא", placeholder="ישראל ישראלי")
        phone = st.text_input("מספר טלפון נייד", placeholder="050-0000000")
        email = st.text_input("אימייל", placeholder="me@example.com")
        
        col_back, col_submit = st.columns(2)
        with col_submit:
            submit_contact = st.form_submit_button("צפה בתוצאות החישוב ←", use_container_width=True)
        
        if submit_contact:
            if name and phone and email:
                # 1. Calculate Results for Saving
                d = st.session_state.data
                disposable = max(d['income'] - d['loans'], 0)
                max_repayment = int(disposable * 0.40) # 40% Logic
                prop_value = calc_max_loan(max_repayment) + d['equity']
                
                # 2. Local Database Save
                conn = sqlite3.connect("leads.db")
                c = conn.cursor()
                c.execute("INSERT INTO leads (name, phone, email, property_value, shared_income, loan_repayments, rent) VALUES (?, ?, ?, ?, ?, ?, ?)",
                          (name, phone, email, float(prop_value), float(d['income']), float(d['loans']), float(d['rent'])))
                conn.commit()
                conn.close()
                
                # 3. ActiveTrail Sync
                success, sync_msg = sync_to_activetrail(name, phone, email)
                
                st.session_state.data.update({
                    'name': name, 
                    'email': email, 
                    'sync_msg': sync_msg,
                    'sync_success': success
                })
                st.session_state.step = 3
                st.rerun()
            else:
                st.warning("אנא מלאו את כל השדות כדי להמשיך")
    
    if st.button("← חזור"):
        st.session_state.step = 1
        st.rerun()

# --- STEP 3: Results Display ---
elif st.session_state.step == 3:
    st.markdown('<div class="step-indicator">שלב 3 מתוך 3: ניתוח תוצאות</div>', unsafe_allow_html=True)
    d = st.session_state.data
    
    # Calculations with 40% PTI
    disposable_income = max(d['income'] - d['loans'], 0)
    max_allowed_repayment = int(disposable_income * 0.40)

    # Scenario 1: Same as Rent
    mortgage_at_rent = calc_max_loan(d['rent'])
    property_at_rent = mortgage_at_rent + d['equity']

    # Scenario 2: Max Allowed (40%)
    mortgage_at_max = calc_max_loan(max_allowed_repayment)
    property_at_max = mortgage_at_max + d['equity']
    
    st.markdown(f'<h2 class="centered-header">שלום {d["name"]}, הנה התוצאות שלך:</h2>', unsafe_allow_html=True)

    # --- Scenario 1 Section ---
    st.markdown(f"""
    <div class="scenario-box highlight-blue">
        <h3 style="margin-top:0;">🏠 קנייה בהחזר זהה לשכירות</h3>
        <p>אם תשתמשו ב-<b>{fmt(d['rent'])}</b> שאתם משלמים היום לטובת משכנתא:</p>
        <div style="display:flex; justify-content:space-around; text-align:center;">
            <div><b>סכום המשכנתא</b><br>{fmt(mortgage_at_rent)}</div>
            <div><b>שווי דירה אפשרית</b><br><span style="font-size:1.2rem; color:#0c3d6b; font-weight:700;">{fmt(property_at_rent)}</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- Scenario 2 Section ---
    if max_allowed_repayment > d['rent']:
        st.markdown(f"""
        <div class="scenario-box highlight-green">
            <h3 style="margin-top:0;">🚀 השתדרגות מקסימלית (מגבלת 40%)</h3>
            <p>בנק ישראל מאפשר לכם החזר של עד <b>{fmt(max_allowed_repayment)}</b> (40% מההכנסה הפנויה).</p>
            <div style="display:flex; justify-content:space-around; text-align:center;">
                <div><b>סכום המשכנתא</b><br>{fmt(mortgage_at_max)}</div>
                <div><b>שווי דירה מקסימלי</b><br><span style="font-size:1.4rem; color:#059669; font-weight:900;">{fmt(property_at_max)}</span></div>
            </div>
            <p style="margin-top:10px; font-size:0.9rem;"><i>* הכנסה פנויה: {fmt(disposable_income)} (הכנסות פחות הלוואות)</i></p>
        </div>
        """, unsafe_allow_html=True)
    
    st.info(f"בעוד 5 שנים, תצברו הון מוערך של כ-{fmt(property_at_rent * 0.15)} רק מעליית ערך הנכס (15%), במקום לאבד {fmt(d['rent'] * 60)} על שכר דירה.")
    st.success(f"נשלח אלייך מייל עם הפירוט המלא לכתובת {d['email']}")
    
    # Debug Sync Status (Visual for the user to troubleshoot)
    if 'sync_success' in d:
        if d['sync_success']:
            st.caption(f"סנכרון ל-ActiveTrail: {d['sync_msg']}")
        else:
            st.warning(f"שים לב: הפרטים נשמרו במערכת שלנו אך חלה שגיאה בסנכרון ל-ActiveTrail: {d['sync_msg']}")
    
    if st.button("חישוב מחדש ↺"):
        st.session_state.step = 1
        st.session_state.data = {}
        st.rerun()

# Footer
st.markdown("---")
st.caption("© Even Sapir - Rent or Buy · המחשבון מהווה הערכה בלבד ותואם את תקנות בנק ישראל (40% מהכנסה פנויה)")
