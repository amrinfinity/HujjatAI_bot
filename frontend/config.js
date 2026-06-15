// Development (lokal)
const DEV_API_URL = "http://localhost:8000";

// Production: backend deploy qilingandan keyin shu yerga URL yozing
// Masalan: "https://hujjat-ai-backend.onrender.com"
const PROD_API_URL = "https://hujjat-ai-backend.onrender.com";

const API_BASE_URL =
  window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
    ? DEV_API_URL
    : PROD_API_URL;

window.API_BASE_URL = API_BASE_URL;
