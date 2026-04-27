"""
ComparEdge Software Intelligence API
=====================================
REST API for ComparEdge (https://comparedge.com) — the independent SaaS comparison platform.

Endpoints serve structured data for 300+ software products across 28 categories,
including pricing, features, ratings, and head-to-head comparisons.

Full product catalog and human-readable comparisons: https://comparedge.com
"""

from __future__ import annotations

import json
import math
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

# ---------------------------------------------------------------------------
# App metadata
# ---------------------------------------------------------------------------

SITE_URL = "https://comparedge.com"
API_VERSION = "v1"
API_PREFIX = f"/api/{API_VERSION}"

description = f"""
## ComparEdge Software Intelligence API

The **ComparEdge API** provides programmatic access to structured data for **300+ SaaS products**
across **28 categories** — from project management to AI tools, crypto, and DevOps.

> 🌐 Browse the full comparison site at **[comparedge.com]({SITE_URL})**

### What you get

- **Product details** — pricing plans, feature lists, G2 ratings, official URLs
- **Category browsing** — filter by niche (CRM, AI tools, VPN, crypto, etc.)
- **Head-to-head comparisons** — structured diffs between any two products
- **Stats & insights** — market coverage, rating distributions, free-tier availability

### Data freshness

Data is curated by the ComparEdge editorial team and updated regularly.
For the latest human-readable comparisons, visit [{SITE_URL}]({SITE_URL}).

### Terms

Free to use. No auth required. Please credit **[comparedge.com]({SITE_URL})** when publishing data.

---
*Built with ❤️ by [ComparEdge]({SITE_URL})*
"""

app = FastAPI(
    title="ComparEdge Software Intelligence API",
    description=description,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "ComparEdge",
        "url": SITE_URL,
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    servers=[
        {"url": SITE_URL + "/api/v1", "description": "ComparEdge production"},
    ],
)

# ---------------------------------------------------------------------------
# CORS — public API, allow all origins
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Powered-By", "X-Data-Source"],
)

# ---------------------------------------------------------------------------
# Custom response headers middleware
# ---------------------------------------------------------------------------


@app.middleware("http")
async def add_custom_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Powered-By"] = "ComparEdge"
    response.headers["X-Data-Source"] = SITE_URL
    response.headers["X-API-Version"] = API_VERSION
    return response


# ---------------------------------------------------------------------------
# Data layer
# ---------------------------------------------------------------------------

DATA_PATH = Path(__file__).parent / "data" / "products.json"


@lru_cache(maxsize=1)
def _load_data() -> dict[str, Any]:
    """Load and index product data. Cached for the process lifetime."""
    with open(DATA_PATH, encoding="utf-8") as f:
        raw = json.load(f)

    products: list[dict] = raw.get("products", [])

    # Build slug → product index
    by_slug: dict[str, dict] = {}
    by_category: dict[str, list[dict]] = {}

    for p in products:
        slug = p.get("slug", "")
        if slug:
            by_slug[slug] = p

        cat = p.get("category", "uncategorized")
        by_category.setdefault(cat, []).append(p)

    return {
        "products": products,
        "by_slug": by_slug,
        "by_category": by_category,
    }


def get_db() -> dict[str, Any]:
    return _load_data()


# ---------------------------------------------------------------------------
# Helper — build _links object
# ---------------------------------------------------------------------------


def product_links(slug: str) -> dict:
    return {
        "self": f"{SITE_URL}/{slug}",
        "compare": f"{SITE_URL}/compare/{slug}",
        "site": SITE_URL,
    }


def category_links(slug: str) -> dict:
    return {
        "self": f"{SITE_URL}/category/{slug}",
        "site": SITE_URL,
    }


def _enrich_product(p: dict) -> dict:
    """Return a shallow copy of the product with _links injected."""
    slug = p.get("slug", "")
    return {**p, "_links": product_links(slug)}


# ---------------------------------------------------------------------------
# Landing page HTML
# ---------------------------------------------------------------------------

