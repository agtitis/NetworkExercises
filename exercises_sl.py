import streamlit
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json
import random
import pandas as pd

import google.generativeai as genai

# 🔥 Μενού σελίδας
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

st.markdown("""
    <style>
        [data-testid=stSidebar] {
            background-color: teal;
            width: 500px; # Set the width to your desired value
        }
    </style>
    """, unsafe_allow_html=True)

# 🔥 Σύνδεση με Firestore
key_dict = json.loads(st.secrets["FIREBASE_KEY"])
cred = credentials.Certificate(key_dict)
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

# 🔥 Αρχικοποίηση GEMINI API
gemini_api_key = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=gemini_api_key)

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

categories = list(set(ex["Κατηγορία άσκησης"] for ex in exercises))


# Συνάρτηση που διαγράφει την απάντηση και επαναφέρει την επιλεγμένη άσκηση όταν αλλάζει η κατηγορία
def reset_category():
    st.session_state.selected_category = st.session_state["category_select"]
    st.session_state.selected_exercise = None  # Καμία επιλεγμένη άσκηση
    st.session_state.user_answer = ""  # Διαγραφή απάντησης
    st.session_state.exercise_solution = None  # Διαγραφή Λύσης
    st.session_state.ai_response = None # Διαγραφή ΑΙ

# Συνάρτηση που διαγράφει μόνο την απάντηση όταν αλλάζει η άσκηση
def reset_exercise():
    if st.session_state.selected_exercise != st.session_state["exercise_select"]:
        st.session_state.user_answer = ""  # Διαγραφή απάντησης
    st.session_state.selected_exercise = st.session_state["exercise_select"]  # Ενημέρωση επιλεγμένης άσκησης
    st.session_state.exercise_solution = None  # Διαγραφή Λύσης
    st.session_state.ai_response = None # Διαγραφή ΑΙ


# Αρχικοποίηση session_state αν δεν υπάρχουν
if "selected_category" not in st.session_state:
    st.session_state.selected_category = categories[0]  # Προεπιλογή στην πρώτη κατηγορία
if "selected_exercise" not in st.session_state:
    st.session_state.selected_exercise = None  # Δεν υπάρχει άσκηση αρχικά
if "user_answer" not in st.session_state:
    st.session_state.user_answer = ""
if "exercise_solution" not in st.session_state:
    st.session_state.exercise_solution = None
if "ai_response" not in st.session_state:
    st.session_state.ai_response = None

# 🔥 Τίτλος σελίδας
st.title("📡 Ασκήσεις Δικτύων")

# 🎨 Sidebar για επιλογή κατηγορίας και άσκησης
with st.sidebar:
    st.image("https://github.com/agtitis/NetworkExercises/raw/refs/heads/main/logo.png", use_container_width=True)

    # 🔥 Επιλογή Κατηγορίας
    st.selectbox(
        "📂 Επιλέξτε Κατηγορία", categories,
        index=categories.index(st.session_state.selected_category),
        key="category_select", on_change=reset_category
    )

    # 🔥 Φιλτράρισμα Ασκήσεων ανά κατηγορία
    filtered_exercises = [ex for ex in exercises if ex["Κατηγορία άσκησης"] == st.session_state.selected_category]
    # 🔥 Επιλογή Άσκησης (αν υπάρχουν διαθέσιμες ασκήσεις)
    if filtered_exercises:
        exercise_titles = [ex["Περιγραφή άσκησης"] for ex in filtered_exercises]

        # Επιλέγουμε την πρώτη άσκηση αν δεν υπάρχει ήδη επιλεγμένη
        if st.session_state.selected_exercise not in exercise_titles:
            st.session_state.selected_exercise = exercise_titles[0]

        st.selectbox(
            "📜 Επιλέξτε Άσκηση", exercise_titles,
            index=exercise_titles.index(st.session_state.selected_exercise),
            key="exercise_select", on_change=reset_exercise
        )
        # Ανάκτηση επιλεγμένης άσκησης
        selected_exercise = st.session_state.selected_exercise
        # 🔥 Ανάκτηση Επιλεγμένης Άσκησης
        exercise = next((ex for ex in filtered_exercises if ex["Περιγραφή άσκησης"] == selected_exercise), None)
    else:
        st.warning("❗ Δεν υπάρχουν ασκήσεις σε αυτή την κατηγορία.")


