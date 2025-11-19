"""
Run Scenario - Main script to execute a scenario simulation
"""
import os
import yaml
import argparse
import requests
import shutil
import logging
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from actor_engine import load_actor, Actor
from world_state import WorldState
from world_state_updater import WorldStateUpdater
from cost_tracker import CostTracker
from metrics_tracker import MetricsTracker
from scenario_state_manager import ScenarioStateManager
from communication_manager import CommunicationManager, ChannelType
from context_manager import ContextManager
from qa_validator import QAValidator
from logging_config import setup_run_logging, log_section, log_subsection, log_cost, log_actor_decision, log_world_update, log_validation, log_error_with_context
from schemas import load_scenario_config, load_actor_config, ScenarioConfig, ActorConfig
from pydantic import ValidationError
from error_handler import ErrorHandler, classify_error, ErrorSeverity
from exogenous_events import ExogenousEventManager


def load_exogenous_events(scenario_path: str) -> ExogenousEventManager:
    """
    Load exogenous events configuration if available

    Args:
        scenario_path: Path to scenario directory

    Returns:
        ExogenousEventManager (possibly empty if no config file)
    """
    events_file = os.path.join(scenario_path, 'exogenous-events.yaml')

    if not os.path.exists(events_file):
        # No events file - return empty manager
        return ExogenousEventManager([])

    try:
        with open(events_file, 'r') as f:
            events_data = yaml.safe_load(f)

        events_config = events_data.get('exogenous_events', [])
        return ExogenousEventManager(events_config)

    except Exception as e:
        # If there's an error loading events, log it but continue without them
        logging.getLogger("scenario_lab").warning(
            f"Could not load exogenous events from {events_file}: {e}\n"
            f"Continuing without exogenous events."
        )
        return ExogenousEventManager([])


def load_scenario(scenario_path: str) -> dict:
    """
    Load and validate scenario definition from YAML

    Args:
        scenario_path: Path to scenario directory

    Returns:
        Validated scenario configuration as dict

    Raises:
        FileNotFoundError: If scenario.yaml not found
        ValidationError: If scenario configuration is invalid
    """
    scenario_file = os.path.join(scenario_path, 'scenario.yaml')

    try:
        if not os.path.exists(scenario_file):
            raise FileNotFoundError(
                f"Scenario file not found: {scenario_file}\n"
                f"Expected scenario.yaml in {scenario_path}"
            )

        with open(scenario_file, 'r') as f:
            yaml_data = yaml.safe_load(f)

        # Validate using Pydantic schema
        scenario_config = load_scenario_config(yaml_data)

        # Return as dict for backward compatibility
        return scenario_config.dict()

    except FileNotFoundError as e:
        error_context = classify_error(
            e,
            operation="Loading scenario definition",
            file_path=scenario_file,
            scenario_name=os.path.basename(scenario_path)
        )
        error_handler = ErrorHandler()
        error_handler.handle_error(error_context)
        raise

    except ValidationError as e:
        # Format Pydantic validation errors nicely
        error_messages = []
        for error in e.errors():
            field = ".".join(str(x) for x in error['loc'])
            message = error['msg']
            error_messages.append(f"  - {field}: {message}")

        error_text = (
            f"Invalid scenario configuration in {scenario_file}:\n" +
            "\n".join(error_messages)
        )

        # Create detailed error context
        validation_error = ValueError(error_text)
        error_context = classify_error(
            validation_error,
            operation="Validating scenario configuration",
            file_path=scenario_file,
            scenario_name=os.path.basename(scenario_path),
            additional_context={'validation_errors': error_messages}
        )
        error_handler = ErrorHandler()
        error_handler.handle_error(error_context)
        raise validation_error from e

    except yaml.YAMLError as e:
        yaml_error = ValueError(f"Invalid YAML syntax in {scenario_file}:\n{str(e)}")
        error_context = classify_error(
            yaml_error,
            operation="Parsing scenario YAML",
            file_path=scenario_file,
            scenario_name=os.path.basename(scenario_path)
        )
        error_handler = ErrorHandler()
        error_handler.handle_error(error_context)
        raise yaml_error


def find_next_run_number(scenario_output_dir: str) -> int:
    """
    Find the next available run number by checking existing run folders

    Args:
        scenario_output_dir: Path to scenario output directory (e.g., output/test-regulation-negotiation)

    Returns:
        Next available run number (e.g., if run-001 and run-002 exist, returns 3)
    """
    if not os.path.exists(scenario_output_dir):
        return 1

    # Find all run-XXX directories
    existing_runs = []
    for item in os.listdir(scenario_output_dir):
        if item.startswith('run-') and os.path.isdir(os.path.join(scenario_output_dir, item)):
            try:
                # Extract number from run-XXX
                run_num = int(item.split('-')[1])
                existing_runs.append(run_num)
            except (ValueError, IndexError):
                # Skip directories that don't match pattern
                continue

    if not existing_runs:
        return 1

    # Return highest + 1
    return max(existing_runs) + 1


