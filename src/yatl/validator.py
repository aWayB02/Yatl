from requests import Response
from typing import Any, Dict
import json
from lxml import etree


class ResponseValidator:
    """Validates an HTTP response against a set of expectations.

    Expectations can include status code, headers, and body content (JSON, XML,
    or plain text). Validation failures raise `AssertionError` with descriptive
    messages.
    """

    def __init__(self, response: Response, expect_spec: Dict[str, Any]):
        """Initializes the validator with a response and expectation spec.

        Args:
            response: The HTTP response to validate.
            expect_spec: A dictionary containing expectations (status, headers, body).
        """
        self.response = response
        self.expect_spec = expect_spec

    def _content_type(self) -> str:
        """Extracts the media type from the response's Content-Type header.

        Returns:
            The media type without parameters, lowercased.
            If the header is missing, returns an empty string.
        """
        ct = self.response.headers.get("content-type", "")
        return ct.split(";")[0].strip().lower()

    def _validate_status(self):
        """Validates that the response status code matches the expected one.

        Raises:
            AssertionError: If the status code does not match.
        """
        expected_status = self.expect_spec.get("status")
        if expected_status is not None and self.response.status_code != expected_status:
            raise AssertionError(
                f"Expected status {expected_status}, got {self.response.status_code}"
            )

    def _normalize_header_value(self, key: str, value: str) -> str:
        """Normalizes a header value for comparison.

        For the Content-Type header, removes parameters (e.g., charset).
        For other headers, returns the value unchanged.

        Args:
            key: Header name.
            value: Header value.

        Returns:
            Normalized value.
        """
        if key.lower() == "content-type":
            # Strip parameters like charset
            return value.split(";")[0].strip().lower()
        return value

    def _validate_headers(self):
        """Validates that all expected headers are present and match.

        Raises:
            AssertionError: If a header is missing or its normalized value
                does not match the expected one.
        """
        expected_headers = self.expect_spec.get("headers")
        if expected_headers:
            for key, expected_value in expected_headers.items():
                actual = self.response.headers.get(key)
                if actual is None:
                    raise AssertionError(f"Header '{key}' is missing")
                # Normalize both values for comparison
                norm_expected = self._normalize_header_value(key, expected_value)
                norm_actual = self._normalize_header_value(key, actual)
                if norm_actual != norm_expected:
                    raise AssertionError(
                        f"Header '{key}' expected '{norm_expected}', got '{norm_actual}' (original: '{actual}')"
                    )

    def _validate_json_body(self, expected_json: Dict[str, Any]):
        """Validates that the JSON response matches the expected structure.

        Args:
            expected_json: A dictionary of expected key‑value pairs.
                Nested dictionaries are validated recursively.

        Raises:
            AssertionError: If the response is not valid JSON, or any key
                is missing, or any value differs.
        """
        try:
            data = self.response.json()
        except json.JSONDecodeError:
            raise AssertionError("Response is not valid JSON")
        self._validate_json_response(data, expected_json)

    def _validate_json_response(
        self, data: Dict[str, Any], expected_json: Dict[str, Any]
    ):
        """Recursively validates a JSON object against an expected dictionary.

        Args:
            data: The actual JSON dictionary (or sub-dictionary).
            expected_json: The expected dictionary for this level.

        Raises:
            AssertionError: If a key is missing or a value mismatches.
        """
        for key, value in expected_json.items():
            if key not in data:
                raise AssertionError(f"Key '{key}' is missing in response")
            if isinstance(data[key], dict) and isinstance(value, dict):
                self._validate_json_response(data[key], value)
            elif data[key] != value:
                raise AssertionError(
                    f"For key '{key}' expected '{value}', got '{data[key]}'"
                )

    def _validate_xml_body(self, expected_xml: Dict[str, Any]):
        """Validates that the XML response contains elements with expected text.

        Args:
            expected_xml: A dictionary mapping XPath expressions to expected
                text values.

        Raises:
            AssertionError: If the response is not valid XML, an XPath matches
                no elements, or the text of the first matching element differs.
        """
        try:
            root = etree.fromstring(self.response.content)
        except etree.XMLSyntaxError:
            raise AssertionError("Response is not valid XML")
        for xpath, expected_value in expected_xml.items():
            elements = root.xpath(xpath)
            if not elements:
                raise AssertionError(f"XML element with xpath '{xpath}' not found")
            actual = elements[0].text
            if actual != expected_value:
                raise AssertionError(
                    f"XML element '{xpath}' expected '{expected_value}', got '{actual}'"
                )

    def _validate_text_body(self, expected_text: str):
        """Validates that the plain‑text response contains a given substring.

        Args:
            expected_text: The substring that must appear in the response body.

        Raises:
            AssertionError: If the substring is not found.
        """
        actual_text = self.response.text
        if expected_text not in actual_text:
            raise AssertionError(
                f"Expected text '{expected_text}' not found in response"
            )

    def check_expectations(self):
        """Runs all validations defined in the expectation spec.

        Validates status, headers, and body (based on content‑type). The body
        validation is dispatched to the appropriate method (JSON, XML, or text).

        Raises:
            AssertionError: If any validation fails.
        """
        self._validate_status()
        self._validate_headers()

        body_spec = self.expect_spec.get("body")
        if body_spec is None:
            return

        content_type = self._content_type()
        if "json" in content_type and "json" in body_spec:
            self._validate_json_body(body_spec["json"])
        elif "xml" in content_type and "xml" in body_spec:
            self._validate_xml_body(body_spec["xml"])
        elif "text/plain" in content_type and "text" in body_spec:
            self._validate_text_body(body_spec["text"])
        else:
            # Fallback: try to validate as JSON if body_spec is dict
            if isinstance(body_spec, dict) and "json" in body_spec:
                self._validate_json_body(body_spec["json"])
            else:
                raise AssertionError(
                    f"Unsupported body validation for content-type: {content_type}"
                )
