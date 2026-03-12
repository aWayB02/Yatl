from jinja2 import Template
from typing import Any, Dict
import hashlib


class TemplateRenderer:
    def __init__(self):
        self._template_cache: Dict[str, Template] = {}

    def _get_template(self, template_str: str) -> Template:
        key = hashlib.md5(template_str.encode()).hexdigest()
        if key not in self._template_cache:
            self._template_cache[key] = Template(template_str)
        return self._template_cache[key]

    def render_data(self, data: Any, context: Dict[str, Any]) -> Any:
        if isinstance(data, str):
            template = self._get_template(data)
            return template.render(context)
        elif isinstance(data, dict):
            return {
                key: self.render_data(value, context) for key, value in data.items()
            }
        elif isinstance(data, list):
            return [self.render_data(item, context) for item in data]
        else:
            return data
