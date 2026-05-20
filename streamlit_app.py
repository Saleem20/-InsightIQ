import json
import os
import re
from collections import Counter
from datetime import datetime
from urllib.error import URLError
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd
import plotly.express as px
import requests
import streamlit as st


st.set_page_config(
    page_title="ProductIQ",
    page_icon="PIQ",
    layout="wide",
    initial_sidebar_state="expanded",
)


CATEGORIES = ["Oral Care", "Home Care", "Personal Care", "Wellness", "OTC", "Beverage", "Food", "Pet Care"]
ATTRIBUTE_TAXONOMY = {
    "Clean Label": ["clean label", "no artificial", "natural", "organic", "plant-based", "free from"],
    "Sustainability": ["recyclable", "refill", "biodegradable", "sustainable", "plastic-free", "eco"],
    "Functional Benefit": ["immune", "energy", "sleep", "gut", "hydration", "repair", "sensitivity", "relief"],
    "Ingredient Led": ["turmeric", "fluoride", "probiotic", "collagen", "protein", "vitamin", "zinc", "niacinamide"],
    "Sensory": ["fresh", "mint", "smooth", "creamy", "fragrance", "taste", "texture", "crunchy"],
    "Value": ["family pack", "refill", "bulk", "affordable", "value", "subscription"],
    "Premium": ["clinical", "dermatologist", "expert", "science", "advanced", "professional"],
    "Convenience": ["on-the-go", "ready to drink", "travel", "single serve", "easy", "portable"],
}
CLAIM_PATTERNS = {
    "Natural": ["natural", "organic", "plant-based", "ayurvedic"],
    "Free From": ["sugar-free", "paraben-free", "fluoride-free", "no artificial", "gluten-free"],
    "Clinically Backed": ["clinical", "clinically", "dermatologist", "dentist", "proven", "tested"],
    "Sustainable": ["recyclable", "biodegradable", "refill", "plastic-free", "eco"],
    "Performance": ["whitening", "repair", "long lasting", "fast acting", "24 hour", "advanced"],
}
STOPWORDS = {
    "with",
    "from",
    "that",
    "this",
    "your",
    "have",
    "into",
    "more",
    "made",
    "product",
    "products",
    "brand",
    "pack",
    "free",
    "care",
}
REQUIRED_COLUMNS = [
    "product_id",
    "product_name",
    "brand",
    "category",
    "source",
    "source_url",
    "description",
    "ingredients",
    "claims",
    "reviews",
    "price",
    "rating",
]


def get_secret(name: str, default: str = "") -> str:
    try:
        value = st.secrets.get(name, default)
    except Exception:
        value = os.getenv(name, default)
    return str(value or "").strip()


def clean_text(value) -> str:
    if pd.isna(value):
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

    renamed = {
        column: re.sub(r"[^a-z0-9]+", "_", str(column).strip().lower()).strip("_")
        for column in df.columns
    }
    working = df.rename(columns=renamed).copy()
    aliases = {
        "product_id": ["product_id", "sku", "asin", "id", "item_id", "gtin"],
        "product_name": ["product_name", "name", "title", "item_name", "product"],
        "brand": ["brand", "manufacturer", "company"],
        "category": ["category", "department", "vertical", "segment"],
        "source": ["source", "retailer", "platform", "site"],
        "source_url": ["source_url", "url", "link", "pdp_url", "product_url"],
        "description": ["description", "body", "copy", "details", "about"],
        "ingredients": ["ingredients", "ingredient_list", "composition"],
        "claims": ["claims", "claim", "features", "bullets", "benefits"],
        "reviews": ["reviews", "review", "consumer_reviews", "comments"],
        "price": ["price", "sale_price", "mrp"],
        "rating": ["rating", "stars", "score"],
    }

    normalized = pd.DataFrame()
    for target, names in aliases.items():
        source = next((name for name in names if name in working.columns), None)
        normalized[target] = working[source] if source else ""

    normalized["product_name"] = normalized["product_name"].apply(clean_text)
    normalized = normalized[normalized["product_name"].str.len() > 0].copy()
    if normalized.empty:
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

    for column in ["product_id", "brand", "category", "source", "source_url", "description", "ingredients", "claims", "reviews"]:
        normalized[column] = normalized[column].apply(clean_text)

    normalized["product_id"] = normalized.apply(
        lambda row: row["product_id"] or f"{row['brand']}|{row['product_name']}|{row['source']}",
        axis=1,
    )
    normalized["category"] = normalized["category"].replace("", "Unassigned")
    normalized["source"] = normalized["source"].replace("", "Uploaded data")
    normalized["price"] = pd.to_numeric(normalized["price"], errors="coerce")
    normalized["rating"] = pd.to_numeric(normalized["rating"], errors="coerce")
    return normalized[REQUIRED_COLUMNS].reset_index(drop=True)


