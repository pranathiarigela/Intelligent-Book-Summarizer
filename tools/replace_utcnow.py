# tools/replace_utcnow.py
from pathlib import Path
p = Path("backend/auth.py")
text = p.read_text(encoding="utf-8")

# Ensure UTC is imported in the datetime import line
# Replace a line like: from datetime import datetime, timedelta
# with: from datetime import datetime, timedelta, UTC
text = text.replace("from datetime import datetime, timedelta", "from datetime import datetime, timedelta, UTC")

# Replace all occurrences of datetime.utcnow() -> datetime.now(UTC)
text = text.replace("datetime.utcnow()", "datetime.now(UTC)")

# Write back
p.write_text(text, encoding="utf-8")
print("Patched backend/auth.py")
