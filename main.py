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

    # 장르 및 국가 열 결측치 처리 및 전처리
    if "genre" in df.columns:
        df["genre"] = df["genre"].fillna("기타").astype(str).str.split("|").str[0]
    if "nation" in df.columns:
        df["nation"] = df["nation"].fillna("기타").astype(str)

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

st.plotly_chart(fig_donut, use_container_width=True)
st.divider()
st.markdown("💡 **이 그래프로 알 수 있는 것:** 박스오피스 상위권 영화들 중 가장 큰 비중을 차지하는 주요 장르 분포와 특정 장르의 쏠림 현상을 한눈에 파악할 수 있습니다.")


# -------------------------------------------------------------------
# 그래프 2: 장르 및 영화별 총 관객 수 (트리맵)
# -------------------------------------------------------------------
st.subheader("2. 장르 및 영화별 총 관객 수 분포")

# 1) 트리맵 전용 데이터프레임 생성 및 결측치 제거
df_tree = df[['genre', 'movieNm', 'total_audi']].dropna().copy()
# 2) 관객 수가 0 이하인 데이터 완벽 제거
df_tree = df_tree[df_tree['total_audi'] > 0]
# 3) 영화 중복 집계를 방지하기 위해 장르/영화명 기준으로 최대 관객수 추출
df_tree = df_tree.groupby(['genre', 'movieNm'], as_index=False)['total_audi'].max()
# 4) 계층 충돌을 막기 위해 '영화명_인덱스' 형태로 완벽하게 독립적인 노드 ID 생성
df_tree['movie_node'] = df_tree['movieNm'] + "_" + df_tree.index.astype(str)

# Plotly 트리맵 생성
fig_treemap = px.treemap(
    df_tree,
    path=[px.Constant("전체 영화"), "genre", "movie_node"],
    values="total_audi",
    title="장르 및 영화별 총 관객 수",
    custom_data=["movieNm"]  # 화면(툴팁)에 보여줄 원래 영화명
)

# 툴팁에 _인덱스가 안보이게 원래 영화명만 출력되도록 설정
fig_treemap.update_traces(
    hovertemplate="<b>%{customdata[0]}</b><br>총 관객 수: %{value:,}명<extra></extra>"
)

st.plotly_chart(fig_treemap, use_container_width=True)
st.divider()
st.markdown("💡 **이 그래프로 알 수 있는 것:** 특정 장르 내에서 어떤 영화가 흥행을 주도했는지 장르 전체 관객 대비 개별 영화의 흥행 기여도를 한눈에 비교할 수 있습니다.")


# -------------------------------------------------------------------
# 그래프 3: 총 관객 수 분포 (히스토그램)
# -------------------------------------------------------------------
st.subheader("3. 총 관객 수 분포")

fig_hist = px.histogram(
    df,
    x="total_audi",
    nbins=30,
    title="총 관객 수 히스토그램",
    labels={"total_audi": "총 관객 수"},
)
# 오류 수정: bar_gap -> bargap
fig_hist.update_layout(xaxis_title="총 관객 수", yaxis_title="영화 수", bargap=0.1)

st.plotly_chart(fig_hist, use_container_width=True)

# 최상위 관객 수 영화 정보
top_movie = df.loc[df["total_audi"].idxmax()]
st.divider()
st.markdown(f"💡 **이 그래프로 알 수 있는 것:** 대부분의 영화가 **500만 명 이하** 구간에 집중되어 있는 롱테일 분포 양상을 보이며, 가장 많은 관객을 동원한 영화는 **{top_movie['movieNm']}**({top_movie['total_audi']:,}명)입니다.")


# -------------------------------------------------------------------
# 그래프 4: 개봉일 스크린 수 vs 총 관객 수 (산점도)
# -------------------------------------------------------------------
st.subheader("4. 개봉일 스크린 수와 총 관객 수의 관계")

fig_scatter = px.scatter(
    df,
    x="first_scrn",
    y="total_audi",
    color="genre",
    hover_name="movieNm",
    title="개봉일 스크린 수 vs 총 관객 수",
    labels={"first_scrn": "개봉일 스크린 수", "total_audi": "총 관객 수", "genre": "장르"},
    hover_data={"first_scrn": ":,d", "total_audi": ":,d", "genre": False},
)
fig_scatter.update_layout(xaxis_title="개봉일 스크린 수", yaxis_title="총 관객 수")

st.plotly_chart(fig_scatter, use_container_width=True)
st.divider()
st.markdown("💡 **이 그래프로 알 수 있는 것:** 초기 스크린 확보 수와 최종 총 관객 수 간의 양의 상관관계를 확인할 수 있으며, 초기 스크린 수가 적음에도 흥행에 성공한 아웃라이어 영화를 탐색할 수 있습니다.")


