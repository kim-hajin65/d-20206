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

    # 장르 열 전처리 (str.split을 사용하여 첫 번째 장르만 추출)
    if "genre" in df.columns:
        df["genre"] = df["genre"].astype(str).str.split("|").str[0]

    # 계층형 차트(트리맵/선버스트)에서 중복 영화명으로 인한 오류 방지를 위해 고유 ID 생성
    if "movieCd" in df.columns and "movieNm" in df.columns:
        df["movie_unique"] = df["movieNm"] + " (" + df["movieCd"].astype(str) + ")"
    else:
        df["movie_unique"] = df["movieNm"]

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

# -------------------------------------------------------------------
# 그래프 2: 장르 및 영화별 총 관객 수 (트리맵)
# -------------------------------------------------------------------
st.subheader("2. 장르 및 영화별 총 관객 수 분포")

# Plotly 트리맵 생성 (고유 ID 사용, 표시 표시는 movieNm 지정)
fig_treemap = px.treemap(
    df,
    path=["genre", "movie_unique"],
    values="total_audi",
    title="장르 및 영화별 총 관객 수",
    hover_data={"total_audi": ":,d", "movieNm": True, "movie_unique": False},
)

# 마우스 오버 시 실제 영화명과 총 관객 수가 표시되도록 설정
fig_treemap.update_traces(
    hovertemplate="<b>%{customdata[1]}</b><br>총 관객 수: %{value:,}명<extra></extra>"
)

# Streamlit에 그래프 출력
st.plotly_chart(fig_treemap, use_container_width=True)

# 구분선 및 해석 구역
st.divider()
st.markdown(
    "💡 **이 그래프로 알 수 있는 것:** 특정 장르 내에서 어떤 영화가 흥행을 주도했는지 장르 전체 관객 대비 개별 영화의 흥행 기여도를 한눈에 비교할 수 있습니다."
)

# -------------------------------------------------------------------
# 그래프 3: 총 관객 수 분포 (히스토그램)
# -------------------------------------------------------------------
st.subheader("3. 총 관객 수 분포")

# Plotly 히스토그램 생성
fig_hist = px.histogram(
    df,
    x="total_audi",
    nbins=30,
    title="총 관객 수 히스토그램",
    labels={"total_audi": "총 관객 수"},
)

fig_hist.update_layout(
    xaxis_title="총 관객 수", yaxis_title="영화 수", bar_gap=0.1
)

st.plotly_chart(fig_hist, use_container_width=True)

# 최상위 관객 수 영화 추출 및 정보 생성
top_movie = df.loc[df["total_audi"].idxmax()]
top_title = top_movie["movieNm"]
top_audi = top_movie["total_audi"]

# 구분선 및 해석 구역
st.divider()
st.markdown(
    f"💡 **이 그래프로 알 수 있는 것:** 대부분의 영화가 **500만 명 이하** 구간에 집중되어 있는 롱테일 분포 양상을 보이며, 가장 많은 관객을 동원한 영화는 **{top_title}**({top_audi:,}명)입니다."
)

# -------------------------------------------------------------------
# 그래프 4: 개봉일 스크린 수 vs 총 관객 수 (산점도)
# -------------------------------------------------------------------
st.subheader("4. 개봉일 스크린 수와 총 관객 수의 관계")

# Plotly 산점도 생성 (x: 개봉일 스크린 수, y: 총 관객 수, 색상: 장르)
fig_scatter = px.scatter(
    df,
    x="first_scrn",
    y="total_audi",
    color="genre",
    hover_name="movieNm",
    title="개봉일 스크린 수 vs 총 관객 수",
    labels={
        "first_scrn": "개봉일 스크린 수",
        "total_audi": "총 관객 수",
        "genre": "장르",
    },
    hover_data={
        "first_scrn": ":,d",
        "total_audi": ":,d",
        "genre": False,
    },
)

fig_scatter.update_layout(
    xaxis_title="개봉일 스크린 수", yaxis_title="총 관객 수"
)

# Streamlit에 그래프 출력
st.plotly_chart(fig_scatter, use_container_width=True)

# 구분선 및 해석 구역
st.divider()
st.markdown(
    "💡 **이 그래프로 알 수 있는 것:** 초기 스크린 확보 수와 최종 총 관객 수 간의 양의 상관관계를 확인할 수 있으며, 초기 스크린 수가 적음에도 흥행에 성공한 아웃라이어 영화를 탐색할 수 있습니다."
)

# -------------------------------------------------------------------
# 그래프 5: 주요 장르별 총 관객 수 분포 (박스플롯)
# -------------------------------------------------------------------
st.subheader("5. 주요 장르별 총 관객 수 분포")

# 영화 수가 10편 이상인 장르만 필터링
genre_counts_series = df["genre"].value_counts()
top_genres = genre_counts_series[genre_counts_series >= 10].index
df_filtered = df[df["genre"].isin(top_genres)]