@st.cache_data
def sample_products() -> pd.DataFrame:
    rows = [
        {
            "product_id": "OC-001",
            "product_name": "FreshMint Clinical Enamel Repair Toothpaste",
            "brand": "FreshMint",
            "category": "Oral Care",
            "source": "Retailer PDP",
            "source_url": "https://example.com/freshmint-enamel",
            "description": "Advanced toothpaste for enamel repair, sensitivity relief, and long lasting mint freshness.",
            "ingredients": "Fluoride, potassium nitrate, hydrated silica, mint flavor",
            "claims": "Dentist recommended, clinically tested, sensitivity relief, enamel repair",
            "reviews": "Works well for sensitive teeth. I like the fresh taste but want clearer ingredient explanation.",
            "price": 6.99,
            "rating": 4.5,
        },
        {
            "product_id": "BEV-014",
            "product_name": "NutriGo Sugar-Free Electrolyte Drink",
            "brand": "NutriGo",
            "category": "Beverage",
            "source": "Marketplace",
            "source_url": "https://example.com/nutrigo-electrolyte",
            "description": "Zero sugar hydration drink with electrolytes, vitamin B12, and light citrus taste.",
            "ingredients": "Water, electrolytes, vitamin B12, stevia, natural flavors",
            "claims": "Sugar-free, hydration, no artificial colors, low calorie",
            "reviews": "Refreshing after gym. Stevia aftertaste is noticeable but better than artificial sweeteners.",
            "price": 2.49,
            "rating": 4.1,
        },
        {
            "product_id": "PC-022",
            "product_name": "GlowCore Collagen Peptide Beauty Powder",
            "brand": "GlowCore",
            "category": "Personal Care",
            "source": "Brand Site",
            "source_url": "https://example.com/glowcore-collagen",
            "description": "Collagen peptide powder with vitamin C for skin glow and hair support.",
            "ingredients": "Collagen peptides, vitamin C, biotin, natural berry flavor",
            "claims": "Beauty from within, skin glow, hair support, science backed",
            "reviews": "Mixes smoothly. I want more proof around visible skin benefits and sourcing.",
            "price": 28.0,
            "rating": 4.3,
        },
        {
            "product_id": "HC-008",
            "product_name": "PureLeaf Refill Surface Cleaner",
            "brand": "PureLeaf",
            "category": "Home Care",
            "source": "Retailer PDP",
            "source_url": "https://example.com/pureleaf-cleaner",
            "description": "Concentrated refill cleaner with biodegradable formula and fresh herbal fragrance.",
            "ingredients": "Plant-based surfactants, fragrance, citric acid",
            "claims": "Biodegradable, refill format, plant-based, safe for daily cleaning",
            "reviews": "Smells clean and reduces plastic. Refill instructions could be simpler.",
            "price": 4.99,
            "rating": 4.6,
        },
        {
            "product_id": "WL-031",
            "product_name": "WellCore Probiotic Gut Health Gummies",
            "brand": "WellCore",
            "category": "Wellness",
            "source": "Marketplace",
            "source_url": "https://example.com/wellcore-gummies",
            "description": "Daily probiotic gummies with prebiotic fiber for digestive wellness.",
            "ingredients": "Probiotic blend, inulin, pectin, natural fruit flavor",
            "claims": "Gut health, digestive balance, vegan, no artificial flavors",
            "reviews": "Tastes good and easy to take. Wish CFU count and strain benefits were clearer.",
            "price": 18.5,
            "rating": 4.2,
        },
    ]
    return pd.DataFrame(rows, columns=REQUIRED_COLUMNS)


