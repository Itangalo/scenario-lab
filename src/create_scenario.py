"""
Scenario Creation Wizard - Interactive CLI tool for creating scenario definitions

This tool helps users create complete scenario configurations through an interactive
question-and-answer workflow, with validation and helpful templates.
"""
import os
import sys
import yaml
from pathlib import Path
from typing import List, Optional, Dict, Any

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
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")


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


def ask_multiline(question: str, default: Optional[str] = None) -> str:
    """
    Ask for multi-line input (end with empty line)

    Args:
        question: Question to ask
        default: Default value

    Returns:
        Multi-line response
    """
    print(f"{Colors.BOLD}{question}{Colors.END}")
    if default:
        print(f"{Colors.BLUE}(Press Enter twice to finish. Type 'default' for template){Colors.END}")
    else:
        print(f"{Colors.BLUE}(Press Enter twice to finish){Colors.END}")

    lines = []
    while True:
        line = input()
        if not line:
            break
        if line.strip().lower() == 'default' and default:
            return default
        lines.append(line)

    result = '\n'.join(lines)
    return result if result else (default or "")


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


def get_common_models() -> Dict[str, str]:
    """
    Return common LLM models with descriptions

    Returns:
        Dict of {model_id: description}
    """
    return {
        "openai/gpt-4o-mini": "Fast, cheap, good for testing ($0.15/M in, $0.60/M out)",
        "openai/gpt-4o": "Balanced, good general purpose ($2.50/M in, $10/M out)",
        "anthropic/claude-3-haiku": "Fast, cheap ($0.25/M in, $1.25/M out)",
        "anthropic/claude-3.5-sonnet": "High quality ($3/M in, $15/M out)",
        "anthropic/claude-3-opus": "Best quality, expensive ($15/M in, $75/M out)",
        "google/gemini-pro": "Good performance ($0.50/M in, $1.50/M out)",
        "meta-llama/llama-3-70b-instruct": "Open source ($0.59/M in, $0.79/M out)",
        "alibaba/tongyi-deepresearch-30b-a3b:free": "Free model for testing",
        "ollama/qwen2.5:14b": "Local Ollama model (free, requires Ollama)",
    }


def select_model(purpose: str = "actor") -> str:
    """
    Interactive model selection

    Args:
        purpose: What the model is for (actor/world_state/validation)

    Returns:
        Selected model ID
    """
    print_info(f"\nCommon LLM models for {purpose}:")
    models = get_common_models()

    model_list = list(models.keys())
    for i, (model_id, description) in enumerate(models.items(), 1):
        print(f"  {i}. {model_id}")
        print(f"     {description}")

    print()

    # Default suggestions based on purpose
    defaults = {
        "actor": "2",  # gpt-4o
        "world_state": "1",  # gpt-4o-mini (cheaper for synthesis)
        "validation": "1",  # gpt-4o-mini (cheap validation)
    }
    default_idx = defaults.get(purpose, "1")

    response = ask_question(
        f"Enter model number or full model ID",
        default_idx
    )

    # Check if it's a number (index)
    if response.isdigit():
        idx = int(response) - 1
        if 0 <= idx < len(model_list):
            return model_list[idx]

    # Assume it's a full model ID
    return response


