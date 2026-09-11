from datetime import datetime, timedelta
import zoneinfo
import pandas as pd
import requests
import streamlit as st

# 페이지 기본 설정
st.set_page_config(
    page_title="어제 박스오피스 순위", page_icon="🎬", layout="wide"
)


# API 요청 및 캐싱 설정 (1시간 = 3600초 동안 결과 기억)
@st.cache_data(ttl=3600)
def fetch_daily_boxoffice(target_date: str, api_key: str):
    """KOBIS 일별 박스오피스 API를 호출하여 데이터를 가져옵니다."""
    url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
    params = {"key": api_key, "targetDt": target_date}

    try:
        response = requests.get(url, params=params, timeout=10)
        # HTTP 요청 에러 확인
        response.raise_for_status()
        data = response.json()

        # 1. API 키 오류 등의 faultInfo 처리 (KOBIS는 키가 틀려도 200 OK 응답 후 faultInfo 전달)
        if "faultInfo" in data:
            message = data["faultInfo"].get(
                "message", "인증키(KOBIS_KEY)가 유효하지 않습니다."
            )
            return None, f"API 오류가 발생했습니다: {message}"

        box_office_result = data.get("boxOfficeResult", {})
        daily_list = box_office_result.get("dailyBoxOfficeList", [])

        # 2. 데이터가 비어 있는 경우
        if not daily_list:
            return (
                None,
                "조회된 영화 목록이 없습니다. 날짜 또는 API 상태를 확인해 주세요.",
            )

        # 정상 데이터 반환
        return daily_list, None

    except requests.exceptions.RequestException as e:
        return (
            None,
            f"네트워크 요청 중 오류가 발생했습니다. (상세 내용: {e})",
        )


def main():
    st.title("🎬 어제 일별 박스오피스 순위")

    # secrets에서 API 키 불러오기
    if "KOBIS_KEY" not in st.secrets:
        st.error("🔑 Streamlit Secrets에 'KOBIS_KEY'가 설정되지 않았습니다.")
        st.info(
            "Streamlit Cloud 설정(Secrets)에서 `KOBIS_KEY = '발급받은키'`를 입력해야 합니다."
        )
        return

    api_key = st.secrets["KOBIS_KEY"]

    # 배포 서버 시계가 해외 기준일 수 있으므로 한국 표준시(Asia/Seoul)로 계산
    seoul_tz = zoneinfo.ZoneInfo("Asia/Seoul")
    now_in_seoul = datetime.now(seoul_tz)
    yesterday_in_seoul = now_in_seoul - timedelta(days=1)
    target_date = yesterday_in_seoul.strftime("%Y%m%d")
    formatted_date = yesterday_in_seoul.strftime("%Y년 %m월 %d일")

    st.caption(f" 기준 날짜: {formatted_date} (한국 시간 기준 어제)")

    # API 데이터 수신
    daily_list, error_message = fetch_daily_boxoffice(target_date, api_key)

    # 오류 또는 빈 데이터 발생 시 한국어 안내 메시지 출력
    if error_message:
        st.error("⚠️ 데이터를 불러올 수 없습니다.")
        st.warning(f"💡 확인 필요한 사항: {error_message}")
        st.markdown(
            """
            **체크리스트:**
            1. Streamlit Secrets에 `KOBIS_KEY`가 바르게 등록되었는지 확인하세요.
            2. [KOBIS 영화관입장권통합전산망 Open API](https://www.kobis.or.kr/kobisopenapi)에서 키 사용 승인이 되었는지 확인하세요.
            3. 네트워크 연결 상태 및 API 서버 정기 점검 여부를 확인하세요.
            """
        )
        return

    # Pandas DataFrame 변환
    df = pd.DataFrame(daily_list)

    # 문자열로 들어오는 숫자 데이터를 정수형(int)으로 정형화
    numeric_columns = [
        "rank",
        "rankInten",
        "audiCnt",
        "audiAcc",
        "scrnCnt",
        "showCnt",
    ]
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    # 순위 기준으로 정렬
    df = df.sort_values(by="rank", ascending=True).reset_index(drop=True)

    # -------------------------------------------------------------
    # 1. 1위 영화 지표 카드 3장 표시
    # -------------------------------------------------------------
    top_movie = df.iloc[0]
    st.markdown(f"### 🏆 1위 영화: {top_movie['movieNm']}")

    col1, col2, col3 = st.columns(3)
    col1.metric(
        label="일일 관객수", value=f"{top_movie['audiCnt']:,} 명"
    )
    col2.metric(
        label="누적 관객수", value=f"{top_movie['audiAcc']:,} 명"
    )
    col3.metric(
        label="상영 스크린수", value=f"{top_movie['scrnCnt']:,} 개"
    )

    st.divider()

    # -------------------------------------------------------------
    # 2. 관객수 상위 5편 막대그래프
    # -------------------------------------------------------------
    st.subheader("📊 관객수 상위 5개 영화")
    top_5_df = df.head(5).copy()

    # Streamlit 차트에 표기하기 편리하도록 가공
    chart_data = top_5_df.set_index("movieNm")[["audiCnt"]]
    chart_data.columns = ["어제 관객수"]
    st.bar_chart(chart_data)

    st.divider()

    # -------------------------------------------------------------
    # 3. 박스오피스 전체 표 시각화
    # -------------------------------------------------------------
    st.subheader("📋 전체 순위표")

    # 표시용 컬럼명 변경 및 가독성 정밀화
    display_df = df[
        ["rank", "movieNm", "openDt", "audiCnt", "audiAcc", "scrnCnt"]
    ].copy()
    display_df.columns = [
        "순위",
        "영화명",
        "개봉일",
        "관객수",
        "누적관객",
        "스크린수",
    ]

    # 숫자 천 단위 쉼표 포맷팅을 적용하여 출력
    st.dataframe(
        display_df.style.format(
            {"관객수": "{:,}", "누적관객": "{:,}", "스크린수": "{:,}"}
        ),
        use_container_width=True,
    )


if __name__ == "__main__":
    main():
