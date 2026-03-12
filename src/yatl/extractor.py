from requests import Response
from typing import Any, Dict
import json
import re
from lxml import etree


class DataExtractor:
    """Extracts data from HTTP responses based on a specification.

    Supports JSON, XML, and text responses. Automatically detects content type
    and applies the appropriate extraction method.
    """

    def __init__(self):
        """Initializes the data extractor."""
        pass

    def _content_type(self, response: Response) -> str:
        """Extracts the media type from the response's Content-Type header.

        Args:
            response: The HTTP response object.

        Returns:
            The media type (e.g., 'application/json') without parameters,
            lowercased. If the header is missing, returns an empty string.
        """
        ct = response.headers.get("content-type", "")
        return ct.split(";")[0].strip().lower()

    def _extract_json(
        self, response: Response, extract_spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extracts fields from a JSON response according to the specification.

        Args:
            response: The HTTP response containing JSON data.
            extract_spec: A dictionary mapping output keys to JSON paths.
                If a path is None, the key is used as a direct field name.
                Currently supports only top-level or nested dict keys (dot notation
                not yet implemented).

        Returns:
            A dictionary with the extracted values.

        Raises:
            ValueError: If the response is not valid JSON, or a specified field
                cannot be found.
        """
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
        """Extracts fields from an XML response using XPath or tag names.

        Args:
            response: The HTTP response containing XML data.
            extract_spec: A dictionary mapping output keys to XPath expressions.
                If an XPath is None, the key is used as a tag name for `findall`.

        Returns:
            A dictionary with the extracted text of the first matching element.

        Raises:
            ValueError: If the response is not valid XML, or no element matches
                the given XPath/tag.
        """
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
        """Extracts substrings from a plain-text or HTML response.

        Args:
            response: The HTTP response with text content.
            extract_spec: A dictionary mapping output keys to patterns.
                If a pattern is None, it is treated as a literal substring.
                Otherwise, it is interpreted as a regular expression.

        Returns:
            A dictionary with the extracted substrings (the first match for each
            pattern). For literal substrings, the extracted value is the pattern
            itself.

        Raises:
            ValueError: If a pattern (literal or regex) is not found in the text.
        """
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
        """Main extraction entry point.

        Determines the content type of the response and delegates to the
        appropriate extraction method (JSON, XML, or text). If the content type
        is not recognized, attempts to parse the response as JSON as a fallback.

        Args:
            response: The HTTP response object.
            extract_spec: A dictionary describing what to extract (format depends
                on the content type).

        Returns:
            A dictionary with the extracted data.

        Raises:
            ValueError: If the content type is unsupported and the fallback JSON
                extraction also fails.
        """
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
