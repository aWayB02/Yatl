import yaml
import requests
from render import TemplateRenderer
from extractor import DataExtractor
from validator import ResponseValidator
import os
from utils import search_files
from request_builder import RequestBuilder


def run_step(step, context: dict):

    data_extractor = DataExtractor()
    template_render = TemplateRenderer()
    resolved_step = template_render.render_data(step, context)
    request_builder = RequestBuilder(step, context, resolved_step)
    response = requests.request(**request_builder.build())

    if "expect" in resolved_step:
        validator = ResponseValidator(response, resolved_step["expect"])
        validator.check_expectations()

    if "extract" in resolved_step:
        extracted = data_extractor.extract(response, resolved_step["extract"])
        context.update(extracted)

    return context


def run_test(yaml_path: str):
    with open(yaml_path, "r", encoding="utf-8") as f:
        test_spec = yaml.safe_load(f)

    def create_context(test_spec: dict):
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
    path = os.getcwd()
    print("-" * 10)
    for file in search_files(path, ".", []):
        run_test(file)
        print("-" * 10)