def execute_bilateral_communications(
    actors: dict,
    communication_manager: CommunicationManager,
    context_manager: ContextManager,
    world_state: WorldState,
    cost_tracker: CostTracker,
    turn: int,
    num_turns: int,
    logger: logging.Logger
):
    """
    Execute Phase 1: Bilateral communications between actors (parallelized for performance)

    Args:
        actors: Dictionary of actor short names to Actor objects
        communication_manager: Manager for all communications
        context_manager: Manager for context windowing
        world_state: Current world state
        cost_tracker: Cost tracking object
        turn: Current turn number
        num_turns: Total number of turns in scenario
        logger: Logger instance
    """

    def _decide_communication(actor_short_name: str, actor: Actor):
        """
        Helper function for a single actor to decide on bilateral communication (runs in parallel)

        Returns:
            Tuple of (actor_short_name, actor, comm_decision, actor_context, other_actor_names)
        """
        # Get contextualized world state for this actor
        actor_context = context_manager.get_context_for_actor(
            actor.name,
            world_state,
            turn,
            communication_manager
        )

        # Get list of other actors
        other_actor_names = [a.name for a in actors.values() if a.name != actor.name]

        # Ask if actor wants to communicate privately (LLM call - runs in parallel)
        comm_decision = None
        if len(other_actor_names) > 0:
            comm_decision = actor.decide_communication(actor_context, turn, num_turns, other_actor_names)

        return (actor_short_name, actor, comm_decision, actor_context, other_actor_names)

    def _respond_to_bilateral(target_actor: Actor, target_context: str, initiator_name: str, message: str):
        """
        Helper function for target actor to respond to bilateral (runs in parallel)

        Returns:
            Tuple of (target_actor, response)
        """
        response = target_actor.respond_to_bilateral(target_context, turn, num_turns, initiator_name, message)
        return (target_actor, response)

    # PHASE 1: Parallel communication decisions
    logger.info(f"  🚀 Evaluating bilateral communication opportunities in parallel...")
    comm_decisions_results = []

    # Limit parallelism to avoid rate limits on free models (max 3 concurrent requests)
    max_parallel = min(3, len(actors))
    with ThreadPoolExecutor(max_workers=max_parallel) as executor:
        # Submit all communication decision tasks
        future_to_actor = {
            executor.submit(_decide_communication, short_name, actor): (short_name, actor)
            for short_name, actor in actors.items()
        }

        # Collect results as they complete
        for future in as_completed(future_to_actor):
            short_name, actor = future_to_actor[future]
            try:
                result = future.result()
                comm_decisions_results.append(result)
            except Exception as e:
                logger.error(f"  ✗ {actor.name} communication decision failed: {e}")
                raise

    # PHASE 2: Process decisions and track costs (sequential to avoid race conditions)
    bilateral_tasks = []  # List of (initiator, target_actor, target_context, message, channel)

    for actor_short_name, actor, comm_decision, actor_context, other_actor_names in comm_decisions_results:
        if comm_decision:
            # Track communication decision cost
            cost_tracker.record_actor_decision(
                actor_name=actor.name,
                turn=turn,
                model=actor.llm_model,
                tokens_used=comm_decision.get('tokens_used', 0)
            )

            if comm_decision['initiate_bilateral']:
                target = comm_decision['target_actor']
                message = comm_decision['message']

                logger.info(f"  → Initiating bilateral: {actor.name} ↔ {target}")

                # Get or create bilateral channel
                channel = communication_manager.get_or_create_bilateral(actor.name, target, turn)

                # Send initiator's message
                communication_manager.send_message(channel.channel_id, actor.name, message)

                # Get target actor
                target_actor = next(a for a in actors.values() if a.name == target)

                # Get contextualized state for target actor
                target_context = context_manager.get_context_for_actor(
                    target,
                    world_state,
                    turn,
                    communication_manager
                )

                # Queue bilateral response for parallel execution
                bilateral_tasks.append((actor.name, target_actor, target_context, message, channel))
            else:
                logger.debug(f"  → No private communication from {actor.name}")

    # PHASE 3: Execute bilateral responses in parallel
    if bilateral_tasks:
        logger.info(f"  🚀 Processing {len(bilateral_tasks)} bilateral responses in parallel...")

        # Limit parallelism to avoid rate limits on free models
        max_parallel = min(3, len(bilateral_tasks))
        with ThreadPoolExecutor(max_workers=max_parallel) as executor:
            # Submit all bilateral response tasks
            future_to_bilateral = {
                executor.submit(_respond_to_bilateral, target_actor, target_context, initiator_name, message):
                    (initiator_name, target_actor, channel)
                for initiator_name, target_actor, target_context, message, channel in bilateral_tasks
            }

            # Collect and process responses
            for future in as_completed(future_to_bilateral):
                initiator_name, target_actor, channel = future_to_bilateral[future]
                try:
                    target_actor_result, response = future.result()

                    # Track response cost
                    cost_tracker.record_actor_decision(
                        actor_name=target_actor.name,
                        turn=turn,
                        model=target_actor.llm_model,
                        tokens_used=response.get('tokens_used', 0)
                    )

                    # Send response
                    communication_manager.send_message(channel.channel_id, target_actor.name, response['response'])

                    logger.info(f"  ✓ Bilateral negotiation completed: {initiator_name} ↔ {target_actor.name}")
                except Exception as e:
                    logger.error(f"  ✗ Bilateral response failed: {e}")
                    raise


def execute_coalition_formation(
    actors: dict,
    communication_manager: CommunicationManager,
    context_manager: ContextManager,
    world_state: WorldState,
    cost_tracker: CostTracker,
    turn: int,
    num_turns: int,
    logger: logging.Logger
) -> list:
    """
    Execute Phase 1: Coalition formation among actors

    Args:
        actors: Dictionary of actor short names to Actor objects
        communication_manager: Manager for all communications
        context_manager: Manager for context windowing
        world_state: Current world state
        cost_tracker: Cost tracking object
        turn: Current turn number
        num_turns: Total number of turns in scenario
        logger: Logger instance

    Returns:
        List of formed coalitions
    """
    formed_coalitions = []

    for actor_short_name, actor in actors.items():
        # Get contextualized world state for this actor
        actor_context = context_manager.get_context_for_actor(
            actor.name,
            world_state,
            turn,
            communication_manager
        )

        # Get list of other actors
        other_actor_names = [a.name for a in actors.values() if a.name != actor.name]

        # Only consider coalition formation if there are at least 2 other actors
        if len(other_actor_names) >= 2:
            logger.debug(f"{actor.name} considering coalition formation...")
            coalition_decision = actor.decide_coalition(actor_context, turn, num_turns, other_actor_names)

            # Track coalition decision cost
            cost_tracker.record_actor_decision(
                actor_name=actor.name,
                turn=turn,
                model=actor.llm_model,
                tokens_used=coalition_decision.get('tokens_used', 0)
            )

            if coalition_decision['propose_coalition']:
                proposed_members = [actor.name] + coalition_decision['members']
                proposed_members_sorted = sorted(proposed_members)

                # Check if this coalition already exists for this turn
                if proposed_members_sorted in [sorted(c['members']) for c in formed_coalitions]:
                    logger.debug(f"  → Coalition already formed with these members")
                    continue

                logger.info(f"  → Proposing coalition with {', '.join(coalition_decision['members'])}")
                logger.info(f"  → Purpose: {coalition_decision['purpose']}")

                # Ask each proposed member to accept or reject
                responses = {}
                all_accepted = True

                for member_name in coalition_decision['members']:
                    member_actor = next(a for a in actors.values() if a.name == member_name)

                    # Get contextualized state for member
                    member_context = context_manager.get_context_for_actor(
                        member_name,
                        world_state,
                        turn,
                        communication_manager
                    )

                    logger.debug(f"{member_name} considering coalition...")
                    response = member_actor.respond_to_coalition(
                        member_context,
                        turn,
                        num_turns,
                        actor.name,
                        proposed_members,
                        coalition_decision['purpose']
                    )

                    # Track response cost
                    cost_tracker.record_actor_decision(
                        actor_name=member_name,
                        turn=turn,
                        model=member_actor.llm_model,
                        tokens_used=response.get('tokens_used', 0)
                    )

                    responses[member_name] = response

                    if response['decision'] != 'accept':
                        all_accepted = False
                        logger.info(f"  → {member_name} rejected coalition")

                # If all members accepted, create coalition channel
                if all_accepted:
                    logger.info(f"  ✓ Coalition formed!")

                    # Create coalition channel
                    channel = communication_manager.create_channel(
                        ChannelType.COALITION,
                        proposed_members,
                        turn
                    )

                    # Record this coalition as formed
                    formed_coalitions.append({
                        'members': proposed_members,
                        'purpose': coalition_decision['purpose'],
                        'channel_id': channel.channel_id
                    })

                    # Coalition members communicate
                    logger.debug("Coalition members coordinating...")
                    for member_name in proposed_members:
                        member_actor = next(a for a in actors.values() if a.name == member_name)

                        # Get contextualized state for member
                        member_context = context_manager.get_context_for_actor(
                            member_name,
                            world_state,
                            turn,
                            communication_manager
                        )

                        # Get previous messages in this coalition
                        previous_messages = channel.get_messages()

                        message_result = member_actor.communicate_in_coalition(
                            member_context,
                            turn,
                            num_turns,
                            proposed_members,
                            coalition_decision['purpose'],
                            previous_messages
                        )

                        # Track communication cost
                        cost_tracker.record_actor_decision(
                            actor_name=member_name,
                            turn=turn,
                            model=member_actor.llm_model,
                            tokens_used=message_result.get('tokens_used', 0)
                        )

                        # Send message to coalition
                        communication_manager.send_message(
                            channel.channel_id,
                            member_name,
                            message_result['message']
                        )

                    logger.info(f"  ✓ Coalition coordination completed")
                else:
                    logger.info(f"  ✗ Coalition rejected by one or more members")
            else:
                logger.debug(f"  → No coalition proposed by {actor.name}")

    return formed_coalitions


