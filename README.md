# HyperLiquid AI Trading Bot

## Overview
This project is an AI-powered trading bot designed for the decentralized exchange HyperLiquid. It leverages predictions from AlloraNetwork's AI and validates trades using Hyperbolic AI models. The bot is fully customizable and supports various trading strategies.

## Features
- **AI Predictions**: Uses AlloraNetwork for market predictions.
- **Trade Validation**: Validates trades with Hyperbolic AI models.
- **Custom Strategies**: Supports user-defined trading strategies.
- **Database Logging**: Logs all trades in a local SQLite database.
- **Environment Configuration**: Easily configurable via a `.env` file.

## Compatibility
This bot is compatible with any Hyperbolic AI model, including but not limited to:
- `deepseek-ai/DeepSeek-R1`
- `deepseek-ai/DeepSeek-V3-0324`

## Requirements
- Python 3.10+
- Dependencies listed in `requirements.txt`

## Setup
1. Clone the repository:
   ```bash
   git clone <repository-url>
   ```
2. Navigate to the project directory:
   ```bash
   cd hyperLiquid-ia-bot
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure the `.env` file with your API keys and settings.

## Usage
Run the bot using:
```bash
python main.py
```

## Future Plans
- Migrate the backend to Node.js.
- Implement a decentralized database using IPFS.
- Integrate smart contracts on the HyperLiquid EVM blockchain.
- Develop a React-based DApp for a modern graphical interface.

## License
This project is licensed under the MIT License.

## Contributing
Contributions are welcome! Please fork the repository and submit a pull request.

## Contact
For questions or support, please contact the project maintainer.

