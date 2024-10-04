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
            st.write("Video info:", info.keys())  # 디버깅을 위해 info의 키들을 출력
            
            subtitle_text = ""
            
            if 'subtitles' in info:
                st.write("Available subtitles:", info['subtitles'].keys())
                for lang in ['ko', 'en']:
                    if lang in info['subtitles']:
                        subtitle_data = info['subtitles'][lang]
                        st.write(f"{lang} subtitle data:", subtitle_data)
                        if isinstance(subtitle_data, list) and len(subtitle_data) > 0:
                            if 'data' in subtitle_data[0]:
                                subtitle_text = subtitle_data[0]['data']
                            elif 'url' in subtitle_data[0]:
                                st.write(f"Subtitle URL found for {lang}")
                                # URL에서 자막을 가져오는 로직 필요
                        break
            
            if not subtitle_text and 'automatic_captions' in info:
                st.write("Available automatic captions:", info['automatic_captions'].keys())
                for lang in ['ko', 'en']:
                    if lang in info['automatic_captions']:
                        auto_subtitle_data = info['automatic_captions'][lang]
                        st.write(f"{lang} automatic subtitle data:", auto_subtitle_data)
                        if isinstance(auto_subtitle_data, list) and len(auto_subtitle_data) > 0:
                            if 'data' in auto_subtitle_data[0]:
                                subtitle_text = auto_subtitle_data[0]['data']
                            elif 'url' in auto_subtitle_data[0]:
                                st.write(f"Automatic subtitle URL found for {lang}")
                                # URL에서 자막을 가져오는 로직 필요
                        break
            
            if subtitle_text:
                return subtitle_text
            else:
                return "No subtitles found or unable to extract subtitle data."
        
        except Exception as e:
            st.error(f"Error occurred: {str(e)}")
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
