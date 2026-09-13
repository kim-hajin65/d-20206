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


# [3. 영화 선택 및 상위 영화 추출]
# 각 영화의 최대 누적관객수를 구해서 내림차순 정렬
movie_rank = (
    df.groupby("영화명")["누적관객수"]
    .max()
    .reset_index()
    .sort_values(by="누적관객수", ascending=False)
)
movie_list = movie_rank["영화명"].tolist()

# 단일 영화 분석용 드롭다운 선택 상자 (1, 2번 그래프용)
selected_movie = st.selectbox("분석할 영화를 선택하세요:", movie_list)

# 사용자가 선택한 개별 영화 데이터 필터링
filtered_df = df[df["영화명"] == selected_movie]


# --- Section 1: 개별 영화 일별 관객수 추이 (선 그래프) ---
st.header("1. 영화별 일별 관객수 변화 추이 (선 그래프)")

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

# 그래프 설명란
st.caption(
    f"💡 **이 그래프로 알 수 있는 것:** '{selected_movie}'의 상영 기간 동안 일별 관객수가 가장 많았던 날(최고 흥행 시점)과 관객수 감소 추세를 파악할 수 있습니다."
)

st.divider()  # 구분선


# --- Section 2: 개별 영화 누적 관객수 추이 (영역 차트) ---
st.header("2. 영화별 누적 관객수 증가 추이 (영역 차트)")

fig2 = px.area(
    filtered_df,
    x="기준일자",
    y="누적관객수",
    title=f"'{selected_movie}'의 누적 관객수 성취 추이",
    labels={"기준일자": "날짜", "누적관객수": "누적 관객수(명)"},
)

# Plotly 그래프 Streamlit에 출력
st.plotly_chart(fig2, use_container_width=True)

# 그래프 설명란
st.caption(
    f"💡 **이 그래프로 알 수 있는 것:** '{selected_movie}'의 누적 관객수가 시간에 따라 어떻게 가파르게 혹은 완만하게 증가하는지 전체적인 흥행 가속도를 한눈에 확인할 수 있습니다."
)

st.divider()  # 구분선


# --- Section 3: 조건 만족 TOP 5 영화 비교 (다중 선 그래프) ---
st.header("3. 장기 흥행 TOP 5 영화 비교 (다중 선 그래프)")

# 1) 영화별 TOP 10 차트 진입 일수(데이터에 등장한 횟수) 계산
movie_days = df.groupby("영화명").size().reset_index(name="등장일수")

# 2) 20일 이상 등장한 영화 목록만 필터링
long_running_movies = movie_days[movie_days["등장일수"] >= 20]["영화명"]

# 3) 조건에 부합하는 영화들 중 누적관객수가 가장 높은 상위 5개 영화 선택
filtered_rank = movie_rank[movie_rank["영화명"].isin(long_running_movies)]
top5_long_running = filtered_rank.head(5)["영화명"].tolist()

# TOP 5 영화 데이터 추출
top5_df = df[df["영화명"].isin(top5_long_running)]

# [다중 선 그래프 그리기]
fig3 = px.line(
    top5_df,
    x="기준일자",
    y="누적관객수",
    color="영화명",  # 영화별 구분 색상 및 범례 적용
    title="TOP 10 진입 20일 이상 영화 중 누적관객수 TOP 5 성장 추이",
    labels={"기준일자": "날짜", "누적관객수": "누적 관객수(명)", "영화명": "영화 제목"},
)

# Plotly 그래프 Streamlit에 출력
st.plotly_chart(fig3, use_container_width=True)

# 그래프 설명란
st.caption(
    f"💡 **이 그래프로 알 수 있는 것:** 박스오피스 TOP 10에 20일 이상 상주하며 장기 흥행한 주요 5개 영화({', '.join(top5_long_running)})의 관객수 누적 페이스와 최종 성과를 비교할 수 있습니다."
)
