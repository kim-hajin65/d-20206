import pandas as pd
import plotly.express as px
import streamlit as st

# 페이지 기본 설정
st.set_page_config(page_title="영화 박스오피스 분석", layout="wide")

# App 제목
st.title("🎬 영화 박스오피스 데이터 분석 앱")


# [1. 데이터 불러오기 및 캐싱]
# @st.cache_data 데코레이터를 사용하여 매번 파일에서 데이터를 새로 불러오지 않고 저장(캐시)해 둔 것을 사용합니다.
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/keep-growing-park/data-science/refs/heads/main/dataset/kobis_1year_boxoffice.csv"
    data = pd.read_csv(url)

    # [2. 데이터 전처리]
    # 결측치가 하나라도 포함된 행은 삭제
    data = data.dropna()

    # '기준일자' 컬럼을 datetime(날짜) 형식으로 변환
    data["기준일자"] = pd.to_datetime(data["기준일자"])

    # 기준일자 오름차순으로 정렬
    data = data.sort_values(by="기준일자", ascending=True)

    return data


# 데이터 로드 실행
df = load_data()


# [3. 영화 선택 기능]
# 중복 없는 영화 목록 추출 및 누적관객수 내림차순 정렬
movie_rank = (
    df.groupby("영화명")["누적관객수"]
    .max()
    .reset_index()
    .sort_values(by="누적관객수", ascending=False)
)
movie_list = movie_rank["영화명"].tolist()

# 사이드바 또는 상단에서 영화를 고를 수 있도록 수선 (모든 그래프에 일괄 적용)
selected_movie = st.selectbox("분석할 영화를 선택하세요:", movie_list)

# 사용자가 선택한 영화 데이터만 필터링
filtered_df = df[df["영화명"] == selected_movie]


# --- Section 1: 영화별 일별 관객수 추이 (선 그래프) ---
st.header("1. 영화별 일별 관객수 변화 추이 (선 그래프)")

# [4. Plotly 선 그래프 그리기]
fig1 = px.line(
    filtered_df,
    x="기준일자",
    y="해당일관객수",
    title=f"'{selected_movie}'의 일별 관객수 변화",
    markers=True,  # 데이터 지점에 점 표시
    labels={"기준일자": "날짜", "해당일관객수": "해당일 관객수(명)"},
)

# Plotly 그래프 Streamlit에 출력
st.plotly_chart(fig1, use_container_width=True)

# [5. 그래프 설명란]
st.caption(
    f"💡 **이 그래프로 알 수 있는 것:** '{selected_movie}'의 상영 기간 동안 일별 관객수가 가장 많았던 날(최고 흥행 시점)과 관객수 감소 추세를 파악할 수 있습니다."
)

st.divider()  # 구분선


# --- Section 2: 영화별 누적 관객수 추이 (영역 차트) ---
st.header("2. 영화별 누적 관객수 증가 추이 (영역 차트)")

# [영역 차트 그리기]
# px.area 함수를 사용하여 기준일자별 누적관객수를 영역차트로 표현합니다.
fig2 = px.area(
    filtered_df,
    x="기준일자",
    y="누적관객수",
    title=f"'{selected_movie}'의 누적 관객수 성취 추이",
    labels={"기준일자": "날짜", "누적관객수": "누적 관객수(명)"},
)

# Plotly 그래프 Streamlit에 출력
st.plotly_chart(fig2, use_container_width=True)

# [그래프 설명란]
st.caption(
    f"💡 **이 그래프로 알 수 있는 것:** '{selected_movie}'의 누적 관객수가 시간에 따라 어떻게 가파르게 혹은 완만하게 증가하는지 전체적인 흥행 가속도를 한눈에 확인할 수 있습니다."
)
