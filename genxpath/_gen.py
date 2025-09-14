from parsel import Selector
from dataclasses import dataclass


def find_xpaths(model: dict[str, str], html_doc: str) -> dict[str, list[str]]:
    """For all model fields finds all possible XPaths to the value."""
    field_xpaths: dict[str, list[str]] = {}

    doc = Selector(text=html_doc)
    for field, sample_value in model.items():
        if sample_value:
            field_xpaths[field] = find_xpaths_for(sample_value, doc)
        else:
            field_xpaths[field] = []

    return field_xpaths


def find_xpaths_for(value: str, doc: Selector) -> list[str]:
    """Value may be in a text node or an attribute - find an xpath to it."""
    xpaths: list[str] = []

    # 1. Find elements that contain value we're looking for.
    selectors = _find_element_with_value(doc, value)
    for sel in selectors:
        # 2. Generate shortest unique XPath for the element.
        xpath = _shortest_unique_xpath(doc, sel.in_elem)
        if sel.in_attr:
            xpath = f"{xpath}/@{sel.in_attr}"
        else:
            xpath = f"{xpath}/text()"

        xpaths.append(xpath)

    # 3. Optionally could infer operations required to extract the exact value.

    return xpaths


def minimize_xpath(doc: Selector | str, xpath: str) -> str:
    """Try to minimize the XPath for a given element."""
    if isinstance(doc, str):
        doc = Selector(text=doc)

    if xpath.endswith("/text()"):
        xpath = xpath[: -len("/text()")]
        text_nodes = True
    else:
        text_nodes = False

    if not (element := next(iter(doc.xpath(xpath)), None)):
        return xpath

    shorter_xpath = _shortest_unique_xpath(doc, element)
    if text_nodes:
        return f"{shorter_xpath}/text()"
    return shorter_xpath


@dataclass
class _ValueSelector:
    value: str
    in_elem: Selector
    in_attr: str | None = None


def _find_element_with_value(doc: Selector, value: str) -> list[_ValueSelector]:
    # Find element with value in text.
    selectors = doc.xpath(f'//*[normalize-space(text())="{value}"]')
    # Find element with value in an attribute.
    attr_selectors = doc.xpath(f'//*[@*[normalize-space()="{value}"]]')
    return [_ValueSelector(value=value, in_elem=sel) for sel in selectors] + [
        _ValueSelector(value=value, in_elem=sel, in_attr=attr)
        for sel in attr_selectors
        for attr, attr_value in sel.attrib.items()
        if attr_value == value
    ]


def _shortest_unique_xpath(doc: Selector, element: Selector) -> str:
    """
    Try to generate the shortest unique XPath for a given element.
    """
    if short_xpath := _xpath_by_attr(doc, element):
        return short_xpath

    full_path: str = element.root.getroottree().getpath(element.root)

    # Try to minimize the full_path by going from children to parents.
    suffix_nodes = list[str]()
    nodes = full_path.split("/")
    while nodes:
        suffix_nodes.insert(0, nodes.pop())

        prefix_xpath = "/".join(nodes)
        prev_elem = doc.xpath(prefix_xpath)
        if short_xpath := _xpath_by_attr(doc, prev_elem):
            return f"{short_xpath}/{'/'.join(suffix_nodes)}"

    # Fallback to full absolute path
    return full_path


def _xpath_by_attr(doc: Selector, element: Selector) -> str | None:
    # 1. Prefer unique ID
    el_id = element.attrib.get("id")
    if el_id and len(doc.xpath(f"//*[@id='{el_id}']")) == 1:
        return f"//*[@id='{el_id}']"

    # 2. Prefer unique attributes
    for attr in ["data-testid", "data-id", "name", "class", "itemprop"]:
        val = element.attrib.get(attr)
        if val and len(doc.xpath(f"//*[@{attr}='{val}']")) == 1:
            return f"//*[@{attr}='{val}']"

    return None
