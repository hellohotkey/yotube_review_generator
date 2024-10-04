import streamlit as st
from yt_dlp import YoutubeDL
import re

def extract_video_id(url: str) -> str:
    pattern = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com|youtu\.be)\/(?:watch\?v=)?(.{11})'
    match = re.match(pattern, url)
    return match.group(1) if match else None

def get_subtitle(url: str) -> str:
    ydl_opts = {
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['ko', 'en'],
        'skip_download': True,
        'outtmpl': '%(id)s.%(ext)s'
    }
    
    with YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            if 'subtitles' in info:
                for lang in ['ko', 'en']:
                    if lang in info['subtitles']:
                        return info['subtitles'][lang][0]['data']
            if 'automatic_captions' in info:
                for lang in ['ko', 'en']:
                    if lang in info['automatic_captions']:
                        return info['automatic_captions'][lang][0]['data']
            return "No subtitles found."
        except Exception as e:
            return f"Error: {str(e)}"

st.title("YouTube 자막 추출기")

url = st.text_input("YouTube URL을 입력하세요")

if st.button("자막 가져오기"):
    if url:
        video_id = extract_video_id(url)
        if video_id:
            subtitle = get_subtitle(url)
            st.text_area("추출된 자막", subtitle, height=300)
        else:
            st.error("올바른 YouTube URL을 입력해주세요.")
    else:
        st.warning("URL을 입력해주세요.")