def execute_actor_decisions(
    actors: dict,
    context_manager: ContextManager,
    world_state: WorldState,
    communication_manager: CommunicationManager,
    cost_tracker: CostTracker,
    metrics_tracker: MetricsTracker,
    qa_validator: QAValidator,
    turn: int,
    num_turns: int,
    output_path: str,
    current_state: str,
    logger: logging.Logger
) -> dict:
    """
    Execute Phase 2: Public actor decisions (parallelized for performance)

    Args:
        actors: Dictionary of actor short names to Actor objects
        context_manager: Manager for context windowing
        world_state: Current world state
        communication_manager: Manager for all communications
        cost_tracker: Cost tracking object
        metrics_tracker: Metrics tracking object
        qa_validator: Quality assurance validator
        turn: Current turn number
        num_turns: Total number of turns in scenario
        output_path: Path to output directory
        current_state: Current world state string
        logger: Logger instance

    Returns:
        Dictionary of actor decisions for world state update
    """

    def _make_single_actor_decision(actor_short_name: str, actor: Actor):
        """
        Helper function to make a single actor's decision (runs in parallel)

        Returns:
            Tuple of (actor_short_name, actor, decision, actor_context, recent_goals)
        """
        # Get contextualized world state for this actor (includes communications)
        actor_context = context_manager.get_context_for_actor(
            actor.name,
            world_state,
            turn,
            communication_manager
        )

        # Extract recent goals from previous turns
        recent_goals = ""
        if turn > 1:
            goals_list = []
            for t in range(max(1, turn - 2), turn):  # Last 2 turns
                past_decision = world_state.get_actor_decisions_for_turn(t).get(actor.name, {})
                if past_decision.get('goals'):
                    goals_list.append(f"**Turn {t}:**\n{past_decision['goals']}\n")
            if goals_list:
                recent_goals = "\n".join(goals_list)

        # Make decision (this is the slow LLM API call - runs in parallel)
        decision = actor.make_decision(actor_context, turn, num_turns, recent_goals=recent_goals)

        return (actor_short_name, actor, decision, actor_context, recent_goals)

    # PARALLEL PHASE: Execute all actor decisions concurrently
    logger.info(f"  🚀 Making decisions for {len(actors)} actors in parallel...")
    actor_results = []

    # Limit parallelism to avoid rate limits on free models (max 3 concurrent requests)
    max_parallel = min(3, len(actors))
    with ThreadPoolExecutor(max_workers=max_parallel) as executor:
        # Submit all actor decision tasks
        future_to_actor = {
            executor.submit(_make_single_actor_decision, short_name, actor): (short_name, actor)
            for short_name, actor in actors.items()
        }

        # Collect results as they complete
        for future in as_completed(future_to_actor):
            short_name, actor = future_to_actor[future]
            try:
                result = future.result()
                actor_results.append(result)
                logger.info(f"  ✓ {actor.name} decision completed")
            except Exception as e:
                logger.error(f"  ✗ {actor.name} decision failed: {e}")
                raise

    # SEQUENTIAL PHASE: Process results and update shared state
    # This must be sequential to avoid race conditions in world_state, cost_tracker, etc.
    logger.info(f"  📝 Recording decisions and tracking metrics...")
    turn_decisions = {}
    actor_decisions_for_world_update = {}

    for actor_short_name, actor, decision, actor_context, recent_goals in actor_results:
        log_actor_decision(logger, actor.name, turn)

        turn_decisions[actor_short_name] = decision

        # Record decision in world state
        world_state.record_actor_decision(turn, actor.name, decision)

        # Track costs
        cost_tracker.record_actor_decision(
            actor_name=actor.name,
            turn=turn,
            model=actor.llm_model,
            tokens_used=decision.get('tokens_used', 0)
        )

        # Extract metrics from actor decision
        metrics_tracker.extract_metrics_from_text(
            turn=turn,
            text=decision['action'],
            actor_name=actor.name
        )

        # Prepare for world state update
        actor_decisions_for_world_update[actor.name] = {
            'reasoning': decision['reasoning'],
            'action': decision['action']
        }

        # Write actor decision to file
        actor_md = world_state.actor_decision_to_markdown(turn, actor.name, decision)
        filename = f"{actor_short_name}-{turn:03d}.md"
        with open(os.path.join(output_path, filename), 'w') as f:
            f.write(actor_md)

        logger.info(f"  ✓ Decision recorded: {decision.get('tokens_used', 0):,} tokens")

        # Validate actor decision consistency (if enabled)
        if qa_validator.is_enabled() and qa_validator.should_run_after_turn():
            validation_result = qa_validator.validate_actor_decision(
                actor_profile=actor.to_dict(),
                world_state=current_state,
                actor_reasoning=decision['reasoning'],
                actor_action=decision['action'],
                turn=turn
            )
            if validation_result and not validation_result.passed:
                severity_emoji = "⚠️" if validation_result.severity != "High" else "❌"
                logger.warning(f"    {severity_emoji} Validation: {validation_result.issues[0] if validation_result.issues else 'Inconsistency detected'}")

    return actor_decisions_for_world_update


