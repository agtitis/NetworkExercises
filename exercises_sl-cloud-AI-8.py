import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json
import random
import pandas as pd

import google.generativeai as genai

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

# 🔥 Αρχικοποίηση GEMINI API
gemini_api_key = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=gemini_api_key)

# 🔥 Αν δεν υπάρχουν τιμές στο session_state, αρχικοποίησέ τις
if "selected_category" not in st.session_state:
    st.session_state.selected_category = None
if "selected_exercise" not in st.session_state:
    st.session_state.selected_exercise = None
if "show_solution" not in st.session_state:
    st.session_state.show_solution = False  # 🔥 Απόκρυψη της λύσης στην αρχή
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # 🔥 Ιστορικό συνομιλίας chatbot

st.title("📡 Ασκήσεις Δικτύων")
col1, col2 = st.columns([2, 1])

with col1:
    # 🔥 Επιλογή Κατηγορίας
    categories = list(set(ex["Κατηγορία άσκησης"] for ex in exercises))
    previous_category = st.session_state.selected_category
    selected_category = st.selectbox("📂 Επιλέξτε Κατηγορία", categories,
                                     index=categories.index(
                                         st.session_state.selected_category) if st.session_state.selected_category else 0)

    if selected_category != previous_category:
        st.session_state.selected_category = selected_category
        st.session_state.selected_exercise = None
        st.session_state.show_solution = False

    # 🔥 Φιλτράρισμα Ασκήσεων ανά κατηγορία
    filtered_exercises = [ex for ex in exercises if ex["Κατηγορία άσκησης"] == selected_category]

    # 🔥 Επιλογή Άσκησης
    exercise_titles = [ex["Περιγραφή άσκησης"] for ex in filtered_exercises]

    if st.session_state.selected_exercise not in exercise_titles:
        st.session_state.selected_exercise = exercise_titles[0] if exercise_titles else None
        st.session_state.show_solution = False

    selected_exercise = st.selectbox("📜 Επιλέξτε Άσκηση", exercise_titles,
                                     index=exercise_titles.index(
                                         st.session_state.selected_exercise) if st.session_state.selected_exercise else 0)

    if selected_exercise != st.session_state.selected_exercise:
        st.session_state.selected_exercise = selected_exercise
        st.session_state.show_solution = False

    # 🔥 Random Επιλογή Άσκησης
    if st.button("🎲 Τυχαία Άσκηση"):
        random_exercise = random.choice(exercises)
        st.session_state.selected_category = random_exercise["Κατηγορία άσκησης"]
        st.session_state.selected_exercise = random_exercise["Περιγραφή άσκησης"]
        st.session_state.show_solution = False
        st.rerun()

with col2:
    st.image("https://github.com/agtitis/NetworkExercises/raw/refs/heads/main/logo.png", use_container_width=True)

# 🔥 Ανάκτηση Επιλεγμένης Άσκησης
exercise = next((ex for ex in filtered_exercises if ex["Περιγραφή άσκησης"] == selected_exercise), None)