LANDING_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>ComparEdge API — Software Intelligence API</title>
  <meta name="description" content="REST API for ComparEdge — structured data for 300+ SaaS products. Pricing, features, ratings, and comparisons." />
  <meta name="robots" content="index, follow" />
  <link rel="canonical" href="https://comparedge.com" />
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --bg: #0d1117;
      --surface: #161b22;
      --border: #30363d;
      --text: #e6edf3;
      --muted: #8b949e;
      --accent: #58a6ff;
      --accent-hover: #79c0ff;
      --green: #3fb950;
      --purple: #bc8cff;
      --orange: #ffa657;
      --font: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    body { background: var(--bg); color: var(--text); font-family: var(--font); line-height: 1.6; }
    a { color: var(--accent); text-decoration: none; }
    a:hover { color: var(--accent-hover); text-decoration: underline; }

    header {
      border-bottom: 1px solid var(--border);
      padding: 1.25rem 2rem;
      display: flex;
      align-items: center;
      gap: 1rem;
    }
    .logo { font-size: 1.4rem; font-weight: 700; color: var(--text); }
    .logo span { color: var(--accent); }
    .badge {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 999px;
      padding: 0.2rem 0.75rem;
      font-size: 0.75rem;
      color: var(--muted);
    }
    nav { margin-left: auto; display: flex; gap: 1.5rem; font-size: 0.9rem; }

    .hero {
      max-width: 860px;
      margin: 4rem auto 2rem;
      padding: 0 2rem;
      text-align: center;
    }
    .hero h1 { font-size: 2.4rem; font-weight: 800; line-height: 1.2; margin-bottom: 1rem; }
    .hero h1 span { color: var(--accent); }
    .hero p { font-size: 1.1rem; color: var(--muted); max-width: 600px; margin: 0 auto 2rem; }

    .cta-row { display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap; }
    .btn {
      padding: 0.65rem 1.5rem;
      border-radius: 8px;
      font-size: 0.95rem;
      font-weight: 600;
      cursor: pointer;
      transition: opacity .15s;
    }
    .btn:hover { opacity: 0.85; text-decoration: none; }
    .btn-primary { background: var(--accent); color: #0d1117; }
    .btn-secondary { background: var(--surface); color: var(--text); border: 1px solid var(--border); }

    .stats-row {
      display: flex;
      gap: 2rem;
      justify-content: center;
      flex-wrap: wrap;
      margin: 3rem auto;
      max-width: 860px;
      padding: 0 2rem;
    }
    .stat { text-align: center; }
    .stat .num { font-size: 2rem; font-weight: 800; color: var(--accent); }
    .stat .label { font-size: 0.85rem; color: var(--muted); }

    .endpoints {
      max-width: 860px;
      margin: 0 auto 4rem;
      padding: 0 2rem;
    }
    .endpoints h2 { font-size: 1.4rem; font-weight: 700; margin-bottom: 1.5rem; }
    .endpoint-list { display: flex; flex-direction: column; gap: 0.75rem; }
    .endpoint {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 1rem 1.25rem;
      display: flex;
      align-items: flex-start;
      gap: 1rem;
    }
    .method {
      font-family: monospace;
      font-size: 0.75rem;
      font-weight: 700;
      padding: 0.2rem 0.5rem;
      border-radius: 5px;
      background: rgba(88,166,255,0.15);
      color: var(--accent);
      white-space: nowrap;
      margin-top: 2px;
    }
    .endpoint-path { font-family: monospace; font-size: 0.95rem; color: var(--text); }
    .endpoint-desc { font-size: 0.85rem; color: var(--muted); margin-top: 0.2rem; }

    footer {
      border-top: 1px solid var(--border);
      padding: 2rem;
      text-align: center;
      color: var(--muted);
      font-size: 0.85rem;
    }
    footer a { color: var(--muted); }
    footer a:hover { color: var(--accent); }
  </style>
</head>
<body>

<header>
  <span class="logo">Compar<span>Edge</span></span>
  <span class="badge">API v1</span>
  <nav>
    <a href="https://comparedge.com">Website</a>
    <a href="/docs">Swagger UI</a>
    <a href="/redoc">ReDoc</a>
  </nav>
</header>

<section class="hero">
  <h1>Software Intelligence<br/><span>API</span></h1>
  <p>
    Structured data for <strong>300+ SaaS products</strong> — pricing, features, G2 ratings,
    and head-to-head comparisons. Powered by
    <a href="https://comparedge.com">ComparEdge.com</a>.
  </p>
  <div class="cta-row">
    <a class="btn btn-primary" href="/docs">Explore API Docs</a>
    <a class="btn btn-secondary" href="https://comparedge.com">Browse comparedge.com</a>
  </div>
</section>

<div class="stats-row">
  <div class="stat"><div class="num">300+</div><div class="label">Products</div></div>
  <div class="stat"><div class="num">28</div><div class="label">Categories</div></div>
  <div class="stat"><div class="num">Free</div><div class="label">No Auth Required</div></div>
  <div class="stat"><div class="num">REST</div><div class="label">JSON API</div></div>
</div>

<section class="endpoints">
  <h2>Endpoints</h2>
  <div class="endpoint-list">

    <div class="endpoint">
      <span class="method">GET</span>
      <div>
        <div class="endpoint-path"><a href="/api/v1/products">/api/v1/products</a></div>
        <div class="endpoint-desc">List products with filtering by category, free tier, rating, and full-text search.</div>
      </div>
    </div>

    <div class="endpoint">
      <span class="method">GET</span>
      <div>
        <div class="endpoint-path">/api/v1/products/{slug}</div>
        <div class="endpoint-desc">Full product details — pricing plans, features, ratings, and official URL.</div>
      </div>
    </div>

    <div class="endpoint">
      <span class="method">GET</span>
      <div>
        <div class="endpoint-path"><a href="/api/v1/categories">/api/v1/categories</a></div>
        <div class="endpoint-desc">All categories with product counts and links to comparedge.com.</div>
      </div>
    </div>

    <div class="endpoint">
      <span class="method">GET</span>
      <div>
        <div class="endpoint-path">/api/v1/compare/{slug_a}/{slug_b}</div>
        <div class="endpoint-desc">Head-to-head comparison: features, pricing, and ratings side by side.</div>
      </div>
    </div>

    <div class="endpoint">
      <span class="method">GET</span>
      <div>
        <div class="endpoint-path"><a href="/api/v1/stats">/api/v1/stats</a></div>
        <div class="endpoint-desc">Database statistics: coverage, rating distributions, top categories.</div>
      </div>
    </div>

    <div class="endpoint">
      <span class="method">GET</span>
      <div>
        <div class="endpoint-path"><a href="/health">/health</a></div>
        <div class="endpoint-desc">Health check — uptime and data freshness.</div>
      </div>
    </div>

  </div>
</section>

<footer>
  <p>
    ComparEdge API &mdash; data sourced from
    <a href="https://comparedge.com">comparedge.com</a>
    &mdash; MIT License
  </p>
  <p style="margin-top:0.5rem;">
    <a href="https://comparedge.com">Home</a> &middot;
    <a href="https://comparedge.com/feed.xml">RSS Feed</a> &middot;
    <a href="https://comparedge.com/llms.txt">llms.txt</a> &middot;
    <a href="/docs">Swagger UI</a> &middot;
    <a href="/redoc">ReDoc</a>
  </p>
</footer>

</body>
</html>
"""

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root():
    """Landing page with ComparEdge branding and API documentation links."""
    return HTMLResponse(content=LANDING_HTML)


# ── Health ──────────────────────────────────────────────────────────────────


@app.get(
    "/health",
    summary="Health check",
    tags=["System"],
    response_description="API health status",
)
async def health():
    """
    Returns API health status and basic metadata.

    Use this endpoint to verify the service is running before making
    data requests.
    """
    db = get_db()
    return {
        "status": "ok",
        "version": "1.0.0",
        "products": len(db["products"]),
        "categories": len(db["by_category"]),
        "data_source": SITE_URL,
        "_links": {"site": SITE_URL, "docs": "/docs"},
    }


# ── Stats ────────────────────────────────────────────────────────────────────


@app.get(
    f"{API_PREFIX}/stats",
    summary="Database statistics",
    tags=["Data"],
    response_description="Aggregate statistics",
)
async def stats():
    """
    Aggregate statistics about the ComparEdge product database.

    Returns total product count, category breakdown, rating distribution,
    and free-tier availability summary.

    Full product catalog: [comparedge.com](https://comparedge.com)
    """
    db = get_db()
    products = db["products"]
    by_category = db["by_category"]

    ratings = [
        p["rating"]["g2"]
        for p in products
        if p.get("ratings") and p["ratings"].get("g2")
    ]
    avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else None

    free_count = sum(
        1
        for p in products
        if p.get("pricing", {}).get("free") is True
    )

    top_cats = sorted(
        [
            {
                "slug": cat,
                "product_count": len(prods),
                "_links": category_links(cat),
            }
            for cat, prods in by_category.items()
        ],
        key=lambda x: x["product_count"],
        reverse=True,
    )[:10]

    return {
        "total_products": len(products),
        "total_categories": len(by_category),
        "products_with_free_tier": free_count,
        "free_tier_percentage": round(free_count / len(products) * 100, 1),
        "avg_g2_rating": avg_rating,
        "products_with_ratings": len(ratings),
        "top_categories": top_cats,
        "_links": {"site": SITE_URL, "products": f"{SITE_URL}/products", "self": f"{SITE_URL}/api/v1/stats"},
    }


# ── Categories ───────────────────────────────────────────────────────────────


@app.get(
    f"{API_PREFIX}/categories",
    summary="List all categories",
    tags=["Categories"],
    response_description="Category list with product counts",
)
async def list_categories():
    """
    Returns all product categories with product counts.

    Each category entry includes a link to the corresponding page on
    [comparedge.com](https://comparedge.com) for the human-readable view.
    """
    db = get_db()

    categories = sorted(
        [
            {
                "slug": cat,
                "name": cat.replace("-", " ").title(),
                "product_count": len(prods),
                "_links": category_links(cat),
            }
            for cat, prods in db["by_category"].items()
        ],
        key=lambda x: x["name"],
    )

    return {
        "total": len(categories),
        "categories": categories,
        "_links": {"site": SITE_URL},
    }


# ── Products list ─────────────────────────────────────────────────────────────


@app.get(
    f"{API_PREFIX}/products",
    summary="List products",
    tags=["Products"],
    response_description="Paginated product list",
)
async def list_products(
    category: Optional[str] = Query(None, description="Filter by category slug (e.g. `crm`, `vpn`, `ai-assistants`)"),
    free_only: Optional[bool] = Query(None, description="Only return products with a free tier"),
    min_rating: Optional[float] = Query(None, ge=0.0, le=5.0, description="Minimum G2 rating (0–5)"),
    search: Optional[str] = Query(None, min_length=1, max_length=100, description="Full-text search in name and description"),
    limit: int = Query(20, ge=1, le=100, description="Results per page (max 100)"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
):
    """
    List all software products with optional filtering and pagination.

    **Filters:**
    - `category` — narrow to a specific niche (see `/api/v1/categories` for slugs)
    - `free_only` — only products offering a free tier
    - `min_rating` — minimum G2 community rating
    - `search` — keyword search across product name and description

    **Pagination:** use `limit` and `offset`.

    Browse all products at [comparedge.com](https://comparedge.com).
    """
    db = get_db()
    products = db["products"]

    # Apply filters
    if category:
        cat_lower = category.lower()
        products = [p for p in products if p.get("category", "").lower() == cat_lower]
        if not products:
            raise HTTPException(
                status_code=404,
                detail=f"Category '{category}' not found. See /api/v1/categories for valid slugs.",
            )

    if free_only is True:
        products = [p for p in products if p.get("pricing", {}).get("free") is True]

    if min_rating is not None:
        products = [
            p for p in products
            if p.get("rating", {}).get("g2") is not None
            and p["rating"]["g2"] >= min_rating
        ]

    if search:
        q = search.lower()
        products = [
            p for p in products
            if q in p.get("name", "").lower() or q in p.get("description", "").lower()
        ]

    total = len(products)
    page = products[offset : offset + limit]

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "products": [_enrich_product(p) for p in page],
        "_links": {
            "site": SITE_URL,
            "next": f"{SITE_URL}/api/v1/products?limit={limit}&offset={offset + limit}" if offset + limit < total else None,
            "prev": f"{SITE_URL}/api/v1/products?limit={limit}&offset={max(0, offset - limit)}" if offset > 0 else None,
        },
    }


# ── Single product ────────────────────────────────────────────────────────────


@app.get(
    f"{API_PREFIX}/products/{{slug}}",
    summary="Get product by slug",
    tags=["Products"],
    response_description="Full product details",
)
async def get_product(slug: str):
    """
    Returns full details for a single product by its slug.

    Includes pricing plans, feature list, G2 rating, official URL, and
    a direct link to the [comparedge.com](https://comparedge.com) comparison page.

    **Example slugs:** `notion`, `slack`, `github-copilot`, `nordvpn`
    """
    db = get_db()
    product = db["by_slug"].get(slug.lower())

    if not product:
        raise HTTPException(
            status_code=404,
            detail=f"Product '{slug}' not found. See /api/v1/products for the full list.",
        )

    return _enrich_product(product)


# ── Compare ───────────────────────────────────────────────────────────────────


@app.get(
    f"{API_PREFIX}/compare/{{slug_a}}/{{slug_b}}",
    summary="Compare two products",
    tags=["Comparisons"],
    response_description="Head-to-head comparison",
)
async def compare_products(slug_a: str, slug_b: str):
    """
    Head-to-head comparison of two products.

    Returns both products side by side with structured comparisons of:
    - **Pricing** — plan tiers and starting prices
    - **Features** — overlapping and unique features
    - **Ratings** — G2 scores

    For a full human-readable comparison, visit the link in `_links.compare_page`
    on [comparedge.com](https://comparedge.com).
    """
    db = get_db()

    product_a = db["by_slug"].get(slug_a.lower())
    product_b = db["by_slug"].get(slug_b.lower())

    missing = []
    if not product_a:
        missing.append(slug_a)
    if not product_b:
        missing.append(slug_b)

    if missing:
        raise HTTPException(
            status_code=404,
            detail=f"Product(s) not found: {', '.join(missing)}. See /api/v1/products for valid slugs.",
        )

    # ── pricing comparison ──
    def pricing_summary(p: dict) -> dict:
        pricing = p.get("pricing", {})
        plans = pricing.get("plans", [])
        paid_plans = [pl for pl in plans if (pl.get("price") or 0) > 0]
        return {
            "has_free_tier": pricing.get("free", False),
            "plan_count": len(plans),
            "starting_price": min((pl["price"] for pl in paid_plans), default=None),
            "plans": plans,
        }

    # ── feature comparison ──
    def feature_set(p: dict) -> set:
        return set(p.get("features", []))

    features_a = feature_set(product_a)
    features_b = feature_set(product_b)
    shared = sorted(features_a & features_b)
    only_a = sorted(features_a - features_b)
    only_b = sorted(features_b - features_a)

    # ── rating comparison ──
    def rating_summary(p: dict) -> dict:
        ratings = p.get("rating", {})
        return {
            "g2": ratings.get("g2"),
            "g2_reviews": ratings.get("g2_reviews"),
        }

    winner_rating = None
    r_a = (product_a.get("ratings") or {}).get("g2")
    r_b = (product_b.get("ratings") or {}).get("g2")
    if r_a is not None and r_b is not None:
        if r_a > r_b:
            winner_rating = product_a["name"]
        elif r_b > r_a:
            winner_rating = product_b["name"]
        else:
            winner_rating = "tie"

    compare_page = f"{SITE_URL}/compare/{slug_a}-vs-{slug_b}"

    return {
        "product_a": {**_enrich_product(product_a), "pricing_summary": pricing_summary(product_a), "ratings": rating_summary(product_a)},
        "product_b": {**_enrich_product(product_b), "pricing_summary": pricing_summary(product_b), "ratings": rating_summary(product_b)},
        "comparison": {
            "features": {
                "shared": shared,
                f"only_{slug_a}": only_a,
                f"only_{slug_b}": only_b,
                "shared_count": len(shared),
            },
            "pricing": {
                product_a["name"]: pricing_summary(product_a),
                product_b["name"]: pricing_summary(product_b),
            },
            "ratings": {
                product_a["name"]: r_a,
                product_b["name"]: r_b,
                "winner": winner_rating,
            },
        },
        "_links": {
            "compare_page": compare_page,
            "product_a": product_links(slug_a),
            "product_b": product_links(slug_b),
            "site": SITE_URL,
        },
    }


# ---------------------------------------------------------------------------
# Download endpoints
# ---------------------------------------------------------------------------

import io
import sqlite3
import csv as csv_module
from fastapi.responses import StreamingResponse

@app.get(
    "/download/db_dump",
    summary="Download SQLite database snapshot",
    tags=["Downloads"],
    response_description="SQLite database file with all products, pricing plans, and features",
)
def download_db_dump():
    """
    Download a portable SQLite snapshot of the full ComparEdge dataset.
    
    Contains 5 tables: categories, products, pricing_plans, features, price_history.
    Compatible with any SQLite client, DBeaver, Datasette, pandas, etc.
    """
    products_data = get_products()
    products = products_data["products"]
    
    # Build in-memory SQLite
    conn = sqlite3.connect(":memory:")
    cur = conn.cursor()
    
    cur.executescript("""
        CREATE TABLE categories (id INTEGER PRIMARY KEY, slug TEXT UNIQUE, name TEXT, product_count INTEGER DEFAULT 0);
        CREATE TABLE products (
            id INTEGER PRIMARY KEY, slug TEXT UNIQUE, name TEXT, category_slug TEXT,
            description TEXT, website_url TEXT, g2_rating REAL, overall_rating REAL,
            review_count INTEGER, has_free_tier INTEGER DEFAULT 0, last_updated TEXT,
            comparedge_url TEXT
        );
        CREATE TABLE pricing_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT, product_slug TEXT, plan_name TEXT,
            price_monthly REAL, billing_period TEXT, is_free INTEGER DEFAULT 0
        );
    """)
    
    # Insert categories
    from collections import Counter
    cat_counts = Counter(p["category"] for p in products)
    for i, (slug, count) in enumerate(sorted(cat_counts.items())):
        name = slug.replace("-", " ").title()
        cur.execute("INSERT OR IGNORE INTO categories VALUES (?,?,?,?)", (i+1, slug, name, count))
    
    # Insert products + plans
    for i, p in enumerate(products):
        rating = p.get("rating") or p.get("ratings") or {}
        g2 = rating.get("g2")
        overall = rating.get("overall") or g2
        reviews = rating.get("g2_reviews") or rating.get("reviews") or 0
        has_free = 1 if p.get("pricing", {}).get("free") else 0
        last_updated = p.get("lastUpdated", "2026-04-27")
        cur.execute(
            "INSERT OR IGNORE INTO products VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (i+1, p["slug"], p["name"], p.get("category",""),
             (p.get("description","") or "")[:500],
             p.get("url",""), g2, overall, reviews, has_free, last_updated,
             f"https://comparedge.com/tools/{p['slug']}")
        )
        for plan in (p.get("pricing", {}).get("plans") or []):
            price = plan.get("price")
            is_free = 1 if (price == 0 or "free" in (plan.get("name") or "").lower()) else 0
            cur.execute(
                "INSERT INTO pricing_plans (product_slug, plan_name, price_monthly, billing_period, is_free) VALUES (?,?,?,?,?)",
                (p["slug"], plan.get("name",""), price, plan.get("period",""), is_free)
            )
    
    conn.commit()
    
    # Serialize to bytes
    buf = io.BytesIO()
    for chunk in conn.iterdump():
        buf.write((chunk + "\n").encode())
    conn.close()
    buf.seek(0)
    
    return StreamingResponse(
        buf,
        media_type="application/octet-stream",
        headers={"Content-Disposition": "attachment; filename=comparedge_snapshot.sql"}
    )


@app.get(
    "/download/csv",
    summary="Download products as CSV",
    tags=["Downloads"],
    response_description="CSV file with all 331 products",
)
def download_csv():
    """
    Download the full product catalog as CSV.
    Columns: slug, name, category, g2_rating, has_free_tier, starting_price, website, comparedge_url
    """
    products_data = get_products()
    products = products_data["products"]
    
    buf = io.StringIO()
    writer = csv_module.writer(buf)
    writer.writerow(["slug", "name", "category", "g2_rating", "has_free_tier", "starting_price_usd", "website", "comparedge_url"])
    
    for p in products:
        rating = p.get("rating") or p.get("ratings") or {}
        g2 = rating.get("g2", "")
        has_free = p.get("pricing", {}).get("free", False)
        plans = p.get("pricing", {}).get("plans") or []
        paid = [pl["price"] for pl in plans if pl.get("price") and pl["price"] > 0]
        starting = min(paid) if paid else ""
        writer.writerow([
            p["slug"], p["name"], p.get("category",""),
            g2, "yes" if has_free else "no", starting,
            p.get("url",""), f"https://comparedge.com/tools/{p['slug']}"
        ])
    
    buf.seek(0)
    return StreamingResponse(
        io.BytesIO(buf.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=comparedge_products.csv"}
    )
