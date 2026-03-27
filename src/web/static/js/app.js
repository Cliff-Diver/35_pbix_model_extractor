/**
 * PBIX Model Extractor – Frontend interakce
 *
 * Obsluhuje upload, výběr dotazů, odesílání analýzy a přepínání diff režimů.
 */

document.addEventListener("DOMContentLoaded", () => {
    initUploadForm();
    initQuerySelection();
    initAnalyzeForm();
    initDiffModeToggle();
    initFileUploadPreview();
});


/* ========================================
   Upload PBIX souboru
   ======================================== */

function initUploadForm() {
    const form = document.getElementById("upload-form");
    if (!form) return;

    const dropZone = document.getElementById("drop-zone");
    const fileInput = document.getElementById("pbix-file");
    const fileInfo = document.getElementById("file-info");
    const fileName = document.getElementById("file-name");
    const uploadBtn = document.getElementById("upload-btn");
    const uploadText = document.getElementById("upload-text");
    const uploadSpinner = document.getElementById("upload-spinner");
    const errorDiv = document.getElementById("upload-error");

    // Drag & drop podpora
    if (dropZone) {
        dropZone.addEventListener("dragover", (e) => {
            e.preventDefault();
            dropZone.classList.add("drag-over");
        });

        dropZone.addEventListener("dragleave", () => {
            dropZone.classList.remove("drag-over");
        });

        dropZone.addEventListener("drop", (e) => {
            e.preventDefault();
            dropZone.classList.remove("drag-over");
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                fileInput.files = files;
                showFileName(files[0].name);
            }
        });
    }

    // Zobrazení názvu souboru při výběru
    if (fileInput) {
        fileInput.addEventListener("change", () => {
            if (fileInput.files.length > 0) {
                showFileName(fileInput.files[0].name);
            }
        });
    }

    function showFileName(name) {
        if (fileInfo && fileName) {
            fileName.textContent = name;
            fileInfo.style.display = "block";
        }
    }

    // Odeslání formuláře přes fetch API
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        if (errorDiv) {
            errorDiv.style.display = "none";
        }

        if (!fileInput.files.length) {
            showError("Vyberte PBIX soubor.");
            return;
        }

        // Zobrazení loading stavu
        uploadBtn.disabled = true;
        uploadBtn.setAttribute("aria-busy", "true");
        if (uploadText) {
            uploadText.style.display = "none";
        }
        if (uploadSpinner) {
            uploadSpinner.style.display = "inline-block";
        }

        const formData = new FormData();
        formData.append("file", fileInput.files[0]);

        try {
            const response = await fetch("/upload", { method: "POST", body: formData });
            const data = await response.json();

            if (!response.ok) {
                showError(data.detail || "Chyba při nahrávání souboru.");
                return;
            }

            // Přesměrování na stránku s dotazy
            window.location.href = `/queries/${data.session_id}`;
        } catch (err) {
            showError("Chyba při komunikaci se serverem.");
        } finally {
            uploadBtn.disabled = false;
            uploadBtn.setAttribute("aria-busy", "false");
            if (uploadText) {
                uploadText.style.display = "inline";
            }
            if (uploadSpinner) {
                uploadSpinner.style.display = "none";
            }
        }
    });

    function showError(message) {
        if (!errorDiv) {
            return;
        }
        errorDiv.textContent = message;
        errorDiv.style.display = "block";
    }
}


/* ========================================
   Výběr dotazů (Select All / Deselect All)
   ======================================== */

function initQuerySelection() {
    const selectAllBtn = document.getElementById("select-all-btn");
    const deselectAllBtn = document.getElementById("deselect-all-btn");

    // Helper – aktualizuje globální čítač z inline skriptu v šabloně
    function triggerCounterUpdate() {
        if (typeof updateSelectionCount === "function") {
            updateSelectionCount();
        }
    }

    if (selectAllBtn) {
        selectAllBtn.addEventListener("click", () => {
            document.querySelectorAll(".query-checkbox").forEach(cb => { cb.checked = true; });
            triggerCounterUpdate();
        });
    }

    if (deselectAllBtn) {
        deselectAllBtn.addEventListener("click", () => {
            document.querySelectorAll(".query-checkbox").forEach(cb => { cb.checked = false; });
            triggerCounterUpdate();
        });
    }
}


