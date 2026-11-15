from pathlib import Path


# مسیر ریشه پروژه؛ چون اسکریپت داخل خود پروژه قرار دارد.
PROJECT_ROOT = Path(__file__).resolve().parent

# مسیر فایل map.txt که باید ساختار پروژه داخل آن ذخیره شود.
MAP_FILE = PROJECT_ROOT / "map_atuo.txt"

# پوشه‌ها و فایل‌هایی که نمی‌خواهیم در ساختار نمایش داده شوند.
IGNORED_NAMES = {
    ".venv",
    "venv",
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".idea",
    ".vscode",
    "Locals",
    "graphify-out",
    "errors",

}

# فایل‌های حساس که بهتر است در خروجی ساختار نمایش داده نشوند.
IGNORED_FILES = {
    ".env",
    "map.txt",
    ".json",
}


def build_tree(directory: Path, prefix: str = "") -> list[str]:
    """
    ورودی:
        directory: مسیر پوشه‌ای که باید بررسی شود.
        prefix: پیشوند لازم برای ساخت ظاهر درختی.

    خروجی:
        list[str]: خطوط ساختار درختی پروژه.
    """

    # فقط فایل‌ها و پوشه‌های قابل نمایش را دریافت می‌کنیم.
    items = [
        item
        for item in directory.iterdir()
        if item.name not in IGNORED_NAMES
        and item.name not in IGNORED_FILES
    ]

    # ابتدا پوشه‌ها و سپس فایل‌ها نمایش داده شوند.
    items.sort(key=lambda item: (item.is_file(), item.name.lower()))

    lines = []

    for index, item in enumerate(items):
        # بررسی می‌کنیم که آیا آخرین مورد این سطح از درخت است.
        is_last = index == len(items) - 1

        # کاراکتر مناسب برای نمایش شاخه درخت.
        branch = "└── " if is_last else "├── "

        # اضافه کردن نام فایل یا پوشه به خروجی.
        lines.append(f"{prefix}{branch}{item.name}")

        # اگر مورد فعلی پوشه باشد، محتویات آن را هم بررسی می‌کنیم.
        if item.is_dir():
            next_prefix = prefix + ("    " if is_last else "│   ")
            lines.extend(build_tree(item, next_prefix))

    return lines


def main() -> None:
    """
    ورودی:
        ندارد.

    خروجی:
        ندارد؛ ساختار پروژه را در ترمینال نمایش داده و
        داخل فایل map.txt ذخیره می‌کند.
    """

    # ایجاد ساختار اولیه با نام پروژه.
    tree_lines = [f"{PROJECT_ROOT.name}/"]

    # ساخت درخت کامل پروژه.
    tree_lines.extend(build_tree(PROJECT_ROOT))

    # تبدیل خطوط به یک متن واحد.
    tree_content = "\n".join(tree_lines) + "\n"

    # نمایش ساختار در ترمینال.
    print(tree_content)

    # ایجاد یا آپدیت map.txt با حالت write.
    # اگر فایل وجود داشته باشد، محتوای قبلی جایگزین می‌شود.
    MAP_FILE.write_text(tree_content, encoding="utf-8")

    # اعلام موفقیت ذخیره فایل.
    print(f"Map updated: {MAP_FILE}")


if __name__ == "__main__":
    main()