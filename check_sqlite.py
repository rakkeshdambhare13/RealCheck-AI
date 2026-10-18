import sys
import sqlite3
import streamlit as st

st.title("RealCheck AI - SQLite Diagnostic")

st.write("Python executable:", sys.executable)
st.write("Python version:", sys.version)
st.write("SQLite module:", sqlite3.__file__)
st.success("SQLite imported successfully!")