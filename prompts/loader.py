"""
Prompt loader for Scenario Lab V3.

Loads and renders Jinja2 templates from the prompts/ directory.
"""
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

# Set up the Jinja2 environment
PROMPT_DIR = Path(__file__).parent
loader = FileSystemLoader(PROMPT_DIR)
env = Environment(loader=loader)

def load_prompt(name: str, **kwargs) -> str:
    """
    Loads a prompt template and renders it with the given context.

    Args:
        name: The name of the prompt template file (e.g., "actor_phase1.txt").
        **kwargs: The context variables to render the template with.

    Returns:
        The rendered prompt as a string.
    """
    template = env.get_template(name)
    return template.render(**kwargs)
