import yaml
import requests
from render import TemplateRenderer
from extractor import DataExtractor
from validator import ResponseValidator


def run_step(step, context):

    template_render = TemplateRenderer()
    data_extractor = DataExtractor()
    resolved_step = template_render.render_data(step, context)

    request_data = resolved_step["request"]
    method = request_data.get("method", "GET").upper()
    url = request_data.get("url", "")
    timeout = request_data.get("timeout", None)
    if not url.startswith(("http://", "https://")):
        base_url = context.get("base_url", "")
        url = base_url.rstrip("/") + "/" + url.lstrip("/")

    headers = request_data.get("headers", {})
    json_body = request_data.get("json")
    params = request_data.get("params")
    cookies = request_data.get("cookies")

    response = requests.request(
        method=method,
        url=url,
        headers=headers,
        json=json_body,
        params=params,
        timeout=timeout,
        cookies=cookies,
    )

    if "expect" in resolved_step:
        validator = ResponseValidator(response, resolved_step["expect"])
        validator.check_expectations()

    if "extract" in resolved_step:
        extracted = data_extractor.extract(response, resolved_step["extract"])
        context.update(extracted)

    return context


def run_test(yaml_path):
    with open(yaml_path, "r", encoding="utf-8") as f:
        test_spec = yaml.safe_load(f)

    def create_context(test_spec):
        context = {}
        for k, v in test_spec.items():
            if k == "steps":
                return context
            context[k] = v
        return context

    context = create_context(test_spec)

    print(f"Run test: {test_spec.get('name', '')}")
    steps = test_spec.get("steps", [])
    for i, step in enumerate(steps, start=1):
        print(f"Step {i}: {step.get('name', '')}")
        context = run_step(step, context)

    print("Test has been completed")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        yaml_path = sys.argv[1]
    else:
        yaml_path = "tests/example.test.yaml"
    run_test(yaml_path)
