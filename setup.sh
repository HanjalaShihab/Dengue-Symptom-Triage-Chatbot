#!/bin/bash
# setup.sh - Complete project setup

echo "Setting up Dengue ML Chatbot Project..."

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Generate synthetic data
echo "Generating synthetic dataset..."
python3 dataset_generator.py

# Train ML model
echo "Training ML model..."
python3 ml_model.py

# Run analysis
echo "Running analysis..."
python analysis.py

echo "✅ Setup complete!"
echo "🎯 Next steps:"
echo "1. Edit bot.py and update BOT_TOKEN"
echo "2. Run the bot: python bot.py"
echo "3. Chat with your bot on Telegram"