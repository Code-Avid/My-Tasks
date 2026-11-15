/* صفحه‌ی تنظیمات: تب‌ها + ویرایشگر ۳ رنگ (HEX / RGB / انتخاب‌گر) + نمونه‌ی زنده */
(function () {
    "use strict";
    var TE = window.ThemeEngine;

    /* ---------- تب‌ها ---------- */
    var tabs = document.querySelectorAll(".set-tab");
    var panels = document.querySelectorAll(".set-panel");
    tabs.forEach(function (tab) {
        tab.addEventListener("click", function () {
            var name = tab.getAttribute("data-tab");
            tabs.forEach(function (t) { t.classList.toggle("active", t === tab); });
            panels.forEach(function (p) { p.classList.toggle("active", p.id === "tab-" + name); });
        });
    });

    /* ---------- ویرایشگر رنگ ---------- */
    var form = document.getElementById("themeForm");
    var preview = document.getElementById("themePreview");
    var note = document.getElementById("previewNote");
    var nameInput = document.getElementById("themeName");
    if (!form || !preview || !TE) return;

    var ROLES = ["bg", "main", "accent"];
    var ROLE_LABELS = { main: "رنگ اصلی", accent: "رنگ تأکیدی" };
    var rows = {};
    var current = {};   // نقش → [r, g, b]
    var initial = {};   // برای دکمه‌ی بازنشانی
    var manualMode = false;
    var previewMode = "dark";
    var modeBtns = document.querySelectorAll("[data-pmode]");

    ROLES.forEach(function (role) {
        var el = form.querySelector('.color-row[data-role="' + role + '"]');
        rows[role] = {
            picker: el.querySelector(".cr-picker"),
            hex: el.querySelector(".cr-hex"),
            rgb: el.querySelector(".cr-rgb")
        };
        var c = TE.parseHex(rows[role].hex.value) || [128, 128, 128];
        current[role] = c;
        initial[role] = c.slice();
    });

    // مقدار هر ۳ ورودی (انتخاب‌گر، HEX، RGB) رو با رنگ فعلی هماهنگ می‌کنه
    // source = ورودی‌ای که کاربر الان داره توش تایپ می‌کنه (دست نمی‌زنیم بهش)
    function syncRow(role, source) {
        var r = rows[role], c = current[role];
        if (source !== "picker") r.picker.value = TE.toHex(c);
        if (source !== "hex") r.hex.value = TE.toHex(c);
        if (source !== "rgb") r.rgb.value = c.join(", ");
        if (source !== "hex") r.hex.classList.remove("bad");
        if (source !== "rgb") r.rgb.classList.remove("bad");
    }

    function colorsHex() {
        return {
            bg: TE.toHex(current.bg),
            main: TE.toHex(current.main),
            accent: TE.toHex(current.accent)
        };
    }

    // نمونه رو با ۳ رنگ فعلی دوباره می‌سازه
    function render() {
        var colors = colorsHex();
        if (!manualMode) previewMode = TE.naturalMode(colors.bg);
        var meta = TE.apply(preview, colors, previewMode);

        modeBtns.forEach(function (b) {
            b.classList.toggle("active", b.getAttribute("data-pmode") === previewMode);
        });

        var adjusted = [];
        if (meta.mainAdjusted) adjusted.push(ROLE_LABELS.main);
        if (meta.accentAdjusted) adjusted.push(ROLE_LABELS.accent);
        note.textContent = adjusted.length
            ? adjusted.join(" و ") + " روی این پس‌زمینه کم‌رنگ بود؛ برای خوانایی دکمه‌ها و متن‌ها کمی تیره/روشن‌تر نمایش داده می‌شه."
            : "";
    }

    ROLES.forEach(function (role) {
        var r = rows[role];

        r.picker.addEventListener("input", function () {
            var c = TE.parseHex(r.picker.value);
            if (!c) return;
            current[role] = c;
            syncRow(role, "picker");
            render();
        });

        r.hex.addEventListener("input", function () {
            var c = TE.parseHex(r.hex.value);
            if (!c) { r.hex.classList.add("bad"); return; }
            current[role] = c;
            syncRow(role, "hex");
            render();
        });
        r.hex.addEventListener("blur", function () { syncRow(role); });

        r.rgb.addEventListener("input", function () {
            var c = TE.parseRgb(r.rgb.value);
            if (!c) { r.rgb.classList.add("bad"); return; }
            current[role] = c;
            syncRow(role, "rgb");
            render();
        });
        r.rgb.addEventListener("blur", function () { syncRow(role); });
    });

    // دکمه‌های شب/روز داخل خودِ نمونه
    modeBtns.forEach(function (b) {
        b.addEventListener("click", function () {
            manualMode = true;
            previewMode = b.getAttribute("data-pmode");
            render();
        });
    });

    // دکمه‌ی «ویرایش» روی هر تم: رنگ‌هاش رو میاره توی ویرایشگر
    document.querySelectorAll(".js-load").forEach(function (btn) {
        btn.addEventListener("click", function () {
            var map = {
                bg: btn.getAttribute("data-bg"),
                main: btn.getAttribute("data-main"),
                accent: btn.getAttribute("data-accent")
            };
            ROLES.forEach(function (role) {
                var c = TE.parseHex(map[role]);
                if (c) { current[role] = c; syncRow(role); }
            });
            nameInput.value = (btn.getAttribute("data-name") || "") + " (کپی)";
            manualMode = false;
            render();
            form.scrollIntoView({ behavior: "smooth", block: "start" });
        });
    });

    // بازنشانی به رنگ‌های تم فعال
    var resetBtn = document.getElementById("resetBtn");
    if (resetBtn) {
        resetBtn.addEventListener("click", function () {
            ROLES.forEach(function (role) {
                current[role] = initial[role].slice();
                syncRow(role);
            });
            nameInput.value = "";
            manualMode = false;
            render();
        });
    }

    // قبل از ارسال، فیلدهای HEX رو استاندارد می‌کنیم (#rrggbb)
    form.addEventListener("submit", function () {
        ROLES.forEach(function (role) { rows[role].hex.value = TE.toHex(current[role]); });
    });

    ROLES.forEach(function (role) { syncRow(role); });
    render();
})();