if exercise:
    st.subheader("📌 Άσκηση")
    st.markdown(f'<div class="styled-box"><b>{exercise["Κείμενο άσκησης"]}</b></div>', unsafe_allow_html=True)

    user_answer = st.text_area("✍️ Γράψτε την απάντησή σας:", height=150)

    # 🔥 Εμφάνιση πίνακα αν υπάρχει
    if "Πίνακας άσκησης" in exercise:
        st.subheader("📊 Πίνακας Άσκησης")
        table_data = exercise["Πίνακας άσκησης"]
        # 🔥 Μετατροπή του λεξικού σε DataFrame για να κρατήσουμε τη σειρά των στηλών
        df = pd.DataFrame.from_dict(table_data)
        # 🔥 Ορισμός της σωστής σειράς στηλών
        custom_order = ["Πεδίο"] + [col for col in df.columns if col != "Πεδίο"]
        df = df[custom_order]  # Ταξινόμηση στη σωστή σειρά
        # 🔥 Εμφάνιση του πίνακα με τη σωστή σειρά στηλών
        #st.table(df)
        edited_df = st.data_editor(df, num_rows="dynamic")  # Επιτρέπει επεξεργασία

    if not st.session_state.show_solution:
        if st.button("🔍 Εμφάνιση Λύσης"):
            st.session_state.show_solution = True
            st.rerun()
    if st.session_state.show_solution:
        st.subheader("🛠 Λύση")
        st.markdown(exercise["Λύση άσκησης"], unsafe_allow_html=True)
        if "Πίνακας λύσης" in exercise:
            st.subheader("📊 Πίνακας λύσης")
            table_data = exercise["Πίνακας λύσης"]
            # 🔥 Μετατροπή του λεξικού σε DataFrame για να κρατήσουμε τη σειρά των στηλών
            df = pd.DataFrame.from_dict(table_data)
            # 🔥 Ορισμός της σωστής σειράς στηλών
            custom_order = ["Πεδίο"] + [col for col in df.columns if col != "Πεδίο"]
            df = df[custom_order]  # Ταξινόμηση στη σωστή σειρά
            # 🔥 Εμφάνιση του πίνακα με τη σωστή σειρά στηλών
            st.table(df)



    # 🔥 Chatbot Αξιολόγησης Απάντησης
    st.subheader("🤖 Βοηθός AI")
    st.session_state.chat_history = []
    if st.button("🧠 Αξιολόγηση Απάντησης"):
        # 🔥 Μετατροπή του Πίνακα Λύσης σε Κείμενο (αν υπάρχει)
        if "Πίνακας λύσης" in exercise:
            solution_table_df = pd.DataFrame.from_dict(exercise["Πίνακας λύσης"])
            solution_table_str = solution_table_df.to_string(index=False)  # Μετατροπή σε μορφή string
        else:
            solution_table_str = "Δεν υπάρχει διαθέσιμος πίνακας λύσης."
        # 🔥 Μετατροπή της απάντησης του μαθητή σε Κείμενο (αν υπάρχει επεξεργασμένος πίνακας)
        if 'edited_df' in locals() and edited_df is not None:
            student_table_str = edited_df.to_string(index=False)
        else:
            student_table_str = "Ο μαθητής δεν συμπλήρωσε τον πίνακα."

        prompt = f"""
        Είσαι ένας εκπαιδευτικός πληροφορικής που ελέγχει απαντήσεις μαθητών. 
        Η άσκηση είναι: "{exercise['Κείμενο άσκησης']}".
        **Η σωστή απάντηση είναι:** "{exercise['Λύση άσκησης']}".
        **Πίνακας Λύσης:** {solution_table_str}
        **Ο μαθητής έγραψε:** "{user_answer}".
        **Απάντηση μαθητή στον πίνακα:** {student_table_str} 
        Δώσε ανατροφοδότηση στον μαθητή για το αν είναι σωστή η απάντηση ή τι πρέπει να διορθώσει.
        """
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        bot_reply = response.text
        st.session_state.chat_history.append(f"🤖 Chatbot: {bot_reply}")

    # 🔥 Εμφάνιση συνομιλίας
    for msg in st.session_state.chat_history:
        st.write(msg)


    # 🔥 Πεδίο ερώτησης προς το Chatbot
    user_question = st.text_input("💬 Ρώτησε το Chatbot:")
    if st.button("✉️ Αποστολή Ερώτησης"):
        if user_question.strip() != "":
            # 🔥 Δημιουργία prompt για το Gemini AI
            prompt = f"""
            Είσαι ένας βοηθός πληροφορικής που απαντά σε ερωτήσεις μαθητών.
            Ο μαθητής ρώτησε: "{user_question}".
            Δώσε μια σαφή και επεξηγηματική απάντηση.
            """

            # 🔥 Αποστολή στο Gemini
            model = genai.GenerativeModel('gemini-2.0-flash')
            response = model.generate_content(prompt)
            bot_reply = response.text

            # 🔥 Προσθήκη της ερώτησης και της απάντησης στο ιστορικό
            st.session_state.chat_history.append(f"👤 Εσύ: {user_question}")
            st.session_state.chat_history.append(f"🤖 Chatbot: {bot_reply}")

            # 🔥 Επαναφόρτωση της σελίδας για να εμφανιστεί η απάντηση χωρίς να χαθεί το ιστορικό
            st.rerun()

else:
    st.warning("❗ Δεν υπάρχουν ασκήσεις σε αυτή την κατηγορία.")
