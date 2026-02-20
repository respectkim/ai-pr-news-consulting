import streamlit as st
if 'GEMINI_API_KEY' in st.secrets:
    api_key = st.secrets['GEMINI_API_KEY']

# 1. 라이브러리 사용
from google import genai

# 2. 요청 사용자 객체 생성
client = genai.Client(api_key=api_key)

#-------------------------네이버 뉴스 검색 연결------------
import requests
from datetime import datetime

def search_naver_news(query: str):
    """
    오늘 하루 동안 배포된 뉴스 기사의 개수를 필터링하여 반환합니다.
    """
    url = 'https://openapi.naver.com/v1/search/news.json'
    headers = {
        'X-Naver-Client-Id': st.secrets['CLIENT_ID'],
        'X-Naver-Client-Secret': st.secrets['CLIENT_SECRET']
    }
    
    # 최신순(date)으로 최대 100개까지 가져옴
    params = {"query": query, "display": 100, "sort": "date"}
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        items = response.json().get('items', [])
        today_str = datetime.now().strftime("%d %b %Y") # 예: 20 Feb 2026
        
        # 오늘 날짜와 일치하는 기사만 필터링
        today_items = [
            item for item in items 
            if today_str in item['pubDate']
        ]
        
        return {
            "today_count": len(today_items),
            "is_more_than_100": len(today_items) >= 100,
            "news_titles": [item['title'].replace('<b>', '').replace('</b>', '') for item in today_items[:3]]
        }
    return {"error": "API 호출 실패"}



# 날짜 조정 함수
def get_today():
    '''이 함수는 날짜 시점에 대한 답변에 사용됨'''
    now = datetime.datetime.now()
    return {'location':'korea seoul', 'year':now.year, 'month':now.month, 'day':now.day}


# 응답제어를 위한 하이퍼 파라미터
from google.genai import types
config = types.GenerateContentConfig(
    max_output_tokens=1000,
    response_mime_type='text/plain',
    temperature=0.2,
    system_instruction=
    '''
    넌 30년차 베테랑 PR 컨설턴트야. 
    사용자가 키워드를 입력하면 'search_naver_news' 도구를 사용해 뉴스 총량을 확인해.
    반드시 다음 형식을 지켜서 답변해: 
    [답변 규칙]
    1. 반드시 '오늘(금일)' 배포된 뉴스 개수만 언급할 것.
    2. 개수가 100개 이상이면 "오늘 하루에만 100건 이상의 기사가 쏟아졌습니다"라고 강조할 것.
    3. 결과는 반드시 다음과 같은 표(Table) 또는 리스트 형식으로 출력할 것. 
    4. 분석 결과에 대해 'PR적 위기' 또는 '기회'인지 분석한 뒤 한 줄 평을 남길 것.
    ''',
    tools=[search_naver_news ]
)


def get_response(question):
    response = client._models.generate_content(
        model= 'gemini-2.5-flash-lite',
        contents = question,
        config= config
    )
    return response.text




#---------------------------------ui 부분------------------
# 3. 채팅화면 ui
# 1) 페이지 기본 서정 - 브라우저 탭 영역
st.set_page_config(
    page_title = '뉴스 배포 현황 봇',
    page_icon= './logo/logo_news.png'
)

# 2) header 영역 (레이아웃: 이미지 + 제목영역 가로 배치)
col1, col2 = st.columns([1.5, 4.5])
with col1:
    st.image('./logo/logo_news.png', width=250)

with col2:
    st.markdown(
        '''
        <h1 'margin-bottom:0;'>뉴스 현황</h1>
        <p>이 챗봇은 검색 결과의 금일 뉴스 총 배포량을 알려주는 봇입니다.</p>
        ''',
        unsafe_allow_html=True
    )
    
#구분선
st.markdown('---')

#3) 채팅 ui 구현
#3-1. messages라는 이름의 변수가 session_state에 존재하는지 확인 후 없으면 첫 문자 지정
if 'messages' not in st.session_state:
    st.session_state.messages = [
        {'role':'assistant', 'content':'보도 배포 현황이 궁금한 기업을 입력'}
    ]

#3-2. session_state에 저장된 'messages'의 메시지를 채팅 ui로 그려내기
for msg in st.session_state.messages:
    st.chat_message(msg['role']).write(msg['content'])

#3-3. 사용자 채팅 메시지를 입력받아 session_state에 저장하고 ui 갱신
question = st.chat_input('뉴스 배포현황이 궁금한 곳을 입력')
if question:
    question = question.replace('\n', '  \n')
    st.session_state.messages.append({'role':'user', 'content':question})
    st.chat_message('user').write(question)

    #응답 대기 영역 - 스피너 표출
    with st.spinner('AI가 응답하는 중'):
        response = get_response(question)
        st.session_state.messages.append({'role':'assistant', 'content':response})
        st.chat_message('assistant').write(response)