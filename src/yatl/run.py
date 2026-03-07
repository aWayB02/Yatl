import os
from step_executor import StepExecutor
from extractor import DataExtractor
from render import TemplateRenderer
import yaml
from itertools import takewhile


class Runner:
    def __init__(
        self,
        data_extractor: DataExtractor,
        template_render: TemplateRenderer,
    ):
        self.data_extractor = data_extractor
        self.template_render = template_render
        self.step_executor = StepExecutor(data_extractor, template_render)

    def _create_context(self, test_spec: dict):
        return {
            k: v for k, v in takewhile(lambda x: x[0] != "steps", test_spec.items())
        }

    def _load_test(self, yaml_path: str):
        with open(yaml_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def run_test(self, yaml_path: str):

        test_spec = self._load_test(yaml_path)
        context = self._create_context(test_spec)

        print(f"Run test: {test_spec.get('name', '')}")
        steps = test_spec.get("steps", [])
        for i, step in enumerate(steps, start=1):
            print(f"Step {i}: {step.get('name', '')}")
            context = self.step_executor.run_step(step, context)

        print("Test has been completed")

    def _search_files(self, current_path: str, item: str, files: list):
        full_path = os.path.join(current_path, item)
        if os.path.isfile(full_path) and (
            item.endswith(".test.yaml") or item.endswith(".test.yml")
        ):
            files.append(full_path)
            return
        elif os.path.isdir(full_path):
            for i in os.listdir(full_path):
                self._search_files(full_path, i, files)
        return files

    def run_all_tests(self):
        print("-" * 10)
        files = self._search_files(os.getcwd(), ".", [])
        for file in files:
            self.run_test(file)
            print("-" * 10)


if __name__ == "__main__":
    runner = Runner(
        DataExtractor(),
        TemplateRenderer(),
    )
    runner.run_all_tests()