def create_actor_interactive() -> Dict[str, Any]:
    """
    Interactive wizard for creating a single actor

    Returns:
        Actor configuration dict
    """
    print_header("Create Actor")

    actor = {}

    # Basic info
    actor['name'] = ask_question("Actor name (full)", "Policy Expert")
    actor['short_name'] = ask_question(
        "Short name (for filenames, no spaces)",
        actor['name'].lower().replace(' ', '-')
    )

    # Model selection
    actor['llm_model'] = select_model("actor")

    # System prompt with template
    print()
    print_info("Now let's create the actor's system prompt...")

    template = f"""You are {actor['name']}. Your mandate is to [DESCRIBE MANDATE].

Your goals are to:
- [GOAL 1]
- [GOAL 2]
- [GOAL 3]

Your constraints:
- [CONSTRAINT 1]
- [CONSTRAINT 2]
- [CONSTRAINT 3]

Your expertise levels:
- [DOMAIN]: [expert/intermediate/novice]
- [DOMAIN]: [expert/intermediate/novice]

Your decision-making style:
[DESCRIBE HOW THIS ACTOR MAKES DECISIONS]"""

    if ask_yes_no("Use template for system prompt?", True):
        actor['system_prompt'] = template
        print_success("Using template (you can edit it later)")
    else:
        actor['system_prompt'] = ask_multiline(
            "Enter system prompt",
            template
        )

    # Description (can be shorter version of system prompt)
    if ask_yes_no("Use system prompt as description?", True):
        actor['description'] = actor['system_prompt'].split('\n\n')[0]
    else:
        actor['description'] = ask_multiline("Enter actor description")

    # Goals
    print()
    print_info("Enter actor goals (one per line, empty line to finish):")
    goals = []
    while True:
        goal = input("  - ").strip()
        if not goal:
            break
        goals.append(goal)

    if not goals:
        goals = ["[Define actor goals]"]

    actor['goals'] = goals

    # Constraints
    print()
    print_info("Enter actor constraints (one per line, empty line to finish):")
    constraints = []
    while True:
        constraint = input("  - ").strip()
        if not constraint:
            break
        constraints.append(constraint)

    if not constraints:
        constraints = ["[Define actor constraints]"]

    actor['constraints'] = constraints

    # Expertise
    print()
    if ask_yes_no("Define expertise areas?", True):
        expertise = {}
        print_info("Enter expertise areas (format: domain=level, empty to finish)")
        print_info("Levels: expert, intermediate, novice")

        while True:
            exp_input = input("  ").strip()
            if not exp_input:
                break

            if '=' in exp_input:
                domain, level = exp_input.split('=', 1)
                expertise[domain.strip()] = level.strip()

        actor['expertise'] = expertise if expertise else {
            "policy": "expert",
            "technology": "intermediate"
        }

    # Decision style
    print()
    decision_style_template = f"""You are [ADJECTIVES: e.g., cautious, pragmatic, bold]. You prioritize [VALUES]
but understand the need for [BALANCE]. You [DECISION APPROACH]."""

    if ask_yes_no("Use template for decision style?", True):
        actor['decision_style'] = decision_style_template
        print_success("Using template")
    else:
        actor['decision_style'] = ask_multiline(
            "Enter decision-making style",
            decision_style_template
        )

    return actor


def create_metric_interactive() -> Dict[str, Any]:
    """
    Interactive wizard for creating a metric definition

    Returns:
        Metric configuration dict
    """
    print()
    print_info("Creating new metric...")

    metric = {}

    metric['description'] = ask_question("Metric description")

    # Type
    print("Metric type:")
    print("  1. Integer")
    print("  2. Float")
    print("  3. String")
    print("  4. Boolean")

    type_choice = ask_question("Select type (1-4)", "1")
    type_map = {"1": "integer", "2": "float", "3": "string", "4": "boolean"}
    metric['type'] = type_map.get(type_choice, "integer")

    # Unit (if numeric)
    if metric['type'] in ['integer', 'float']:
        metric['unit'] = ask_question("Unit (e.g., hours, FLOPS, USD)", "")

    # Extraction method
    print()
    print("Extraction method:")
    print("  1. Regex (automatic pattern matching)")
    print("  2. Manual (set by analyst)")

    extraction_choice = ask_question("Select method (1-2)", "1")
    metric['extraction_method'] = "regex" if extraction_choice == "1" else "manual"

    # Pattern (if regex)
    if metric['extraction_method'] == "regex":
        metric['pattern'] = ask_question(
            "Regex pattern",
            r'(\d+)\s*hours?'
        )

    # Actor specific
    metric['actor_specific'] = ask_yes_no("Is this metric specific to one actor?", False)

    if metric['actor_specific']:
        metric['actor'] = ask_question("Which actor?")

    return metric


