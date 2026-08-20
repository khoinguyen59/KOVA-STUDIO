import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

def clean_all_boms():
    cleaned = 0
    for root, dirs, files in os.walk(PROJECT_ROOT):
        if "venv" in root or ".git" in root or "build" in root or "dist" in root:
            continue
        for f in files:
            if f.endswith((".py", ".json", ".spec", ".md", ".txt", ".bat", ".ass", ".srt")):
                filepath = os.path.join(root, f)
                try:
                    with open(filepath, "rb") as handle:
                        content = handle.read()
                    if content.startswith(b"\xef\xbb\xbf"):
                        content = content[3:]
                        with open(filepath, "wb") as handle:
                            handle.write(content)
                        print(f"Cleaned BOM from: {os.path.relpath(filepath, PROJECT_ROOT)}")
                        cleaned += 1
                except Exception as exc:
                    print(f"Error checking {filepath}: {exc}")
    print(f"Total files cleaned: {cleaned}")

if __name__ == "__main__":
    clean_all_boms()
