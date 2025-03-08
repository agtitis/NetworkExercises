import streamlit as st
import pandas as pd
import requests
from io import BytesIO


# Φόρτωση του Excel αρχείου
FILE_PATH = "https://github.com/agtitis/NetworkExercises/raw/refs/heads/main/askiseis.xlsx"
@st.cache_data
def load_data():
    response = requests.get(FILE_PATH)
    if response.status_code != 200:
        st.error("Αποτυχία φόρτωσης του αρχείου!")
        return None
    return pd.read_excel(BytesIO(response.content), engine="openpyxl")

df = load_data()
if df is None:
    st.stop()
    
# Streamlit app

# URL εικόνας από το GitHub (αντικατέστησε το με το πραγματικό URL)
background_url = "https://github.com/agtitis/NetworkExercises/raw/refs/heads/main/logo.jpg" 

st.markdown(
    f"""
    <style>
    .stApp {{
        background: url("{background_url}") no-repeat top center fixed;
        background-size: cover;
    }}
    .stButton>button {{
        background-color: #00897B; /* Teal (Material Design) */
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 20px;
        font-size: 16px;
    }}
    .stSelectbox>div {{
        background-color: #26A69A; /* Light Teal */
        color: white;
        border-radius: 8px;
        padding: 5px;
    }}
    .stTextArea>div>div>input {{
        background-color: #E0F2F1; /* Very Light Teal */
        color: #004D40; /* Dark Teal */
        font-size: 16px;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

st.title("Ασκήσεις δικτύων")

# Επιλογή κατηγορίας άσκησης
category = st.selectbox("Επιλέξτε κατηγορία", df["Κατηγορία άσκησης"].unique(), index=0)

# Φιλτράρισμα των ασκήσεων βάσει κατηγορίας
filtered_df = df[df["Κατηγορία άσκησης"] == category]

# Drop-down για επιλογή άσκησης με βάση τον ΑΑ
exercise_id = st.selectbox("Επιλέξτε Άσκηση", filtered_df["Περιγραφή άσκησης"].tolist())

# Επιλογή της άσκησης
exercise = filtered_df[filtered_df["Περιγραφή άσκησης"] == exercise_id].iloc[0]

st.subheader("Άσκηση")
st.text_area("", exercise["Κείμενο άσκησης"], height=150, disabled=True)

# Πεδίο εισαγωγής απάντησης
user_answer = st.text_area("Γράψτε την απάντησή σας:", height=150)

# Κουμπί για εμφάνιση λύσης
if st.button("Εμφάνιση λύσης"):
    st.subheader("Λύση")
    st.text_area("", exercise["Λύση άσκησης"], height=150, disabled=True)

st.write("\n**Οδηγίες:** Επιλέξτε κατηγορία, διαλέξτε άσκηση και γράψτε την απάντησή σας. Πατήστε 'Εμφάνιση λύσης' για έλεγχο!")
