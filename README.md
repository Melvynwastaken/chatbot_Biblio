# Biblio Chatbot

Biblio is a Python-based chatbot that uses Wikipedia API to provide information and can respond to specific queries based on predefined patterns.

## Features

- **Wikipedia Integration**: Fetches summaries and specific details from Wikipedia pages.
- **Pattern Matching**: Matches user queries to predefined patterns to perform actions like retrieving birth dates, polar radius, decision dates, hex triplets, and RGB values from Wikipedia infoboxes.
- **Natural Language Queries**: Supports natural language queries for easier interaction.
- **Extensible Responses**: Allows for customizable responses for greetings, farewells, and other interactions via a JSON configuration file.

## Installation

1. Clone the repository:

git clone https://github.com/yourusername/Biblio.git

2. Install dependencies:
pip install -r requirements.txt


## Usage

1. Ensure you have Python 3.x installed on your system.

2. Run the chatbot:

python biblio_chatbot.py


3. Interaction:
- Type "search for [topic]" to search for information on Wikipedia.
- Ask specific questions like "When was Albert Einstein born?" or "What is the polar radius of Earth?".
- Greet the chatbot with "hello", "hi", or "hey" to receive a friendly response.
- Type "bye" to exit the chatbot.

## Configuration

- **responses.json**: Customize responses for greetings, farewells, fallbacks, and other interactions by modifying this JSON file.

## Contributing

Contributions are welcome! If you'd like to contribute to Biblio Chatbot, please fork the repository and create a pull request with your proposed changes.

## License

This project is licensed under the MIT License - see the [LICENSE] file for details.
