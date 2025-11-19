"""
Cache CLI - Command-line tool for managing response cache

Usage:
    python3 src/cache_cli.py stats   # Show cache statistics
    python3 src/cache_cli.py clear   # Clear cache
    python3 src/cache_cli.py info    # Show cache configuration
"""
import argparse
import sys
from pathlib import Path
from response_cache import get_global_cache


def show_stats():
    """Show cache statistics"""
    cache = get_global_cache()
    cache.print_stats()


def show_info():
    """Show cache configuration"""
    cache = get_global_cache()

    print("\n" + "=" * 60)
    print("CACHE CONFIGURATION")
    print("=" * 60)
    print(f"Enabled:             {cache.enabled}")
    print(f"Cache directory:     {cache.cache_dir or 'Memory only'}")
    print(f"TTL:                 {cache.ttl}s ({cache.ttl / 3600:.1f} hours)" if cache.ttl > 0 else "TTL:                 No expiration")
    print(f"Max memory entries:  {cache.max_memory_entries}")
    print(f"Current size:        {cache.get_size()} entries")
    print("=" * 60 + "\n")

    print("Environment Variables:")
    print("  SCENARIO_CACHE_ENABLED=true/false    # Enable/disable caching")
    print("  SCENARIO_CACHE_DIR=path              # Cache directory")
    print("  SCENARIO_CACHE_TTL=seconds           # Time-to-live")
    print()


def clear_cache():
    """Clear all cache entries"""
    cache = get_global_cache()

    # Confirm
    print(f"\n⚠️  This will clear all {cache.get_size()} cache entries.")
    response = input("Are you sure? (yes/no): ")

    if response.lower() in ['yes', 'y']:
        cache.clear()
        print("✓ Cache cleared successfully\n")
    else:
        print("Cancelled\n")


def main():
    parser = argparse.ArgumentParser(
        description="Manage LLM response cache",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/cache_cli.py stats    # Show statistics
  python src/cache_cli.py clear    # Clear cache
  python src/cache_cli.py info     # Show configuration

Environment Variables:
  SCENARIO_CACHE_ENABLED    Enable/disable caching (default: true)
  SCENARIO_CACHE_DIR        Cache directory (default: .cache/responses)
  SCENARIO_CACHE_TTL        Time-to-live in seconds (default: 3600)
"""
    )

    parser.add_argument(
        'command',
        choices=['stats', 'clear', 'info'],
        help='Command to execute'
    )

    args = parser.parse_args()

    if args.command == 'stats':
        show_stats()
    elif args.command == 'clear':
        clear_cache()
    elif args.command == 'info':
        show_info()


if __name__ == '__main__':
    main()
