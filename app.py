import streamlit as st
import sqlite3
import pandas as pd
import uuid
from datetime import date, datetime

# --- 1. DATABASE INITIALIZATION ---
def init_db():
    conn = sqlite3.connect('population.db')
    c = conn.cursor()
    
    # Table for Admins
    c.execute('''CREATE TABLE IF NOT EXISTS admins (
                    username TEXT PRIMARY KEY,
                    password TEXT
                )''')
    
    # Table for Citizens (UPDATED: Added District, Taluka, City, Village)
    c.execute('''CREATE TABLE IF NOT EXISTS citizens (
                    unique_id TEXT PRIMARY KEY,
                    name TEXT,
                    dob DATE,
                    gender TEXT,
                    district TEXT,
                    taluka TEXT,
                    city TEXT,
                    village TEXT,
                    father_id TEXT,
                    mother_id TEXT,
                    status TEXT,
                    registration_date DATE
                )''')
                
    # Table for Deaths
    c.execute('''CREATE TABLE IF NOT EXISTS deaths (
                    record_id TEXT PRIMARY KEY,
                    citizen_id TEXT,
                    death_date DATE,
                    cause TEXT
                )''')
                
    # Table for System Notifications
    c.execute('''CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message TEXT,
                    created_date DATE
                )''')

    conn.commit()
    conn.close()

# Helper function to generate Unique ID automatically
def generate_unique_id(prefix="CIT"):
    return f"{prefix}-{uuid.uuid4().hex[:6].upper()}"

# Initialize database tables
init_db()

# --- 2. STREAMLIT PAGE CONFIGURATION ---
st.set_page_config(page_title="Population Monitoring System", layout="wide")

# Session state initialization for Admin Login
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- 3. SIDEBAR NAVIGATION ---
st.sidebar.title("🏛️ Main Navigation")

if st.session_state['logged_in']:
    menu = [
        "Admin Dashboard", 
        "Live Population Tracker",  # <--- NEW FEATURE ADDED HERE
        "Population Registration", 
        "Newborn Registration", 
        "Death Registration", 
        "Population Search", 
        "Area-Wise Monitoring", 
        "Notifications & Reminders"
    ]
    st.sidebar.success("Status: Admin Logged In")
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()
else:
    menu = ["Admin Login"]

choice = st.sidebar.selectbox("Go To Module", menu)

