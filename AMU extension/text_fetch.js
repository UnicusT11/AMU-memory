let lastText = "";
let isInjecting = false;

// ===== Tool：Get current input =====
function getInputBox() {
  const active = document.activeElement;

  if (active) {
    if (active.tagName === "TEXTAREA") return active;
    if (active.getAttribute("contenteditable") === "true") return active;
  }

  return (
    document.querySelector("textarea") ||
    document.querySelector('[contenteditable="true"]')
  );
}

// ===== Tool：Get input text =====
function getInputText(el) {
  if (!el) return "";

  if (el.tagName === "TEXTAREA") {
    return el.value;
  }

  if (el.getAttribute("contenteditable") === "true") {
    return el.innerText;
  }

  return "";
}

// ===== Tool：Set input text =====
function setInputText(el, text) {
  if (!el) return;

  if (el.tagName === "TEXTAREA") {
    el.value = text;
    el.dispatchEvent(new Event("input", { bubbles: true }));
    el.dispatchEvent(new Event("change", { bubbles: true }));
    return;
  }

  if (el.getAttribute("contenteditable") === "true") {
    el.innerText = text;
    el.dispatchEvent(new Event("input", { bubbles: true }));
  }
}

// ===== Insert the returned content at the top of the input box =====
function prependToInputBox(insertText) {
  const input = getInputBox();
  if (!input || !insertText) return;

  isInjecting = true;

  const oldText = getInputText(input).trim();
  const newText = `${insertText}\n\n${oldText}`.trim();

  setInputText(input, newText);

  setTimeout(() => {
    isInjecting = false;
  }, 100);
}

// ===== Get the current mode =====
function getMode() {
  return new Promise((resolve) => {
    chrome.storage.local.get(["mode"], (res) => {
      resolve(res.mode || "chat");
    });
  });
}

// ===== Send to API =====
async function sendToAPI(text) {
  const mode = await getMode();

  // chat mode：Skip without retrieving or storing
  if (mode === "chat") {
    console.log("🟡 chat mode：Skip API");
    return;
  }

  chrome.storage.local.get(["apiUrl"], async (res) => {
    const apiUrl = res.apiUrl;

    if (!apiUrl) {
      console.warn("⚠️ Unconfigured apiUrl");
      return;
    }

    try {
      const response = await fetch(apiUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          text: text,
          mode: mode,
          time: Date.now()
        })
      });

      const data = await response.json();
      console.log("✅ API return:", data);

      // retrieve mode：Insert the returned prompt at the top of the input box
      if (mode === "retrieve" && data?.data) {
        prependToInputBox(data.data);
      }

      // save mode：Call the API only; do not modify the input box
      if (mode === "save") {
        console.log("💾 save mode：sent to API");
      }

    } catch (err) {
      console.error("❌ API error:", err);
    }
  });
}

// ===== Save to local=====
function saveToLocal(text) {
  chrome.storage.local.get(["history"], (res) => {
    const history = res.history || [];

    history.push({
      text: text,
      time: new Date().toLocaleString()
    });

    chrome.storage.local.set({ history });

    console.log("✅ Saved to local:", text);
  });
}

// ===== Unified sending logic =====
function handleSend() {
  if (isInjecting) return;

  const input = getInputBox();
  const text = getInputText(input).trim();

  if (!text) return;

  // Prevent duplicate triggers
  if (text === lastText) return;
  lastText = text;

  console.log("📩 Send to catch:", text);

  sendToAPI(text);
}

// ===== Core：Listening Alt + C =====
function bindListener() {
  document.addEventListener("keydown", (e) => {
    if (e.altKey && e.key.toLowerCase() === "c") {
      setTimeout(handleSend, 50);
    }
  });

  console.log("✅ Input listening is running");
}

// ===== Start =====
const observer = new MutationObserver(() => {
  if (!window.__input_logger_started__) {
    window.__input_logger_started__ = true;
    bindListener();
    chrome.storage.local.get(null, console.log);
  }
});

observer.observe(document.body, {
  childList: true,
  subtree: true
});