from .render import TemplateRenderer
from .extractor import DataExtractor
from .validator import ResponseValidator
from .request_builder import RequestBuilder
import requests
from typing import Any, Dict


class StepExecutor:
    def __init__(
        self,
        data_extractor: DataExtractor,
        template_renderer: TemplateRenderer,
    ):
        self.data_extractor = data_extractor
        self.template_renderer = template_renderer

    def _create_request(
        self, context: Dict[str, Any], resolved_step: Dict[str, Any]
    ) -> requests.Response:
        request_builder = RequestBuilder(context, resolved_step)
        data = request_builder.build_request_data()
        response = requests.request(**data)
        return response

    def run_step(self, step: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        resolved_step = self.template_renderer.render_data(step, context)
        response = self._create_request(context, resolved_step)

        if "expect" in resolved_step:
            validator = ResponseValidator(response, resolved_step["expect"])
            validator.check_expectations()

        if "extract" in resolved_step:
            extracted = self.data_extractor.extract(response, resolved_step["extract"])
            context.update(extracted)

        return context
