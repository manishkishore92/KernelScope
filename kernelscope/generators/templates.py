from __future__ import annotations

from importlib.resources import files
from typing import Any

from jinja2 import Template


def render_template(name: str, **context: Any) -> str:
    template_text = files("kernelscope").joinpath("templates", name).read_text(encoding="utf-8")
    return Template(template_text).render(**context)