def read_uploaded_file(uploaded_file) -> pd.DataFrame:
    if uploaded_file is None:
        return pd.DataFrame(columns=REQUIRED_COLUMNS)
    name = uploaded_file.name.lower()
    if name.endswith(".csv"):
        return normalize_columns(pd.read_csv(uploaded_file))
    if name.endswith((".xlsx", ".xls")):
        return normalize_columns(pd.read_excel(uploaded_file))
    return pd.DataFrame(columns=REQUIRED_COLUMNS)


def extract_listing_from_url(url: str) -> dict:
    request = Request(url, headers={"User-Agent": "ProductIQ/1.0"})
    with urlopen(request, timeout=8) as response:
        html = response.read().decode("utf-8", errors="ignore")
    title = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.I | re.S)
    description = re.search(
        r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']',
        html,
        flags=re.I | re.S,
    )
    text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.I | re.S)
    text = clean_text(re.sub(r"<[^>]+>", " ", text))
    return {
        "product_id": url,
        "product_name": clean_text(title.group(1) if title else url),
        "brand": "",
        "category": "Unassigned",
        "source": "Web listing",
        "source_url": url,
        "description": clean_text(description.group(1) if description else text[:900]),
        "ingredients": "",
        "claims": text[:1400],
        "reviews": "",
        "price": np.nan,
        "rating": np.nan,
    }


def read_listing_urls(raw_urls: str) -> tuple[pd.DataFrame, list[str]]:
    rows = []
    errors = []
    urls = [url.strip() for url in re.split(r"[\n,]+", raw_urls or "") if url.strip()]
    for url in urls[:10]:
        try:
            rows.append(extract_listing_from_url(url))
        except (URLError, TimeoutError, ValueError, OSError) as exc:
            errors.append(f"{url} ({exc.__class__.__name__})")
    return pd.DataFrame(rows, columns=REQUIRED_COLUMNS), errors


def keyword_hits(text: str, taxonomy: dict[str, list[str]]) -> list[str]:
    lowered = text.lower()
    return [label for label, terms in taxonomy.items() if any(term in lowered for term in terms)]


def top_terms(series: pd.Series, limit: int = 10) -> list[str]:
    words = []
    for text in series.fillna(""):
        words.extend(
            word
            for word in re.findall(r"[a-z][a-z-]{3,}", text.lower())
            if word not in STOPWORDS
        )
    return [word for word, _count in Counter(words).most_common(limit)]


def enrich_products(df: pd.DataFrame) -> pd.DataFrame:
    enriched = df.copy()
    full_text = (
        enriched["product_name"].fillna("")
        + " "
        + enriched["description"].fillna("")
        + " "
        + enriched["ingredients"].fillna("")
        + " "
        + enriched["claims"].fillna("")
        + " "
        + enriched["reviews"].fillna("")
    )
    enriched["attribute_groups"] = full_text.apply(lambda text: ", ".join(keyword_hits(text, ATTRIBUTE_TAXONOMY)) or "Unclassified")
    enriched["claim_types"] = full_text.apply(lambda text: ", ".join(keyword_hits(text, CLAIM_PATTERNS)) or "No explicit claim")
    enriched["ingredient_signals"] = enriched["ingredients"].apply(lambda text: ", ".join(top_terms(pd.Series([text]), 6)))
    enriched["review_concepts"] = enriched["reviews"].apply(lambda text: ", ".join(top_terms(pd.Series([text]), 6)))
    enriched["listing_depth"] = full_text.apply(lambda text: min(100, int(len(text.split()) / 2)))
    enriched["opportunity_score"] = (
        enriched["attribute_groups"].ne("Unclassified").astype(int) * 20
        + enriched["claim_types"].ne("No explicit claim").astype(int) * 20
        + enriched["reviews"].str.len().gt(20).astype(int) * 20
        + enriched["rating"].fillna(3).clip(0, 5) * 8
        + enriched["listing_depth"].clip(0, 100) * 0.2
    ).round(0)
    enriched["attribution"] = enriched.apply(
        lambda row: f"{row['source']} | {row['source_url']}" if row["source_url"] else row["source"],
        axis=1,
    )
    return enriched


