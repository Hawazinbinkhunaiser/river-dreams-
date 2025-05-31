import streamlit as st
import openai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import requests

# ---- Config ----
st.set_page_config(page_title="Dream-to-Song Composer", layout="centered")
st.title("🎵 Dream-to-Song Composer")
st.markdown("Turn a collection of dreams into a song using GPT and Suno!")

# ---- API Keys (Streamlit secrets) ----
openai.api_key = st.secrets["OPENAI_API_KEY"]
SUNO_API_KEY = st.secrets["SUNO_API_KEY"]

# ---- Google Sheets Reader ----
def fetch_dreams(sheet_url):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["GCP_SERVICE_ACCOUNT"], scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_url(sheet_url)
    worksheet = sheet.get_worksheet(0)
    records = worksheet.get_all_records()
    dreams = [row['dream'] for row in records if row.get('dream')]
    return dreams

# ---- OpenAI: Combine dreams into lyrics ----
def generate_combined_lyrics(dreams):
    combined_text = "\n".join(f"- {dream}" for dream in dreams)
    prompt = f"""
You are a poetic songwriter. Write a song that weaves together the following dreams into a beautiful, emotional piece with verses and chorus.

Dreams:
{combined_text}

Write the lyrics in song format.
"""
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9
    )
    return response.choices[0].message.content.strip()

# ---- Call Suno API ----
def send_to_suno(lyrics):
    api_url = "https://api.suno.ai/generate"  # Replace with actual Suno endpoint
    headers = {
        "Authorization": f"Bearer {SUNO_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "lyrics": lyrics,
        "style": "pop"
    }
    response = requests.post(api_url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json().get("song_url", "Song URL not found.")
    else:
        return f"Error from Suno: {response.text}"

# ---- UI ----
sheet_url = st.text_input("Paste your public Google Sheet URL (must have a 'dream' column):")

if st.button("Generate Song") and sheet_url:
    with st.spinner("Fetching dreams and composing your song..."):
        try:
            dreams = fetch_dreams(sheet_url)
            if not dreams:
                st.warning("No dreams found in the sheet.")
            else:
                lyrics = generate_combined_lyrics(dreams)
                st.subheader("🎤 Lyrics")
                st.text_area("Generated Song Lyrics", lyrics, height=300)

                # Send to Suno
                st.subheader("🎧 Your Song")
                song_url = send_to_suno(lyrics)
                st.markdown(f"[Click to listen to your AI-generated song]({song_url})")
        except Exception as e:
            st.error(f"Error: {e}")
