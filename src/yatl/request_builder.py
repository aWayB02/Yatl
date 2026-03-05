

class RequestBuilder:
    def __init__(self, step, context: dict, resolved_step: dict):
        self.step = step
        self.context = context
        self.resolved_step = resolved_step

    def build(self):
        request_data = self.resolved_step["request"]
        method = request_data.get("method", "GET").upper()
        url: str = request_data.get("url", "")
        timeout = request_data.get("timeout", None)
        if not url.startswith(("http://", "https://")):
            base_url = self.context.get("base_url", "")
            url = base_url.rstrip("/") + "/" + url.lstrip("/")

        headers = request_data.get("headers", {})
        json_body = request_data.get("json")
        params = request_data.get("params")
        cookies = request_data.get("cookies")
        return {
            "method": method,
            "url": url,
            "timeout": timeout,
            "headers": headers,
            "json": json_body,
            "params": params,
            "cookies": cookies,
        }
