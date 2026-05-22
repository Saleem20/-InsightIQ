"""
Brand catalog for BrandTrack KPIs.

Top brands per category per country, sourced from public market-share reports
(Statista / Euromonitor / company data, 2024-2026 approximate rankings).
Edit this file to add or remove brands without touching app logic.
"""

from typing import Dict, List

# Country code -> human name (used in UI labels)
COUNTRIES: Dict[str, str] = {
    "US": "United States",
    "IN": "India",
    "CN": "China",
    "GB": "United Kingdom",
}

# Default category-level search context appended to brand queries.
# Improves recall and disambiguation on common-word brand names.
CATEGORY_CONTEXT: Dict[str, str] = {
    "Toothpaste": "toothpaste oral care",
    "Mouthwash": "mouthwash oral rinse",
    "VMS": "vitamins minerals supplements",
    "Beverages": "soft drink beverage",
    "Digestive": "antacid digestive health",
    "Shoes": "shoes footwear sneakers",
    "SUV": "SUV car model",
}

# Brand catalog: {category: {country: [brand_1, brand_2, ...]}}
# Cleaned from the source markdown — multi-brand cells split, "Others" dropped.
CATALOG: Dict[str, Dict[str, List[str]]] = {
    "Toothpaste": {
        "US": ["Crest", "Colgate", "Sensodyne", "Arm & Hammer"],
        "IN": ["Colgate", "Pepsodent", "Sensodyne", "Close-Up", "Patanjali Dant Kanti", "Dabur Red"],
        "CN": ["Yunnan Baiyao", "Darlie", "Colgate", "Crest", "Zhonghua"],
        "GB": ["Colgate", "Sensodyne", "Oral-B", "Aquafresh"],
    },
    "Mouthwash": {
        "US": ["Listerine", "Crest", "Colgate"],
        "IN": ["Listerine", "Colgate", "Closeup"],
        "CN": ["Listerine", "Colgate", "Yunnan Baiyao"],
        "GB": ["Listerine", "Corsodyl", "Colgate"],
    },
    "VMS": {
        "US": ["Centrum", "Nature Made", "One A Day", "Vitafusion"],
        "IN": ["Himalaya", "Dabur", "Patanjali", "Supradyn"],
        "CN": ["By-Health", "Centrum", "Tong Ren Tang"],
        "GB": ["Vitabiotics", "Seven Seas", "Centrum", "Berocca", "Haliborange"],
    },
    "Beverages": {
        "US": ["Coca-Cola", "Pepsi", "Mountain Dew", "Dr Pepper", "Sprite"],
        "IN": ["Coca-Cola", "Thums Up", "Pepsi", "Sprite", "Limca", "Maaza"],
        "CN": ["Nongfu Spring", "Coca-Cola", "Sprite", "Wanglaoji"],
        "GB": ["Coca-Cola", "Pepsi", "Lucozade"],
    },
    "Digestive": {
        "US": ["Pepcid", "Gaviscon", "Tums", "Alka-Seltzer", "Prilosec"],
        "IN": ["Digene", "Gelusil", "Eno", "Pudin Hara"],
        "CN": ["Gaviscon", "Bayer Digestive"],
        "GB": ["Pepcid", "Gaviscon", "Rennie", "Gaviscon Double Action"],
    },
    "Shoes": {
        "US": ["Nike", "Skechers", "Adidas", "Under Armour", "New Balance"],
        "IN": ["Bata", "Nike", "Adidas", "Relaxo", "Red Chief"],
        "CN": ["Belle", "Li Ning", "Anta", "Nike", "Adidas"],
        "GB": ["Nike", "Adidas", "Clarks", "Dr. Martens"],
    },
    "SUV": {
        "US": ["Toyota RAV4", "Honda CR-V", "Chevrolet Equinox", "Tesla Model Y"],
        "IN": ["Hyundai Creta", "Kia Seltos", "Tata Nexon", "Mahindra XUV", "Maruti Brezza"],
        "CN": ["Tesla Model Y", "BYD Song", "Toyota RAV4"],
        "GB": ["Ford Puma", "Kia Sportage", "Nissan Qashqai"],
    },
}


def categories() -> List[str]:
    return list(CATALOG.keys())


def brands_for(category: str, country: str) -> List[str]:
    return CATALOG.get(category, {}).get(country, [])


def context_for(category: str, country: str) -> str:
    base = CATEGORY_CONTEXT.get(category, category.lower())
    country_name = COUNTRIES.get(country, country)
    return f"{base} {country_name}".strip()


def as_dataframe():
    """Return the catalog as a tidy DataFrame for inspection or export."""
    import pandas as pd

    rows = []
    for category, by_country in CATALOG.items():
        for country, brands in by_country.items():
            for rank, brand in enumerate(brands, start=1):
                rows.append(
                    {
                        "category": category,
                        "country": country,
                        "country_name": COUNTRIES.get(country, country),
                        "rank": rank,
                        "brand": brand,
                    }
                )
    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = as_dataframe()
    print(df.to_string(index=False))
    print(f"\nTotal: {len(df)} brand x country combinations across {df['category'].nunique()} categories.")
