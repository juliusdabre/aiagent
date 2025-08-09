import asyncio, re, subprocess, sys
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
from playwright.async_api import async_playwright

# Ensure Chromium is available (first boot on Streamlit Cloud)
def _ensure_chromium_installed():
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"],
                       check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception:
        # postBuild should install it; ignore failures here
        pass

_ensure_chromium_installed()

PRICE_RX = re.compile(r"\$?\s*([0-9][0-9\.,]{2,})", re.I)

@dataclass
class PropertyCard:
    title: str
    address: str
    price_text: str
    url: str
    beds: Optional[str] = None
    baths: Optional[str] = None
    parking: Optional[str] = None
    suburb: Optional[str] = None

def parse_price_to_number(price_text: str) -> Optional[int]:
    if not price_text:
        return None
    txt = price_text.replace(" ", "").lower()
    m = PRICE_RX.search(txt)
    if not m:
        return None
    num = m.group(1).replace(",", "")
    try:
        val = float(num)
        if "k" in txt and val < 5000:
            val *= 1000
        return int(round(val))
    except:
        return None

async def fetch_page_listings(page, url: str) -> List[PropertyCard]:
    await page.goto(url, wait_until="domcontentloaded")
    await page.wait_for_timeout(1000)

    cards = []
    listing_cards = await page.locator('[data-testid="listing-card-wrapper"]').all()
    for lc in listing_cards:
        try:
            link = await lc.locator('a[data-testid="listing-card-link"]').first.get_attribute("href")
            full_url = f"https://www.realestate.com.au{link}" if link and link.startswith("/") else (link or "")
            title = await lc.locator('[data-testid="listing-card-title"]').first.text_content()
            address = await lc.locator('[data-testid="listing-card-subtitle"]').first.text_content()
            price_text = await lc.locator('[data-testid="listing-card-price"]').first.text_content()
            beds = await lc.locator('[data-testid="property-features-text"]:has-text("bed")').first.text_content().catch(lambda _: None)
            baths = await lc.locator('[data-testid="property-features-text"]:has-text("bath")').first.text_content().catch(lambda _: None)
            parking = await lc.locator('[data-testid="property-features-text"]:has-text("car")').first.text_content().catch(lambda _: None)

            # suburb: first part before comma, stripped
            suburb = (address or "").split(",")[0].strip() if address else None

            cards.append(PropertyCard(
                title=(title or "").strip(),
                address=(address or "").strip(),
                price_text=(price_text or "").strip(),
                url=full_url or "",
                beds=beds or None,
                baths=baths or None,
                parking=parking or None,
                suburb=suburb or None
            ))
        except:
            continue
    return cards

def _state_slug(state_code: str) -> str:
    code = (state_code or "").strip().lower()
    return code or "wa"

async def find_properties(min_price: int, max_price: int, state_code: str = "wa", max_pages: int = 5) -> List[Dict]:
    """
    Crawl realestate.com.au listings for a given Australian state and price range.
    state_code: One of wa, nsw, vic, qld, sa, tas, act, nt.
    """
    state = _state_slug(state_code)
    base = "https://www.realestate.com.au/buy/between-{}-{}-in-{}/list-{}"
    results: List[PropertyCard] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for page_num in range(1, max_pages + 1):
            url = base.format(min_price, max_price, state, page_num)
            page_cards = await fetch_page_listings(page, url)
            if not page_cards:
                break
            for c in page_cards:
                num = parse_price_to_number(c.price_text)
                if num is None:
                    continue
                if min_price <= num <= max_price:
                    results.append(c)
            await page.wait_for_timeout(900)

        await browser.close()

    seen = set()
    uniq: List[Dict] = []
    for c in results:
        if c.url in seen:
            continue
        seen.add(c.url)
        uniq.append(asdict(c))
    return uniq