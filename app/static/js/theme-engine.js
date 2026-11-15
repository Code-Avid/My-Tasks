/* ===================================================================
   ThemeEngine — موتور تم رنگی

   ورودی: فقط ۳ رنگ
       bg      رنگ ۱ · پس‌زمینه
       main    رنگ ۲ · اصلی
       accent  رنگ ۳ · تأکیدی
   و حالت (mode): "dark" یا "light"

   خروجی: همه‌ی متغیرهای CSS پروژه (--bg, --card, --text, --n1 ... )
   که روی عنصر داده‌شده (معمولاً <html>) ست می‌شن.

   همه‌ی رنگ‌های پروژه از همین‌جا میان؛ پس با عوض شدن ۳ رنگ، کل پروژه عوض می‌شه.
   این فایل هم برای کل سایت و هم برای «نمونه‌ی زنده» در صفحه‌ی تنظیمات استفاده می‌شه.
   =================================================================== */
(function (global) {
    "use strict";

    var WHITE = [255, 255, 255];
    var BLACK = [0, 0, 0];
    var DARK_INK = [8, 10, 20];
    var LS_MODE = "tm_mode";
    var LS_SIG = "tm_sig";

    var state = { theme: null, mode: "dark" };

    /* ---------------- ابزارهای رنگ ---------------- */
    function clamp(n) { return Math.max(0, Math.min(255, n)); }

    // HEX: #rgb یا #rrggbb (با # یا بدون #)
    function parseHex(input) {
        if (input === null || input === undefined) return null;
        var m = String(input).trim().match(/^#?([0-9a-f]{3}|[0-9a-f]{6})$/i);
        if (!m) return null;
        var h = m[1];
        if (h.length === 3) h = h[0] + h[0] + h[1] + h[1] + h[2] + h[2];
        return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
    }

    // RGB: "12, 34, 56" یا "12 34 56" یا "rgb(12,34,56)"
    function parseRgb(input) {
        if (input === null || input === undefined) return null;
        var m = String(input).trim().match(/^(?:rgb\(\s*)?(\d{1,3})\s*[,\s]\s*(\d{1,3})\s*[,\s]\s*(\d{1,3})\s*\)?$/i);
        if (!m) return null;
        var rgb = [parseInt(m[1], 10), parseInt(m[2], 10), parseInt(m[3], 10)];
        if (rgb[0] > 255 || rgb[1] > 255 || rgb[2] > 255) return null;
        return rgb;
    }

    function toHex(rgb) {
        return "#" + rgb.map(function (c) {
            var h = Math.round(clamp(c)).toString(16);
            return h.length < 2 ? "0" + h : h;
        }).join("");
    }

    function triple(rgb) {
        return rgb.map(function (c) { return Math.round(clamp(c)); }).join(", ");
    }
    function rgb(c) { return "rgb(" + triple(c) + ")"; }
    function rgba(c, a) { return "rgba(" + triple(c) + ", " + a + ")"; }

    function lin(c) {
        c = c / 255;
        return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
    }
    function lum(c) {
        return 0.2126 * lin(c[0]) + 0.7152 * lin(c[1]) + 0.0722 * lin(c[2]);
    }
    function contrast(a, b) {
        var l1 = lum(a), l2 = lum(b);
        if (l1 < l2) { var t = l1; l1 = l2; l2 = t; }
        return (l1 + 0.05) / (l2 + 0.05);
    }
    function mix(a, b, t) {
        return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t];
    }

    // اگه رنگ روی پس‌زمینه خیلی کم‌رنگ باشه، کمی تیره/روشن‌ترش می‌کنیم تا خوانا بمونه
    function ink(color, ref, min) {
        if (contrast(color, ref) >= min) return color;
        var target = lum(ref) > 0.179 ? BLACK : WHITE;
        for (var t = 0.05; t <= 1.0001; t += 0.05) {
            var c = mix(color, target, t);
            if (contrast(c, ref) >= min) return c;
        }
        return target;
    }

    // رنگ متن روی یک سطح رنگی (دکمه‌ی پرشده و ...)
    function onColor(fill) {
        return contrast(fill, DARK_INK) >= contrast(fill, WHITE) ? DARK_INK : WHITE;
    }

    /* ---------------- حالت شب/روز ---------------- */
    function naturalOf(bg) { return lum(bg) < 0.3 ? "dark" : "light"; }

    // حالت طبیعی یک پالت (پس‌زمینه‌ی تیره = شب، روشن = روز)
    function naturalMode(bgHex) {
        return naturalOf(parseHex(bgHex) || [7, 7, 13]);
    }

    // اگه کاربر حالت مخالفِ حالت طبیعی پالت رو بخواد، پس‌زمینه وارونه می‌شه
    function baseFor(bg, mode) {
        if (mode === naturalOf(bg)) return bg;
        return mode === "light" ? mix(bg, WHITE, 0.93) : mix(bg, BLACK, 0.90);
    }

    /* ---------------- محاسبه‌ی همه‌ی متغیرها ---------------- */
    function compute(colors, mode) {
        var bgIn = parseHex(colors.bg) || [7, 7, 13];
        var mainIn = parseHex(colors.main) || [168, 85, 247];
        var accentIn = parseHex(colors.accent) || [0, 229, 255];

        var isDark = mode === "dark";
        var base = baseFor(bgIn, mode);

        var text = mix(isDark ? WHITE : [12, 12, 24], base, 0.10);
        var muted = mix(text, base, 0.34);
        var bg2 = mix(base, isDark ? WHITE : BLACK, 0.06);
        var surface = mix(mix(base, WHITE, isDark ? 0.05 : 0.60), mainIn, 0.16);
        var side = isDark ? mix(base, BLACK, 0.30) : mix(base, WHITE, 0.78);
        var borderSrc = mix(mainIn, text, 0.35);

        // n1 = تأکیدی (دکمه‌ها، لینک فعال)   n2 = اصلی (گرادیان، سطح)
        var n1 = ink(accentIn, base, 3);
        var n2 = ink(mainIn, base, 3);
        // n3 = موفقیت (انجام شد)   n4 = خطر (حذف)  ← معنای ثابت دارن
        var n3 = ink(isDark ? [57, 255, 136] : [22, 163, 74], base, 3);
        var n4 = ink(isDark ? [255, 77, 109] : [225, 29, 72], base, 3);
        var grad = mix(n1, n2, 0.5);

        var vars = {
            "--bg": rgb(base),
            "--bg-2": rgb(bg2),
            "--card": rgba(surface, isDark ? 0.72 : 0.85),
            "--side": rgba(side, isDark ? 0.92 : 0.95),
            "--text": rgb(text),
            "--muted": rgb(muted),
            "--muted-rgb": triple(muted),
            "--border": rgba(borderSrc, isDark ? 0.22 : 0.25),
            "--input": rgba(text, isDark ? 0.06 : 0.05),
            "--n1": triple(n1),
            "--n2": triple(n2),
            "--n3": triple(n3),
            "--n4": triple(n4),
            "--on-n1": rgb(onColor(n1)),
            "--on-n2": rgb(onColor(n2)),
            "--on-n3": rgb(onColor(n3)),
            "--on-grad": rgb(onColor(grad)),
            "--glow": isDark ? "1" : "0.45",
            "--brand-bg": toHex(bgIn),
            "--brand-main": toHex(mainIn),
            "--brand-accent": toHex(accentIn)
        };

        return {
            vars: vars,
            meta: { mainAdjusted: n2 !== mainIn, accentAdjusted: n1 !== accentIn }
        };
    }

    function apply(el, colors, mode) {
        var out = compute(colors, mode);
        for (var k in out.vars) {
            if (Object.prototype.hasOwnProperty.call(out.vars, k)) {
                el.style.setProperty(k, out.vars[k]);
            }
        }
        el.setAttribute("data-bs-theme", mode);
        return out.meta;
    }

    function analyze(colors, mode) { return compute(colors, mode).meta; }

    /* ---------------- راه‌اندازی صفحه ---------------- */
    function boot(theme) {
        var sig = [theme.bg, theme.main, theme.accent].join("|").toLowerCase();
        var mode = null, storedSig = null;
        try {
            mode = localStorage.getItem(LS_MODE);
            storedSig = localStorage.getItem(LS_SIG);
        } catch (e) {}

        // تم عوض شده (یا اولین بار)؛ حالت طبیعی پالت رو بگیر
        if (storedSig !== sig || (mode !== "dark" && mode !== "light")) {
            mode = naturalMode(theme.bg);
            try {
                localStorage.setItem(LS_MODE, mode);
                localStorage.setItem(LS_SIG, sig);
            } catch (e) {}
        }

        state.theme = theme;
        state.mode = mode;
        apply(document.documentElement, theme, mode);
        return mode;
    }

    function setMode(mode) {
        if (mode !== "dark" && mode !== "light") return;
        state.mode = mode;
        try { localStorage.setItem(LS_MODE, mode); } catch (e) {}
        if (state.theme) apply(document.documentElement, state.theme, mode);
    }

    function getMode() { return state.mode; }

    global.ThemeEngine = {
        parseHex: parseHex,
        parseRgb: parseRgb,
        toHex: toHex,
        contrast: contrast,
        naturalMode: naturalMode,
        compute: compute,
        analyze: analyze,
        apply: apply,
        boot: boot,
        setMode: setMode,
        getMode: getMode
    };
})(typeof window !== "undefined" ? window : globalThis);