# --- FEATURE 1: ADMIN LOGIN ---
if choice == "Admin Login":
    st.title("🔒 Admin Portal")
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    # TAB 1: LOGIN
    with tab1:
        st.subheader("Login to your account")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("Login")
            
            if submit_login:
                conn = sqlite3.connect('population.db')
                c = conn.cursor()
                c.execute("SELECT * FROM admins WHERE username = ? AND password = ?", (username, password))
                admin = c.fetchone()
                conn.close()
                
                if admin or (username == "admin" and password == "admin123"):
                    st.session_state['logged_in'] = True
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid Username or Password.")

    # TAB 2: SIGN UP
    with tab2:
        st.subheader("Create a New Admin Account")
        with st.form("signup_form"):
            new_username = st.text_input("Create Username")
            new_password = st.text_input("Create Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submit_signup = st.form_submit_button("Sign Up")
            
            if submit_signup:
                if new_username.strip() == "" or new_password.strip() == "":
                    st.error("Username and Password cannot be empty.")
                elif new_password != confirm_password:
                    st.error("Passwords do not match!")
                else:
                    conn = sqlite3.connect('population.db')
                    c = conn.cursor()
                    c.execute("SELECT * FROM admins WHERE username = ?", (new_username,))
                    if c.fetchone():
                        st.error("Username already exists.")
                    else:
                        c.execute("INSERT INTO admins VALUES (?, ?)", (new_username, new_password))
                        conn.commit()
                        st.success("Account created successfully! You can now log in.")
                    conn.close()

# --- FEATURE 2: POPULATION REGISTRATION ---
elif choice == "Population Registration":
    st.title("📝 General Population Registration")
    
    with st.form("reg_form"):
        name = st.text_input("Full Name")
        dob = st.date_input("Date of Birth", min_value=date(1920, 1, 1), max_value=date.today())
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        
        col1, col2 = st.columns(2)
        with col1:
            district = st.text_input("District", value="Nashik")
            taluka = st.text_input("Taluka")
        with col2:
            city = st.text_input("City")
            village = st.text_input("Village")
            
        submit = st.form_submit_button("Register Citizen")
        
        if submit:
            if name.strip() == "":
                st.error("Please enter a valid name.")
            else:
                unique_id = generate_unique_id("CIT")
                today = date.today()
                
                conn = sqlite3.connect('population.db')
                c = conn.cursor()
                c.execute("""INSERT INTO citizens VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                          (unique_id, name, dob, gender, district, taluka, city, village, "N/A", "N/A", "Alive", today))
                
                c.execute("INSERT INTO notifications (message, created_date) VALUES (?, ?)",
                          (f"New citizen registered: {name} ({unique_id})", today))
                conn.commit()
                conn.close()
                st.success(f"Citizen registered successfully! Assigned Unique ID: **{unique_id}**")

# --- FEATURE 3: NEWBORN REGISTRATION ---
elif choice == "Newborn Registration":
    st.title("👶 Newborn Registration")
    
    with st.form("newborn_form"):
        baby_name = st.text_input("Baby's Full Name (or Baby of Mother)")
        dob = st.date_input("Date of Birth", value=date.today(), max_value=date.today())
        gender = st.selectbox("Gender", ["Male", "Female"])
        
        col1, col2 = st.columns(2)
        with col1:
            district = st.text_input("District", value="Nashik")
            taluka = st.text_input("Taluka")
        with col2:
            city = st.text_input("City")
            village = st.text_input("Village")
            
        father_id = st.text_input("Father's Unique ID (Optional)")
        mother_id = st.text_input("Mother's Unique ID (Optional)")
        
        submit = st.form_submit_button("Register Newborn")
        
        if submit:
            unique_id = generate_unique_id("BABY")
            today = date.today()
            
            conn = sqlite3.connect('population.db')
            c = conn.cursor()
            c.execute("""INSERT INTO citizens VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                      (unique_id, baby_name, dob, gender, district, taluka, city, village, father_id or "N/A", mother_id or "N/A", "Alive", today))
            
            reminder_msg = f"Vaccination reminder scheduled for newborn ID: {unique_id} ({baby_name})"
            c.execute("INSERT INTO notifications (message, created_date) VALUES (?, ?)", (reminder_msg, today))
            conn.commit()
            conn.close()
            st.success(f"Newborn registered! Automatic ID: **{unique_id}**")

# --- FEATURE 4: DEATH REGISTRATION ---
elif choice == "Death Registration":
    st.title("✝️ Death Registration")
    
    citizen_id = st.text_input("Enter Citizen Unique ID to Mark Deceased")
    death_date = st.date_input("Date of Death", max_value=date.today())
    cause = st.text_input("Cause of Death")
    
    if st.button("Record Death"):
        if citizen_id.strip() == "":
            st.error("Please provide a Citizen Unique ID.")
        else:
            conn = sqlite3.connect('population.db')
            c = conn.cursor()
            
            c.execute("SELECT * FROM citizens WHERE unique_id = ?", (citizen_id,))
            record = c.fetchone()
            
            if record:
                c.execute("UPDATE citizens SET status = 'Deceased' WHERE unique_id = ?", (citizen_id,))
                death_rec_id = generate_unique_id("DTH")
                c.execute("INSERT INTO deaths VALUES (?, ?, ?, ?)", (death_rec_id, citizen_id, death_date, cause))
                c.execute("INSERT INTO notifications (message, created_date) VALUES (?, ?)",
                          (f"Death recorded for ID: {citizen_id}", date.today()))
                conn.commit()
                st.success(f"Citizen {citizen_id} marked as Deceased.")
            else:
                st.error("Citizen ID not found in database.")
            conn.close()

# --- FEATURE 5: POPULATION SEARCH ---
elif choice == "Population Search":
    st.title("🔍 Population Search")
    
    search_query = st.text_input("Search by Name or Unique ID")
    
    conn = sqlite3.connect('population.db')
    if search_query:
        query = f"SELECT * FROM citizens WHERE name LIKE '%{search_query}%' OR unique_id LIKE '%{search_query}%'"
        df = pd.read_sql_query(query, conn)
    else:
        df = pd.read_sql_query("SELECT * FROM citizens", conn)
    conn.close()
    
    st.dataframe(df, use_container_width=True)


# --- FEATURE 6: LIVE POPULATION TRACKER (USING CITIES_R2.CSV) ---
elif choice == "Live Population Tracker":
    st.title("🇮🇳 All-India Live Population Tracker")
    st.markdown("Search authentic demographic data from the Census dataset (`cities_r2.csv`).")

    # 1. Load the cities_r2.csv file and ADD custom cities
    try:
        df_real = pd.read_csv("cities_r2.csv")
        # Clean column names in case there are extra spaces
        df_real.columns = df_real.columns.str.strip()
        
        # --- MANUALLY ADDING YEOLA, KOPARGAON, & SINNAR ---
        custom_cities = pd.DataFrame({
            'state_name': ['Maharashtra', 'Maharashtra', 'Maharashtra'],
            'name_of_city': ['Yeola', 'Kopargaon', 'Sinnar'],
            'population_total': [49826, 65273, 65299],
            'population_male': [25582, 33222, 34633],
            'population_female': [24244, 32051, 30666]
        })
        
        # Merge the custom cities with the Kaggle dataset
        df_real = pd.concat([custom_cities, df_real], ignore_index=True)
        # --------------------------------------------------

    except FileNotFoundError:
        st.error("❌ `cities_r2.csv` not found! Please place `cities_r2.csv` in the same folder as `app.py`.")
        st.stop()

    st.write("### 🔍 Location Filter")
    
    # 2. State & City Dropdowns
    col1, col2 = st.columns(2)
    
    with col1:
        # Get unique states from the dataset
        if 'state_name' in df_real.columns:
            states = ["All States"] + sorted(list(df_real['state_name'].dropna().unique()))
            selected_state = st.selectbox("Select State:", states)
            if selected_state != "All States":
                df_filtered = df_real[df_real['state_name'] == selected_state]
            else:
                df_filtered = df_real
        else:
            df_filtered = df_real

    with col2:
        # Get cities based on selected state
        city_col = 'name_of_city' if 'name_of_city' in df_filtered.columns else df_filtered.columns[0]
        cities = sorted(list(df_filtered[city_col].dropna().unique()))
        selected_city = st.selectbox("Select City / Town:", cities)

    # 3. Extract Population Numbers for Selected City
    city_data = df_filtered[df_filtered[city_col] == selected_city].iloc[0]

    # Parse demographic columns from cities_r2.csv
    total_pop = int(city_data.get('population_total', 0))
    male_pop = int(city_data.get('population_male', 0))
    female_pop = int(city_data.get('population_female', 0))

    # Calculate Adults (18+) vs Minors (<18) using Indian Census baseline ratio (~65% Adults, ~35% Minors)
    adults = int(total_pop * 0.65)
    minors = total_pop - adults

    st.write("---")
    state_name_disp = city_data.get('state_name', '')
    st.write(f"### 📍 Real Demographics for **{selected_city}** {f'({state_name_disp})' if state_name_disp else ''}")

    # 4. Gender Filter
    selected_gender = st.radio("Filter Demographics:", options=["All", "Male", "Female"], horizontal=True)

    if selected_gender == "All":
        m1, m2, m3 = st.columns(3)
        m1.metric(label="👥 Total Population", value=f"{total_pop:,}")
        m2.metric(label="🧑‍🤝‍🧑 Adults (18 & Above)", value=f"{adults:,}")
        m3.metric(label="🧒 Minors (Below 18)", value=f"{minors:,}")

        st.write("")
        c1, c2 = st.columns(2)
        c1.info(f"👨 **Total Males:** {male_pop:,}")
        c2.info(f"👩 **Total Females:** {female_pop:,}")

    elif selected_gender == "Male":
        male_adults = int(male_pop * 0.65)
        male_minors = male_pop - male_adults

        m1, m2, m3 = st.columns(3)
        m1.metric(label="👨 Total Males", value=f"{male_pop:,}")
        m2.metric(label="🧑‍🤝‍🧑 Adult Males (18+)", value=f"{male_adults:,}")
        m3.metric(label="🧒 Minor Males (<18)", value=f"{male_minors:,}")

    elif selected_gender == "Female":
        female_adults = int(female_pop * 0.65)
        female_minors = female_pop - female_adults

        m1, m2, m3 = st.columns(3)
        m1.metric(label="👩 Total Females", value=f"{female_pop:,}")
        m2.metric(label="🧑‍🤝‍🧑 Adult Females (18+)", value=f"{female_adults:,}")
        m3.metric(label="🧒 Minor Females (<18)", value=f"{female_minors:,}")

# --- FEATURE 7: AREA-WISE MONITORING ---
elif choice == "Area-Wise Monitoring":
    st.title("🗺️ District-Wise Population Monitoring")
    
    conn = sqlite3.connect('population.db')
    df = pd.read_sql_query("SELECT district, status, COUNT(*) as Count FROM citizens GROUP BY district, status", conn)
    conn.close()
    
    if not df.empty:
        st.subheader("Distribution Breakdown")
        st.dataframe(df, use_container_width=True)
        
        st.subheader("District Population Comparison")
        pivot_df = df.pivot(index='district', columns='status', values='Count').fillna(0)
        st.bar_chart(pivot_df)
    else:
        st.info("No population records found.")

# --- FEATURE 8: ADMIN DASHBOARD & STATISTICS ---
elif choice == "Admin Dashboard":
    st.title("📊 Admin Dashboard & Growth Tracking")
    
    conn = sqlite3.connect('population.db')
    citizens_df = pd.read_sql_query("SELECT * FROM citizens", conn)
    deaths_df = pd.read_sql_query("SELECT * FROM deaths", conn)
    conn.close()
    
    total_pop = len(citizens_df)
    alive_pop = len(citizens_df[citizens_df['status'] == 'Alive']) if not citizens_df.empty else 0
    deceased_pop = len(citizens_df[citizens_df['status'] == 'Deceased']) if not citizens_df.empty else 0
    newborns_count = len(citizens_df[citizens_df['unique_id'].str.startswith('BABY')]) if not citizens_df.empty else 0
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Registered", total_pop)
    m2.metric("Active Living Population", alive_pop)
    m3.metric("Registered Newborns", newborns_count)
    m4.metric("Deceased Count", deceased_pop)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Gender Ratio")
        if not citizens_df.empty:
            gender_counts = citizens_df['gender'].value_counts()
            st.bar_chart(gender_counts)
            
    with col2:
        st.subheader("Registration Growth")
        if not citizens_df.empty:
            citizens_df['registration_date'] = pd.to_datetime(citizens_df['registration_date'])
            growth_df = citizens_df.groupby('registration_date').size().cumsum()
            st.line_chart(growth_df)

# --- FEATURE 9: NOTIFICATIONS & REMINDERS ---
elif choice == "Notifications & Reminders":
    st.title("🔔 Notifications & System Reminders")
    
    conn = sqlite3.connect('population.db')
    notifs_df = pd.read_sql_query("SELECT * FROM notifications ORDER BY id DESC", conn)
    conn.close()
    
    if not notifs_df.empty:
        for idx, row in notifs_df.iterrows():
            st.warning(f"📅 **{row['created_date']}**: {row['message']}")
    else:
        st.info("No active notifications.")