from requests import Response
from typing import Any, Dict
import json
from lxml import etree


class ResponseValidator:
    def __init__(self, response: Response, expect_spec: Dict[str, Any]):
        self.response = response
        self.expect_spec = expect_spec

    def _content_type(self) -> str:
        ct = self.response.headers.get("content-type", "")
        return ct.split(";")[0].strip().lower()

    def _validate_status(self):
        expected_status = self.expect_spec.get("status")
        if expected_status is not None and self.response.status_code != expected_status:
            raise AssertionError(
                f"Expected status {expected_status}, got {self.response.status_code}"
            )

    def _normalize_header_value(self, key: str, value: str) -> str:
        """Normalize header value for comparison."""
        if key.lower() == "content-type":
            # Strip parameters like charset
            return value.split(";")[0].strip().lower()
        return value

    def _validate_headers(self):
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
        try:
            data = self.response.json()
        except json.JSONDecodeError:
            raise AssertionError("Response is not valid JSON")
        self._validate_json_response(data, expected_json)

    def _validate_json_response(
        self, data: Dict[str, Any], expected_json: Dict[str, Any]
    ):
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
        actual_text = self.response.text
        if expected_text not in actual_text:
            raise AssertionError(
                f"Expected text '{expected_text}' not found in response"
            )

    def check_expectations(self):
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
