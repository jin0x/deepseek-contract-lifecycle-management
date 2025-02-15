import streamlit as st
import os

# Paths
UPLOAD_DIR = "contracts/uploaded_contracts"
# BACKGROUND_IMAGE = ""

# Ensure directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Simulated Authentication (No DB, Just Session State)
users = {}  # Dictionary to store user credentials temporarily

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "page" not in st.session_state:
    st.session_state.page = "landing"
if "user_email" not in st.session_state:
    st.session_state.user_email = ""

# Navigation Functions
def go_to_login():
    st.session_state.page = "login"

def go_to_dashboard():
    st.session_state.page = "dashboard"
    st.session_state.authenticated = True

def logout():
    st.session_state.authenticated = False
    st.session_state.page = "login"

# Landing Page
def show_landing_page():
    st.markdown("""
        <style>
        [data-testid="stAppViewContainer"] {
            background-color: #0e1117;
        }
        .main {
            background-color: #0e1117;
        }
        .landing-container {
            display: flex;
            align-items: center;
            gap: 4rem;
            padding: 2rem;
            background-color: #0e1117;
            margin: -6rem -4rem;
            min-height: 100vh;
            flex-direction: row; /* Ensures text left, image right */
        }
        .landing-text {
            flex: 1;
            padding: 2rem;
            color: white;
        }
        .landing-title {
            font-size: 3.5rem;
            font-weight: 800;
            margin-bottom: 1.5rem;
            line-height: 1.2;
            color: white;
        }
        .landing-subtitle {
            font-size: 1.2rem;
            color: #94a3b8;
            margin-bottom: 2rem;
            line-height: 1.6;
        }
        .landing-image {
            flex: 1;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        @media (max-width: 768px) {
            .landing-container {
                flex-direction: column-reverse;
                text-align: center;
            }
            .landing-text, .landing-image {
                padding: 1rem;
            }
            .landing-title {
                font-size: 2.5rem;
            }
        }
        </style>
        <div class="landing-container">
            <div class="landing-text">
                <h1 class="landing-title">Bringing the Power of AI to Contract Management</h1>
                <p class="landing-subtitle">
                    Increase contracting efficiency by 80% across your business with our intuitive, 
                    customizable, and AI-powered contract management solution.
                </p>
            </div>
            <div class="landing-image">
                <img src="" alt="Contract Management" style="max-width: 100%; height: auto;">
            </div>
        </div>
    """, unsafe_allow_html=True)

    # "Get Started" button
    if st.button("Get Started", key="get-started-btn"):
        go_to_login()


# Login & Sign-Up Page
def show_login_page():
    st.title("Login / Sign Up")
    option = st.radio("", ["Login", "Sign Up"], horizontal=True)

    if option == "Login":
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if email in users and users[email] == password:
                st.session_state.user_email = email
                go_to_dashboard()
            else:
                st.error("Invalid credentials or user not found.")
    
    else:  # Signup
        name = st.text_input("Full Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        contract_type = st.selectbox("Contract Type", ["Service Agreement", "NDA", "Employment Contract", "Other"])
        contract_file = st.file_uploader("Upload Contract", type=["pdf"])

        if st.button("Sign Up & Upload"):
            if name and email and password and contract_file:
                users[email] = password  # Store user temporarily
                with open(os.path.join(UPLOAD_DIR, contract_file.name), "wb") as f:
                    f.write(contract_file.getbuffer())
                st.session_state.user_email = email
                st.success("Account created successfully! Redirecting...")
                go_to_dashboard()
            else:
                st.error("Please fill in all fields.")

# Dashboard
def show_dashboard():
    st.title(f"Welcome, {st.session_state.user_email}")
    st.write("Upload contracts for analysis.")

    contract_type = st.selectbox("Contract Type", ["Service Agreement", "NDA", "Employment Contract", "Other"])
    contract_file = st.file_uploader("Upload Contract", type=["pdf"])

    if st.button("Submit for Analysis"):
        if contract_file:
            with open(os.path.join(UPLOAD_DIR, contract_file.name), "wb") as f:
                f.write(contract_file.getbuffer())
            st.success(f"Contract '{contract_file.name}' submitted successfully!")
        else:
            st.error("Please upload a contract.")

    if st.button("Logout"):
        logout()


# Page Routing
if st.session_state.page == "landing":
    show_landing_page()
elif st.session_state.page == "login":
    show_login_page()
elif st.session_state.authenticated:
    show_dashboard()
else:
    show_login_page()
