import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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

st.divider()  # 구분선


# --- Section 4: 전체 박스오피스 총 관객수 및 7일 이동평균선 ---
st.header("4. 전체 박스오피스 총 관객수 및 7일 이동평균선")

# 1) 기준일자별 TOP 10 영화 전체의 해당일관객수 합계 산출
daily_total = df.groupby("기준일자")["해당일관객수"].sum().reset_index()

# 2) 7일 이동평균(Rolling Average) 계산
daily_total["7일_이동평균"] = (
    daily_total["해당일관객수"].rolling(window=7).mean()
)

# 3) Plotly graph_objects를 이용해 원본 선과 이동평균선 함께 그리기
fig4 = go.Figure()

# 원본 일별 총관객수 (연한 색상)
fig4.add_trace(
    go.Scatter(
        x=daily_total["기준일자"],
        y=daily_total["해당일관객수"],
        mode="lines",
        name="일별 총 관객수",
        line=dict(color="rgba(150, 180, 230, 0.5)", width=1.5),  # 연하고 얇은 선
    )
)

# 7일 이동평균선 (진한 색상)
fig4.add_trace(
    go.Scatter(
        x=daily_total["기준일자"],
        y=daily_total["7일_이동평균"],
        mode="lines",
        name="7일 이동평균",
        line=dict(color="#1f77b4", width=3),  # 진하고 두꺼운 선
    )
)

# 그래프 레이아웃 설정
fig4.update_layout(
    title="기준일자별 TOP 10 총 관객수 및 7일 이동평균 추이",
    xaxis_title="날짜",
    yaxis_title="총 관객수(명)",
    hovermode="x unified",
)

# Plotly 그래프 Streamlit에 출력
st.plotly_chart(fig4, use_container_width=True)

# 그래프 설명란
st.caption(
    "💡 **이 그래프로 알 수 있는 것:** 주말과 평일 사이의 격렬한 관객수 변동(노이즈)을 평활화하여, 전체 극장가의 계절적 성수기와 비수기 흐름 및 시장 전체의 관객수 증감 트렌드를 명확하게 파악할 수 있습니다."
)

st.divider()  # 구분선


# --- Section 5: 월별 전체 관객수 합계 (막대그래프) ---
st.header("5. 월별 전체 관객수 합계 (막대그래프)")

# 1) 기준일자에서 월 정보(YYYY-MM) 추출
daily_total["연월"] = daily_total["기준일자"].dt.to_period("M").astype(str)

# 2) 월(연월) 단위로 그룹화하여 해당일관객수 총합 집계
monthly_total = (
    daily_total.groupby("연월")["해당일관객수"].sum().reset_index()
)

# 3) Plotly 막대그래프 생성
fig5 = px.bar(
    monthly_total,
    x="연월",
    y="해당일관객수",
    title="월별 극장가 총 관객수 합계",
    text_auto=".2s",  # 막대 상단에 간략한 숫자 표기 (예: 1.2M)
    labels={"연월": "년-월", "해당일관객수": "월별 총 관객수(명)"},
)

# 막대그래프 색상 및 레이아웃 조정
fig5.update_traces(
    marker_color="#2b5c8f", textposition="outside"
)  # 막대 색상 지정 및 숫자 위치 설정
fig5.update_layout(xaxis_type="category")  # 월 단위 범주형 축 적용

# Plotly 그래프 Streamlit에 출력
st.plotly_chart(fig5, use_container_width=True)

# 그래프 설명란
st.caption(
    "💡 **이 그래프로 알 수 있는 것:** 1년 동안 연월별 전체 극장 이용객의 누적 규모를 비교하여, 어느 달이 영화 시장의 최대 성수기였는지 혹은 비수기였는지 한눈에 파악할 수 있습니다."
)

st.divider()  # 구분선


# --- Section 6: 월×요일별 관객수 분포 (캘린더 히트맵) ---
st.header("6. 월별/요일별 관객수 분포 (히트맵)")

# 1) 히트맵 전용 컬럼 생성
heatmap_df = daily_total.copy()

# yyyy-mm-dd 날짜 문자열 컬럼 생성 (마우스 호버용)
heatmap_df["날짜문자열"] = heatmap_df["기준일자"].dt.strftime("%Y-%m-%d")

# 요일 이름 추출 및 월요일~일요일 순서 정렬을 위한 범주 설정
days_order = [
    "월요일",
    "화요일",
    "수요일",
    "목요일",
    "금요일",
    "토요일",
    "일요일",
]
heatmap_df["요일"] = heatmap_df["기준일자"].dt.day_name()

# 한글 요일명 매핑
day_map = {
    "Monday": "월요일",
    "Tuesday": "화요일",
    "Wednesday": "수요일",
    "Thursday": "목요일",
    "Friday": "금요일",
    "Saturday": "토요일",
    "Sunday": "일요일",
}
heatmap_df["요일"] = heatmap_df["요일"].map(day_map)

# 2) Plotly 히트맵 생성
fig6 = px.density_heatmap(
    heatmap_df,
    x="요일",
    y="연월",
    z="해당일관객수",
    category_orders={"요일": days_order},  # 요일 순서를 월요일~일요일로 고정
    color_continuous_scale="Viridis",  # 관객수가 많을수록 진하고 밝은 색상
    title="월별/요일별 박스오피스 전체 관객수 히트맵",
    labels={
        "요일": "요일",
        "연월": "년-월",
        "해당일관객수": "관객수(명)",
    },
    hover_data={"날짜문자열": True, "해당일관객수": ":,명"},  # 마우스 올릴 때 yyyy-mm-dd 표기
)

# 마우스 툴팁(Hover) 레이아웃 커스텀
fig6.update_traces(
    hovertemplate="<b>날짜: %{customdata[0]}</b><br>요일: %{x}<br>월: %{y}<br>관객수: %{z:,.0f}명<extra></extra>"
)

fig6.update_layout(
    xaxis_title="요일",
    yaxis_title="년-월",
    coloraxis_colorbar=dict(title="관객수(명)"),
)

# Plotly 그래프 Streamlit에 출력
st.plotly_chart(fig6, use_container_width=True)

# 그래프 설명란
st.caption(
    "💡 **이 그래프로 알 수 있는 것:** 각 월별로 주말(토·일)과 평일(월~목) 간 관객수 격차의 정도를 확인하고, 연중 특정 공휴일이나 명절이 껴 있는 일자에 관객수가 비정상적으로 집중되었는지 한눈에 시각적으로 파악할 수 있습니다."
)
