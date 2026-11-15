"""یک بار با اینترنت اجرا کن تا فایل‌های آفلاین دانلود بشن."""
import os
import urllib.request

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", "static", "vendor")

BS = "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.rtl.min.css"
ICONS = "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font"
VAZIR = "https://cdn.jsdelivr.net/npm/vazirmatn@33.0.3/fonts/webfonts/Vazirmatn%5Bwght%5D.woff2"

FILES = [
    (BS, "bootstrap/bootstrap.rtl.min.css"),
    (ICONS + "/bootstrap-icons.min.css", "bootstrap-icons/bootstrap-icons.min.css"),
    (ICONS + "/fonts/bootstrap-icons.woff2", "bootstrap-icons/fonts/bootstrap-icons.woff2"),
    (ICONS + "/fonts/bootstrap-icons.woff", "bootstrap-icons/fonts/bootstrap-icons.woff"),
    (VAZIR, "fonts/Vazirmatn.woff2"),
]

for url, rel in FILES:
    dest = os.path.join(BASE, *rel.split("/"))
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    try:
        print("دانلود:", rel)
        urllib.request.urlretrieve(url, dest)
    except Exception as e:
        print("  ناموفق:", e)

print("\nتمام شد.")

