(function () {
    const root = document.documentElement;
    const themeBtn = document.getElementById("themeToggle");
    const themeIcon = document.getElementById("themeIcon");
    const themeLabel = document.getElementById("themeLabel");
    const sidebar = document.getElementById("sidebar");
    const menuBtn = document.getElementById("menuToggle");

    /* ---------- حالت شب / روز ----------
       رنگ‌ها رو موتور تم (theme-engine.js) از روی ۳ رنگِ تم فعال می‌سازه.
       اینجا فقط دکمه رو وصل می‌کنیم. */
    function currentMode() {
        if (window.ThemeEngine) return window.ThemeEngine.getMode();
        return root.getAttribute("data-bs-theme") || "dark";
    }

    function refreshThemeButton(mode) {
        if (mode === "dark") {
            themeIcon.className = "bi bi-sun-fill";
            themeLabel.textContent = "حالت روز";
        } else {
            themeIcon.className = "bi bi-moon-stars-fill";
            themeLabel.textContent = "حالت شب";
        }
    }

    refreshThemeButton(currentMode());

    themeBtn.addEventListener("click", function () {
        const next = currentMode() === "dark" ? "light" : "dark";
        if (window.ThemeEngine) {
            window.ThemeEngine.setMode(next);
        } else {
            root.setAttribute("data-bs-theme", next);
        }
        refreshThemeButton(next);
    });

    /* ---------- منوی موبایل ---------- */
    menuBtn.addEventListener("click", function (e) {
        e.stopPropagation();
        sidebar.classList.toggle("open");
    });

    document.addEventListener("click", function (e) {
        if (!sidebar.contains(e.target)) sidebar.classList.remove("open");
    });

    /* ---------- فرم افزودن: انتخاب نوع تسک (فقط صفحه‌ی امروز) ---------- */
    const addForm = document.getElementById("addForm");
    const daysPicker = document.getElementById("daysPicker");
    const catPicker = document.getElementById("catPicker");

    if (addForm && daysPicker) {
        const kindInputs = addForm.querySelectorAll('input[name="kind"]');
        const dayBoxes = daysPicker.querySelectorAll('input[name="weekdays"]');

        function currentKind() {
            const sel = addForm.querySelector('input[name="kind"]:checked');
            return sel ? sel.value : "random";
        }

        function syncKind() {
            const kind = currentKind();
            // روزهای هفته فقط برای «هفتگی»
            daysPicker.classList.toggle("is-hidden", kind !== "weekly");
            // انتخاب دسته فقط برای «رندم»
            if (catPicker) catPicker.classList.toggle("is-hidden", kind !== "random");
        }

        kindInputs.forEach(function (r) { r.addEventListener("change", syncKind); });
        syncKind();

        // دکمه‌های میان‌بر (فرد / زوج / همه / پاک)
        daysPicker.querySelectorAll(".preset-btn").forEach(function (btn) {
            btn.addEventListener("click", function () {
                const wanted = btn.dataset.days.split(",").filter(Boolean);
                dayBoxes.forEach(function (box) {
                    box.checked = wanted.indexOf(box.value) !== -1;
                });
            });
        });

        // برای تسک هفتگی حداقل یک روز لازمه
        addForm.addEventListener("submit", function (e) {
            if (currentKind() === "weekly") {
                const any = Array.prototype.some.call(dayBoxes, function (b) { return b.checked; });
                if (!any) {
                    e.preventDefault();
                    alert("حداقل یک روز از هفته رو انتخاب کن.");
                }
            }
        });
    }
})();
