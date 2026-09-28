let currentMode = "chat";

// ===== Update button's highlight =====
function updateModeUI(mode) {
  document.querySelectorAll(".mode-btn").forEach((btn) => {
    if (btn.dataset.mode === mode) {
      btn.classList.add("active");
    } else {
      btn.classList.remove("active");
    }
  });
}

// ===== Restore system when Page loading =====
document.addEventListener("DOMContentLoaded", () => {
  chrome.storage.local.get(["apiUrl", "mode"], (res) => {
    if (res.apiUrl) {
      document.getElementById("apiUrl").value = res.apiUrl;
    }

    currentMode = res.mode || "chat";
    updateModeUI(currentMode);
  });
});

// ===== Mode button =====
document.querySelectorAll(".mode-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    currentMode = btn.dataset.mode;
    updateModeUI(currentMode);
  });
});

// ===== SAVE =====
document.getElementById("saveBtn").addEventListener("click", () => {
  const url = document.getElementById("apiUrl").value.trim();

  chrome.storage.local.set(
    {
      apiUrl: url,
      mode: currentMode
    },
    () => {
      document.getElementById("status").innerText =
        `✅ saved（mode: ${currentMode}）`;
    }
  );
});