import streamlit as st
import cloudinary

cloudinary.config(
    cloud_name=st.secrets["cloudinary_cloud_name"],
    api_key=st.secrets["cloudinary_api_key"],
    api_secret=st.secrets["cloudinary_api_secret"]
    secure=True

)