# -------------------------------------------------------------------
# 그래프 5: 주요 장르별 총 관객 수 분포 (박스플롯)
# -------------------------------------------------------------------
st.subheader("5. 주요 장르별 총 관객 수 분포")

genre_counts_series = df["genre"].value_counts()
top_genres = genre_counts_series[genre_counts_series >= 10].index
df_filtered = df[df["genre"].isin(top_genres)]

fig_box = px.box(
    df_filtered,
    x="genre",
    y="total_audi",
    color="genre",
    hover_name="movieNm",
    points="outliers",
    title="영화 10편 이상 장르별 총 관객 수 분포 (Boxplot)",
    labels={"genre": "장르", "total_audi": "총 관객 수"},
    hover_data={"total_audi": ":,d", "genre": False},
)
fig_box.update_layout(xaxis_title="장르", yaxis_title="총 관객 수", showlegend=False)

st.plotly_chart(fig_box, use_container_width=True)
st.divider()
st.markdown("💡 **이 그래프로 알 수 있는 것:** 주요 장르별 관객 수의 중간값과 편차를 비교할 수 있으며, 박스 밖의 아웃라이어 점들을 통해 장르 평균을 훨씬 뛰어넘는 대흥행작들을 식별할 수 있습니다.")


# -------------------------------------------------------------------
# 그래프 6: 개봉일 스크린 수 vs 총 관객 수 (버블 차트)
# -------------------------------------------------------------------
st.subheader("6. 개봉일 스크린 수, 총 관객 수, 개봉 첫 주 관객 수의 관계")

fig_bubble = px.scatter(
    df,
    x="first_scrn",
    y="total_audi",
    size="first_week_audi",
    color="genre",
    hover_name="movieNm",
    size_max=40,
    title="개봉일 스크린 수 vs 총 관객 수 (버블 크기: 개봉 첫 주 관객 수)",
    labels={"first_scrn": "개봉일 스크린 수", "total_audi": "총 관객 수", "first_week_audi": "개봉 첫 주 관객 수", "genre": "장르"},
    hover_data={"first_scrn": ":,d", "total_audi": ":,d", "first_week_audi": ":,d", "genre": False},
)
fig_bubble.update_layout(xaxis_title="개봉일 스크린 수", yaxis_title="총 관객 수")

st.plotly_chart(fig_bubble, use_container_width=True)
st.divider()
st.markdown("💡 **이 그래프로 알 수 있는 것:** 스크린 수와 총 관객 수 외에도 '개봉 첫 주 관객 수'를 함께 비교하여 대기만성형으로 흥행했는지를 식별할 수 있습니다.")


# -------------------------------------------------------------------
# 그래프 7: 제작 국가 및 장르별 영화 편수 (선버스트 차트)
# -------------------------------------------------------------------
st.subheader("7. 제작 국가 및 장르별 영화 편수 분포")

# 선버스트 차트 오류 방지를 위해 명확히 집계(groupby) 후 0 초과 값만 사용
df_sun = df[['nation', 'genre']].dropna().copy()
df_sun_count = df_sun.groupby(['nation', 'genre']).size().reset_index(name='count')
df_sun_count = df_sun_count[df_sun_count['count'] > 0]

fig_sunburst = px.sunburst(
    df_sun_count,
    path=[px.Constant("전체 국가"), "nation", "genre"],
    values="count",
    title="제작 국가 - 장르별 영화 편수 (Sunburst)",
)
fig_sunburst.update_traces(hovertemplate="<b>%{label}</b><br>영화 편수: %{value}편<extra></extra>")

st.plotly_chart(fig_sunburst, use_container_width=True)
st.divider()
st.markdown("💡 **이 그래프로 알 수 있는 것:** 각 제작 국가별로 제작된 영화 수의 총량과 주로 제작된 장르의 다변화 정도를 계층적 원형 구조로 한눈에 비교할 수 있습니다.")


# -------------------------------------------------------------------
# 그래프 8: 10위권 체류 날수 vs 총 관객 수 (산점도)
# -------------------------------------------------------------------
st.subheader("8. 10위권 체류 기간과 총 관객 수의 관계")

fig_days_scatter = px.scatter(
    df,
    x="days_in_top10",
    y="total_audi",
    hover_name="movieNm",
    title="10위권에 오래 머문 영화는 총 관객도 많은가",
    labels={"days_in_top10": "10위권에 머문 날수", "total_audi": "총 관객 수"},
    hover_data={"days_in_top10": ":,d", "total_audi": ":,d"},
)
fig_days_scatter.update_layout(xaxis_title="10위권에 머문 날수", yaxis_title="총 관객 수")

st.plotly_chart(fig_days_scatter, use_container_width=True)
st.divider()
st.markdown("💡 **이 그래프로 알 수 있는 것:** 10위권 박스오피스에 장기간 머무른 영화일수록 최종 총 관객 수가 늘어나는 강한 양의 상관관계(장기 흥행 특성)를 시각적으로 보여줍니다.")
