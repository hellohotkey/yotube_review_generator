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

def fetch_transcript_with_api(video_id: str) -> str:
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return ' '.join(entry['text'] for entry in transcript)
    except Exception as e:
        st.warning(f"YouTube Transcript API로 자막 추출 실패: {str(e)}")
        return None

def fetch_transcript_with_ytdlp(url: str) -> str:
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
                        subtitle = info['subtitles'][lang][0]['data']
                        return ' '.join(line for line in subtitle.splitlines() if line and not line[0].isdigit())
            if 'automatic_captions' in info:
                for lang in ['ko', 'en']:
                    if lang in info['automatic_captions']:
                        subtitle = info['automatic_captions'][lang][0]['data']
                        return ' '.join(line for line in subtitle.splitlines() if line and not line[0].isdigit())
        except Exception as e:
            st.error(f"yt-dlp로 자막 추출 실패: {str(e)}")
    return None

st.title("YouTube 자막 추출기")

url = st.text_input("YouTube URL을 입력하세요")

if st.button("자막 가져오기"):
    if url:
        video_id = extract_video_id(url)
        if video_id:
            try:
                title, description = get_video_info(url)
                st.subheader(f"비디오 제목: {title}")
                
                transcript = fetch_transcript_with_api(video_id)
                if not transcript:
                    st.info("YouTube Transcript API 실패. yt-dlp로 시도 중...")
                    transcript = fetch_transcript_with_ytdlp(url)
                
                if transcript:
                    st.text_area("추출된 자막", transcript, height=300)
                    st.download_button(
                        label="자막 다운로드",
                        data=transcript,
                        file_name=f"{title}_transcript.txt",
                        mime="text/plain"
                    )
                else:
                    st.error("자막을 추출할 수 없습니다.")
            except Exception as e:
                st.error(f"오류 발생: {str(e)}")
        else:
            st.error("올바른 YouTube URL을 입력해주세요.")
    else:
        st.warning("URL을 입력해주세요.")
