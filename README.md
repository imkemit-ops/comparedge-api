# ComparEdge Software Intelligence API

> **REST API for [ComparEdge](https://comparedge.com)** — the independent SaaS & software comparison platform.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)](https://fastapi.tiangolo.com)
[![Deployed on Railway](https://img.shields.io/badge/Railway-deployed-purple)](https://railway.app)

Structured data for **300+ software products** across **28 categories** — pricing plans, feature lists,
G2 ratings, and head-to-head comparisons. All sourced from [comparedge.com](https://comparedge.com).

---

## 🌐 Links

| Resource | URL |
|---|---|
| **Main site** | [comparedge.com](https://comparedge.com) |
| **Swagger UI** | `<your-api-url>/docs` |
| **ReDoc** | `<your-api-url>/redoc` |
| **RSS Feed** | [comparedge.com/feed.xml](https://comparedge.com/feed.xml) |
| **LLMs.txt** | [comparedge.com/llms.txt](https://comparedge.com/llms.txt) |
| **GitHub** | [comparedge/awesome-saas-comparison-data](https://github.com/comparedge/awesome-saas-comparison-data) |

---

## 🚀 Quick Start

### Run locally

```bash
git clone https://github.com/comparedge/awesome-saas-comparison-data
cd comparedge-api

pip install -r requirements.txt
uvicorn main:app --reload
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

### Docker

```bash
docker build -t comparedge-api .
docker run -p 8000:8000 comparedge-api
```

---

## 📡 Endpoints

All endpoints return JSON with an `_links` object containing relevant [comparedge.com](https://comparedge.com) URLs.

### `GET /`
HTML landing page with API overview and links.

---

### `GET /api/v1/products`
List products with filtering and pagination.

**Query parameters:**

| Param | Type | Default | Description |
|---|---|---|---|
| `category` | string | — | Filter by category slug (e.g. `crm`, `vpn`, `ai-assistants`) |
| `free_only` | boolean | — | Only products with a free tier |
| `min_rating` | float | — | Minimum G2 rating (0–5) |
| `search` | string | — | Full-text search in name & description |
| `limit` | int | `20` | Results per page (max 100) |
| `offset` | int | `0` | Pagination offset |

**Example:**
```bash
curl "https://your-api.railway.app/api/v1/products?category=vpn&free_only=true&limit=5"
```

**Response:**
```json
{
  "total": 12,
  "limit": 5,
  "offset": 0,
  "products": [
    {
      "slug": "protonvpn",
      "name": "ProtonVPN",
      "category": "vpn",
      "description": "Privacy-focused VPN from the makers of ProtonMail",
      "pricing": { "free": true, "plans": [...] },
      "ratings": { "g2": 4.5 },
      "_links": {
        "self": "https://comparedge.com/protonvpn",
        "compare": "https://comparedge.com/compare/protonvpn",
        "site": "https://comparedge.com"
      }
    }
  ],
  "_links": { "site": "https://comparedge.com", "next": "...", "prev": null }
}
```

---

### `GET /api/v1/products/{slug}`
Full product details by slug.

**Example:**
```bash
curl "https://your-api.railway.app/api/v1/products/notion"
```

---

### `GET /api/v1/categories`
All categories with product counts.

**Example:**
```bash
curl "https://your-api.railway.app/api/v1/categories"
```

**Response:**
```json
{
  "total": 28,
  "categories": [
    {
      "slug": "crm",
      "name": "Crm",
      "product_count": 14,
      "_links": { "self": "https://comparedge.com/category/crm", "site": "https://comparedge.com" }
    }
  ],
  "_links": { "site": "https://comparedge.com" }
}
```

---

### `GET /api/v1/compare/{slug_a}/{slug_b}`
Head-to-head product comparison.

**Example:**
```bash
curl "https://your-api.railway.app/api/v1/compare/notion/confluence"
```

**Response includes:**
- Both products with full details
- `comparison.features` — shared features, and features unique to each product
- `comparison.pricing` — plan tiers for both
- `comparison.ratings` — G2 scores and winner
- `_links.compare_page` — link to full comparison on [comparedge.com](https://comparedge.com)

---

### `GET /api/v1/stats`
Database statistics.

**Example:**
```bash
curl "https://your-api.railway.app/api/v1/stats"
```

**Response:**
```json
{
  "total_products": 331,
  "total_categories": 28,
  "products_with_free_tier": 187,
  "free_tier_percentage": 56.5,
  "avg_g2_rating": 4.43,
  "products_with_ratings": 298,
  "top_categories": [...],
  "_links": { "site": "https://comparedge.com" }
}
```

---

### `GET /health`
Health check.

```bash
curl "https://your-api.railway.app/health"
# → { "status": "ok", "products": 331, "categories": 28, ... }
```

---

## 🚂 Deploy to Railway

1. Fork this repo
2. Create a new Railway project → **Deploy from GitHub**
3. Railway auto-detects `Procfile` and deploys

No environment variables required. The app is fully self-contained.

---

## 📦 Categories

Full list of available category slugs:

`accounting` · `ai-agents` · `ai-assistants` · `ai-coding` · `ai-image` · `ai-productivity`
`ai-video` · `ai-voice` · `ai-writing` · `cloud-hosting` · `crm` · `crypto-analytics`
`crypto-exchanges` · `crypto-portfolio-trackers` · `crypto-tax` · `crypto-telegram-bots`
`crypto-trading-bots` · `crypto-wallets` · `defi-tools` · `design-tools` · `dex`
`email-marketing` · `llm` · `password-managers` · `project-management`
`video-conferencing` · `vpn` · `website-builders`

---

## 🗂️ Data

Data is curated by the [ComparEdge](https://comparedge.com) editorial team.
For the human-readable product pages and comparisons, visit [comparedge.com](https://comparedge.com).

The raw dataset is also available as a machine-readable feed:
- **RSS:** [comparedge.com/feed.xml](https://comparedge.com/feed.xml)
- **LLM-friendly:** [comparedge.com/llms.txt](https://comparedge.com/llms.txt)

---

## 📄 License

MIT — see [LICENSE](LICENSE).

Data sourced from [comparedge.com](https://comparedge.com). Please credit ComparEdge when publishing data.
