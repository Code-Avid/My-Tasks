CREATE TABLE IF NOT EXISTS projects (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    is_archived INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- دسته‌بندی تسک‌های رندم. color: عدد 1 تا 4 (نگاشت به --n1 تا --n4 در CSS)
CREATE TABLE IF NOT EXISTS categories (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT    NOT NULL,
    color      INTEGER NOT NULL DEFAULT 1,
    created_at TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- kind: daily | weekly | project | random
-- weekdays: فقط برای weekly. مثل "0,2,4" (0=شنبه ... 6=جمعه)
-- category_id: فقط برای random
CREATE TABLE IF NOT EXISTS tasks (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    title        TEXT    NOT NULL,
    kind         TEXT    NOT NULL DEFAULT 'random',
    weekdays     TEXT    NOT NULL DEFAULT '',
    project_id   INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    category_id  INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    is_done      INTEGER NOT NULL DEFAULT 0,
    created_at   TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS subtasks (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id      INTEGER NOT NULL,
    title        TEXT    NOT NULL,
    is_done      INTEGER NOT NULL DEFAULT 0,
    completed_at TEXT,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

-- ثبت انجام‌شدن تسک‌های تکراری (روزانه/هفتگی) به‌ازای هر روز
CREATE TABLE IF NOT EXISTS task_logs (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id   INTEGER NOT NULL,
    done_date TEXT    NOT NULL,
    UNIQUE (task_id, done_date),
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

-- تم‌های رنگی. هر تم = ۳ رنگ (HEX):
--   c_bg = پس‌زمینه ، c_main = رنگ اصلی ، c_accent = رنگ تأکیدی
-- slug: فقط برای تم‌های پیش‌فرض (is_builtin=1). تم‌های کاستوم slug ندارن (NULL).
CREATE TABLE IF NOT EXISTS themes (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    slug       TEXT UNIQUE,
    name       TEXT    NOT NULL,
    c_bg       TEXT    NOT NULL,
    c_main     TEXT    NOT NULL,
    c_accent   TEXT    NOT NULL,
    is_builtin INTEGER NOT NULL DEFAULT 0,
    created_at TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- تنظیمات عمومی به‌صورت کلید/مقدار (مثلاً active_theme_id)
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
