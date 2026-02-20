# 🎮 SteamSense

> Predictor ML inteligente para encontrar el momento óptimo de comprar juegos en Steam. 
> Sincroniza tu librería de Steam, analiza históricos de precios y obtén recomendaciones personalizadas.

## ✨ Características

- 🔐 **Autenticación con Steam** - Sincroniza tu perfil y librería automáticamente
- 💰 **Historial de Precios** - Analiza tendencias de precios en tiempo real
- 🤖 **Predicción ML** - Modelo GradientBoosting que predice cuándo es el mejor momento para comprar
- 📊 **Dashboard Personal** - Controla tu librería, wishlist y recomendaciones
- 🎯 **Recomendaciones Personalizadas** - Basadas en tus juegos y patrones de compra
- 🔄 **Sincronización Automática** - Mantén tus datos siempre actualizados

---

## 📚 Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| **Backend** | FastAPI + Python 3.11+ |
| **Base de datos** | DuckDB (archivo local) |
| **Autenticación** | Steam OpenID + JWT |
| **Datos externos** | Steam Web API + IsThereAnyDeal API |
| **ML** | scikit-learn (GradientBoosting) |
| **Frontend** | Next.js 14 + React 18 + TypeScript + Tailwind CSS |
| **Deploy** | Render.com |

---

## 📁 Estructura del Proyecto

```
steamsense/
├── backend/
│   ├── src/
│   │   ├── api/              ← Clientes de APIs (Steam, IsThereAnyDeal)
│   │   │   ├── client.py
│   │   │   ├── steam_auth.py    ← Autenticación OpenID + JWT
│   │   │   ├── steam_client.py  ← Cliente Steam Web API
│   │   │   └── schemas.py
│   │   ├── db/               ← DuckDB: tablas, queries, conexión
│   │   │   ├── connection.py
│   │   │   ├── models.py
│   │   │   ├── queries.py
│   │   │   └── user_queries.py
│   │   ├── ml/               ← Features, modelo, training
│   │   │   ├── model.py
│   │   │   ├── features.py
│   │   │   └── train.py
│   │   ├── routes/           ← Endpoints FastAPI
│   │   │   ├── games.py
│   │   │   ├── auth.py          ← Login de Steam
│   │   │   ├── user.py          ← Librería, wishlist, recomendaciones
│   │   │   ├── prices.py
│   │   │   ├── predict.py
│   │   │   ├── sync.py
│   │   │   └── stats.py
│   │   └── services/         ← Lógica de negocio
│   │       ├── sync_service.py
│   │       ├── predict_service.py
│   │       └── price_service.py
│   ├── main.py               ← Punto de entrada FastAPI
│   ├── config.py             ← Configuración (dotenv)
│   ├── requirements.txt
│   └── data/
│       └── steamsense.duckdb ← Base de datos (ignorada en git)
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx         ← Landing page
│   │   │   ├── dashboard/       ← Dashboard personal (autenticado)
│   │   │   ├── explore/         ← Explorar juegos
│   │   │   └── game/[id]/       ← Detalle de juego
│   │   ├── components/          ← Componentes reutilizables
│   │   │   ├── Navbar.tsx
│   │   │   ├── GameCard.tsx
│   │   │   ├── PriceChart.tsx
│   │   │   ├── PriceHistoryTable.tsx
│   │   │   ├── NextSalePredictor.tsx
│   │   │   └── ...
│   │   └── lib/
│   │       ├── api.ts          ← Cliente HTTP
│   │       ├── auth.ts         ← Lógica de autenticación
│   │       └── types.ts
│   ├── package.json
│   ├── tailwind.config.js
│   └── tsconfig.json
│
├── render.yaml               ← Configuración de deploy
├── .env.example              ← Variables de entorno
└── README.md
```

---

## 🚀 Quick Start

### Backend

```bash
# 1. Navegar al backend
cd backend

# 2. Crear entorno virtual
python -m venv .venv

# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Edita .env y agrega:
# - ITAD_API_KEY (IsThereAnyDeal)
# - STEAM_API_KEY (Steam Web API)
# - JWT_SECRET (para tokens)

# 5. Iniciar servidor
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
# 1. Navegar al frontend
cd frontend

# 2. Instalar dependencias
npm install

# 3. Crear archivo .env.local
# NEXT_PUBLIC_API_URL=http://localhost:8000

# 4. Desarrollo
npm run dev
# Accede a http://localhost:3000
```

---

## 🔐 Autenticación con Steam

El proyecto soporta login con Steam OpenID + JWT:

```bash
# 1. Click en "Login con Steam" en el frontend
# 2. Se redirige a Steam para autorizar
# 3. Steam retorna al callback con openid.sig
# 4. Backend valida y genera JWT
# 5. JWT se almacena en localStorage y se usa en headers: Authorization: Bearer <token>
```

Endpoints de autenticación:
```
POST   /auth/steam/login        Inicia OpenID con Steam
GET    /auth/steam/callback     Recibe respuesta de Steam, crea JWT
POST   /auth/logout             Logout (frontend solo)
GET    /me/library              Obtiene librería sincronizada
POST   /me/library/sync         Sincroniza librería desde Steam
GET    /me/wishlist             Obtiene wishlist
GET    /me/recommendations      Obtiene recomendaciones personalizadas
```