def synthesize_and_validate_world_state(
    world_state: WorldState,
    world_state_updater: WorldStateUpdater,
    current_state: str,
    actor_decisions: dict,
    scenario_name: str,
    turn: int,
    num_turns: int,
    output_path: str,
    cost_tracker: CostTracker,
    metrics_tracker: MetricsTracker,
    qa_validator: QAValidator,
    world_state_model: str,
    logger: logging.Logger,
    exogenous_event_manager: ExogenousEventManager = None
) -> dict:
    """
    Synthesize world state update using LLM and validate

    Args:
        world_state: WorldState object
        world_state_updater: World state updater object
        current_state: Current world state string
        actor_decisions: Dictionary of actor decisions
        scenario_name: Name of the scenario
        turn: Current turn number
        num_turns: Total number of turns
        output_path: Path to output directory
        cost_tracker: Cost tracking object
        metrics_tracker: Metrics tracking object
        qa_validator: Quality assurance validator
        world_state_model: LLM model for world state updates
        logger: Logger instance
        exogenous_event_manager: Optional manager for background events

    Returns:
        World update result dictionary
    """
    log_world_update(logger, turn)

    # Get exogenous events for this turn
    exogenous_events = []
    if exogenous_event_manager:
        # Get current metrics for conditional events
        current_metrics = metrics_tracker.get_current_metrics() if hasattr(metrics_tracker, 'get_current_metrics') else None
        exogenous_events = exogenous_event_manager.get_events_for_turn(turn, current_metrics)

        if exogenous_events:
            logger.info(f"  📋 {len(exogenous_events)} background event(s) occurring this turn")
            for event in exogenous_events:
                logger.debug(f"     - {event['name']}")

    world_update_result = world_state_updater.update_world_state(
        current_state=current_state,
        turn=turn,
        total_turns=num_turns,
        actor_decisions=actor_decisions,
        scenario_name=scenario_name,
        exogenous_events=exogenous_events
    )

    new_state = world_update_result['updated_state']
    world_state.update_state(new_state)

    # Track world state update costs
    cost_tracker.record_world_state_update(
        turn=turn,
        model=world_state_model,
        tokens_used=world_update_result['metadata'].get('tokens_used', 0)
    )

    # Extract metrics from world state
    metrics_tracker.extract_metrics_from_text(
        turn=turn,
        text=new_state
    )

    # Write updated world state
    world_state_md = world_state.to_markdown(turn)
    with open(os.path.join(output_path, f'world-state-{turn:03d}.md'), 'w') as f:
        f.write(world_state_md)

    logger.info(f"  ✓ World state updated: {world_update_result['metadata'].get('tokens_used', 0):,} tokens")

    # Validate world state update (if enabled)
    if qa_validator.is_enabled() and qa_validator.should_run_after_turn():
        # Extract just the action text for each actor
        actor_actions_text = {name: data['action'] for name, data in actor_decisions.items()}

        validation_result = qa_validator.validate_world_state_update(
            previous_world_state=current_state,
            actor_actions=actor_actions_text,
            new_world_state=new_state,
            turn=turn
        )
        if validation_result and not validation_result.passed:
            severity_emoji = "⚠️" if validation_result.severity != "High" else "❌"
            logger.warning(f"    {severity_emoji} World state validation: {validation_result.issues[0] if validation_result.issues else 'Inconsistency detected'}")

        # Generate turn validation report
        qa_validator.generate_turn_report(turn, output_path)

    return world_update_result


