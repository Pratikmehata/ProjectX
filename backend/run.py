#!/usr/bin/env python3
"""
PC Recommendation Engine - CLI Interface
Run this script to get PC build recommendations
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.main_engine import PCRecommendationEngine


def print_banner():
    """Print welcome banner"""
    print("=" * 70)
    print("  🖥️  PC RECOMMENDATION ENGINE 🖥️")
    print("  Get the perfect PC build for your needs and budget")
    print("=" * 70)
    print()


def print_usage_examples():
    """Print usage examples"""
    print("📖 USAGE EXAMPLES:")
    print("-" * 70)
    print("  Gaming PC for ₹80,000:")
    print("    python run.py --budget 80000 --intent \"gaming 1080p\"")
    print()
    print("  Video editing workstation:")
    print("    python run.py --budget 150000 --intent \"video editing 4K\"")
    print()
    print("  Office PC:")
    print("    python run.py --budget 40000 --intent \"office work\"")
    print()
    print("  Interactive mode:")
    print("    python run.py --interactive")
    print("-" * 70)
    print()


def interactive_mode(engine):
    """Run interactive recommendation mode"""
    print("🎮 INTERACTIVE MODE")
    print("-" * 70)
    print()
    
    # Show available intents
    print("Available use cases:")
    intents = engine.get_intents()
    for i, intent in enumerate(intents, 1):
        print(f"  {i}. {intent}")
    print()
    
    # Get user input
    user_input = input("💬 What will you use this PC for?\n   > ").strip()
    print()
    
    while True:
        budget_input = input("💰 What's your budget (in ₹)?\n   > ").strip()
        print()
        
        try:
            # Remove commas and convert
            budget = int(budget_input.replace(',', ''))
            if budget < 30000:
                print("⚠️  Budget too low. Minimum recommended budget is ₹30,000.")
                print()
                continue
            break
        except ValueError:
            print("❌ Invalid budget. Please enter a number.")
            print()
    
    # Get resolution preference
    print("📺 Select target resolution:")
    print("  1. 1080p (Full HD)")
    print("  2. 1440p (Quad HD)")
    print("  3. 4K (Ultra HD)")
    resolution_choice = input("   > ").strip()
    print()
    
    resolutions = {
        '1': '1080p',
        '2': '1440p',
        '3': '4K'
    }
    resolution = resolutions.get(resolution_choice, '1080p')
    
    # Get recommendation
    print("=" * 70)
    print("🔍 ANALYZING YOUR REQUIREMENTS...")
    print("=" * 70)
    print()
    
    result = engine.recommend(user_input, budget, resolution)
    
    print()
    print("=" * 70)
    print("📋 YOUR RECOMMENDATION")
    print("=" * 70)
    print()
    print(result['message'])
    print()
    
    # Show compatibility report
    if result['type'] == 'recommendation':
        print("=" * 70)
        print("🔧 COMPATIBILITY CHECK")
        print("=" * 70)
        print()
        
        compat_report = engine.get_compatibility_report(result['build'])
        for item in compat_report:
            print(f"{item['status']} - {item['components']}")
        print()
    
    return result


def main():
    """Main entry point"""
    print_banner()
    
    # Get API key from environment (optional)
    ai_api_key = os.environ.get('GEMINI_API_KEY') or os.environ.get('OPENAI_API_KEY')
    
    # Initialize engine
    data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    
    try:
        engine = PCRecommendationEngine(data_path, ai_api_key=ai_api_key)
    except Exception as e:
        print(f"❌ Error initializing engine: {e}")
        print("   Make sure data files exist in the 'data' folder.")
        sys.exit(1)
    
    # Parse command line arguments
    args = sys.argv[1:]
    
    if '--help' in args or '-h' in args:
        print_usage_examples()
        print("OPTIONS:")
        print("  --budget <amount>     Set budget in ₹")
        print("  --intent <text>       Describe your use case")
        print("  --resolution <res>    Set target resolution (1080p/1440p/4K)")
        print("  --interactive, -i     Run in interactive mode")
        print("  --help, -h            Show this help message")
        print()
        sys.exit(0)
    
    if '--interactive' in args or '-i' in args or len(args) == 0:
        # Interactive mode
        interactive_mode(engine)
        
        # Ask if user wants another recommendation
        while True:
            print()
            again = input("🔄 Would you like another recommendation? (y/n): ").strip().lower()
            if again in ['y', 'yes']:
                print()
                interactive_mode(engine)
            else:
                print()
                print("Thank you for using PC Recommendation Engine! 👋")
                break
    else:
        # Command line mode
        budget = None
        intent = None
        resolution = '1080p'
        
        i = 0
        while i < len(args):
            if args[i] == '--budget' and i + 1 < len(args):
                try:
                    budget = int(args[i + 1].replace(',', ''))
                    i += 2
                except ValueError:
                    print("❌ Invalid budget")
                    sys.exit(1)
            elif args[i] == '--intent' and i + 1 < len(args):
                intent = args[i + 1]
                i += 2
            elif args[i] == '--resolution' and i + 1 < len(args):
                resolution = args[i + 1]
                i += 2
            else:
                i += 1
        
        if budget is None or intent is None:
            print("❌ Please provide both --budget and --intent")
            print_usage_examples()
            sys.exit(1)
        
        # Get recommendation
        result = engine.recommend(intent, budget, resolution)
        
        if result['type'] == 'error':
            print(f"❌ {result['message']}")
            sys.exit(1)
        
        print(result['message'])
        print()
        
        # Show compatibility report
        print("=" * 70)
        print("🔧 COMPATIBILITY CHECK")
        print("=" * 70)
        print()
        
        compat_report = engine.get_compatibility_report(result['build'])
        for item in compat_report:
            print(f"{item['status']} - {item['components']}")
        print()


if __name__ == "__main__":
    main()
