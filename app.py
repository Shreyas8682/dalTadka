import os
import uuid
import streamlit as st
from datetime import datetime
from streamlit_oauth import OAuth2Component
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests
from auth_config import client_id, client_secret
from db.database import create_tables, connect_db, delete_all_user_photos
from face_engine.face_model import FaceEngine
import cloudinary_config
import cloudinary.uploader
from face_engine.matcher import find_matches


# Setup
st.set_page_config("dalTadka – Find Your Photos", layout="wide")
os.makedirs("uploads", exist_ok=True)
create_tables()
face_engine = FaceEngine()
redirect_uri = "https://daltadka.streamlit.app"

oauth = OAuth2Component(
    client_id=client_id,
    client_secret=client_secret,
    authorize_endpoint="https://accounts.google.com/o/oauth2/v2/auth",
    token_endpoint="https://oauth2.googleapis.com/token",
)

menu = st.sidebar.radio("Menu", ["Home", "Find Me", "Photographer Upload", "My Uploads"])
token = st.session_state.get("token")
user = st.session_state.get("user")

if (menu in ["Photographer Upload", "My Uploads"]) and not token:
    st.info("🔐 Please login with Google to continue.")
    token = oauth.authorize_button(
        name="Login with Google",
        redirect_uri=redirect_uri,
        scope="openid email profile",
        key="google_login"
    )
    if token:
        try:
            id_token_value = token.get("token", {}).get("id_token", "")
            idinfo = google_id_token.verify_oauth2_token(id_token_value, requests.Request(), client_id)
            st.session_state.token = token
            st.session_state.user = idinfo
            st.success(f"✅ Logged in as {idinfo['email']}")
            st.rerun()
        except Exception as e:
            st.error("❌ Login failed.")
            st.exception(e)
            st.stop()

if st.sidebar.button("🚪 Logout"):
    st.session_state.clear()
    st.rerun()

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
                if url:  # only show image if URL is valid
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
            matched_results = find_matches(query_embedding, threshold=0.6)

            if not matched_results:
                st.info("😕 No matching photos found.")
            else:
                st.success(f"✅ Found {len(matched_results)} matching photo(s)")

                cols = st.columns(4)
                for i, match in enumerate(matched_results):
                    with cols[i % 4]:
                        st.image(match["path"], caption=f"Score: {match['score']}", use_container_width=True)

# ---------- PHOTOGRAPHER UPLOAD ----------
elif menu == "Photographer Upload":
    st.title("📄 Photographer Upload")
    if not user:
        st.warning("🔐 Please login with Google first.")
        st.stop()

    email = user["email"]
    st.success(f"✅ Logged in as {email}")
    uploaded_files = st.file_uploader("Upload photos", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

    if st.button("Submit") and uploaded_files:
        conn = connect_db()
        c = conn.cursor()
        saved = 0
        total = len(uploaded_files)
        progress_bar = st.progress(0, text="Uploading...")

        try:
            for i, file in enumerate(uploaded_files):
                try:
                    # 1. Save locally
                    photo_id = str(uuid.uuid4())
                    filename = f"{photo_id}.jpg"
                    filepath = os.path.join("uploads", filename)
                    with open(filepath, "wb") as f:
                        f.write(file.read())

                    # 2. Upload to Cloudinary
                    cloud_res = cloudinary.uploader.upload(filepath)
                    cloud_url = cloud_res.get("secure_url")

                    # 3. Insert metadata into DB
                    timestamp = datetime.now().isoformat()
                    c.execute(
                        "INSERT INTO photos (image_id, local_path, cloudinary_url, photographer_email, timestamp) VALUES (?, ?, ?, ?, ?)",
                        (photo_id, filepath, cloud_url, email, timestamp)
                    )
                    photo_db_id = c.lastrowid

                    # 4. Get embeddings and insert
                    embeddings = face_engine.get_face_embeddings(filepath)
                    for emb in embeddings:
                        enc_str = ",".join(map(str, emb))
                        c.execute("INSERT INTO encodings (photo_id, encoding) VALUES (?, ?)", (photo_db_id, enc_str))

                    saved += 1
                    progress_bar.progress((i + 1) / total, text=f"Uploaded {i + 1}/{total}")
                except Exception as e:
                    st.error(f"❌ Failed to upload image {file.name}: {e}")

            conn.commit()
        finally:
            conn.close()
            progress_bar.empty()

        st.success(f"✅ Uploaded {saved}/{total} photo(s) successfully.")

# ---------- MY UPLOADS ----------
elif menu == "My Uploads":
    st.title("🗂️ Your Uploaded Photos")
    if not user:
        st.warning("🔐 Please login with Google first.")
        st.stop()

    email = user["email"]
    conn = connect_db()
    c = conn.cursor()
    c.execute("SELECT id, cloudinary_url, timestamp FROM photos WHERE photographer_email = ?", (email,))
    rows = c.fetchall()

    if st.button("🗑️ Delete All My Uploads"):
        delete_all_user_photos(email)  # Clean Cloudinary + DB
        st.success("✅ All your uploaded photos deleted.")
        st.rerun()

    conn.close()

    if not rows:
        st.info("You haven’t uploaded any photos yet.")
    else:
        cols = st.columns(4)
        for i, (_, url, ts) in enumerate(rows):
            with cols[i % 4]:
                st.image(url, caption=f"📅 {ts.split('T')[0]}", use_container_width=True)
