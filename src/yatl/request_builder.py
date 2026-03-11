class RequestBuilder:
    def __init__(self, context: dict, resolved_step: dict):
        self.context = context
        self.resolved_step = resolved_step

    def _build_url(self, url: str) -> str:
        base_url: str = self.context.get("base_url", "")
        return base_url.rstrip("/") + "/" + url.lstrip("/")

    def build(self):
        request_data: dict = self.resolved_step["request"]
        method = str(request_data.get("method", "GET")).upper()
        url: str = request_data.get("url", "")
        timeout = request_data.get("timeout", None)
        url = self._build_url(url)
        headers = request_data.get("headers", {})
        body: dict = request_data.get("body", {})
        json = body.get("json")
        params = request_data.get("params", {})
        cookies = request_data.get("cookies", {})
        return {
            "method": method,
            "url": url,
            "timeout": timeout,
            "headers": headers,
            "json": json,
            "params": params,
            "cookies": cookies,
        }
