import pandas as pd
import plotly.express as px
import streamlit as st

# 페이지 기본 설정
st.set_page_config(
    page_title="영화 데이터 - 분포와 관계",
    page_icon="🎬",
    layout="wide",
)

# App 제목
st.title("🎬 영화 데이터 - 분포와 관계")


# 데이터 로드 및 전처리
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_movies.csv"
    df = pd.read_csv(url)

    # 장르 열 전처리 (세로막대 기호 '|' 기준 첫 번째 장르만 추출)
    if "genre" in df.columns:
        df["genre"] = df["genre"].astype(str).apply(lambda x: x.split("|")[0])

    return df


df = load_data()

# -------------------------------------------------------------------
# 그래프 1: 장르별 영화 편수 (도넛 그래프)
# -------------------------------------------------------------------
st.subheader("1. 장르별 영화 편수 분포")

# 장르별 영화 편수 집계
genre_counts = df["genre"].value_counts().reset_index()
genre_counts.columns = ["genre", "count"]

# Plotly 도넛 그래프 생성
fig_donut = px.pie(
    genre_counts,
    names="genre",
    values="count",
    hole=0.4,
    title="장르별 영화 비율",
)

# 마우스 오버 시 편수(value)와 비율(percent) 표시 설정
fig_donut.update_traces(
    hoverinfo="label+value+percent", textinfo="percent+label"
)

# Streamlit에 그래프 출력
st.plotly_chart(fig_donut, use_container_width=True)

# 구분선 및 해석 구역
st.divider()
st.markdown(
    "💡 **이 그래프로 알 수 있는 것:** 박스오피스 상위권 영화들 중 가장 큰 비중을 차지하는 주요 장르 분포와 특정 장르의 쏠림 현상을 한눈에 파악할 수 있습니다."
)