def get_openai_summary(df: pd.DataFrame, business_goal: str, model: str) -> tuple[dict, str]:
    api_key = get_secret("OPENAI_API_KEY")
    if not api_key:
        return {}, "OPENAI_API_KEY is not configured"
    try:
        from openai import OpenAI
    except ImportError:
        return {}, "OpenAI package is not installed"

    sample = df.head(40)[
        [
            "product_name",
            "brand",
            "category",
            "attribute_groups",
            "claim_types",
            "ingredient_signals",
            "review_concepts",
            "opportunity_score",
            "attribution",
        ]
    ].to_dict(orient="records")
    prompt = {
        "role": "You are a product data enrichment strategist for CPG and retail teams.",
        "business_goal": business_goal,
        "records": sample,
        "instruction": (
            "Return strict JSON with keys executive_summary, growth_opportunities, assortment_gaps, "
            "attribute_recommendations, attribution_risks. Use concise business language."
        ),
    }
    try:
        client = OpenAI(api_key=api_key)
        response = client.responses.create(model=model, input=json.dumps(prompt))
        text = response.output_text.strip()
        match = re.search(r"\{.*\}", text, flags=re.S)
        return json.loads(match.group(0) if match else text), ""
    except Exception as exc:
        return {}, f"GPT enrichment failed ({exc.__class__.__name__})"