/* ========================================
   Analýza dotazů – odeslání na API
   ======================================== */

function initAnalyzeForm() {
    // Tlačítko je mimo skrytý formulář – nasloucháme na click, ne na form submit
    const analyzeBtn = document.getElementById("analyze-btn");
    if (!analyzeBtn) return;

    const errorDiv = document.getElementById("analyze-error");

    analyzeBtn.addEventListener("click", async () => {
        if (errorDiv) errorDiv.style.display = "none";

        // Získání vybraných dotazů
        const selectedIds = Array.from(document.querySelectorAll(".query-checkbox:checked"))
            .map(cb => cb.value);

        if (selectedIds.length === 0) {
            showError("Vyberte alespoň jeden dotaz.");
            return;
        }

        // Nastavení vybraných ID do skrytého pole
        document.getElementById("selected-query-ids").value = selectedIds.join(",");

        // Loading stav přes aria-busy (Pico CSS spinner)
        analyzeBtn.disabled = true;
        analyzeBtn.setAttribute("aria-busy", "true");

        // Sestavení FormData ručně – instrukce jsou mimo skrytý formulář
        const form = document.getElementById("analyze-form");
        const formData = new FormData(form);

        // Přidání instruction-files z panelu instrukcí
        const instrFiles = document.getElementById("instruction-files");
        if (instrFiles && instrFiles.files.length > 0) {
            for (const file of instrFiles.files) {
                formData.append("instruction_files", file);
            }
        }

        // Přidání inline textu instrukcí
        const instrText = document.getElementById("instructions-text");
        if (instrText && instrText.value.trim()) {
            formData.append("instructions_text", instrText.value.trim());
        }

        try {
            const response = await fetch("/analyze", { method: "POST", body: formData });
            const data = await response.json();

            if (!response.ok) {
                showError(data.detail || "Chyba při analýze.");
                return;
            }

            if (data.error) {
                showError(data.error);
                return;
            }

            // Přesměrování na stránku s diffem
            window.location.href = `/diff/${data.session_id}`;
        } catch (err) {
            showError("Chyba při komunikaci se serverem.");
        } finally {
            analyzeBtn.disabled = false;
            analyzeBtn.setAttribute("aria-busy", "false");
        }
    });

    function showError(message) {
        if (errorDiv) {
            errorDiv.textContent = message;
            errorDiv.style.display = "block";
        }
    }
}


/* ========================================
   Přepínání unified / side-by-side diff
   ======================================== */