def run_scenario(scenario_path: str, output_path: str = None, max_turns: int = None, credit_limit: float = None, resume_mode: bool = False, verbose: bool = False):
    """
    Run a complete scenario simulation

    Args:
        scenario_path: Path to the scenario directory
        output_path: Path to output directory (default: output/<scenario-name>/run-001)
        max_turns: Optional maximum number of turns to execute before halting
        credit_limit: Optional cost limit - halt if exceeded
        resume_mode: If True, resume from existing state in output_path
        verbose: If True, enable DEBUG logging
    """
    # Set up temporary logger for initialization
    logger = logging.getLogger("scenario_lab")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
        logger.addHandler(handler)

    if not resume_mode:
        logger.info(f"Loading scenario from: {scenario_path}")
    else:
        logger.info(f"Resuming scenario from: {output_path}")

    # Initialize state manager first (needed for resume check)
    state_manager = None
    saved_state = None
    start_turn = 1
    started_at = None

    # Handle resume mode
    if resume_mode:
        if output_path is None:
            raise ValueError("--resume requires the run directory path")

        state_manager = ScenarioStateManager(output_path)

        if not state_manager.state_exists():
            raise ValueError(f"No scenario state found in {output_path}")

        saved_state = state_manager.load_state()

        if saved_state['status'] == 'completed':
            logger.info("This scenario run is already completed.")
            return

        # Override scenario_path and other params from saved state
        scenario_path = saved_state['scenario_path']
        start_turn = saved_state['current_turn'] + 1
        started_at = saved_state['execution_metadata']['started_at']

        logger.info(f"  Status: {saved_state['status']}")
        if saved_state['halt_reason']:
            logger.info(f"  Previous halt reason: {saved_state['halt_reason']}")
        logger.info(f"  Resuming from turn {start_turn} of {saved_state['total_turns']}")

    # Load scenario definition
    scenario = load_scenario(scenario_path)
    scenario_name = scenario['name']

    # Load exogenous events (background events independent of actors)
    exogenous_event_manager = load_exogenous_events(scenario_path)

    if not resume_mode:
        logger.info(f"Scenario: {scenario_name}")
        if exogenous_event_manager and exogenous_event_manager.events:
            logger.info(f"  Exogenous events: {len(exogenous_event_manager.events)} configured")

    # Set up output directory
    if not resume_mode:
        if output_path is None:
            # Find project root (where this script's parent directory is)
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(script_dir)
            scenario_dir_name = os.path.basename(scenario_path)
            scenario_output_dir = os.path.join(project_root, 'output', scenario_dir_name)

            # Find next available run number
            run_number = find_next_run_number(scenario_output_dir)
            output_path = os.path.join(scenario_output_dir, f'run-{run_number:03d}')

        os.makedirs(output_path, exist_ok=True)
        logger.info(f"Output directory: {output_path}")

        # Create state manager for new run
        state_manager = ScenarioStateManager(output_path)

    # Now set up proper logging with file output
    logger = setup_run_logging(Path(output_path), verbose=verbose)

    # Initialize Phase 1 components
    if not resume_mode:
        log_section(logger, "Initializing components")

    # Communication manager - restore or create new
    if resume_mode and saved_state and 'communication_manager_state' in saved_state:
        communication_manager = CommunicationManager.from_dict(saved_state['communication_manager_state'])
        logger.debug("Restored communication manager")
    else:
        # Get actor names for communication manager
        actor_full_names = []
        if resume_mode and saved_state:
            actor_full_names = [actor_data['name'] for actor_data in saved_state['actors'].values()]
        else:
            # Will be populated after loading actors
            pass
        communication_manager = None  # Will be created after loading actors

    # Cost tracker - restore or create new
    if resume_mode and saved_state:
        cost_tracker = CostTracker()
        cost_tracker.total_cost = saved_state['cost_tracker_state']['total_cost']
        cost_tracker.total_tokens = saved_state['cost_tracker_state']['total_tokens']
        cost_tracker.costs_by_actor = saved_state['cost_tracker_state']['costs_by_actor']
        cost_tracker.costs_by_turn = saved_state['cost_tracker_state']['costs_by_turn']
        cost_tracker.world_state_costs = saved_state['cost_tracker_state']['world_state_costs']

        # Convert ISO string timestamps back to datetime objects
        start_time_str = saved_state['cost_tracker_state'].get('start_time')
        if start_time_str:
            try:
                cost_tracker.start_time = datetime.fromisoformat(start_time_str)
            except (ValueError, TypeError) as e:
                logger.warning(f"Could not parse start_time '{start_time_str}': {e}")

        end_time_str = saved_state['cost_tracker_state'].get('end_time')
        if end_time_str:
            try:
                cost_tracker.end_time = datetime.fromisoformat(end_time_str)
            except (ValueError, TypeError) as e:
                logger.warning(f"Could not parse end_time '{end_time_str}': {e}")

        logger.info(f"Restored cost tracker: ${cost_tracker.total_cost:.4f}, {cost_tracker.total_tokens:,} tokens")
    else:
        cost_tracker = CostTracker()

    # Metrics tracker - restore or create new
    metrics_config_path = os.path.join(scenario_path, 'metrics.yaml')
    if resume_mode and saved_state:
        metrics_tracker = MetricsTracker(metrics_config_path if os.path.exists(metrics_config_path) else None)
        metrics_tracker.metrics_by_turn = saved_state['metrics_tracker_state']['metrics_by_turn']
        metrics_tracker.final_metrics = saved_state['metrics_tracker_state']['final_metrics']
        logger.info(f"Restored metrics tracker: {len(metrics_tracker.metrics_by_turn)} turns")
    else:
        metrics_tracker = MetricsTracker(metrics_config_path if os.path.exists(metrics_config_path) else None)

    # QA Validator - always create new (validation doesn't need to be restored)
    qa_validator = QAValidator(scenario_path, os.getenv('OPENROUTER_API_KEY'))
    if not resume_mode and qa_validator.is_enabled():
        logger.info("QA validation enabled")

    # World state updater
    world_state_model = scenario.get('world_state_model', 'alibaba/tongyi-deepresearch-30b-a3b:free')
    world_state_updater = WorldStateUpdater(world_state_model)
    if not resume_mode:
        logger.info(f"World state model: {world_state_model}")

    # World state - restore or create new
    if resume_mode and saved_state:
        # Create WorldState with initial state
        world_state = WorldState(
            initial_state=saved_state['world_state']['states']['0'],
            scenario_name=saved_state['world_state']['scenario_name'],
            turn_duration=saved_state['world_state']['turn_duration']
        )
        # Restore saved data
        world_state.current_turn = saved_state['world_state']['current_turn']
        world_state.states = {int(k): v for k, v in saved_state['world_state']['states'].items()}  # Convert string keys to int
        world_state.actor_decisions = {int(k): v for k, v in saved_state['world_state']['actor_decisions'].items()}  # Convert string keys to int
        logger.info(f"Restored world state: turn {world_state.current_turn}")
    else:
        world_state = WorldState(
            initial_state=scenario['initial_world_state'],
            scenario_name=scenario_name,
            turn_duration=scenario['turn_duration']
        )

    # Get scenario system prompt
    scenario_system_prompt = scenario.get('system_prompt', '')

    # Load actors - restore or create new
    actors = {}
    actor_models = {}
    if resume_mode and saved_state:
        # Recreate actors from saved state
        for short_name, actor_data in saved_state['actors'].items():
            actor = load_actor(scenario_path, short_name, scenario_system_prompt)
            actors[short_name] = actor
            actor_models[actor.name] = actor.llm_model
        logger.info(f"Restored {len(actors)} actors")
    else:
        # Load actors from scenario definition
        for actor_short_name in scenario['actors']:
            actor = load_actor(scenario_path, actor_short_name, scenario_system_prompt)
            actors[actor_short_name] = actor
            actor_models[actor.name] = actor.llm_model
            logger.info(f"Loaded actor: {actor.name} ({actor_short_name}) - {actor.llm_model}")

    # Create communication manager now that we have actors
    if communication_manager is None:
        actor_full_names = [actor.name for actor in actors.values()]
        communication_manager = CommunicationManager(actor_full_names)
        if not resume_mode:
            logger.debug("Communication manager initialized")

    # Create context manager
    context_window_size = scenario.get('context_window_size', 3)  # Default to 3 turns
    context_manager = ContextManager(window_size=context_window_size)
    if not resume_mode:
        logger.info(f"Context manager initialized: window size {context_window_size}")

    # Estimate costs (only for new runs)
    num_turns = scenario['turns']
    if not resume_mode:
        log_section(logger, "Cost Estimation")
        cost_estimate = cost_tracker.estimate_scenario_cost(
            num_actors=len(actors),
            num_turns=num_turns,
            actor_models=actor_models,
            world_state_model=world_state_model
        )

        logger.info("Cost Estimate:")
        logger.info(f"  Actors: ${cost_estimate['total'] - cost_estimate['world_state']:.4f}")
        logger.info(f"  World State: ${cost_estimate['world_state']:.4f}")
        logger.info(f"  Total Estimated: ${cost_estimate['total']:.4f}")
        logger.info(f"  Total Tokens (est): {cost_estimate['total_tokens_estimated']:,}")

    # Write initial world state (only for new runs)
    if not resume_mode:
        initial_state_md = world_state.to_markdown(0)
        with open(os.path.join(output_path, 'world-state-000.md'), 'w') as f:
            f.write(initial_state_md)
        logger.debug("Wrote initial world state")

        # Start cost tracking for new runs
        cost_tracker.start_tracking()
    else:
        log_section(logger, "Resuming execution")

    # Run simulation for specified number of turns
    if not resume_mode:
        log_section(logger, f"Running {num_turns} turns")
    else:
        remaining_turns = num_turns - start_turn + 1
        logger.info(f"Continuing for {remaining_turns} more turn(s)...")

    for turn in range(start_turn, num_turns + 1):
        try:
            log_section(logger, f"TURN {turn}")

            # Check credit limit before processing turn
            if credit_limit and cost_tracker.total_cost >= credit_limit:
                logger.warning(f"⚠️  Credit limit reached: ${cost_tracker.total_cost:.4f} >= ${credit_limit:.4f}")
                state_manager.save_state(
                    scenario_name=scenario_name,
                    scenario_path=scenario_path,
                    status='halted',
                    current_turn=turn - 1,  # Last completed turn
                    total_turns=num_turns,
                    world_state=world_state,
                    actors=actors,
                    cost_tracker=cost_tracker,
                    metrics_tracker=metrics_tracker,
                    communication_manager=communication_manager,
                    halt_reason='credit_limit',
                    started_at=started_at
                )
                logger.info("Scenario halted. Resume with:")
                logger.info(f"  python3 src/run_scenario.py --resume {output_path}")
                return

            current_state = world_state.get_current_state()

            # PHASE 1: Private Communications (optional)
            log_subsection(logger, "Phase 1: Private Communications")

            # Execute bilateral communications
            execute_bilateral_communications(
                actors=actors,
                communication_manager=communication_manager,
                context_manager=context_manager,
                world_state=world_state,
                cost_tracker=cost_tracker,
                turn=turn,
                num_turns=num_turns,
                logger=logger
            )

            # Export bilateral communications to files
            communication_manager.export_channels_to_files(output_path, scenario_name, turn)

            # Coalition Formation (after bilateral negotiations)
            log_subsection(logger, "Coalition Formation")

            # Execute coalition formation
            formed_coalitions = execute_coalition_formation(
                actors=actors,
                communication_manager=communication_manager,
                context_manager=context_manager,
                world_state=world_state,
                cost_tracker=cost_tracker,
                turn=turn,
                num_turns=num_turns,
                logger=logger
            )

            # Export coalition communications to files (if any formed)
            if formed_coalitions:
                communication_manager.export_channels_to_files(output_path, scenario_name, turn)

            # PHASE 2: Public Actions
            log_subsection(logger, "Phase 2: Public Actions")

            # Execute actor decisions
            actor_decisions_for_world_update = execute_actor_decisions(
                actors=actors,
                context_manager=context_manager,
                world_state=world_state,
                communication_manager=communication_manager,
                cost_tracker=cost_tracker,
                metrics_tracker=metrics_tracker,
                qa_validator=qa_validator,
                turn=turn,
                num_turns=num_turns,
                output_path=output_path,
                current_state=current_state,
                logger=logger
            )

            # Update world state using LLM synthesis and validate
            world_update_result = synthesize_and_validate_world_state(
                world_state=world_state,
                world_state_updater=world_state_updater,
                current_state=current_state,
                actor_decisions=actor_decisions_for_world_update,
                scenario_name=scenario_name,
                turn=turn,
                num_turns=num_turns,
                output_path=output_path,
                cost_tracker=cost_tracker,
                metrics_tracker=metrics_tracker,
                qa_validator=qa_validator,
                world_state_model=world_state_model,
                logger=logger,
                exogenous_event_manager=exogenous_event_manager
            )

            # Save state after successful turn completion
            state_manager.save_state(
                scenario_name=scenario_name,
                scenario_path=scenario_path,
                status='running',
                current_turn=turn,
                total_turns=num_turns,
                world_state=world_state,
                actors=actors,
                cost_tracker=cost_tracker,
                metrics_tracker=metrics_tracker,
                communication_manager=communication_manager,
                halt_reason=None,
                started_at=started_at
            )

            # Check if max_turns reached
            if max_turns and turn >= max_turns:
                logger.warning(f"⚠️  Reached maximum turns limit: {max_turns}")
                state_manager.mark_halted('max_turns')
                logger.info(f"Scenario halted after {max_turns} turn(s). Resume with:")
                logger.info(f"  python3 src/run_scenario.py --resume {output_path}")
                return

        except requests.exceptions.HTTPError as e:
            # Create error context
            error_context = classify_error(
                e,
                operation=f"Running scenario turn {turn}",
                scenario_name=scenario_name,
                turn_number=turn,
                cost_so_far=cost_tracker.total_cost
            )

            if e.response.status_code == 429:
                # Rate limit error - save state and exit gracefully
                logger.warning("⚠️  Rate limit error encountered")
                state_manager.save_state(
                    scenario_name=scenario_name,
                    scenario_path=scenario_path,
                    status='halted',
                    current_turn=turn - 1,  # Last completed turn
                    total_turns=num_turns,
                    world_state=world_state,
                    actors=actors,
                    cost_tracker=cost_tracker,
                    metrics_tracker=metrics_tracker,
                    communication_manager=communication_manager,
                    halt_reason='rate_limit',
                    started_at=started_at
                )

                # Handle with user-friendly message
                error_handler = ErrorHandler()
                error_handler.handle_error(error_context)

                logger.info("Scenario halted due to API rate limit.")
                logger.info(f"Last completed turn: {turn - 1}")
                logger.info("Wait a few minutes, then resume with:")
                logger.info(f"  python3 src/run_scenario.py --resume {output_path}")
                return
            else:
                # Other HTTP errors - handle and re-raise
                error_handler = ErrorHandler()
                should_continue, recovery_actions = error_handler.handle_error(error_context)

                if not should_continue:
                    # Save state before halting
                    state_manager.save_state(
                        scenario_name=scenario_name,
                        scenario_path=scenario_path,
                        status='halted',
                        current_turn=turn - 1,
                        total_turns=num_turns,
                        world_state=world_state,
                        actors=actors,
                        cost_tracker=cost_tracker,
                        metrics_tracker=metrics_tracker,
                        communication_manager=communication_manager,
                        halt_reason='api_error',
                        started_at=started_at
                    )
                    logger.info(f"Scenario halted at turn {turn - 1}")
                    logger.info(f"Resume with: python3 src/run_scenario.py --resume {output_path}")

                raise

        except KeyboardInterrupt:
            # User interrupted (Ctrl+C)
            logger.warning("\n⚠️  Scenario interrupted by user")
            state_manager.save_state(
                scenario_name=scenario_name,
                scenario_path=scenario_path,
                status='halted',
                current_turn=turn - 1 if turn > start_turn else start_turn - 1,
                total_turns=num_turns,
                world_state=world_state,
                actors=actors,
                cost_tracker=cost_tracker,
                metrics_tracker=metrics_tracker,
                communication_manager=communication_manager,
                halt_reason='manual',
                started_at=started_at
            )
            logger.info(f"\nScenario halted at turn {turn - 1 if turn > start_turn else start_turn - 1}")
            logger.info("Resume with:")
            logger.info(f"  python3 src/run_scenario.py --resume {output_path}")
            return

        except Exception as e:
            # Unexpected error - save state and provide helpful message
            logger.error(f"\n⚠️  Unexpected error: {str(e)}")
            logger.debug(f"Error type: {type(e).__name__}", exc_info=True)

            state_manager.save_state(
                scenario_name=scenario_name,
                scenario_path=scenario_path,
                status='halted',
                current_turn=turn - 1 if turn > start_turn else start_turn - 1,
                total_turns=num_turns,
                world_state=world_state,
                actors=actors,
                cost_tracker=cost_tracker,
                metrics_tracker=metrics_tracker,
                communication_manager=communication_manager,
                halt_reason='error',
                started_at=started_at
            )

            logger.info(f"\nScenario halted at turn {turn - 1 if turn > start_turn else start_turn - 1} due to error")
            logger.info(f"Cost so far: ${cost_tracker.total_cost:.4f}")
            logger.info("\nState has been saved. You can:")
            logger.info(f"  1. Resume: python3 src/run_scenario.py --resume {output_path}")
            logger.info(f"  2. Check logs: {output_path}/scenario.log")
            logger.info(f"  3. Report issue: https://github.com/anthropics/claude-code/issues")

            raise

    # End cost tracking
    cost_tracker.end_tracking()

    # Set final metrics
    metrics_tracker.set_final_metrics()

    # Generate validation summary report (if enabled)
    if qa_validator.is_enabled():
        qa_validator.generate_summary_report(output_path)
        log_section(logger, "Validation Summary")
        logger.info(f"Total validation checks: {len(qa_validator.validation_results)}")
        passed = sum(1 for r in qa_validator.validation_results if r.passed)
        logger.info(f"Passed: {passed}/{len(qa_validator.validation_results)}")
        logger.info(f"Validation tokens: {qa_validator.total_tokens:,}")

    # Mark scenario as completed
    state_manager.mark_completed()

    # Print summaries
    cost_tracker.print_summary()
    metrics_tracker.print_summary()

    # Save cost and metrics data (including validation costs)
    cost_data = cost_tracker.get_summary()
    if qa_validator.is_enabled():
        cost_data['validation'] = qa_validator.get_validation_costs()

    with open(os.path.join(output_path, 'costs.json'), 'w') as f:
        import json
        json.dump(cost_data, f, indent=2)

    metrics_tracker.save_to_file(os.path.join(output_path, 'metrics.json'))

    log_section(logger, "Scenario Complete!")
    logger.info(f"Output saved to: {output_path}")
    logger.info("  - Markdown files: world-state and actor decisions")
    logger.info("  - costs.json: Cost breakdown")
    logger.info("  - metrics.json: Metrics data")
    logger.info("  - scenario-state.json: Execution state")
    logger.info("  - scenario.log: Detailed execution log")
    if qa_validator.is_enabled():
        logger.info("  - validation-*.md: Validation reports")
        logger.info("  - validation-summary.md: Overall validation results")


