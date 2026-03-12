from typing import Any, Dict, Union


class RequestBuilder:
    """Builds request arguments for `requests.request` from a resolved test step.

    Takes a context (global variables) and a resolved step (after template
    rendering) and produces a dictionary of keyword arguments suitable for
    `requests.request`.
    """

    def __init__(self, context: Dict[str, Any], resolved_step: Dict[str, Any]):
        """Initializes the builder with context and step data.

        Args:
            context: Global variables (e.g., base_url, previously extracted values).
            resolved_step: A single test step with resolved templates.
        """
        self.context = context
        self.resolved_step = resolved_step

    def _build_url(self, url: str) -> str:
        """Constructs a full URL by prepending the base URL from context.

        Args:
            url: The relative or absolute URL from the step.

        Returns:
            The absolute URL. If the context contains a `base_url`, it is
            prepended (with proper slash handling). If `url` is already absolute,
            the base URL is ignored (but currently not implemented).
        """
        base_url: str = self.context.get("base_url", "")
        return base_url.rstrip("/") + "/" + url.lstrip("/")

    def build_request_data(self) -> Dict[str, Any]:
        """Produces the keyword arguments for `requests.request`.

        Extracts method, URL, headers, parameters, cookies, timeout, and body
        from the step's `request` block. Automatically sets Content‑Type headers
        based on the body format (JSON, XML, text, form‑data, files).

        Returns:
            A dictionary that can be unpacked as `requests.request(**kwargs)`.

        Raises:
            ValueError: If the body has an unsupported type.
        """
        request_data: Dict[str, Any] = self.resolved_step["request"]
        method = str(request_data.get("method", "GET")).upper()
        url: str = request_data.get("url", "")
        timeout = request_data.get("timeout", None)
        url = self._build_url(url)
        headers = request_data.get("headers", {})
        body: Union[Dict[str, Any], str, None] = request_data.get("body")
        params = request_data.get("params", {})
        cookies = request_data.get("cookies", {})

        kwargs: Dict[str, Any] = {
            "method": method,
            "url": url,
            "timeout": timeout,
            "headers": headers,
            "params": params,
            "cookies": cookies,
        }

        if body is not None:
            if isinstance(body, dict):
                if "json" in body:
                    kwargs["json"] = body["json"]
                    if "Content-Type" not in headers:
                        headers["Content-Type"] = "application/json"
                elif "xml" in body:
                    xml_content = body["xml"]
                    if isinstance(xml_content, str):
                        kwargs["data"] = xml_content
                        if "Content-Type" not in headers:
                            headers["Content-Type"] = "application/xml"
                elif "text" in body:
                    kwargs["data"] = body["text"]
                    if "Content-Type" not in headers:
                        headers["Content-Type"] = "text/plain"
                elif "form" in body:
                    kwargs["data"] = body["form"]
                    if "Content-Type" not in headers:
                        headers["Content-Type"] = "application/x-www-form-urlencoded"
                elif "files" in body:
                    kwargs["files"] = body["files"]
                else:
                    kwargs["json"] = body
            elif isinstance(body, str):
                kwargs["data"] = body
                if "Content-Type" not in headers:
                    headers["Content-Type"] = "text/plain"
            else:
                raise ValueError(f"Unsupported body type: {type(body)}")

        kwargs["headers"] = headers
        return kwargs