function initDiffModeToggle() {
    const diffPage = document.querySelector("[data-diff-page]");
    if (!diffPage) return;

    const buttons = document.querySelectorAll(".mode-toggle-btn");
    const fontSizeInput = document.getElementById("diff-font-size");
    const fontSizeValue = document.getElementById("diff-font-size-value");
    const showEmptyLinesInput = document.getElementById("diff-show-empty-lines");
    const wideLayoutInput = document.getElementById("diff-wide-layout");

    const storageKeys = {
        mode: "pbix-diff-mode",
        fontSize: "pbix-diff-font-size",
        showEmptyLines: "pbix-diff-show-empty-lines",
        wideLayout: "pbix-diff-wide-layout",
    };

    function loadSetting(key, fallback) {
        try {
            const value = window.localStorage.getItem(key);
            return value === null ? fallback : value;
        } catch (_err) {
            return fallback;
        }
    }

    function saveSetting(key, value) {
        try {
            window.localStorage.setItem(key, value);
        } catch (_err) {
            // Local storage nemusí být dostupné, UI ale funguje dál.
        }
    }

    function applyMode(mode) {
        const activeMode = mode === "unified" ? "unified" : "side-by-side";

        buttons.forEach(btn => {
            btn.classList.toggle("active", btn.dataset.mode === activeMode);
        });

        document.querySelectorAll(".diff-side-by-side").forEach(el => {
            el.style.display = activeMode === "side-by-side" ? "block" : "none";
        });
        document.querySelectorAll(".diff-unified").forEach(el => {
            el.style.display = activeMode === "unified" ? "block" : "none";
        });

        saveSetting(storageKeys.mode, activeMode);
    }

    function applyFontSize(size) {
        const clampedSize = Math.min(18, Math.max(11, Number(size) || 13));
        const lineHeight = clampedSize >= 16 ? 1.55 : clampedSize <= 12 ? 1.35 : 1.45;

        diffPage.style.setProperty("--diff-font-size", `${clampedSize}px`);
        diffPage.style.setProperty("--diff-line-height", String(lineHeight));

        if (fontSizeInput) {
            fontSizeInput.value = String(clampedSize);
        }
        if (fontSizeValue) {
            fontSizeValue.value = `${clampedSize} px`;
            fontSizeValue.textContent = `${clampedSize} px`;
        }

        saveSetting(storageKeys.fontSize, String(clampedSize));
    }

    function applyEmptyLines(showEmptyLines) {
        const enabled = Boolean(showEmptyLines);
        diffPage.dataset.showEmptyLines = enabled ? "true" : "false";
        if (showEmptyLinesInput) {
            showEmptyLinesInput.checked = enabled;
        }
        saveSetting(storageKeys.showEmptyLines, String(enabled));
    }

    function applyWideLayout(useWideLayout) {
        const enabled = Boolean(useWideLayout);
        document.body.classList.toggle("diff-layout-wide", enabled);
        if (wideLayoutInput) {
            wideLayoutInput.checked = enabled;
        }
        saveSetting(storageKeys.wideLayout, String(enabled));
    }

    const initialMode = loadSetting(storageKeys.mode, "side-by-side");
    const initialFontSize = loadSetting(storageKeys.fontSize, fontSizeInput ? fontSizeInput.value : "13");
    const initialShowEmptyLines = loadSetting(storageKeys.showEmptyLines, "false") === "true";
    const initialWideLayout = loadSetting(storageKeys.wideLayout, "true") !== "false";

    applyMode(initialMode);
    applyFontSize(initialFontSize);
    applyEmptyLines(initialShowEmptyLines);
    applyWideLayout(initialWideLayout);

    buttons.forEach(btn => {
        btn.addEventListener("click", () => {
            applyMode(btn.dataset.mode);
        });
    });

    if (fontSizeInput) {
        fontSizeInput.addEventListener("input", () => {
            applyFontSize(fontSizeInput.value);
        });
    }

    if (showEmptyLinesInput) {
        showEmptyLinesInput.addEventListener("change", () => {
            applyEmptyLines(showEmptyLinesInput.checked);
        });
    }

    if (wideLayoutInput) {
        wideLayoutInput.addEventListener("change", () => {
            applyWideLayout(wideLayoutInput.checked);
        });
    }
}


/* ========================================
   Náhled nahraných markdown souborů
   ======================================== */

function initFileUploadPreview() {
    const fileInput = document.getElementById("instruction-files");
    const listDiv = document.getElementById("uploaded-files-list");
    if (!fileInput || !listDiv) return;

    fileInput.addEventListener("change", () => {
        listDiv.innerHTML = "";
        if (fileInput.files.length > 0) {
            const ul = document.createElement("ul");
            for (const file of fileInput.files) {
                const li = document.createElement("li");
                li.textContent = file.name;
                ul.appendChild(li);
            }
            listDiv.appendChild(ul);
        }
    });
}
