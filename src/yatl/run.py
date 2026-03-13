import os
from .step_executor import StepExecutor
from .extractor import DataExtractor
from .render import TemplateRenderer
import yaml
from itertools import takewhile


class Runner:
    """Orchestrates the execution of YAML-based test suites.

    Loads test specifications from YAML files, runs each step sequentially,
    and maintains a context that is passed between steps.
    """

    def __init__(
        self,
        data_extractor: DataExtractor,
        template_render: TemplateRenderer,
    ):
        """Initializes the runner with required services.

        Args:
            data_extractor: Used to extract values from HTTP responses.
            template_render: Used to render templates in test steps.
        """
        self.data_extractor = data_extractor
        self.template_render = template_render
        self.step_executor = StepExecutor(data_extractor, template_render)

    def create_context(self, test_spec: dict):
        """Creates the initial context from the test specification.

        The context consists of all top‑level keys that appear before the
        "steps" key in the YAML document. This typically includes `base_url`,
        `name`, `description`, and any user‑defined variables.

        Args:
            test_spec: The parsed YAML dictionary.

        Returns:
            A dictionary containing the initial context.
        """
        return {
            k: v for k, v in takewhile(lambda x: x[0] != "steps", test_spec.items())
        }

    def _load_test(self, yaml_path: str):
        """Loads and parses a YAML test file.

        Args:
            yaml_path: Path to the .test.yaml or .test.yml file.

        Returns:
            The parsed YAML as a dictionary, or None if the file is empty.
        """
        with open(yaml_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _is_skipped_test(self, test_spec: dict):
        """Checks if a test is skipped based on the "scip" flag.

        Args:
            test_spec: The parsed YAML dictionary.

        Returns:
            True if the test is skipped, False otherwise.
        """
        if test_spec.get("skip", False):
            print(f"Test {test_spec.get('name', '')} skipped")
            return True
        return False

    def _is_skipped_step(self, step: dict):
        """Checks if a step is skipped based on the "skip" flag.

        Args:
            step: The parsed YAML dictionary.

        Returns:
            True if the step is skipped, False otherwise.
        """
        if step.get("skip", False):
            print(f"Step {step.get('name', '')} skipped")
            return True
        return False

    def run_test(self, yaml_path: str):
        """Executes a single test file.

        Loads the test, creates the initial context, runs each step in order,
        and prints progress messages. The context is updated after each step
        with extracted values.

        Args:
            yaml_path: Path to the test YAML file.
        """
        test_spec: dict = self._load_test(yaml_path)
        if test_spec is None:
            return
        context = self.create_context(test_spec)
        if self._is_skipped_test(test_spec):
            return
        print(f"Run test: {test_spec.get('name', '')}")
        steps = test_spec.get("steps", [])
        for i, step in enumerate(steps, start=1):
            step: dict
            if step is None:
                continue
            if self._is_skipped_step(step):
                continue
            print(f"Step {i}: {step.get('name', '')}")
            context = self.step_executor.run_step(step, context)

        print("Test has been completed")

    def _search_files(self, current_path: str, item: str, files: list):
        """Recursively searches for test files with a .test.yaml/.test.yml suffix.

        Args:
            current_path: Base directory for the search.
            item: Current file or directory name relative to `current_path`.
            files: Accumulator list where found file paths are appended.

        Returns:
            The same `files` list (modified in-place).
        """
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
        """Discovers and runs all test files in the current working directory.

        Searches recursively for files ending with .test.yaml or .test.yml,
        executes each one, and prints separators between tests.
        """
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
