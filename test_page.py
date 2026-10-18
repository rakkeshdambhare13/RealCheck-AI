
import streamlit as st

st.set_page_config(page_title="RealCheck AI Test", layout="wide")

st.title("RealCheck AI")
st.success("Streamlit is rendering correctly!")
st.write("If you can see this message, the basic page works.")

uploaded_file = st.file_uploader(
    "Upload an image to test",
    type=["jpg", "jpeg", "png"]
)

if uploaded_file:
    st.image(uploaded_file, caption="Test image", width=400)
