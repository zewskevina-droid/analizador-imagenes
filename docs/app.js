const form = document.querySelector("#analyzeForm");
const imageInput = document.querySelector("#imageInput");
const promptInput = document.querySelector("#promptInput");
const messages = document.querySelector("#messages");
const sendButton = document.querySelector("#sendButton");
const fileLabel = document.querySelector("#fileLabel");
const settingsButton = document.querySelector("#settingsButton");
const settingsPanel = document.querySelector("#settingsPanel");
const backendUrlInput = document.querySelector("#backendUrl");
const saveBackend = document.querySelector("#saveBackend");

const backendKey = "image-analyzer-backend-url";

function defaultBackendUrl() {
  const localHosts = ["localhost", "127.0.0.1"];
  if (localHosts.includes(window.location.hostname)) {
    return window.location.origin;
  }
  return localStorage.getItem(backendKey) || "";
}

function getBackendUrl() {
  return (localStorage.getItem(backendKey) || defaultBackendUrl()).replace(/\/$/, "");
}

function addMessage(role, text, imageUrl = null) {
  const article = document.createElement("article");
  article.className = `message ${role}`;

  const paragraph = document.createElement("p");
  paragraph.textContent = text;
  article.append(paragraph);

  if (imageUrl) {
    const image = document.createElement("img");
    image.className = "preview";
    image.src = imageUrl;
    image.alt = "Imagen seleccionada";
    article.append(image);
  }

  messages.append(article);
  messages.scrollTop = messages.scrollHeight;
  return article;
}

function setLoading(isLoading) {
  sendButton.disabled = isLoading;
  imageInput.disabled = isLoading;
  promptInput.disabled = isLoading;
  sendButton.textContent = isLoading ? "Analizando..." : "Analizar";
}

imageInput.addEventListener("change", () => {
  const file = imageInput.files?.[0];
  fileLabel.textContent = file ? file.name : "Elegir imagen";
});

settingsButton.addEventListener("click", () => {
  settingsPanel.hidden = !settingsPanel.hidden;
  backendUrlInput.value = getBackendUrl();
});

saveBackend.addEventListener("click", () => {
  const value = backendUrlInput.value.trim().replace(/\/$/, "");
  if (value) {
    localStorage.setItem(backendKey, value);
  } else {
    localStorage.removeItem(backendKey);
  }
  settingsPanel.hidden = true;
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const file = imageInput.files?.[0];
  if (!file) {
    addMessage("error", "Selecciona una imagen antes de analizar.");
    return;
  }

  const backendUrl = getBackendUrl();
  if (!backendUrl) {
    settingsPanel.hidden = false;
    addMessage("error", "Configura primero la URL del backend Python.");
    return;
  }

  const prompt = promptInput.value.trim() || "Describe esta imagen con detalle.";
  const previewUrl = URL.createObjectURL(file);
  addMessage("user", prompt, previewUrl);

  const pendingMessage = addMessage("assistant", "Estoy revisando la imagen...");
  const data = new FormData();
  data.append("image", file);
  data.append("prompt", prompt);

  try {
    setLoading(true);
    const response = await fetch(`${backendUrl}/api/analyze`, {
      method: "POST",
      body: data,
    });

    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(payload.detail || "No se pudo analizar la imagen.");
    }

    pendingMessage.querySelector("p").textContent = payload.analysis;
  } catch (error) {
    pendingMessage.className = "message error";
    pendingMessage.querySelector("p").textContent = error.message;
  } finally {
    setLoading(false);
    URL.revokeObjectURL(previewUrl);
  }
});