# Plotly 박스플롯 생성
fig_box = px.box(
    df_filtered,
    x="genre",
    y="total_audi",
    color="genre",
    hover_name="movieNm",
    points="outliers",
    title="영화 10편 이상 장르별 총 관객 수 분포 (Boxplot)",
    labels={
        "genre": "장르",
        "total_audi": "총 관객 수",
    },
    hover_data={
        "total_audi": ":,d",
        "genre": False,
    },
)

fig_box.update_layout(
    xaxis_title="장르", yaxis_title="총 관객 수", showlegend=False
)

# Streamlit에 그래프 출력
st.plotly_chart(fig_box, use_container_width=True)

# 구분선 및 해석 구역
st.divider()
st.markdown(
    "💡 **이 그래프로 알 수 있는 것:** 주요 장르별 관객 수의 중간값과 편차를 비교할 수 있으며, 박스 밖의 아웃라이어 점들을 통해 장르 평균을 훨씬 뛰어넘는 대흥행작들을 식별할 수 있습니다."
)

# -------------------------------------------------------------------
# 그래프 6: 개봉일 스크린 수 vs 총 관객 수 (버블 차트 - 크기: 개봉 첫 주 관객)
# -------------------------------------------------------------------
st.subheader("6. 개봉일 스크린 수, 총 관객 수, 개봉 첫 주 관객 수의 관계")

# Plotly 버블 차트 생성 (size: first_week_audi 추가)
fig_bubble = px.scatter(
    df,
    x="first_scrn",
    y="total_audi",
    size="first_week_audi",
    color="genre",
    hover_name="movieNm",
    size_max=40,
    title="개봉일 스크린 수 vs 총 관객 수 (버블 크기: 개봉 첫 주 관객 수)",
    labels={
        "first_scrn": "개봉일 스크린 수",
        "total_audi": "총 관객 수",
        "first_week_audi": "개봉 첫 주 관객 수",
        "genre": "장르",
    },
    hover_data={
        "first_scrn": ":,d",
        "total_audi": ":,d",
        "first_week_audi": ":,d",
        "genre": False,
    },
)

fig_bubble.update_layout(
    xaxis_title="개봉일 스크린 수", yaxis_title="총 관객 수"
)

# Streamlit에 그래프 출력
st.plotly_chart(fig_bubble, use_container_width=True)

# 구분선 및 해석 구역
st.divider()
st.markdown(
    "💡 **이 그래프로 알 수 있는 것:** 스크린 수와 총 관객 수 외에도 '개봉 첫 주 관객 수(버블 크기)'를 함께 비교함으로써, 초반 흥행 기세가 최종 관객 수까지 그대로 이어졌는지 아니면 입소문 등을 통해 대기만성형으로 흥행했는지를 시각적으로 식별할 수 있습니다."
)

# -------------------------------------------------------------------
# 그래프 7: 제작 국가 및 장르별 영화 편수 (선버스트 차트)
# -------------------------------------------------------------------
st.subheader("7. 제작 국가 및 장르별 영화 편수 분포")

# Plotly 선버스트 차트 생성 (계층 구조: nation -> genre)
fig_sunburst = px.sunburst(
    df,
    path=["nation", "genre"],
    title="제작 국가 - 장르별 영화 편수 (Sunburst)",
)

fig_sunburst.update_traces(
    hovertemplate="<b>%{label}</b><br>영화 편수: %{value}편<extra></extra>"
)

# Streamlit에 그래프 출력
st.plotly_chart(fig_sunburst, use_container_width=True)

# 구분선 및 해석 구역
st.divider()
st.markdown(
    "💡 **이 그래프로 알 수 있는 것:** 각 제작 국가별로 제작된 영화 수의 총량과, 각 국가 내부에서 주로 제작된 장르의 다변화 정도를 계층적 원형 구조로 한눈에 비교할 수 있습니다."
)

# -------------------------------------------------------------------
# 그래프 8: 10위권 체류 날수 vs 총 관객 수 (산점도)
# -------------------------------------------------------------------
st.subheader("8. 10위권 체류 기간과 총 관객 수의 관계")

# Plotly 산점도 생성 (x: days_in_top10, y: total_audi)
fig_days_scatter = px.scatter(
    df,
    x="days_in_top10",
    y="total_audi",
    hover_name="movieNm",
    title="10위권에 오래 머문 영화는 총 관객도 많은가",
    labels={
        "days_in_top10": "10위권에 머문 날수",
        "total_audi": "총 관객 수",
    },
    hover_data={
        "days_in_top10": ":,d",
        "total_audi": ":,d",
    },
)

fig_days_scatter.update_layout(
    xaxis_title="10위권에 머문 날수", yaxis_title="총 관객 수"
)

# Streamlit에 그래프 출력
st.plotly_chart(fig_days_scatter, use_container_width=True)

# 구분선 및 해석 구역
st.divider()
st.markdown(
    "💡 **이 그래프로 알 수 있는 것:** 10위권 박스오피스에 장기간 머무른 영화일수록 최종 총 관객 수가 늘어나는 강한 양의 상관관계(장기 흥행 특성)를 시각적으로 보여줍니다."
)
