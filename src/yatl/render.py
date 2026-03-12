from jinja2 import Template
from typing import Any, Dict
import hashlib


class TemplateRenderer:
    """Renders Jinja2 templates embedded in test steps.

    Templates can appear as strings anywhere in the step specification.
    The renderer traverses dictionaries and lists recursively, rendering
    every string value with the given context.
    """

    def __init__(self):
        """Initializes the renderer with an empty template cache."""
        self._template_cache: Dict[str, Template] = {}

    def _get_template(self, template_str: str) -> Template:
        """Retrieves a compiled Jinja2 template from the cache, compiling if needed.

        The cache key is the MD5 hash of the template string to avoid storing
        duplicate templates.

        Args:
            template_str: The raw template string.

        Returns:
            A compiled Jinja2 Template object.
        """
        key = hashlib.md5(template_str.encode()).hexdigest()
        if key not in self._template_cache:
            self._template_cache[key] = Template(template_str)
        return self._template_cache[key]

    def render_data(self, data: Any, context: Dict[str, Any]) -> Any:
        """Recursively renders all template strings in a data structure.

        Strings are treated as Jinja2 templates and rendered with the context.
        Dictionaries and lists are traversed recursively; other types are
        returned unchanged.

        Args:
            data: The input data (string, dict, list, or any other type).
            context: The variables to use when rendering templates.

        Returns:
            The same data structure with all template strings replaced by
            their rendered values.
        """
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
