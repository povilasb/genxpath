"""Web browser utils for interactive XPath generation."""

from asyncio import Queue
import typing as t
from typing import TypedDict

from playwright.async_api import async_playwright, Page

# Some JavaScript utils to be run on a Web browser to communicate with Python.
_JS_INIT = """
() => {
    function getXPath(element) {
        const path = [];
        while (element && element.nodeType === Node.ELEMENT_NODE) {
            let index = 0;
            let sibling = element.previousElementSibling;
            while (sibling) {
                if (sibling.tagName === element.tagName) {
                    index++;
                }
                sibling = sibling.previousElementSibling;
            }

            const tagName = element.tagName.toLowerCase();
            const pathIndex = index > 0 ? `[${index + 1}]` : '';
            path.unshift(tagName + pathIndex);
            element = element.parentElement;
        }

        return '/' + path.join('/');
    }

    function addHoverBorder(event) {
        event.target.style.border = "2px solid red";
        event.target.addEventListener("mouseout", removeHoverBorder);

        pyEmitEvent({"event": "element_hover", "xpath": getXPath(event.target)});
    }

    function removeHoverBorder(event) {
        event.target.style.border = '';
    }

    document.querySelectorAll('*').forEach(element => {
        element.style.cursor = 'crosshair';
        element.addEventListener('mouseover', addHoverBorder);
    });
}
"""


class ElementHoverEvent(TypedDict):
    event: t.Literal["element_hover"]
    xpath: str


class HtmlLoadedEvent(TypedDict):
    event: t.Literal["html_loaded"]
    html: str


class WebBrowser:
    def __init__(self):
        self._page = None
        self._browser = None
        self._playwright = None

        self.events: Queue[ElementHoverEvent | HtmlLoadedEvent] = Queue()

    async def start(self) -> None:
        self._playwright = await async_playwright().__aenter__()
        self._browser = await self._playwright.firefox.launch(headless=False)
        self._page = await self._browser.new_page()
        self._page.on("load", lambda page: page.evaluate(_JS_INIT))

        async def on_html_loaded(page: Page):
            html = await page.content()
            await self.events.put({"event": "html_loaded", "html": html})

        self._page.on("domcontentloaded", lambda page: on_html_loaded(page))
        await self._page.expose_function(
            "pyEmitEvent", lambda event: self.events.put(event)
        )

    async def stop(self) -> None:
        if self._page is not None:
            await self._page.close()
            self._page = None

        if self._browser is not None:
            await self._browser.close()
            self._browser = None

        if self._playwright is not None:
            await self._playwright.stop()
            self._playwright = None

    async def goto(self, url: str) -> str:
        assert self._page is not None

        await self._page.goto(url)
        html_doc = await self._page.content()

        return html_doc
