import yaml
import requests
from jinja2 import Template
import json


def render_data(data, context):

    if isinstance(data, str):
        return Template(data).render(context)
    elif isinstance(data, dict):
        return {key: render_data(value, context) for key, value in data.items()}
    elif isinstance(data, list):
        return [render_data(item, context) for item in data]
    else:
        return data


def extract_data(response, extract_spec):
    extracted = {}
    if response.headers.get("content-type") == "application/json":
        resp_json = response.json()
    else:
        resp_json = None

    for key, path in extract_spec.items():
        if path is None:
            if resp_json and key in resp_json:
                extracted[key] = resp_json[key]
            else:
                raise ValueError(f"Поле '{key}' не найдено в JSON-ответе")
        else:
            if resp_json and path in resp_json:
                extracted[key] = resp_json[path]
            else:
                raise ValueError(f"Не удалось извлечь '{key}' по пути '{path}'")
    return extracted


def check_expectations(response, expect_spec):
    expected_status = expect_spec.get("status")
    if expected_status is not None and response.status_code != expected_status:
        raise AssertionError(
            f"Ожидался статус {expected_status}, получен {response.status_code}"
        )

    expected_json = expect_spec.get("json")
    if expected_json is not None:
        try:
            resp_json = response.json()
        except json.JSONDecodeError:
            raise AssertionError("Ответ не является JSON, но ожидался JSON")

        for key, value in expected_json.items():
            if key not in resp_json:
                raise AssertionError(f"В ответе отсутствует ключ '{key}'")
            if resp_json[key] != value:
                raise AssertionError(
                    f"По ключу '{key}' ожидалось '{value}', получено '{resp_json[key]}'"
                )


def run_step(step, context):
    resolved_step = render_data(step, context)

    request_data = resolved_step["request"]
    method = request_data.get("method", "GET").upper()
    url = request_data["url"]
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
        check_expectations(response, resolved_step["expect"])

    if "extract" in resolved_step:
        extracted = extract_data(response, resolved_step["extract"])
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
    run_test("tests/example.test.yaml")
