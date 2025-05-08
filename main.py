
import streamlit as st

st.title("AI Web Scraper")
url=st.text_input("Enter the URL to scrape:")


if st.button("Scrape"):
    st.write("Scraping the URL...")
