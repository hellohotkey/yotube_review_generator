import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from yt_dlp import YoutubeDL
import re

def extract_video_id(url: str) -> str:
    pattern = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com|youtu\.be)\/(?:watch\?v=)?(.{11})'
    match = re.match(pattern, url)
    return match.group(1) if match else None

def get_video_info(url: str) -> tuple:
    with YoutubeDL() as ydl:
        info = ydl.extract_info(url, download=False)
        return info.get('title', ''), info.get('description', '')

def fetch_transcript(video_id: str) -> str:
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return ' '.join(entry['text'] for entry in transcript)
    except Exception as e:
        return f"자막을 가져오는 데 실패했습니다: {str(e)}"

st.title("YouTube 자막 추출기")

url = st.text_input("YouTube URL을 입력하세요")

if st.button("자막 가져오기"):
    if url:
        video_id = extract_video_id(url)
        if video_id:
            try:
                title, description = get_video_info(url)
                st.subheader(f"비디오 제목: {title}")
                
                transcript = fetch_transcript(video_id)
                st.text_area("추출된 자막", transcript, height=300)
                
                st.download_button(
                    label="자막 다운로드",
                    data=transcript,
                    file_name=f"{title}_transcript.txt",
                    mime="text/plain"
                )
            except Exception as e:
                st.error(f"오류 발생: {str(e)}")
        else:
            st.error("올바른 YouTube URL을 입력해주세요.")
    else:
        st.warning("URL을 입력해주세요.")
