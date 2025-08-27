import streamlit as st
st.title("Company Policy Assistant")
user_query = st.text_input("Hello! How can I help you today?")
if st.button("Submit"):
    st.write("You asked:", user_query) # We will replace this later