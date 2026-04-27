# Download Endpoints

The ComparEdge API provides two bulk download endpoints for offline analysis, ML training, and data integration.

---

## GET /download/db_dump

Download a portable SQLite snapshot of the full ComparEdge dataset.

**URL:** `https://comparedge-api.up.railway.app/download/db_dump`

**Response:** Binary `.sql` file (SQLite dump format)

**Content-Disposition:** `attachment; filename=comparedge_snapshot.sql`

### Schema

The dump contains 3 tables:

| Table | Description |
|-------|-------------|
| `categories` | 28 categories with slugs and product counts |
| `products` | 331 products with slug, name, ratings, free tier flag, comparedge URL |
| `pricing_plans` | Per-product pricing plans with monthly price and billing period |

### Usage examples

```bash
# Download and inspect with sqlite3
curl -o comparedge.sql https://comparedge-api.up.railway.app/download/db_dump
sqlite3 comparedge.db < comparedge.sql
sqlite3 comparedge.db "SELECT name, g2_rating FROM products ORDER BY g2_rating DESC LIMIT 10;"
```

```python
# Load into pandas
import sqlite3, pandas as pd
conn = sqlite3.connect("comparedge.db")
df = pd.read_sql("SELECT * FROM products", conn)
print(df.head())
```

---

## GET /download/csv

Download the full product catalog as a flat CSV file.

**URL:** `https://comparedge-api.up.railway.app/download/csv`

**Response:** UTF-8 CSV file

**Content-Disposition:** `attachment; filename=comparedge_products.csv`

### Columns

| Column | Type | Description |
|--------|------|-------------|
| `slug` | string | Unique product identifier |
| `name` | string | Product display name |
| `category` | string | Category slug (e.g. `crm`, `ai-assistants`) |
| `g2_rating` | float | G2 community rating (0–5) |
| `has_free_tier` | yes/no | Whether a free plan is available |
| `starting_price_usd` | float | Lowest paid plan price per month |
| `website` | string | Official product website |
| `comparedge_url` | string | ComparEdge comparison page URL |

### Usage examples

```bash
# Download CSV
curl -o comparedge_products.csv https://comparedge-api.up.railway.app/download/csv

# Quick analysis with csvkit
csvstat comparedge_products.csv
csvgrep -c category -m ai-assistants comparedge_products.csv | csvlook
```

```python
import pandas as pd
df = pd.read_csv("comparedge_products.csv")
print(df[df["has_free_tier"] == "yes"].sort_values("g2_rating", ascending=False).head(10))
```

---

## Related Resources

- **HuggingFace Dataset:** [ComparEdge/saas-market-intelligence](https://huggingface.co/datasets/ComparEdge/saas-market-intelligence) — PDF market report + SQL schema
- **Kaggle Dataset:** [comparedge/saas-ai-tools-market-2026](https://www.kaggle.com/datasets/comparedge/saas-ai-tools-market-2026) — Full SQLite database
- **GitHub:** [comparedge/awesome-saas-comparison-data](https://github.com/comparedge/awesome-saas-comparison-data) — Raw JSON data files