def branch_scenario(source_run_path: str, branch_at_turn: int, verbose: bool = False) -> str:
    """
    Create a new run branching from an existing run at a specific turn

    Args:
        source_run_path: Path to the source run directory
        branch_at_turn: Turn number to branch from
        verbose: If True, enable DEBUG logging

    Returns:
        Path to the new branch run directory
    """
    # Set up simple logger for branching
    logger = logging.getLogger("scenario_lab.branch")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
        logger.addHandler(handler)

    logger.info(f"Branching from: {source_run_path}")
    logger.info(f"Branch point: Turn {branch_at_turn}")

    # Load source state
    source_state_manager = ScenarioStateManager(source_run_path)

    if not source_state_manager.state_exists():
        raise ValueError(f"No scenario state found in {source_run_path}")

    source_state = source_state_manager.load_state()

    # Validate branch point
    if branch_at_turn > source_state['current_turn']:
        raise ValueError(
            f"Cannot branch at turn {branch_at_turn}: "
            f"source run only completed {source_state['current_turn']} turn(s)"
        )

    if branch_at_turn < 0:
        raise ValueError(f"Branch turn must be >= 0 (got {branch_at_turn})")

    # Find next run number in the scenario output directory
    scenario_output_dir = os.path.dirname(source_run_path)
    new_run_number = find_next_run_number(scenario_output_dir)
    new_run_path = os.path.join(scenario_output_dir, f'run-{new_run_number:03d}')

    os.makedirs(new_run_path, exist_ok=True)
    logger.info(f"Creating branch: {new_run_path}")

    # Copy initial world state (turn 0)
    shutil.copy(
        os.path.join(source_run_path, 'world-state-000.md'),
        os.path.join(new_run_path, 'world-state-000.md')
    )

    # Copy outputs up to and including branch point
    for turn in range(1, branch_at_turn + 1):
        # Copy world state file
        world_state_file = f'world-state-{turn:03d}.md'
        if os.path.exists(os.path.join(source_run_path, world_state_file)):
            shutil.copy(
                os.path.join(source_run_path, world_state_file),
                os.path.join(new_run_path, world_state_file)
            )

        # Copy actor decision files
        for actor_data in source_state['actors'].values():
            actor_file = f"{actor_data['short_name']}-{turn:03d}.md"
            if os.path.exists(os.path.join(source_run_path, actor_file)):
                shutil.copy(
                    os.path.join(source_run_path, actor_file),
                    os.path.join(new_run_path, actor_file)
                )

    # Create truncated state for the branch
    # Truncate world state to branch point
    truncated_world_state = {
        'current_state': source_state['world_state']['states'][str(branch_at_turn)],
        'current_turn': branch_at_turn,
        'turn_duration': source_state['world_state']['turn_duration'],
        'scenario_name': source_state['world_state']['scenario_name'],
        'states': {k: v for k, v in source_state['world_state']['states'].items() if int(k) <= branch_at_turn},
        'actor_decisions': {k: v for k, v in source_state['world_state']['actor_decisions'].items() if int(k) <= branch_at_turn}
    }

    # Truncate cost tracker to branch point
    truncated_costs_by_turn = {k: v for k, v in source_state['cost_tracker_state']['costs_by_turn'].items() if int(k) <= branch_at_turn}

    # Recalculate totals
    total_cost = 0.0
    total_tokens = 0
    for turn_data in truncated_costs_by_turn.values():
        total_cost += turn_data['total']
        # Sum actor tokens
        for actor_costs in turn_data.get('actor_costs', {}).values():
            # Note: individual token counts not stored per actor in turn data, so we can't recalculate perfectly
            pass

    # Truncate costs by actor
    truncated_costs_by_actor = {}
    for actor_name, actor_costs in source_state['cost_tracker_state']['costs_by_actor'].items():
        actor_turns = [t for t in actor_costs['turns'] if t['turn'] <= branch_at_turn]
        if actor_turns:
            truncated_costs_by_actor[actor_name] = {
                'turns': actor_turns,
                'total_cost': sum(t['cost'] for t in actor_turns),
                'total_tokens': sum(t['tokens'] for t in actor_turns)
            }

    # Truncate world state costs
    truncated_world_state_costs = [
        wsc for wsc in source_state['cost_tracker_state']['world_state_costs']
        if wsc['turn'] <= branch_at_turn
    ]

    # Recalculate total tokens from actors + world state
    total_tokens = sum(a['total_tokens'] for a in truncated_costs_by_actor.values())
    total_tokens += sum(wsc['tokens'] for wsc in truncated_world_state_costs)
    total_cost = sum(a['total_cost'] for a in truncated_costs_by_actor.values())
    total_cost += sum(wsc['cost'] for wsc in truncated_world_state_costs)

    truncated_cost_tracker = {
        'total_cost': total_cost,
        'total_tokens': total_tokens,
        'costs_by_actor': truncated_costs_by_actor,
        'costs_by_turn': truncated_costs_by_turn,
        'world_state_costs': truncated_world_state_costs,
        'start_time': source_state['cost_tracker_state'].get('start_time'),
        'end_time': None  # Branch hasn't completed yet
    }

    # Truncate metrics to branch point
    truncated_metrics_by_turn = {
        k: v for k, v in source_state['metrics_tracker_state']['metrics_by_turn'].items()
        if int(k) <= branch_at_turn
    }

    # Create new state file for branch
    # Branch is halted at branch point so it can be resumed
    branch_state = {
        'scenario_name': source_state['scenario_name'],
        'scenario_path': source_state['scenario_path'],
        'status': 'halted',
        'halt_reason': 'branched',
        'current_turn': branch_at_turn,
        'total_turns': source_state['total_turns'],
        'completed_turns': list(range(1, branch_at_turn + 1)) if branch_at_turn > 0 else [],
        'world_state': truncated_world_state,
        'actors': source_state['actors'],
        'cost_tracker_state': truncated_cost_tracker,
        'metrics_tracker_state': {
            'metrics_by_turn': truncated_metrics_by_turn,
            'final_metrics': {}
        },
        'execution_metadata': {
            'started_at': source_state['execution_metadata']['started_at'],
            'last_updated': source_state['execution_metadata']['last_updated'],
            'output_path': new_run_path,
            'branched_from': source_run_path,
            'branch_point': branch_at_turn
        }
    }

    # Write branch state
    branch_state_manager = ScenarioStateManager(new_run_path)
    with open(branch_state_manager.state_file, 'w') as f:
        import json
        json.dump(branch_state, f, indent=2)

    logger.info("✓ Branch created successfully")
    logger.info(f"  Source: {source_run_path}")
    logger.info(f"  Branch: {new_run_path}")
    logger.info(f"  Branched at turn: {branch_at_turn}")
    logger.info(f"  Copied {branch_at_turn} turn(s) of history")
    logger.info(f"  Cost so far: ${total_cost:.4f} ({total_tokens:,} tokens)")
    logger.info(f"\nContinue from turn {branch_at_turn + 1} with:")
    logger.info(f"  python3 src/run_scenario.py --resume {new_run_path}")

    return new_run_path


