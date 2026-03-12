from requests import Response
from typing import Any, Dict
import json
import re
from lxml import etree


class DataExtractor:
    def __init__(self):
        pass

    def _content_type(self, response: Response) -> str:
        ct = response.headers.get("content-type", "")
        return ct.split(";")[0].strip().lower()

    def _extract_json(
        self, response: Response, extract_spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        extracted = {}
        try:
            data = response.json()
        except json.JSONDecodeError:
            raise ValueError("Response is not valid JSON")

        for key, path in extract_spec.items():
            if path is None:
                if key in data:
                    extracted[key] = data[key]
                else:
                    raise ValueError(f"Field '{key}' not found in JSON response")
            else:
                # Simple dot notation? For now assume nested dict key
                # TODO: implement JSONPath
                if isinstance(data, dict) and path in data:
                    extracted[key] = data[path]
                else:
                    raise ValueError(f"Failed to extract '{key}' at path '{path}'")
        return extracted

    def _extract_xml(
        self, response: Response, extract_spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        extracted = {}
        try:
            root = etree.fromstring(response.content)
        except etree.XMLSyntaxError:
            raise ValueError("Response is not valid XML")

        for key, xpath in extract_spec.items():
            if xpath is None:
                # Use key as tag name
                elements = root.findall(key)
            else:
                elements = root.xpath(xpath)
            if elements:
                # Take first element's text
                extracted[key] = elements[0].text
            else:
                raise ValueError(f"XML element '{key}' not found with xpath '{xpath}'")
        return extracted

    def _extract_text(
        self, response: Response, extract_spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        extracted = {}
        text = response.text
        for key, pattern in extract_spec.items():
            if pattern is None:
                # Treat pattern as literal substring
                if pattern in text:
                    extracted[key] = pattern
                else:
                    raise ValueError(f"Pattern '{pattern}' not found in text")
            else:
                # Use regex
                match = re.search(pattern, text)
                if match:
                    extracted[key] = match.group(0)
                else:
                    raise ValueError(f"Regex '{pattern}' not found in text")
        return extracted

    def extract(
        self, response: Response, extract_spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        content_type = self._content_type(response)

        if "json" in content_type:
            return self._extract_json(response, extract_spec)
        elif "xml" in content_type:
            return self._extract_xml(response, extract_spec)
        elif "text/plain" in content_type or "text/html" in content_type:
            return self._extract_text(response, extract_spec)
        else:
            # Fallback to trying JSON if possible
            try:
                return self._extract_json(response, extract_spec)
            except ValueError:
                raise ValueError(f"Unsupported content-type: {content_type}")