# 🎭 Δύο στήλες για εμφάνιση άσκησης και βοηθού AI
col1, col2 = st.columns([2, 1])  # Αριστερά μεγαλύτερη στήλη, δεξιά μικρότερη
with col1:  # 🔹 Αριστερή στήλη (Άσκηση & Λύση)
    if exercise:
        st.subheader("📌 Άσκηση")
        st.markdown(f'<div class="styled-box"><b>{exercise["Κείμενο άσκησης"]}</b></div>', unsafe_allow_html=True)

        # Πεδίο απάντησης που κρατάει το state
        user_answer = st.text_area("✍️ Γράψτε την απάντησή σας:", value=st.session_state.user_answer,
                                   height=150, key="user_answer")
        # 🔥 Εμφάνιση πίνακα αν υπάρχει
        if "Πίνακας άσκησης" in exercise:
            st.subheader("📊 Πίνακας Άσκησης")
            table_data = exercise["Πίνακας άσκησης"]
            # 🔥 Μετατροπή του λεξικού σε DataFrame για να κρατήσουμε τη σειρά των στηλών
            df = pd.DataFrame.from_dict(table_data)
            # 🔥 Ορισμός της σωστής σειράς των στηλών
            column_order = exercise["Column_Order"]
            df = df[column_order]  # Εφαρμογή της σωστής σειράς
            # 🔥 Εμφάνιση του πίνακα με τη σωστή σειρά στηλών
            edited_df = st.data_editor(df)  # Επιτρέπει επεξεργασία

        if st.button("🔍 Εμφάνιση Λύσης"):
            st.session_state.exercise_solution = exercise["Λύση άσκησης"]  # Αποθήκευση της λύσης
            st.session_state.ai_response = None  # Διαγραφή απάντησης AI για αποφυγή σύγχυσης
        # Εμφάνιση λύσης αν έχει αποθηκευτεί
        if st.session_state.exercise_solution:
            st.subheader("🛠 Λύση")
            st.markdown(st.session_state.exercise_solution, unsafe_allow_html=True)
            if "Πίνακας λύσης" in exercise:
                st.subheader("📊 Πίνακας λύσης")
                table_data = exercise["Πίνακας λύσης"]
                # 🔥 Μετατροπή του λεξικού σε DataFrame για να κρατήσουμε τη σειρά των στηλών
                df = pd.DataFrame.from_dict(table_data)
                # 🔥 Ορισμός της σωστής σειράς των στηλών
                column_order = exercise["Column_Order"]
                df = df[column_order]  # Εφαρμογή της σωστής σειράς
                # 🔥 Εμφάνιση του πίνακα με τη σωστή σειρά στηλών
                st.table(df)

with col2:  # 🤖 Δεξιά στήλη (Βοηθός AI)
    # 🔥 Chatbot Αξιολόγησης Απάντησης
    st.subheader("🤖 Βοηθός AI")
    st.markdown(" :smile: :red[Όχι 100% αξιόπιστος]")
    if st.button("🧠 Αξιολόγηση Απάντησης"):
        # 🔥 Μετατροπή του Πίνακα Λύσης σε Κείμενο (αν υπάρχει)
        if "Πίνακας λύσης" in exercise:
            solution_table_df = pd.DataFrame.from_dict(exercise["Πίνακας λύσης"])
            column_order = exercise["Column_Order"]
            solution_table_df = solution_table_df[column_order]
            solution_table_str = solution_table_df.to_string(index=False)  # Μετατροπή σε μορφή string
        else:
            solution_table_str = "Δεν υπάρχει διαθέσιμος πίνακας λύσης."
        # 🔥 Μετατροπή της απάντησης του μαθητή σε Κείμενο (αν υπάρχει επεξεργασμένος πίνακας)
        if 'edited_df' in locals() and edited_df is not None:
            student_table_str = edited_df.to_string(index=False)
        else:
            student_table_str = "Ο μαθητής δεν συμπλήρωσε τον πίνακα."
        prompt = f"""
        Ρόλος: Είσαι ένας εκπαιδευτικός πληροφορικής που διδάσκει το μάθημα Δίκτυα Υπολογιστών
        σε μαθητές Επαγγελματικού Λυκείου στην Ελλάδα.. 
        Η άσκηση είναι: "{exercise['Κείμενο άσκησης']}".
        **Η σωστή απάντηση είναι:** "{exercise['Λύση άσκησης']}".
        **Πίνακας Λύσης:** {solution_table_str}
        **Ο μαθητής έγραψε:** "{user_answer}".
        **Απάντηση μαθητή στον πίνακα:** {student_table_str} 
        Έργο: Δώσε ανατροφοδότηση στον μαθητή για το αν είναι σωστή η απάντηση ή τι πρέπει να διορθώσει
        με βάση το βιβλίο Δίκτυα Υπολογιστών Γ' ΕΠΑΛ.
        Προδιαγραφές: Να είναι υποστηρικτικός και δώσεις κάποια στοιχεία για να φτάσει ο μαθητής στη λύση μόνος του.
        """
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        st.session_state.ai_response = response.text  # Αποθήκευση απάντησης AI
        st.session_state.exercise_solution = None  # Διαγραφή λύσης αν εμφανιστεί το AI response

    # Εμφάνιση απάντησης AI αν έχει αποθηκευτεί
    if st.session_state.ai_response:
        st.subheader("🤖 Απάντηση Βοηθού AI")
        st.write(st.session_state.ai_response)