def main():
    parser = argparse.ArgumentParser(description='Run a Scenario Lab simulation')
    parser.add_argument('scenario', nargs='?', help='Path to scenario directory')
    parser.add_argument('--output', '-o', help='Output directory path', default=None)
    parser.add_argument('--resume', help='Resume from run directory path')
    parser.add_argument('--branch-from', help='Branch from existing run directory')
    parser.add_argument('--branch-at-turn', type=int, help='Turn to branch from (requires --branch-from)')
    parser.add_argument('--max-turns', type=int, help='Stop after this many turns')
    parser.add_argument('--credit-limit', type=float, help='Halt if cost exceeds this amount')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose (DEBUG) logging')

    args = parser.parse_args()

    # Handle branching mode
    if args.branch_from:
        if args.branch_at_turn is None:
            parser.error("--branch-at-turn is required when using --branch-from")

        branch_scenario(args.branch_from, args.branch_at_turn, verbose=args.verbose)
        return

    # Handle resume mode
    if args.resume:
        run_scenario(
            scenario_path=None,  # Will be loaded from state
            output_path=args.resume,
            max_turns=args.max_turns,
            credit_limit=args.credit_limit,
            resume_mode=True,
            verbose=args.verbose
        )
    else:
        if not args.scenario:
            parser.error("scenario path is required unless using --resume or --branch-from")

        run_scenario(
            scenario_path=args.scenario,
            output_path=args.output,
            max_turns=args.max_turns,
            credit_limit=args.credit_limit,
            resume_mode=False,
            verbose=args.verbose
        )


if __name__ == '__main__':
    main()
