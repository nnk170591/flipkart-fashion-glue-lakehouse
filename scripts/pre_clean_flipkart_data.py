import pandas as pd

# ✅ Try a more tolerant encoding for reading
df = pd.read_csv(
    "C:/Users/Khoa/Downloads/flipkart_fashion_data.csv",
    encoding="latin1",   # <-- tolerant encoding
    low_memory=False
)

# 🔹 Clean encoding issues: remove or replace non-UTF8 chars
def clean_text(text):
    if isinstance(text, str):
        # remove invisible or invalid chars
        return text.encode("utf-8", "ignore").decode("utf-8", "ignore")
    return text

for col in df.columns:
    df[col] = df[col].apply(clean_text)

# 🔹 Optional: Normalize column names
df.columns = [c.strip().replace(" ", "_").lower() for c in df.columns]

# 🔹 Save as proper UTF-8 encoded CSV
df.to_csv("flipkart_fashion_clean.csv", index=False, encoding="utf-8")

print("✅ Clean CSV generated successfully as UTF-8: flipkart_fashion_clean.csv")
