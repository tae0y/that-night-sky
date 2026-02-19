"""Poetic night-sky narrative generation using the Claude API."""

import os

import anthropic

# IAU abbreviation → Korean full name
_IAU_TO_KO: dict[str, str] = {
    "And": "안드로메다",
    "Ant": "공기펌프",
    "Aps": "극락조",
    "Aql": "독수리",
    "Aqr": "물병",
    "Ara": "제단",
    "Ari": "양",
    "Aur": "마차부",
    "Boo": "목동",
    "CMa": "큰개",
    "CMi": "작은개",
    "CVn": "사냥개",
    "Cae": "조각칼",
    "Cam": "기린",
    "Cap": "염소",
    "Car": "용골",
    "Cas": "카시오페이아",
    "Cen": "켄타우로스",
    "Cep": "세페우스",
    "Cet": "고래",
    "Cha": "카멜레온",
    "Cir": "컴퍼스",
    "Cnc": "게",
    "Col": "비둘기",
    "Com": "머리털",
    "CrA": "남쪽왕관",
    "CrB": "북쪽왕관",
    "Crt": "컵",
    "Cru": "남십자",
    "Crv": "까마귀",
    "Cyg": "백조",
    "Del": "돌고래",
    "Dor": "황새치",
    "Dra": "용",
    "Equ": "조랑말",
    "Eri": "에리다누스",
    "For": "화로",
    "Gem": "쌍둥이",
    "Gru": "두루미",
    "Her": "헤라클레스",
    "Hor": "시계",
    "Hya": "바다뱀",
    "Hyi": "물뱀",
    "Ind": "인디언",
    "LMi": "작은사자",
    "Lac": "도마뱀",
    "Leo": "사자",
    "Lep": "토끼",
    "Lib": "천칭",
    "Lup": "이리",
    "Lyn": "살쾡이",
    "Lyr": "거문고",
    "Men": "테이블산",
    "Mic": "현미경",
    "Mon": "외뿔소",
    "Mus": "파리",
    "Nor": "직각자",
    "Oct": "팔분의",
    "Oph": "뱀주인",
    "Ori": "오리온",
    "Pav": "공작",
    "Peg": "페가수스",
    "Per": "페르세우스",
    "Phe": "봉황",
    "Pic": "화가",
    "PsA": "남쪽물고기",
    "Psc": "물고기",
    "Pup": "고물",
    "Pyx": "나침반",
    "Ret": "그물",
    "Scl": "조각가",
    "Sco": "전갈",
    "Sct": "방패",
    "Ser": "뱀",
    "Sex": "육분의",
    "Sge": "화살",
    "Sgr": "궁수",
    "Tau": "황소",
    "Tel": "망원경",
    "TrA": "남쪽삼각형",
    "Tri": "삼각형",
    "Tuc": "큰부리새",
    "UMa": "큰곰",
    "UMi": "작은곰",
    "Vel": "돛",
    "Vir": "처녀",
    "Vol": "날치",
    "Vul": "여우",
}


def generate_night_description(
    address: str,
    when: str,
    visible_constellation_names: tuple[str, ...],
    theme: str = "",
) -> str:
    """Generate a poetic Korean narrative about the night sky.

    Args:
        address: Location name (normalized geocoder address or raw input).
        when: Date/time string ("YYYY-MM-DD HH:MM").
        visible_constellation_names: IAU abbreviations of constellations visible that night.
        theme: Optional occasion/theme (e.g. "생일", "기일", "첫 만남"). Empty string = model chooses.

    Returns:
        A single Korean paragraph of poetic prose.
    """
    constellations_str = (
        ", ".join(
            _IAU_TO_KO.get(name, name) for name in visible_constellation_names[:10]
        )
        if visible_constellation_names
        else "알 수 없음"
    )

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        system=(
            "당신은 밤하늘을 소재로 우화적이고 시적인 단문을 쓰는 작가예요.\n\n"
            "규칙:\n"
            "- 반드시 한 문단(3-5문장) 이내로 작성\n"
            "- 탄생, 죽음, 사랑, 우정 중 하나의 정서를 중심 주제로 삼을 것\n"
            "- 별자리 이름을 직접 나열하지 말고 이야기 속에 녹일 것\n"
            "- 설명적 문장 금지; 서사·은유·감각 이미지 위주로\n"
            "- 마지막 문장은 여운을 남기는 열린 결말로\n\n"
            "추가 규칙:\n"
            "- '특별한 날' 입력은 그 날의 감정적 본질(그리움, 축하, 경이, 애도 등)로"
            " 내면화한 뒤 글에 반영할 것\n"
            "- 입력된 단어(기일, 기념일 등)를 글에 직접 쓰지 말 것\n"
            "- 죽음을 연상시키는 날이라면 슬픔보다 연결과 기억의 정서로 승화시킬 것\n"
        ),
        messages=[
            {
                "role": "user",
                "content": (
                    f"날짜/시각: {when}\n"
                    f"장소: {address}\n"
                    f"보이는 별자리: {constellations_str}\n"
                    + (f"이 날의 의미: {theme}\n" if theme else "")
                    + "\n위 조건으로 한 문단 글을 작성하세요."
                    + "'이 날의 의미' 입력이 없으면 날짜, 시간, 계절, 별자리 조합에서 어울리는 정서를 스스로 선택할 것"
                ),
            }
        ],
    )
    return message.content[0].text  # type: ignore[union-attr]
