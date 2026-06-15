# Hujjat AI — Professional Shartnomalar Generatori

Telegram Mini App va veb-interfeys orqali O'zbekistonda rasmiy shartnomalar, ijara hujjatlari va xizmat aktlarini PDF formatida yaratish.

## Loyiha tuzilmasi

```
HujjatAI-MVP/
├── frontend/          # Statik HTML/CSS/JS
│   ├── index.html
│   ├── config.js      # API manzili (dev/prod)
│   ├── freelance_jismoniy.html
│   ├── individual_legal.html
│   ├── legal_legal.html
│   ├── rental.html
│   ├── act.html
│   └── style.css
├── backend/           # FastAPI + ReportLab PDF
│   ├── main.py
│   ├── config.py
│   ├── schemas.py
│   └── fonts/
├── documents/         # Generatsiya qilingan PDF'lar
├── .env               # Muhit o'zgaruvchilari (git'ga kirmaydi)
├── .env.example
├── requirements.txt
└── README.md
```

## O'rnatish

### 1. Kutubxonalarni o'rnatish

```bash
pip install -r requirements.txt
```

### 2. Muhit o'zgaruvchilarini sozlash

```bash
cp .env.example .env
```

`.env` faylini ochib, kerakli qiymatlarni kiriting:

| O'zgaruvchi | Tavsif |
|-------------|--------|
| `HOST` | Backend host (default: `127.0.0.1`) |
| `PORT` | Backend port (default: `8000`) |
| `FRONTEND_URL` | CORS uchun frontend manzili |
| `BOT_TOKEN` | Telegram bot tokeni (keyinroq) |

## Ishga tushirish (Development)

**Backend** (birinchi terminal):

```bash
cd backend
python main.py
```

**Telegram bot** (ikkinchi terminal):

```bash
cd backend
python bot.py
```

**Frontend** (uchinchi terminal):

```bash
cd frontend
python -m http.server 5500
```

Brauzerda oching: `http://localhost:5500`

## API endpointlar

| Endpoint | Hujjat turi |
|----------|-------------|
| `POST /generate-mobile-app` | Freelance / mobil ilova shartnomasi |
| `POST /generate-individual-legal` | Jismoniy–yuridik shartnoma |
| `POST /generate-legal-legal` | Yuridik–yuridik shartnoma |
| `POST /generate-rental` | Uy ijara shartnomasi |
| `POST /generate-act` | Xizmat ko'rsatish akti |
| `GET /download/{filename}` | PDF yuklab olish |

## Frontend API konfiguratsiyasi

`frontend/config.js` faylida:

- **Development:** `localhost` da ishlaganda → `http://localhost:8000`
- **Production:** boshqa domenlarda → `PROD_API_URL` (bo'sh = relative URL)

Frontend va backend alohida deploy qilinganda `PROD_API_URL` ga backend manzilini yozing:

```javascript
const PROD_API_URL = "https://hujjat-ai-backend.onrender.com";
```

## Deploy

### Frontend (Vercel / Netlify)

1. `frontend/` papkasini deploy qiling
2. Environment variables kerak emas (statik sayt)
3. Alohida backend bo'lsa, `config.js` dagi `PROD_API_URL` ni yangilang

### Backend (Render / Railway)

1. `backend/` papkasini deploy qiling
2. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
3. Environment variables:
   - `FRONTEND_URL` = frontend URL (masalan: `https://hujjat-ai.vercel.app`)
   - `BOT_TOKEN` = Telegram bot tokeni

## Telegram

Bot: [@HujjatAI_Bot](https://t.me/HujjatAI_Bot)

---

© 2026 Hujjat AI
