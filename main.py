from datetime import datetime, timedelta
import zoneinfo
import pandas as pd
import requests
import streamlit as st

# 페이지 기본 설정 (와이드 레이아웃 사용)
st.set_page_config(
    page_title="일별 박스오피스 조회", page_icon="🎬", layout="wide"
)


# API 응답 결과를 1시간 동안 기억하는 캐시 함수
# 날짜(target_date)와 API키(api_key) 조합별로 결과를 저장합니다.
@st.cache_data(ttl=3600)
def fetch_daily_boxoffice(target_date: str, api_key: str):
    """KOBIS API를 호출하여 입력받은 날짜의 박스오피스 데이터를 가져옵니다."""
    url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
    params = {"key": api_key, "targetDt": target_date}

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        # 1. API 키 오류 등 faultInfo 상자가 반환된 경우
        if "faultInfo" in data:
            message = data["faultInfo"].get(
                "message", "인증키가 유효하지 않습니다."
            )
            return None, f"API 오류가 발생했습니다: {message}"

        box_office_result = data.get("boxOfficeResult", {})
        daily_list = box_office_result.get("dailyBoxOfficeList", [])

        # 2. 고른 날짜의 영화 목록이 비어 있는 경우 (집계 전이거나 데이터 없음)
        if not daily_list:
            return None, "그날은 아직 집계 전입니다."

        return daily_list, None

    except requests.exceptions.RequestException as e:
        return (
            None,
            f"네트워크 요청 중 오류가 발생했습니다. (상세 내용: {e})",
        )


def main():
    st.title("🎬 일별 박스오피스 순위 조회")

    # Secrets에 저장된 KOBIS_KEY 검증
    if "KOBIS_KEY" not in st.secrets:
        st.error("🔑 Streamlit Secrets에 'KOBIS_KEY'가 설정되지 않았습니다.")
        st.info(
            "Streamlit Cloud 설정의 Secrets 메뉴에서 `KOBIS_KEY = '발급받은키'`를 등록해 주세요."
        )
        return

    api_key = st.secrets["KOBIS_KEY"]

    # 배포 서버 시계와 상관없이 항상 한국 시간(Asia/Seoul) 기준으로 어제 날짜 계산
    seoul_tz = zoneinfo.ZoneInfo("Asia/Seoul")
    now_in_seoul = datetime.now(seoul_tz)
    yesterday_in_seoul = (now_in_seoul - timedelta(days=1)).date()

    # 달력(Date Input)으로 조회할 날짜 선택
    # max_value를 어제로 고정하여 오늘 이후 날짜는 선택 불가능하게 설정
    selected_date = st.date_input(
        "📅 조회할 날짜를 선택하세요 (가장 최근 가능 날짜: 어제)",
        value=yesterday_in_seoul,
        max_value=yesterday_in_seoul,
    )

    target_date_str = selected_date.strftime("%Y%m%d")
    formatted_date_str = selected_date.strftime("%Y년 %m월 %d일")

    st.caption(f"선택한 날짜: {formatted_date_str}")

    # API 데이터 불러오기 (캐싱 적용)
    daily_list, error_message = fetch_daily_boxoffice(
        target_date_str, api_key
    )

    # 에러 또는 빈 결과(집계 전) 처리
    if error_message:
        if error_message == "그날은 아직 집계 전입니다.":
            st.info(f"💡 {error_message}")
        else:
            st.error("⚠️ 데이터를 불러올 수 없습니다.")
            st.warning(f"💡 {error_message}")
            st.markdown(
                """
                **확인 필요 사항:**
                1. Streamlit Secrets에 `KOBIS_KEY`가 올바르게 설정되었는지 확인하세요.
                2. KOBIS OpenAPI 사이트에서 키가 정상 승인 상태인지 확인하세요.
                """
            )
        return

    # Pandas 데이터프레임으로 변환
    df = pd.DataFrame(daily_list)

    # 문자열 숫자를 정수형(int)으로 정형화
    numeric_cols = [
        "rank",
        "rankInten",
        "audiCnt",
        "audiAcc",
        "scrnCnt",
        "showCnt",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    # 순위 오름차순 정렬
    df = df.sort_values(by="rank", ascending=True).reset_index(drop=True)

    # 1. 누적관객 100만 명 이상 영화 이름 옆에 🏆 이모지 추가
    df["display_movieNm"] = df.apply(
        lambda row: f"{row['movieNm']} 🏆"
        if row["audiAcc"] >= 1_000_000
        else row["movieNm"],
        axis=1,
    )

    # 2. 전날 대비 순위 증감(rankInten) 화살표 표시 로직
    # - 양수: 빨간 위 화살표
    # - 음수: 파란 아래 화살표
    # - 0: 유지(-)
    def format_rank_change(val):
        if val > 0:
            return f"🔴 ⬆️ {val}"
        elif val < 0:
            return f"🔵 ⬇️ {abs(val)}"
        return "-"

    df["순위변동"] = df["rankInten"].apply(format_rank_change)

    # -------------------------------------------------------------
    # 1위 영화 지표 카드 3개
    # -------------------------------------------------------------
    top_movie = df.iloc[0]
    st.markdown(f"### 🏆 1위 영화: {top_movie['display_movieNm']}")

    col1, col2, col3 = st.columns(3)
    col1.metric("일일 관객수", f"{top_movie['audiCnt']:,} 명")
    col2.metric("누적 관객수", f"{top_movie['audiAcc']:,} 명")
    col3.metric("상영 스크린수", f"{top_movie['scrnCnt']:,} 개")

    st.divider()

    # -------------------------------------------------------------
    # 관객수 상위 5개 영화 막대그래프
    # -------------------------------------------------------------
    st.subheader("📊 관객수 상위 5개 영화")
    top_5_df = df.head(5)
    chart_data = top_5_df.set_index("display_movieNm")[["audiCnt"]]
    chart_data.columns = ["관객수"]
    st.bar_chart(chart_data)

    st.divider()

    # -------------------------------------------------------------
    # 박스오피스 전체 순위표
    # -------------------------------------------------------------
    st.subheader("📋 전체 순위표")

    display_df = df[
        [
            "rank",
            "순위변동",
            "display_movieNm",
            "openDt",
            "audiCnt",
            "audiAcc",
            "scrnCnt",
        ]
    ].copy()

    display_df.columns = [
        "순위",
        "순위변동",
        "영화명",
        "개봉일",
        "관객수",
        "누적관객",
        "스크린수",
    ]

    # 천 단위 쉼표 서식 적용 후 출력
    st.dataframe(
        display_df.style.format(
            {"관객수": "{:,}", "누적관객": "{:,}", "스크린수": "{:,}"}
        ),
        use_container_width=True,
    )


if __name__ == "__main__":
    main()
