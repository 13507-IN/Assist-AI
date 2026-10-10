import asyncio
import logging
from typing import Any, Optional
from urllib.parse import urljoin, urlparse

import aiohttp
from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)


class CompanyResearchService:
    """Verify suggested companies against their public websites."""

    def __init__(self, concurrency: int = 5, timeout_seconds: int = 8):
        self.session: Optional[aiohttp.ClientSession] = None
        self.semaphore = asyncio.Semaphore(concurrency)
        self.timeout = aiohttp.ClientTimeout(total=timeout_seconds)

    async def initialize(self) -> None:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=self.timeout,
                headers={"User-Agent": "OutreachAI/1.0 company-research"},
            )

    async def close(self) -> None:
        if self.session and not self.session.closed:
            await self.session.close()

    async def research_companies(self, companies: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Research at most five company websites concurrently."""
        return await asyncio.gather(*(self.research_company(company) for company in companies))

    async def research_company(self, company: dict[str, Any]) -> dict[str, Any]:
        async with self.semaphore:
            researched = dict(company)
            website = self._normalise_url(researched.get("website"))
            researched["website"] = website
            if not website:
                researched["research_error"] = "Gemini did not provide a company website"
                return researched

            try:
                homepage = await self._fetch(website)
                parsed = self._parse_html(homepage, researched["name"])
                hiring = await self._check_hiring_pages(website)
                researched.update(
                    {
                        "summary": parsed.get("description")
                        or parsed.get("preview")
                        or researched.get("reasoning", ""),
                        "domain": urlparse(website).netloc.removeprefix("www."),
                        "hiring_signal": (
                            "active" if hiring.get("active") else researched.get("hiring_signal", "unknown")
                        ),
                        "source": hiring.get("source") or website,
                        "research_error": None,
                    }
                )
            except Exception as exc:
                researched["research_error"] = f"Website check failed: {exc}"
                logger.warning("Website check failed for %s: %s", researched.get("name"), exc)
            return researched

    async def _fetch(self, url: str) -> str:
        if self.session is None:
            await self.initialize()
        assert self.session is not None
        async with self.session.get(url, allow_redirects=True) as response:
            response.raise_for_status()
            return await response.text(errors="ignore")

    async def _check_hiring_pages(self, website: str) -> dict[str, Any]:
        for path in ("careers", "jobs"):
            url = urljoin(website.rstrip("/") + "/", path)
            try:
                html = await self._fetch(url)
                if self._has_active_job_postings(html):
                    return {"active": True, "source": url}
            except Exception:
                continue
        return {"active": False, "source": website}

    @staticmethod
    def _normalise_url(value: Optional[str]) -> Optional[str]:
        if not value:
            return None
        value = value.strip()
        return value if value.startswith(("http://", "https://")) else f"https://{value}"

    @staticmethod
    def _parse_html(html: str, company_name: str) -> dict[str, Optional[str]]:
        soup = BeautifulSoup(html, "lxml")
        title = soup.find("title")
        description = soup.find("meta", attrs={"name": "description"})
        paragraphs = " ".join(
            paragraph.get_text(" ", strip=True) for paragraph in soup.find_all("p")[:5]
        )
        return {
            "company_name": company_name,
            "title": title.get_text(" ", strip=True) if title else None,
            "description": description.get("content", "").strip() if description else None,
            "preview": paragraphs[:500] or None,
        }

    @staticmethod
    def _has_active_job_postings(html: str) -> bool:
        text = BeautifulSoup(html, "lxml").get_text(" ", strip=True).lower()
        signals = (
            "open position",
            "open role",
            "job opening",
            "join our team",
            "we are hiring",
            "view jobs",
        )
        return any(signal in text for signal in signals)
