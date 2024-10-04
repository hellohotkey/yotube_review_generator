import streamlit as st
import os
from dotenv import load_dotenv
import openai
import re
import pyperclip
import requests
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, VideoUnavailable

# Load environment variables
load_dotenv()

# Set up API keys
openai.api_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")
youtube_api_key = os.getenv("YOUTUBE_API_KEY") or st.secrets.get("YOUTUBE_API_KEY")

if not openai.api_key:
    st.error("OpenAI API 키가 설정되지 않았습니다.")
    st.stop()

if not youtube_api_key:
    st.error("YouTube API 키가 설정되지 않았습니다.")
    st.stop()

# Set page config for full screen
st.set_page_config(layout="wide")

# Custom CSS for better UI
st.markdown("""
<style>
    .stApp { max-width: 100%; padding-top: 2rem; }
    .stButton>button { width: 100%; background-color: #ff4b4b !important; color: white; }
    .stButton>button:hover { background-color: #ff7171 !important; }
    .stTextInput>div>div>input { font-size: 1.2rem; }
    .stTextArea>div>textarea { font-size: 1.1rem; }
    .divider { margin: 1rem 0; border-top: 1px solid #e0e0e0; }
</style>
""", unsafe_allow_html=True)

def extract_video_id(url: str) -> str:
    patterns = [
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?v=([^&]+)',
        r'(?:https?:\/\/)?(?:www\.)?youtu\.be\/([^?]+)',
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/embed\/([^?]+)',
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/v\/([^?]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None

def check_video_availability(video_id: str) -> bool:
    url = f"https://www.googleapis.com/youtube/v3/videos?id={video_id}&key={youtube_api_key}&part=status"
    response = requests.get(url)
    if response.status_code == 200:
        items = response.json().get('items', [])
        if items and items[0]['status']['privacyStatus'] == 'public':
            return True
    return False

def fetch_transcript(video_id: str) -> str:
    # Attempt to fetch transcript using youtube-transcript-api
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['ko', 'en'])
        return transcript_to_text(transcript)
    except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable):
        st.warning("유튜브 트랜스크립트 API로 자막을 가져오지 못했습니다. YouTube Data API로 시도합니다...")
    except Exception as e:
        st.warning(f"유튜브 트랜스크립트 API 오류: {str(e)}. YouTube Data API로 시도합니다...")

    # Fallback to YouTube Data API if youtube-transcript-api fails
    url = f"https://www.googleapis.com/youtube/v3/captions?videoId={video_id}&key={youtube_api_key}&part=snippet"
    response = requests.get(url)
    if response.status_code == 200:
        items = response.json().get('items', [])
        for item in items:
            if item['snippet']['language'] in ['ko', 'en']:
                caption_id = item['id']
                caption_url = f"https://www.googleapis.com/youtube/v3/captions/{caption_id}?key={youtube_api_key}&tfmt=srt"
                caption_response = requests.get(caption_url, headers={"Accept": "application/json"})
                if caption_response.status_code == 200:
                    return caption_response.text
    st.error("이 동영상의 자막을 가져올 수 없습니다.")
    return None

def transcript_to_text(transcript):
    return " ".join(item['text'] for item in transcript)

def generate_review(transcript, keywords, length_option):
    length_map = {
        "짧게 (100자)": 100,
        "보통 (200자)": 200,
        "길게 (300자)": 300
    }
    target_length = length_map[length_option]

    try:
        prompt = f"""YouTube 동영상 관람평을 작성해주세요. 다음 지침을 따라주세요:
        1. 영상을 실제로 본 것처럼 개인적인 느낌과 감상을 자유롭게 표현하세요.
        2. 인상 깊었던 점, 좋았던 점, 응원의 말 등을 포함해주세요.
        3. 다음 키워드를 자연스럽게 포함시켜주세요: {', '.join(keywords)}
        4. 일반 시청자의 눈높이에 맞춰 쉽고 친근한 언어로 작성해주세요.
        5. 적절한 이모티콘을 사용하여 글에 생동감을 더해주세요.
        6. 한글로 약 {target_length}자 내외로 작성해주세요.

        자막 내용: {transcript}
        """

        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 YouTube 동영상 시청자입니다."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500
        )
        return response.choices[0].message['content'], response['usage']
    except Exception as e:
        st.error(f"관람평 생성에 실패했습니다: {str(e)}")
        return None, None

def copy_to_clipboard(text):
    pyperclip.copy(text)
    st.success("관람평이 클립보드에 복사되었습니다!")

def calculate_cost(usage):
    input_cost_per_1m = 0.150
    output_cost_per_1m = 0.600

    input_tokens = usage['prompt_tokens']
    output_tokens = usage['completion_tokens']

    input_cost = (input_tokens / 1000000) * input_cost_per_1m
    output_cost = (output_tokens / 1000000) * output_cost_per_1m

    total_cost = input_cost + output_cost
    total_cost_krw = total_cost * 1300

    return total_cost_krw

def main():
    st.title("🎥 YouTube 동영상 관람평 작성기")

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        url = st.text_input("YouTube URL을 입력해주세요", help="YouTube 동영상의 전체 URL을 입력하세요.")
    
    with col2:
        keywords = st.text_input("키워드 (쉼표로 구분)", help="관람평에 포함하고 싶은 키워드를 쉼표로 구분하여 입력하세요.")
        keywords = [keyword.strip() for keyword in keywords.split(',') if keyword.strip()]

    with col3:
        length_option = st.selectbox("글 길이", ["짧게 (100자)", "보통 (200자)", "길게 (300자)"], index=1, help="생성될 관람평의 길이를 선택하세요.")

    if st.button("🔍 자막 가져오기", help="입력한 URL에서 자막을 가져옵니다."):
        if url:
            video_id = extract_video_id(url)
            if video_id:
                with st.spinner("자막을 가져오는 중입니다..."):
                    transcript = fetch_transcript(video_id)
                    if transcript:
                        st.session_state.transcript = transcript
                        st.success("자막을 성공적으로 불러왔습니다.")
            else:
                st.error("올바른 YouTube URL을 입력해주세요.")
        else:
            st.warning("YouTube URL을 입력해주세요.")

    if 'transcript' in st.session_state:
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("자막")
            edited_transcript = st.text_area("", st.session_state.transcript, height=300, help="자동으로 가져온 자막입니다. 필요한 경우 수정할 수 있습니다.")
        
            if st.button("✍️ 관람평 작성하기", help="입력한 자막과 키워드를 바탕으로 관람평을 생성합니다."):
                with st.spinner("관람평을 작성 중입니다..."):
                    review, usage = generate_review(edited_transcript, keywords, length_option)
                    if review and usage:
                        st.session_state.review = review
                        st.session_state.usage = usage

        with col2:
            if 'review' in st.session_state:
                st.subheader("관람평")
                st.text_area("", st.session_state.review, height=300)
                if st.button("📋 관람평 복사하기", help="생성된 관람평을 클립보드에 복사합니다."):
                    copy_to_clipboard(st.session_state.review)
                
                if 'usage' in st.session_state:
                    usage = st.session_state.usage
                    cost = calculate_cost(usage)
                    st.info(f"토큰 사용량: {usage['total_tokens']} (입력: {usage['prompt_tokens']}, 출력: {usage['completion_tokens']}) | 예상 비용: {cost:.2f}원")

if __name__ == "__main__":
    main()
