
import streamlit as st

st.set_page_config(page_title="RealCheck UI Test", layout="wide")

st.title("RealCheck AI - UI Test")
st.success("Streamlit is working!")

option = st.radio(
    "Choose an option",
    ["Image Detection", "Video Detection", "Multimodal Fusion", "History"],
)

st.write("Selected option:", option)