def save_to_postgres(df: pd.DataFrame, business_goal: str, summary: dict) -> str:
    database_url = get_secret("DATABASE_URL")
    if not database_url:
        return "DATABASE_URL is not configured"
    try:
        import psycopg2
        from psycopg2.extras import execute_values
    except ImportError:
        return "PostgreSQL package is not installed"

    try:
        with psycopg2.connect(database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS product_enrichment_runs (
                        id BIGSERIAL PRIMARY KEY,
                        created_at TIMESTAMPTZ DEFAULT now(),
                        business_goal TEXT,
                        product_count INTEGER,
                        summary JSONB
                    );
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS enriched_products (
                        product_id TEXT,
                        run_id BIGINT REFERENCES product_enrichment_runs(id) ON DELETE CASCADE,
                        product_name TEXT,
                        brand TEXT,
                        category TEXT,
                        source TEXT,
                        source_url TEXT,
                        attribute_groups TEXT,
                        claim_types TEXT,
                        ingredient_signals TEXT,
                        review_concepts TEXT,
                        opportunity_score NUMERIC,
                        attribution TEXT,
                        PRIMARY KEY (product_id, run_id)
                    );
                    """
                )
                cur.execute(
                    "INSERT INTO product_enrichment_runs (business_goal, product_count, summary) VALUES (%s, %s, %s) RETURNING id",
                    (business_goal, len(df), json.dumps(summary or {})),
                )
                run_id = cur.fetchone()[0]
                rows = [
                    (
                        row["product_id"],
                        run_id,
                        row["product_name"],
                        row["brand"],
                        row["category"],
                        row["source"],
                        row["source_url"],
                        row["attribute_groups"],
                        row["claim_types"],
                        row["ingredient_signals"],
                        row["review_concepts"],
                        float(row["opportunity_score"]),
                        row["attribution"],
                    )
                    for row in df.to_dict(orient="records")
                ]
                execute_values(
                    cur,
                    """
                    INSERT INTO enriched_products (
                        product_id, run_id, product_name, brand, category, source, source_url,
                        attribute_groups, claim_types, ingredient_signals, review_concepts,
                        opportunity_score, attribution
                    ) VALUES %s
                    ON CONFLICT DO NOTHING
                    """,
                    rows,
                )
        return f"Saved enrichment run #{run_id} to PostgreSQL"
    except Exception as exc:
        return f"PostgreSQL save failed ({exc.__class__.__name__})"


st.markdown(
    """
    <style>
    .main .block-container { max-width: 1280px; padding-top: 1.25rem; }
    .hero {
        border: 1px solid #d9e2ec;
        border-radius: 8px;
        padding: 22px 24px;
        background: #f7fafc;
        margin-bottom: 18px;
    }
    .hero h1 { margin: 0 0 6px 0; font-size: 2.1rem; letter-spacing: 0; }
    .hero p { margin: 0; color: #52606d; }
    .insight {
        border: 1px solid #c6f6d5;
        border-left: 4px solid #0f766e;
        background: #f0fff4;
        border-radius: 8px;
        padding: 14px 16px;
        margin-bottom: 10px;
    }
    .note {
        border: 1px solid #d9e2ec;
        background: #ffffff;
        border-radius: 8px;
        padding: 12px 14px;
    }
    div[data-testid="stMetric"] {
        border: 1px solid #d9e2ec;
        border-radius: 8px;
        padding: 12px;
        background: #ffffff;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
        <h1>ProductIQ</h1>
        <p>AI-powered product data enrichment, insights, and attribution management for CPGs and retailers.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.title("ProductIQ")
    st.caption("Enrich product data with attributes, concepts, claims, ingredients, reviews, and source attribution.")
    data_source = st.selectbox(
        "Product data source",
        ["Demo product data", "Upload product file", "Product listing URLs", "Upload + listing URLs"],
    )
    category_filter = st.multiselect("Category focus", CATEGORIES, default=[])
    business_goal = st.text_area(
        "Business goal",
        value="Identify product attribute opportunities and growth whitespace across the current assortment.",
        height=92,
    )
    uploaded_file = None
    listing_urls = ""
    if data_source in {"Upload product file", "Upload + listing URLs"}:
        uploaded_file = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx", "xls"])
    if data_source in {"Product listing URLs", "Upload + listing URLs"}:
        listing_urls = st.text_area("Product listing URLs", placeholder="Paste one URL per line", height=110)
    use_openai = st.checkbox("Use OpenAI GPT insights", value=bool(get_secret("OPENAI_API_KEY")))
    model_name = st.text_input("OpenAI model", value=get_secret("OPENAI_MODEL", "gpt-4.1-mini"))
    persist = st.checkbox("Save to PostgreSQL", value=bool(get_secret("DATABASE_URL")))
    run_analysis = st.button("Enrich Products", type="primary", use_container_width=True)


frames = []
errors = []
if data_source == "Demo product data":
    frames.append(sample_products())
if data_source in {"Upload product file", "Upload + listing URLs"}:
    uploaded_df = read_uploaded_file(uploaded_file)
    if not uploaded_df.empty:
        frames.append(uploaded_df)
if data_source in {"Product listing URLs", "Upload + listing URLs"} and run_analysis:
    url_df, errors = read_listing_urls(listing_urls)
    if not url_df.empty:
        frames.append(url_df)
if not frames:
    frames.append(sample_products())
    st.info("Showing demo product data until a file or listing URL is provided.")
if errors:
    st.warning("Some listing URLs could not be read: " + "; ".join(errors[:3]))

products = pd.concat(frames, ignore_index=True).drop_duplicates(subset=["product_id", "source_url"])
if category_filter:
    filtered = products[products["category"].isin(category_filter)]
    if not filtered.empty:
        products = filtered

enriched = enrich_products(products)

summary = {}
if run_analysis and use_openai:
    with st.spinner("Generating AI enrichment insights..."):
        summary, ai_warning = get_openai_summary(enriched, business_goal, model_name)
    if ai_warning:
        st.warning(ai_warning)
elif use_openai:
    st.info("Click Enrich Products to generate GPT-powered insights.")

if run_analysis and persist:
    st.info(save_to_postgres(enriched, business_goal, summary))

metric_cols = st.columns(5)
metric_cols[0].metric("Products", f"{len(enriched):,}")
metric_cols[1].metric("Brands", f"{enriched['brand'].replace('', np.nan).nunique():,}")
metric_cols[2].metric("Categories", f"{enriched['category'].nunique():,}")
metric_cols[3].metric("Avg. opportunity", f"{enriched['opportunity_score'].mean():.0f}")
metric_cols[4].metric("Sources", f"{enriched['source'].nunique():,}")

st.markdown("### Executive Insight")
fallback_summary = (
    "The enriched product asset highlights claim territories, ingredient signals, review concepts, "
    "and attribution trails that can support assortment planning, content optimization, and whitespace discovery."
)
st.markdown(
    f"""
    <div class="insight">
    <strong>AI summary</strong><br>{summary.get("executive_summary", fallback_summary)}
    </div>
    """,
    unsafe_allow_html=True,
)

tab_overview, tab_attributes, tab_opportunities, tab_attribution, tab_data = st.tabs(
    ["Overview", "Attributes", "Opportunities", "Attribution", "Enriched Data"]
)

with tab_overview:
    col1, col2 = st.columns(2)
    category_counts = enriched["category"].value_counts().reset_index()
    category_counts.columns = ["Category", "Products"]
    col1.plotly_chart(px.bar(category_counts, x="Category", y="Products", color="Category"), use_container_width=True)
    score_by_brand = enriched.groupby("brand", as_index=False)["opportunity_score"].mean().sort_values("opportunity_score", ascending=False)
    col2.plotly_chart(px.bar(score_by_brand, x="brand", y="opportunity_score", color="opportunity_score", color_continuous_scale="Teal"), use_container_width=True)

with tab_attributes:
    exploded = enriched.assign(attribute_groups=enriched["attribute_groups"].str.split(", ")).explode("attribute_groups")
    attribute_counts = exploded["attribute_groups"].value_counts().reset_index()
    attribute_counts.columns = ["Attribute group", "Products"]
    st.plotly_chart(px.bar(attribute_counts, x="Products", y="Attribute group", orientation="h", color="Products", color_continuous_scale="Viridis"), use_container_width=True)
    st.dataframe(
        enriched[["product_name", "brand", "category", "attribute_groups", "claim_types", "ingredient_signals", "review_concepts"]],
        hide_index=True,
        use_container_width=True,
    )

with tab_opportunities:
    if summary:
        for label, key in [
            ("Growth opportunities", "growth_opportunities"),
            ("Assortment gaps", "assortment_gaps"),
            ("Attribute recommendations", "attribute_recommendations"),
        ]:
            st.write(label)
            for item in summary.get(key, []):
                st.markdown(f'<div class="note">{item}</div>', unsafe_allow_html=True)
    st.dataframe(
        enriched.sort_values("opportunity_score", ascending=False)[
            ["product_name", "brand", "category", "opportunity_score", "attribute_groups", "claim_types", "review_concepts"]
        ],
        hide_index=True,
        use_container_width=True,
    )

with tab_attribution:
    attribution_counts = enriched["source"].value_counts().reset_index()
    attribution_counts.columns = ["Source", "Products"]
    st.plotly_chart(px.pie(attribution_counts, names="Source", values="Products", hole=0.45), use_container_width=True)
    st.dataframe(
        enriched[["product_name", "brand", "source", "source_url", "attribution"]],
        hide_index=True,
        use_container_width=True,
    )

with tab_data:
    st.dataframe(enriched, hide_index=True, use_container_width=True)
