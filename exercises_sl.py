import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json
import random

# set page
st.set_page_config(
    page_title="Ασκήσεις δικτύων App",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Report a bug': "mailto:agtitis@gmail.com",
        'About': "Μία **cool** εφαρμογή για την εξάσκηση στις ασκήσεις δικτύων (*Beta*)!"
    }
)


# 🔥 Σύνδεση με Firestore
key_dict = json.loads(st.secrets["FIREBASE_KEY"])
cred = credentials.Certificate(key_dict)

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()

# 🔥 Φόρτωση των ασκήσεων
@st.cache_data
def load_data():
    exercises_ref = db.collection("exercises")
    docs = exercises_ref.stream()
    data = [doc.to_dict() for doc in docs]
    return data if data else None

exercises = load_data()
if exercises is None:
    st.error("❌ Δεν βρέθηκαν ασκήσεις στη βάση δεδομένων!")
    st.stop()

# 🔥 Αν δεν υπάρχουν τιμές στο session_state, αρχικοποίησέ τις
if "selected_category" not in st.session_state:
    st.session_state.selected_category = None

if "selected_exercise" not in st.session_state:
    st.session_state.selected_exercise = None

if "show_solution" not in st.session_state:
    st.session_state.show_solution = False  # 🔥 Απόκρυψη της λύσης στην αρχή

st.title("📡 Ασκήσεις Δικτύων")

col1, col2 = st.columns([2, 1])

with col1:
    # 🔥 Επιλογή Κατηγορίας
    categories = list(set(ex["Κατηγορία άσκησης"] for ex in exercises))

    previous_category = st.session_state.selected_category
    selected_category = st.selectbox("📂 Επιλέξτε Κατηγορία", categories,
                                     index=categories.index(st.session_state.selected_category) if st.session_state.selected_category else 0)

    # Αν αλλάξει η κατηγορία, κάνουμε reset την επιλεγμένη άσκηση και τη λύση
    if selected_category != previous_category:
        st.session_state.selected_category = selected_category
        st.session_state.selected_exercise = None
        st.session_state.show_solution = False  # 🔥 Κρύβουμε τη λύση

    # 🔥 Φιλτράρισμα Ασκήσεων ανά κατηγορία
    filtered_exercises = [ex for ex in exercises if ex["Κατηγορία άσκησης"] == selected_category]

    # 🔥 Επιλογή Άσκησης με έλεγχο ύπαρξης
    exercise_titles = [ex["Περιγραφή άσκησης"] for ex in filtered_exercises]

    if st.session_state.selected_exercise not in exercise_titles:
        st.session_state.selected_exercise = exercise_titles[0] if exercise_titles else None
        st.session_state.show_solution = False  # 🔥 Κρύβουμε τη λύση

    selected_exercise = st.selectbox("📜 Επιλέξτε Άσκηση", exercise_titles,
                                     index=exercise_titles.index(st.session_state.selected_exercise) if st.session_state.selected_exercise else 0)

    # Αν αλλάξει η άσκηση, κρύβουμε τη λύση
    if selected_exercise != st.session_state.selected_exercise:
        st.session_state.selected_exercise = selected_exercise
        st.session_state.show_solution = False  # 🔥 Κρύβουμε τη λύση

    # 🔥 Random Επιλογή Άσκησης (ενημερώνει τα selectbox)
    if st.button("🎲 Τυχαία Άσκηση"):
        random_exercise = random.choice(exercises)  # Επιλογή τυχαίας άσκησης
        st.session_state.selected_category = random_exercise["Κατηγορία άσκησης"]
        st.session_state.selected_exercise = random_exercise["Περιγραφή άσκησης"]
        st.session_state.show_solution = False  # 🔥 Απόκρυψη της λύσης
        st.rerun()  # 🔄 Refresh για να ενημερωθούν τα selectbox

with col2:
    st.image("https://github.com/agtitis/NetworkExercises/raw/refs/heads/main/logo.png", use_container_width=True)

# 🔥 Ανάκτηση Επιλεγμένης Άσκησης
exercise = next((ex for ex in filtered_exercises if ex["Περιγραφή άσκησης"] == selected_exercise), None)

if exercise:
    st.subheader("📌 Άσκηση")
    st.markdown(f'<div class="styled-box"><b>{exercise["Κείμενο άσκησης"]}</b></div>', unsafe_allow_html=True)

    # 🔥 Πεδίο απάντησης
    user_answer = st.text_area("✍️ Γράψτε την απάντησή σας:", height=150)

    # 🔥 Εμφάνιση Λύσης με Κουμπί
    if not st.session_state.show_solution:
        if st.button("🔍 Εμφάνιση Λύσης"):
            st.session_state.show_solution = True
            st.rerun()  # 🔄 Κάνει refresh για να ενημερώσει την εμφάνιση της λύσης

    if st.session_state.show_solution:
        st.subheader("🛠 Λύση")
        st.markdown(exercise["Λύση άσκησης"], unsafe_allow_html=True)

    st.write("🔹 **Οδηγίες:** Επιλέξτε κατηγορία, διαλέξτε άσκηση ή πατήστε 'Τυχαία Άσκηση'. Γράψτε την απάντησή σας και ανοίξτε τη λύση για έλεγχο!")
else:
    st.warning("❗ Δεν υπάρχουν ασκήσεις σε αυτή την κατηγορία.")
