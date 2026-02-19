"""Poetic night-sky narrative generation using the Claude API."""

import os

import anthropic


def generate_night_description(
    address: str,
    when: str,
    visible_constellation_names: tuple[str, ...],
) -> str:
    """Generate a poetic Korean narrative about the night sky.

    Args:
        address: Location name (normalized geocoder address or raw input).
        when: Date/time string ("YYYY-MM-DD HH:MM").
        visible_constellation_names: IAU abbreviations of constellations visible that night.

    Returns:
        A single Korean paragraph of poetic prose.
    """
    constellations_str = (
        ", ".join(visible_constellation_names[:10])
        if visible_constellation_names
        else "알 수 없음"
    )

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        messages=[
            {
                "role": "user",
                "content": (
                    f"장소: {address}\n"
                    f"날짜/시각: {when}\n"
                    f"보이는 별자리: {constellations_str}\n\n"
                    "위 정보를 바탕으로, 그날 밤하늘을 바라보는 사람의 감성을 담은 "
                    "한국어 한 문단(3~4문장)을 써줘. "
                    "별자리 이름은 직접 언급하지 말고, 그 밤의 분위기와 감정을 서술해줘. "
                    "낭만적이고 시적인 톤으로."
                ),
            }
        ],
    )
    return message.content[0].text  # type: ignore[union-attr]
