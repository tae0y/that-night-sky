"""별자리 지도 생성 CLI 진입점.

상단의 where/when 변수를 수정 후 실행:
    uv run python src/thatnightsky/starchart.py
"""

from dotenv import load_dotenv

load_dotenv()

from thatnightsky.compute import run
from thatnightsky.models import QueryInput
from thatnightsky.renderers.static import save_static_chart

where = "부산광역시 가야동"
when = "1995-01-15 00:00"

sky_data = run(QueryInput(address=where, when=when))
path = save_static_chart(sky_data)
print(f"저장됨: {path}")
