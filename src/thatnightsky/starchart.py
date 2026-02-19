"""CLI entry point for star chart generation.

Edit the where/when variables at the top, then run:
    uv run python src/thatnightsky/starchart.py
"""

from dotenv import load_dotenv

load_dotenv()

from thatnightsky.compute import run  # noqa: E402
from thatnightsky.models import QueryInput  # noqa: E402
from thatnightsky.renderers.static import save_static_chart  # noqa: E402

where = "부산광역시 가야동"
when = "1995-01-15 00:00"

sky_data = run(QueryInput(address=where, when=when))
path = save_static_chart(sky_data)
print(f"Saved: {path}")
