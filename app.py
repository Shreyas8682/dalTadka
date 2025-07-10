import os
import uuid
import streamlit as st
from datetime import datetime
from db.database import create_tables, connect_db
from face_engine.face_model import FaceEngine
from face_engine.matcher import find_matches
import streamlit as st
import streamlit as st
import streamlit as st
import time

# Only show intro once per session
if 'intro_shown' not in st.session_state:
    st.session_state.intro_shown = False

if not st.session_state.intro_shown:
    st.markdown("""
        <style>
        html, body, [data-testid="stAppViewContainer"] {
            background-color: black;
            height: 100vh;
            overflow: hidden;
        }

        .intro-container {
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            height: 100vh;
            color: white;
            font-family: 'Courier New', monospace;
            font-size: 28px;
            animation: fadein 1s ease-in;
        }

        .typing {
            border-right: 2px solid white;
            white-space: nowrap;
            overflow: hidden;
            animation: typing 3s steps(40, end), blink .75s step-end infinite;
        }

        .by-text {
            margin-top: 20px;
            opacity: 0;
            animation: fadeInText 2s ease-in forwards;
            animation-delay: 3.2s;
        }

        @keyframes typing {
            from { width: 0 }
            to { width: 100% }
        }

        @keyframes blink {
            from, to { border-color: transparent }
            50% { border-color: white; }
        }

        @keyframes fadeInText {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        @keyframes fadein {
            from { opacity: 0 }
            to { opacity: 1 }
        }
        </style>

        <div class="intro-container">
            <div class="typing">Presenting you... dalTadka — The Ultimate Photo Finder</div>
            <div class="by-text">by Shreyas</div>
        </div>
    """, unsafe_allow_html=True)

    time.sleep(4.5)
    st.session_state.intro_shown = True
    st.rerun()

# ======================
# 🎯 Your Actual Homepage
# ======================
st.set_page_config(page_title="dalTadka", layout="centered")
st.title("Welcome to dalTadka 👋")
st.subheader("Find your face in any photo — even in crowds, blurs, or partial views.")


# Setup
st.set_page_config("dalTadka – Find Your Photos", layout="wide")
os.makedirs("uploads", exist_ok=True)
create_tables()
face_engine = FaceEngine()

# Navigation menu
menu = st.sidebar.radio("Menu", ["Home", "Find Me", "Photographer Upload", "My Uploads"])

# ---------- HOME ----------
if menu == "Home":
    st.title("📸 dalTadka – Discover Yourself in Photos")
    st.write("Browse recent public photos uploaded by photographers.")

    conn = connect_db()
    c = conn.cursor()
    c.execute("SELECT cloudinary_url, photographer_email, timestamp FROM photos ORDER BY timestamp DESC")
    rows = c.fetchall()
    conn.close()

    if not rows:
        st.info("No photos yet.")
    else:
        cols = st.columns(4)
        for i, (url, email, ts) in enumerate(rows):
            with cols[i % 4]:
                if url:
                    st.image(url, caption=f"{email}\n📅 {ts.split('T')[0]}", use_container_width=True)
                else:
                    st.warning("⚠️ Image URL missing for this photo.")

# ---------- FIND ME ----------
elif menu == "Find Me":
    st.title("🧃 Upload Your Selfie to Explore Matching Photos")
    selfie_file = st.file_uploader("Upload a clear selfie (frontal preferred)", type=["jpg", "jpeg", "png"])

    if selfie_file:
        selfie_path = os.path.join("uploads", f"selfie_{uuid.uuid4()}.jpg")
        with open(selfie_path, "wb") as f:
            f.write(selfie_file.read())
        st.image(selfie_path, caption="Uploaded Selfie", width=200)

        with st.spinner("🔍 Searching all photos for face matches..."):
            embeddings = face_engine.get_face_embeddings(selfie_path)
            if not embeddings:
                st.warning("⚠️ No face detected in selfie. Try another image.")
                st.stop()
            query_embedding = embeddings[0]
            st.write(f"🧠 Selfie embedding length: {len(query_embedding)}")
            matched_results = find_matches(query_embedding, threshold=0.4)
            if not matched_results:
                st.info("😕 No matching photos found.")
            else:
                st.success(f"✅ Found {len(matched_results)} matching photo(s)")
                cols = st.columns(4)
                for i, match in enumerate(matched_results):
                    with cols[i % 4]:
                        st.image(match["url"], caption=f"Score: {match['score']}", use_container_width=True)

# ---------- PHOTOGRAPHER UPLOAD ----------
elif menu == "Photographer Upload":
    st.title("📄 Photographer Upload")
    st.warning("⚠️ This feature is currently disabled.")
    st.info("Images are now uploaded directly via a separate script to Cloudinary.")

# ---------- MY UPLOADS ----------
elif menu == "My Uploads":
    st.title("📄 My Uploads")
    st.warning("⚠️ This feature is currently disabled.")
    st.info("Images are now uploaded directly via a separate script to Cloudinary.")
