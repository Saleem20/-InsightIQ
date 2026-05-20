# ProductIQ

AI-powered product data enrichment, insights, and attribution management for CPGs and retailers.

## What It Does

ProductIQ enriches existing product data with attributes, claims, ingredient signals, review concepts, opportunity scores, and source attribution.

It supports:

- Demo product data for quick review
- CSV/XLSX product uploads
- Product listing URL extraction
- OpenAI GPT executive insights when configured
- PostgreSQL persistence when configured

## Run Locally

```powershell
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Recommended Upload Columns

The app automatically maps common product fields:

- `product_id`, `sku`, `asin`, `gtin`
- `product_name`, `name`, `title`
- `brand`, `manufacturer`
- `category`, `department`, `vertical`
- `source`, `retailer`, `platform`
- `source_url`, `url`, `product_url`
- `description`, `claims`, `features`, `ingredients`, `reviews`
- `price`, `rating`

## Streamlit Secrets

Add these in Streamlit Cloud under **App settings -> Secrets** when needed:

```toml
OPENAI_API_KEY = "your_openai_key"
OPENAI_MODEL = "gpt-4.1-mini"
DATABASE_URL = "postgresql://user:password@host:5432/database"
```

The app runs without secrets. OpenAI and PostgreSQL features activate when credentials are present.
