import streamlit as st
import googleapiclient.discovery
import re
from youtube_transcript_api import YouTubeTranscriptApi

# YouTube Data API 키 설정
API_KEY = st.secrets["youtube_api_key"]  # Streamlit의 secrets에서 API 키를 가져옵니다.

def extract_video_id(url: str) -> str:
    pattern = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com|youtu\.be)\/(?:watch\?v=)?(.{11})'
    match = re.match(pattern, url)
    return match.group(1) if match else None

def get_video_info(video_id: str) -> tuple:
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=API_KEY)
    request = youtube.videos().list(
        part="snippet",
        id=video_id
    )
    response = request.execute()
    if response["items"]:
        snippet = response["items"][0]["snippet"]
        return snippet["title"], snippet["description"]
    return "", ""

def fetch_transcript(video_id: str) -> str:
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['ko', 'en'])
        return ' '.join(entry['text'] for entry in transcript)
    except Exception as e:
        st.warning(f"자막 추출 실패: {str(e)}")
        return None

st.title("YouTube 자막 추출기")

url = st.text_input("YouTube URL을 입력하세요")

if st.button("자막 가져오기"):
    if url:
        video_id = extract_video_id(url)
        if video_id:
            try:
                title, description = get_video_info(video_id)
                st.subheader(f"비디오 제목: {title}")
                
                transcript = fetch_transcript(video_id)
                
                if transcript:
                    st.text_area("추출된 자막", transcript, height=300)
                    st.download_button(
                        label="자막 다운로드",
                        data=transcript,
                        file_name=f"{title}_transcript.txt",
                        mime="text/plain"
                    )
                else:
                    st.error("자막을 추출할 수 없습니다. 이 비디오에 자막이 없거나 접근이 제한되어 있을 수 있습니다.")
            except Exception as e:
                st.error(f"오류 발생: {str(e)}")
        else:
            st.error("올바른 YouTube URL을 입력해주세요.")
    else:
        st.warning("URL을 입력해주세요.")