---

## 📡 API Endpoints Principales

### 🎮 Juegos
```
GET    /games/search?q=...      Buscar juegos
GET    /games/{game_id}         Info completa de un juego
GET    /games/top               Top juegos más vendidos
```

### 💰 Precios
```
GET    /prices/{game_id}/history    Historial de precios
GET    /prices/{game_id}/stats      Estadísticas (min, max, avg)
GET    /prices/{game_id}/forecast   Proyección de próximo descuento
```

### 🤖 Predicciones
```
GET    /predict/{game_id}       Predicción: BUY, WAIT, WATCH
GET    /predict/batch?appids=   Múltiples predicciones
```

### 🔄 Sincronización
```
POST   /sync/game/{appid}       Sincronizar un juego específico
POST   /sync/top?top_n=200      Sincronizar top N juegos
POST   /sync/user/{steam_id}    Sincronizar librería de usuario
```

### 📊 Estadísticas
```
GET    /stats/trending          Juegos en tendencia
GET    /stats/on-sale           Juegos actualmente en descuento
GET    /stats/summary           Resumen general de precios
```

### 🏥 Salud
```
GET    /health                  Estado de la API y componentes
GET    /                        Info de versión
```

---

## 🤖 Entrenar el Modelo ML

```bash
cd backend

# 1. Sincronizar datos primero (toma tiempo)
curl -X POST "http://localhost:8000/sync/top?top_n=200"

# 2. Entrenar el modelo
python -m src.ml.train --db ./data/steamsense.duckdb --epochs 100

# El modelo se guarda en: src/ml/artifacts/model.pkl
```

---

## 🧪 Testing

```bash
# Backend
cd backend
pytest tests/

# Frontend
cd frontend
npm test
```

---

## 🌍 Ejemplos de Uso

### Buscar un juego y ver predicción
```bash
curl -X GET "http://localhost:8000/games/search?q=Elden%20Ring"
# Obtén el game_id

curl -X GET "http://localhost:8000/predict/{game_id}"
# {
#   "game_id": "...",
#   "score": 8.5,
#   "signal": "BUY",
#   "reason": "Precio en mínimo histórico",
#   "confidence": 0.92
# }
```

### Login y obtener librería personalizada
```bash
# 1. Ir a http://localhost:3000 y hacer login con Steam
# 2. Automáticamente sincroniza tu librería desde Steam
# 3. En el dashboard ves juegos para comprar basados en tus juegos
```

---

## 📦 Variables de Entorno (.env)

```env
# IsThereAnyDeal
ITAD_API_KEY=tu_clave_aqui

# Steam Web API
STEAM_API_KEY=tu_clave_aqui

# DuckDB
DUCKDB_PATH=./data/steamsense.duckdb

# JWT
JWT_SECRET=tu_secreto_muy_seguro

# Entorno
ENV=development
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Sincronización
TOP_N_GAMES=200
```

---

## 🚀 Deploy en Render.com

### Backend
1. Conecta el repositorio en [Render.com](https://render.com)
2. Crea un nuevo Web Service
3. Build command: `pip install -r backend/requirements.txt`
4. Start command: `uvicorn backend.main:app --host 0.0.0.0 --port 10000`
5. Agrega variables de entorno en Settings:
   - `ITAD_API_KEY`
   - `STEAM_API_KEY`
   - `JWT_SECRET`
   - `ENV=production`

### Frontend
1. Crea otro Web Service para el frontend
2. Build command: `cd frontend && npm install && npm run build`
3. Start command: `cd frontend && npm run start`
4. Agrega variable: `NEXT_PUBLIC_API_URL=https://tu-backend.onrender.com`

### Base de datos
1. Agrega un Persistent Disk a tu Web Service del backend
2. Mount path: `/app/data`
3. Size: 10GB (o la que necesites)

---

## 🐛 Troubleshooting

**Error: "STEAM_API_KEY no configurada"**
- Verifica que tengas `STEAM_API_KEY` en `.env`
- Obtén una en https://steamcommunity.com/dev/apikey

**Error: "DuckDB locked"**
- Cierra otras instancias del servidor
- Elimina `data/steamsense.duckdb-wal` si existe

**El login de Steam no funciona**
- Verifica que el `return_to` en `steam_auth.py` coincida con tu dominio
- En local debe ser `http://localhost:8000`

**Frontend no puede conectar al backend**
- Revisa `NEXT_PUBLIC_API_URL` en `.env.local`
- Verifica CORS en `config.py` del backend

---

## 📝 Commits Recientes

- ✅ Autenticación con Steam (OpenID + JWT)
- ✅ Sincronización de librería de usuario
- ✅ Dashboard personal con estadísticas
- ✅ Componentes de gráficos y predicción
- ✅ Historial de precios interactivo
- ✅ Sistema de recomendaciones

---

## 📄 Licencia

MIT

## 👨‍💻 Autor

Felix - SteamSense Project

---

**¡No olvides dejar una ⭐ en GitHub!**
