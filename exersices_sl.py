import streamlit as st
import pandas as pd
import random

# Φόρτωση του Excel αρχείου
FILE_PATH = "https://github.com/agtitis/NetworkExercises/raw/refs/heads/main/askiseis.xlsx"
@st.cache_data
def load_data():
    return pd.read_excel(FILE_PATH)

df = load_data()

# Streamlit app
st.title("Εξασκητής Υποδικτύωσης")

# Επιλογή κατηγορίας άσκησης
category = st.selectbox("Επιλέξτε κατηγορία", df["Κατηγορία άσκησης"].unique(), index=0)

# Φιλτράρισμα των ασκήσεων βάσει κατηγορίας
filtered_df = df[df["Κατηγορία άσκησης"] == category]

# Drop-down για επιλογή άσκησης με βάση τον ΑΑ
exercise_id = st.selectbox("Επιλέξτε Άσκηση", filtered_df["Αύξων αριθμός άσκησης"].tolist())

# Επιλογή της άσκησης
exercise = filtered_df[filtered_df["Αύξων αριθμός άσκησης"] == exercise_id].iloc[0]

st.subheader("Άσκηση")
st.text_area("", exercise["Κείμενο άσκησης"], height=150, disabled=True)

# Πεδίο εισαγωγής απάντησης
user_answer = st.text_area("Γράψτε την απάντησή σας:", height=150)

# Κουμπί για εμφάνιση λύσης
if st.button("Εμφάνιση λύσης"):
    st.subheader("Λύση")
    st.text_area("", exercise["Λύση άσκησης"], height=150, disabled=True)

st.write("\n**Οδηγίες:** Επιλέξτε κατηγορία, διαλέξτε άσκηση και γράψτε την απάντησή σας. Πατήστε 'Εμφάνιση λύσης' για έλεγχο!")
