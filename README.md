# 🖥️ PC Recommendation Engine

A comprehensive Python-based PC build recommendation system that suggests optimal component combinations based on user requirements, budget, and intended use case.

## Features

- **Intent Classification**: Automatically detects user needs from natural language input
- **Budget Optimization**: Finds the best component combinations within budget constraints
- **Compatibility Checking**: Ensures all components work together
- **Multi-Tier Support**: Handles entry-level to high-end builds
- **AI Fallback**: Optional AI-powered recommendations when data is insufficient
- **PSU & Cabinet Suggestions**: Recommends power supply and case based on build

## Supported Use Cases

- 🎮 Gaming (FPS, AAA, Esports)
- 🎬 Video Editing
- 🎨 3D Modeling / CAD
- 📺 Streaming
- 💻 Programming / Development
- 📊 Office / Productivity

## Project Structure

```
pc_recommendation_engine/
├── data/
│   ├── cpu.csv           # CPU component database
│   ├── gpu.csv           # GPU component database
│   ├── motherboard.csv   # Motherboard database
│   ├── ram.csv           # RAM module database
│   └── storage.csv       # Storage device database
├── src/
│   ├── __init__.py
│   ├── data_loader.py           # Component database loader
│   ├── intent_classifier.py     # User intent detection
│   ├── compatibility_engine.py  # Component compatibility checker
│   ├── tier_selector.py         # Performance tier selector
│   ├── budget_optimizer.py      # Budget optimization engine
│   ├── psu_cabinet_suggester.py # PSU and case recommender
│   ├── ai_fallback.py           # AI-powered fallback
│   └── main_engine.py           # Main orchestration engine
├── run.py                # CLI interface
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Installation

1. Clone or download the project
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Interactive Mode

Run without arguments for interactive mode:

```bash
python run.py
```

### Command Line Mode

```bash
# Gaming PC for ₹80,000
python run.py --budget 80000 --intent "gaming 1080p"

# Video editing workstation
python run.py --budget 150000 --intent "video editing 4K"

# Office PC
python run.py --budget 40000 --intent "office work"
```

### As a Python Module

```python
from src.main_engine import PCRecommendationEngine

# Initialize engine
engine = PCRecommendationEngine('data/')

# Get recommendation
result = engine.recommend(
    user_input="I want to play competitive FPS games",
    budget=80000,
    resolution='1080p'
)

print(result['message'])
```

## Sample Output

```
============================================================
🖥️ PC Build Recommendation for Gaming at 1080p
============================================================

### 📦 Core Components
**CPU**: AMD Ryzen 5 5600 - ₹12,500
**GPU**: AMD Radeon RX 6600 - ₹20,500
**MOTHERBOARD**: MSI A520M-A PRO - ₹5,500
**RAM**: G.Skill Ripjaws V 16GB DDR4 - ₹4,800
**STORAGE**: Crucial P3 500GB NVMe SSD - ₹3,500

**Subtotal (Core Components)**: ₹46,800

### ⚡ Power & Case
**Recommended PSU**: 550W (₹4,000 - ₹6,000)
**Recommended Cabinet**: Mid Tower (₹4,000 - ₹7,000)

**Total Estimated Price**: ₹54,800 - ₹59,800
```

## Component Database

The engine includes a sample database with:
- **25 CPUs**: Intel (12th-14th gen) and AMD (Ryzen 5000/7000 series)
- **26 GPUs**: NVIDIA (RTX 30/40 series), AMD (RX 6000/7000 series), Intel Arc
- **26 Motherboards**: Various chipsets for Intel and AMD
- **22 RAM Modules**: DDR4 and DDR5 options
- **27 Storage Devices**: NVMe SSDs from various manufacturers

### Adding Custom Components

You can add your own components by editing the CSV files in the `data/` folder. Ensure:
- Price column is named "Price"
- CPU has "Socket" and "Core Count" columns
- GPU has "Memory" and "TDP" columns
- Motherboard has "Socket/CPU" and "Memory Type" columns
- RAM has "Type" and "Size" columns
- Storage has "Type" and "Capacity" columns

## AI Fallback (Optional)

To enable AI-powered recommendations when the dataset is insufficient:

1. Get a Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Set environment variable:
   ```bash
   export GEMINI_API_KEY="your-api-key"
   ```
3. Or pass directly when initializing:
   ```python
   engine = PCRecommendationEngine('data/', ai_api_key='your-api-key')
   ```

## Budget Ranges

| Budget Range | Tier | Description |
|-------------|------|-------------|
| < ₹50,000 | Entry-Level | Basic computing needs |
| ₹50,000 - ₹80,000 | Budget | Best performance per rupee |
| ₹80,000 - ₹150,000 | Mid-Range | Balanced performance and value |
| ₹150,000 - ₹250,000 | High-End | Premium components |
| > ₹250,000 | Enthusiast | Maximum performance |

## API Reference

### PCRecommendationEngine

```python
PCRecommendationEngine(data_path, ai_api_key=None)
```

**Methods:**

- `recommend(user_input, budget, resolution='1080p')` - Get PC build recommendation
- `get_compatibility_report(build)` - Get compatibility check report
- `get_alternative_builds(user_input, budget, resolution, count)` - Get alternative options
- `get_intents()` - Get list of supported use cases

## Troubleshooting

### "No components found" error
- Check that CSV files exist in the `data/` folder
- Verify CSV files have proper headers and data

### Budget too low
- Minimum recommended budget is ₹30,000
- For gaming, consider at least ₹50,000

### Compatibility issues
- The engine automatically checks socket compatibility
- RAM type (DDR4/DDR5) is matched with motherboard support

## License

This project is open source and available for personal and commercial use.

## Contributing

Feel free to:
- Add more components to the database
- Improve optimization algorithms
- Add new use cases
- Report bugs or suggest features
