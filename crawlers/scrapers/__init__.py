from .base_scraper import BaseScraper
try:
    from .cmcc_scraper import ChinaMobileScraper
except Exception:
    ChinaMobileScraper = None

try:
    from .telecom_scraper import ChinaTelecomScraper
except Exception:
    ChinaTelecomScraper = None

__all__ = ["BaseScraper", "ChinaTelecomScraper", "ChinaMobileScraper"]
