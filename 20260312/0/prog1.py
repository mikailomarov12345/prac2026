from pathlib import Path

cwd = Path(".")
print(*list(cwd.glob("../../*")))
