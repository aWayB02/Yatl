from .render import TemplateRenderer
from .extractor import DataExtractor
from .validator import ResponseValidator
from .request_builder import RequestBuilder
import requests
from typing import Any, Dict


class StepExecutor:
    """Executes a single test step.

    Responsibilities:
      - Render templates in the step using the current context.
      - Build and send the HTTP request.
      - Validate the response against expectations (if any).
      - Extract data from the response and update the context.
    """

    def __init__(
        self,
        data_extractor: DataExtractor,
        template_renderer: TemplateRenderer,
    ):
        """Initializes the step executor with required services.

        Args:
            data_extractor: Used to extract values from responses.
            template_renderer: Used to render templates in the step.
        """
        self.data_extractor = data_extractor
        self.template_renderer = template_renderer

    def _create_request(
        self, context: Dict[str, Any], resolved_step: Dict[str, Any]
    ) -> requests.Response:
        """Builds and sends the HTTP request described by the step.

        Args:
            context: The current context (contains base_url, previous extracts, etc.)
            resolved_step: The step dictionary after template rendering.

        Returns:
            The HTTP response object.
        """
        request_builder = RequestBuilder(context, resolved_step)
        data = request_builder.build_request_data()
        response = requests.request(**data)
        return response

    def run_step(self, step: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Executes a single test step and returns the updated context.

        The step is first rendered with the current context, then the request
        is sent. If the step contains an `expect` block, the response is validated.
        If it contains an `extract` block, values are extracted and added to the
        context for subsequent steps.

        Args:
            step: The raw step dictionary (may contain templates).
            context: The current context (global variables).

        Returns:
            The updated context (with newly extracted values, if any).
        """
        resolved_step = self.template_renderer.render_data(step, context)
        response = self._create_request(context, resolved_step)

        if "expect" in resolved_step:
            validator = ResponseValidator(response, resolved_step["expect"])
            validator.check_expectations()

        if "extract" in resolved_step:
            extracted = self.data_extractor.extract(response, resolved_step["extract"])
            context.update(extracted)

        return context
