"""
Batch Config Wizard - Interactive CLI tool for creating batch configurations

This tool helps users create batch configuration files through an interactive
question-and-answer workflow, with validation and helpful suggestions.
"""
import os
import sys
import yaml
from pathlib import Path
from typing import List, Optional, Dict

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class Colors:
    """ANSI color codes for terminal output"""
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text: str):
    """Print a header with formatting"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")


def print_info(text: str):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")


def ask_question(question: str, default: Optional[str] = None) -> str:
    """
    Ask user a question and return response

    Args:
        question: Question to ask
        default: Default value (shown in brackets)

    Returns:
        User's response (or default if empty)
    """
    if default:
        prompt = f"{Colors.BOLD}{question}{Colors.END} [{default}]: "
    else:
        prompt = f"{Colors.BOLD}{question}{Colors.END}: "

    response = input(prompt).strip()

    if not response and default:
        return default

    return response


def ask_yes_no(question: str, default: bool = True) -> bool:
    """
    Ask yes/no question

    Args:
        question: Question to ask
        default: Default answer

    Returns:
        True for yes, False for no
    """
    default_str = "Y/n" if default else "y/N"
    response = ask_question(f"{question} ({default_str})", "")

    if not response:
        return default

    return response.lower() in ['y', 'yes']


def validate_scenario_path(path: str) -> bool:
    """Validate that scenario path exists and has required files"""
    if not os.path.exists(path):
        return False

    scenario_yaml = os.path.join(path, 'scenario.yaml')
    if not os.path.exists(scenario_yaml):
        return False

    return True


def get_scenario_actors(scenario_path: str) -> List[str]:
    """
    Extract actor names from scenario

    Args:
        scenario_path: Path to scenario directory

    Returns:
        List of actor short names
    """
    actors = []
    actors_dir = os.path.join(scenario_path, 'actors')

    if os.path.exists(actors_dir):
        for filename in os.listdir(actors_dir):
            if filename.endswith('.yaml'):
                actor_file = os.path.join(actors_dir, filename)
                try:
                    with open(actor_file, 'r') as f:
                        actor_config = yaml.safe_load(f)
                        short_name = actor_config.get('short_name', actor_config.get('name', ''))
                        if short_name:
                            actors.append(short_name)
                except Exception:
                    continue

    return actors


def get_common_models() -> Dict[str, str]:
    """
    Return common LLM models with descriptions

    Returns:
        Dict of {model_id: description}
    """
    return {
        "openai/gpt-4o-mini": "OpenAI GPT-4o Mini (Fast, cheap, good for testing)",
        "openai/gpt-4o": "OpenAI GPT-4o (Balanced, good general purpose)",
        "anthropic/claude-3-haiku": "Anthropic Claude 3 Haiku (Fast, cheap)",
        "anthropic/claude-3.5-sonnet": "Anthropic Claude 3.5 Sonnet (High quality)",
        "anthropic/claude-3-opus": "Anthropic Claude 3 Opus (Best quality, expensive)",
        "google/gemini-pro": "Google Gemini Pro (Good performance)",
        "meta-llama/llama-3-70b-instruct": "Meta Llama 3 70B (Open source)",
    }


def select_models() -> List[str]:
    """
    Interactive model selection

    Returns:
        List of selected model IDs
    """
    print_info("Common LLM models:")
    models = get_common_models()

    model_list = list(models.keys())
    for i, (model_id, description) in enumerate(models.items(), 1):
        print(f"  {i}. {model_id}")
        print(f"     {description}")

    print()
    response = ask_question("Enter model numbers (comma-separated) or full model IDs", "1,3")

    selected = []
    for item in response.split(','):
        item = item.strip()

        # Check if it's a number (index)
        if item.isdigit():
            idx = int(item) - 1
            if 0 <= idx < len(model_list):
                selected.append(model_list[idx])
        else:
            # Assume it's a full model ID
            selected.append(item)

    return selected


def create_batch_config_interactive():
    """Main interactive wizard for creating batch configuration"""
    print_header("Batch Configuration Wizard")
    print("This wizard will help you create a batch configuration file.")
    print("Press Ctrl+C at any time to cancel.\n")

    config = {}

    try:
        # Experiment name
        config['experiment_name'] = ask_question(
            "Experiment name",
            "My Batch Experiment"
        )

        # Description
        config['description'] = ask_question(
            "Brief description (optional)",
            ""
        )

        # Base scenario
        while True:
            scenario_path = ask_question(
                "Path to base scenario",
                "scenarios/test-regulation-negotiation"
            )

            if validate_scenario_path(scenario_path):
                config['base_scenario'] = scenario_path
                print_success(f"Valid scenario found at {scenario_path}")
                break
            else:
                print_error(f"Scenario not found or invalid: {scenario_path}")
                if not ask_yes_no("Try again?"):
                    return None

        # Get actors from scenario
        actors = get_scenario_actors(scenario_path)
        if actors:
            print_info(f"Found {len(actors)} actors: {', '.join(actors)}")

        # Runs per variation
        while True:
            runs_str = ask_question(
                "Runs per variation (for statistical significance)",
                "10"
            )
            try:
                runs = int(runs_str)
                if runs > 0:
                    config['runs_per_variation'] = runs
                    break
                else:
                    print_error("Must be a positive number")
            except ValueError:
                print_error("Must be a number")

        # Max parallel
        while True:
            parallel_str = ask_question(
                "Maximum parallel runs (consider API rate limits)",
                "2"
            )
            try:
                parallel = int(parallel_str)
                if parallel > 0:
                    config['max_parallel'] = parallel
                    break
                else:
                    print_error("Must be a positive number")
            except ValueError:
                print_error("Must be a number")

        # Timeout
        timeout_str = ask_question(
            "Timeout per run (seconds)",
            "1800"
        )
        try:
            config['timeout_per_run'] = int(timeout_str)
        except ValueError:
            config['timeout_per_run'] = 1800

        # Budget limit
        if ask_yes_no("Set a budget limit?", True):
            while True:
                budget_str = ask_question("Budget limit (USD)", "20.00")
                try:
                    budget = float(budget_str)
                    if budget > 0:
                        config['budget_limit'] = budget
                        break
                    else:
                        print_error("Must be positive")
                except ValueError:
                    print_error("Must be a number")

        # Cost per run limit
        if ask_yes_no("Set a per-run cost limit?", True):
            while True:
                limit_str = ask_question("Per-run cost limit (USD)", "1.00")
                try:
                    limit = float(limit_str)
                    if limit > 0:
                        config['cost_per_run_limit'] = limit
                        break
                    else:
                        print_error("Must be positive")
                except ValueError:
                    print_error("Must be a number")

        # Variations
        print_info("\nNow let's configure parameter variations...")
        variations = []

        while True:
            print(f"\n{Colors.BOLD}Variation #{len(variations) + 1}{Colors.END}")

            if not actors:
                print_warning("No actors found in scenario. You'll need to specify actor manually.")
                actor_name = ask_question("Actor short name")
            else:
                print(f"Available actors: {', '.join(actors)}")
                actor_name = ask_question(
                    "Which actor to vary?",
                    actors[0] if actors else ""
                )

            print("\nSelect LLM models for this actor:")
            models = select_models()

            if models:
                variations.append({
                    'type': 'actor_model',
                    'actor': actor_name,
                    'values': models
                })
                print_success(f"Added variation: {actor_name} with {len(models)} models")

            if not ask_yes_no("Add another variation?", False):
                break

        config['variations'] = variations

        # Calculate total runs
        total_variations = 1
        for var in variations:
            total_variations *= len(var['values'])
        total_runs = total_variations * config['runs_per_variation']

        print_info(f"\nThis will create {total_variations} variation(s) × {config['runs_per_variation']} runs = {total_runs} total runs")

        # Output directory
        default_output = f"experiments/{config['experiment_name'].lower().replace(' ', '-')}"
        config['output_dir'] = ask_question(
            "Output directory",
            default_output
        )

        # Other settings
        config['save_individual_runs'] = ask_yes_no("Save individual run outputs?", True)
        config['aggregate_metrics'] = ask_yes_no("Generate aggregated metrics?", True)

        # Save configuration
        output_dir = config['output_dir']
        os.makedirs(output_dir, exist_ok=True)

        config_file = os.path.join(output_dir, 'batch-config.yaml')

        print(f"\n{Colors.BOLD}Configuration Preview:{Colors.END}")
        print(yaml.dump(config, default_flow_style=False, sort_keys=False))

        if ask_yes_no(f"Save to {config_file}?", True):
            with open(config_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)

            print_success(f"Configuration saved to {config_file}")
            print_info(f"\nTo run this batch:")
            print(f"  python src/batch_runner.py {config_file}")
            print_info(f"\nTo preview without running:")
            print(f"  python src/batch_runner.py {config_file} --dry-run")

            return config_file
        else:
            print_warning("Configuration not saved")
            return None

    except KeyboardInterrupt:
        print("\n\nWizard cancelled.")
        return None
    except Exception as e:
        print_error(f"Error: {e}")
        return None


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Interactive wizard for creating batch configurations'
    )
    parser.add_argument(
        '--interactive',
        action='store_true',
        default=True,
        help='Run in interactive mode (default)'
    )

    args = parser.parse_args()

    config_file = create_batch_config_interactive()

    if config_file:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