def load_example_scenario() -> Dict[str, Any]:
    """
    Load the example scenario configuration

    Returns:
        Dict with 'scenario', 'actors', 'metrics', 'validation' keys
    """
    example_path = "scenarios/example-policy-negotiation"

    if not os.path.exists(example_path):
        print_warning("Example scenario not found - will start from scratch")
        return {}

    result = {}

    # Load scenario.yaml
    scenario_file = os.path.join(example_path, "scenario.yaml")
    if os.path.exists(scenario_file):
        with open(scenario_file, 'r') as f:
            result['scenario'] = yaml.safe_load(f)

    # Load actors
    actors_dir = os.path.join(example_path, "actors")
    if os.path.exists(actors_dir):
        result['actors'] = []
        for actor_file in os.listdir(actors_dir):
            if actor_file.endswith('.yaml'):
                actor_path = os.path.join(actors_dir, actor_file)
                with open(actor_path, 'r') as f:
                    result['actors'].append(yaml.safe_load(f))

    # Load metrics
    metrics_file = os.path.join(example_path, "metrics.yaml")
    if os.path.exists(metrics_file):
        with open(metrics_file, 'r') as f:
            result['metrics'] = yaml.safe_load(f)

    # Load validation rules
    validation_file = os.path.join(example_path, "validation-rules.yaml")
    if os.path.exists(validation_file):
        with open(validation_file, 'r') as f:
            result['validation'] = yaml.safe_load(f)

    return result


