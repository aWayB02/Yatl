from typing import Any, Dict, Union


class RequestBuilder:
    def __init__(self, context: Dict[str, Any], resolved_step: Dict[str, Any]):
        self.context = context
        self.resolved_step = resolved_step

    def _build_url(self, url: str) -> str:
        base_url: str = self.context.get("base_url", "")
        return base_url.rstrip("/") + "/" + url.lstrip("/")

    def build_request_data(self) -> Dict[str, Any]:
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