def create_scenario_interactive():
    """Main interactive wizard for creating scenario configuration"""
    print_header("Scenario Creation Wizard")
    print("This wizard will help you create a complete scenario configuration.")
    print("Press Ctrl+C at any time to cancel.\n")

    # Ask if user wants to start from example
    print_info("You can start from scratch or use the example scenario as a template.")
    print_info("The example demonstrates all features with detailed comments.")
    print()
    use_example = ask_yes_no("Start from example scenario? (Recommended for first-time users)", True)

    # Load example if requested
    example_data = {}
    if use_example:
        example_data = load_example_scenario()
        if example_data:
            print_success("Loaded example scenario - you can modify any values as we go")
        else:
            print_warning("Could not load example - starting from scratch")
            use_example = False
    print()

    scenario = {}
    actors_list = []
    metrics_dict = {}

    try:
        # ============================================================
        # BASIC SCENARIO INFO
        # ============================================================
        print_header("Step 1: Basic Information")

        # Use example values as defaults if available
        example_scenario = example_data.get('scenario', {})

        default_name = example_scenario.get('name', "New Policy Scenario")
        default_desc = example_scenario.get('description', "A scenario exploring policy decisions")

        if use_example:
            print_info(f"Example name: {default_name}")
            print_info(f"Example description: {default_desc}")
            print()

        scenario['name'] = ask_question(
            "Scenario name",
            default_name
        )

        scenario['description'] = ask_question(
            "Brief description",
            default_desc
        )

        # ============================================================
        # SYSTEM PROMPT
        # ============================================================
        print_header("Step 2: System Prompt")
        print_info("The system prompt sets the context for all actors")

        # Use example or fallback to default
        default_system_prompt = example_scenario.get('system_prompt', """You are participating in a multi-turn scenario simulation focused on AI policy and governance.
Your goal is to act realistically as your assigned role, making strategic decisions that align
with your character's goals, constraints, and decision-making style.

Be specific and concrete in your actions. Consider both short-term tactics and long-term strategy.
Your decisions should reflect realistic policy negotiation dynamics, including compromise,
strategic positioning, and consideration of stakeholder interests.""")

        if use_example and example_scenario.get('system_prompt'):
            print_info("Example system prompt:")
            print(f"{Colors.BLUE}{default_system_prompt[:200]}...{Colors.END}")
            print()

        if ask_yes_no("Use default/example system prompt?", True):
            scenario['system_prompt'] = default_system_prompt
        else:
            scenario['system_prompt'] = ask_multiline(
                "Enter system prompt",
                default_system_prompt
            )

        # ============================================================
        # INITIAL WORLD STATE
        # ============================================================
        print_header("Step 3: Initial World State")
        print_info("Describe the starting situation for the scenario")

        default_world_state = example_scenario.get('initial_world_state',
            "The year is [YEAR]. [DESCRIBE INITIAL SITUATION]\n\nKey issues:\n- [ISSUE 1]\n- [ISSUE 2]")

        if use_example and example_scenario.get('initial_world_state'):
            print_info("Example world state (first 300 chars):")
            print(f"{Colors.BLUE}{default_world_state[:300]}...{Colors.END}")
            print()

        scenario['initial_world_state'] = ask_multiline(
            "Enter initial world state",
            default_world_state
        )

        # ============================================================
        # TURNS AND DURATION
        # ============================================================
        print_header("Step 4: Scenario Parameters")

        default_turns = str(example_scenario.get('turns', 3))
        default_duration = example_scenario.get('turn_duration', "1 month")

        if use_example:
            print_info(f"Example: {default_turns} turns, {default_duration} each")
            print()

        while True:
            turns_str = ask_question("Number of turns", default_turns)
            try:
                turns = int(turns_str)
                if turns > 0:
                    scenario['turns'] = turns
                    break
                else:
                    print_error("Must be positive")
            except ValueError:
                print_error("Must be a number")

        scenario['turn_duration'] = ask_question(
            "Duration of each turn",
            default_duration
        )

        # ============================================================
        # WORLD STATE MODEL
        # ============================================================
        print_header("Step 5: World State Model")
        print_info("This model synthesizes world state updates from actor actions")

        if use_example and example_scenario.get('world_state_model'):
            print_info(f"Example uses: {example_scenario['world_state_model']}")
            print()

        scenario['world_state_model'] = select_model("world_state")

        # ============================================================
        # ACTORS
        # ============================================================
        print_header("Step 6: Create Actors")
        print_info("Add at least 2 actors for an interesting scenario")

        # If using example, offer to load example actors
        example_actors = example_data.get('actors', [])
        if use_example and example_actors:
            print()
            print_info(f"Example has {len(example_actors)} actors:")
            for ex_actor in example_actors:
                print(f"  - {ex_actor.get('name', 'Unknown')} ({ex_actor.get('short_name', 'unknown')})")
            print()

            if ask_yes_no("Use example actors as starting point?", True):
                actors_list = example_actors.copy()
                print_success(f"Loaded {len(actors_list)} actors from example")
                print_info("You can modify them or add more actors below")
                print()

        # Add or create actors
        while len(actors_list) < 2 or ask_yes_no(f"Add another actor? (currently {len(actors_list)})", len(actors_list) < 3):
            actor = create_actor_interactive()
            actors_list.append(actor)
            print_success(f"Added actor: {actor['name']}")

        # Actor names for scenario.yaml
        scenario['actors'] = [actor['short_name'] for actor in actors_list]

        # ============================================================
        # METRICS
        # ============================================================
        print_header("Step 7: Metrics (Optional)")

        # Check if example has metrics
        example_metrics = example_data.get('metrics', {})
        if use_example and example_metrics.get('metrics'):
            print_info(f"Example has {len(example_metrics['metrics'])} metrics defined")
            print_info("You can use these as a starting point or create your own")
            print()

            if ask_yes_no("Use example metrics?", True):
                metrics_dict = example_metrics.copy()
                metrics_dict['scenario_name'] = scenario['name']  # Update scenario name
                print_success(f"Loaded {len(metrics_dict.get('metrics', {}))} metrics from example")
            else:
                if ask_yes_no("Define metrics to track?", True):
                    metrics_dict['scenario_name'] = scenario['name']
                    metrics_dict['metrics'] = {}

                    while True:
                        metric_name = ask_question("Metric name (snake_case, empty to finish)", "")
                        if not metric_name:
                            break

                        metric_config = create_metric_interactive()
                        metrics_dict['metrics'][metric_name] = metric_config
                        print_success(f"Added metric: {metric_name}")
        else:
            if ask_yes_no("Define metrics to track?", True):
                metrics_dict['scenario_name'] = scenario['name']
                metrics_dict['metrics'] = {}

                while True:
                    metric_name = ask_question("Metric name (snake_case, empty to finish)", "")
                    if not metric_name:
                        break

                    metric_config = create_metric_interactive()
                    metrics_dict['metrics'][metric_name] = metric_config
                    print_success(f"Added metric: {metric_name}")

        # ============================================================
        # VALIDATION RULES
        # ============================================================
        print_header("Step 8: Validation Rules (Optional)")

        example_validation = example_data.get('validation', {})
        if use_example and example_validation:
            print_info("Example has validation configured")
            print_info(f"Model: {example_validation.get('validation_model', 'not specified')}")
            print()

        use_validation = ask_yes_no("Enable automated validation?", True)
        validation_config = None

        if use_validation:
            # If example exists, use its model as default
            default_val_model = example_validation.get('validation_model') if example_validation else None

            validation_config = {
                'validation_model': select_model("validation"),
                'checks': {
                    'actor_decision_consistency': {
                        'enabled': ask_yes_no("  Enable actor decision consistency checks?", True)
                    },
                    'world_state_coherence': {
                        'enabled': ask_yes_no("  Enable world state coherence checks?", True)
                    },
                    'information_access_consistency': {
                        'enabled': ask_yes_no("  Enable information access checks?", True)
                    }
                },
                'run_after_each_turn': True,
                'generate_turn_reports': True
            }

        # ============================================================
        # SAVE CONFIGURATION
        # ============================================================
        print_header("Step 9: Save Scenario")

        # Determine output path
        scenario_dir_name = scenario['name'].lower().replace(' ', '-')
        default_path = f"scenarios/{scenario_dir_name}"
        scenario_path = ask_question("Output directory", default_path)

        # Create directory structure
        os.makedirs(scenario_path, exist_ok=True)
        os.makedirs(os.path.join(scenario_path, 'actors'), exist_ok=True)

        # Preview
        print(f"\n{Colors.BOLD}Scenario Preview:{Colors.END}")
        print(f"Name: {scenario['name']}")
        print(f"Actors: {len(actors_list)}")
        print(f"Turns: {scenario['turns']}")
        print(f"Metrics: {len(metrics_dict.get('metrics', {}))}")
        print(f"Validation: {'Enabled' if validation_config else 'Disabled'}")
        print(f"Output: {scenario_path}")

        if not ask_yes_no(f"\nSave scenario to {scenario_path}?", True):
            print_warning("Scenario not saved")
            return None

        # Save scenario.yaml
        scenario_file = os.path.join(scenario_path, 'scenario.yaml')
        with open(scenario_file, 'w') as f:
            yaml.dump(scenario, f, default_flow_style=False, sort_keys=False)
        print_success(f"Saved scenario.yaml")

        # Save actor files
        for actor in actors_list:
            actor_file = os.path.join(scenario_path, 'actors', f"{actor['short_name']}.yaml")
            with open(actor_file, 'w') as f:
                yaml.dump(actor, f, default_flow_style=False, sort_keys=False)
            print_success(f"Saved actors/{actor['short_name']}.yaml")

        # Save metrics.yaml
        if metrics_dict.get('metrics'):
            metrics_file = os.path.join(scenario_path, 'metrics.yaml')
            with open(metrics_file, 'w') as f:
                yaml.dump(metrics_dict, f, default_flow_style=False, sort_keys=False)
            print_success(f"Saved metrics.yaml")

        # Save validation-rules.yaml
        if validation_config:
            # Load full template from existing scenario
            template_path = "scenarios/test-regulation-negotiation/validation-rules.yaml"
            if os.path.exists(template_path):
                with open(template_path, 'r') as f:
                    full_validation = yaml.safe_load(f)

                # Update with user choices
                full_validation['validation_model'] = validation_config['validation_model']
                full_validation['checks'] = validation_config['checks']

                validation_file = os.path.join(scenario_path, 'validation-rules.yaml')
                with open(validation_file, 'w') as f:
                    yaml.dump(full_validation, f, default_flow_style=False, sort_keys=False)
                print_success(f"Saved validation-rules.yaml")

        # Final instructions
        print()
        print_header("Scenario Created Successfully!")
        print_info("Next steps:")
        print(f"  1. Review and edit files in: {scenario_path}")
        print(f"  2. Run the scenario:")
        print(f"     python src/run_scenario.py {scenario_path}")
        print(f"  3. For batch experiments:")
        print(f"     python src/create_batch_config.py")

        return scenario_path

    except KeyboardInterrupt:
        print("\n\nWizard cancelled.")
        return None
    except Exception as e:
        print_error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Interactive wizard for creating scenario configurations'
    )
    parser.add_argument(
        '--interactive',
        action='store_true',
        default=True,
        help='Run in interactive mode (default)'
    )

    args = parser.parse_args()

    scenario_path = create_scenario_interactive()

    if scenario_path:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
