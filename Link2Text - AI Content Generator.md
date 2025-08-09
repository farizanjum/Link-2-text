# Link2Text - AI Content Generator

A powerful web application that transforms tech/AI articles into WhatsApp-friendly content with relevant images, proper formatting, and source attribution.

## Features

- **URL Processing**: Convert any tech/AI article URL into shareable content
- **Direct Text Input**: Format your own text with AI assistance
- **AI Model Selection**: Choose between ChatGPT (premium quality) or Mistral (free)
- **Dynamic Cover Images**: Automatically retrieves relevant images using:
  - OpenGraph metadata extraction from articles
  - Bing Image Search for contextually relevant images
- **Minimal Emoji Usage**: Professional formatting with restrained emoji use
- **Web Search Integration**: Enhanced content with references and citations (Mistral only)
- **Format-Only Mode**: Quick formatting without changing content
- **WhatsApp Integration**: Direct sharing to WhatsApp with proper formatting
- **Modern UI**: Glassmorphism design with futuristic elements

## Technical Implementation

### Backend
- **Flask**: Python web framework for the backend
- **newspaper3k**: Article extraction and OpenGraph image retrieval
- **NLTK**: Natural language processing for keyword extraction
- **OpenAI API**: ChatGPT integration for premium content generation
- **Mistral API**: Free alternative AI model with web search capabilities

### Frontend
- **HTML/CSS/JavaScript**: Modern responsive interface
- **Bootstrap**: Framework for responsive design
- **Glassmorphism**: Modern UI design with transparency effects
- **Font Awesome**: Icon library for enhanced visual elements

## Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the application:
   ```
   cd src
   python main.py
   ```

## Usage

1. **URL Mode**:
   - Paste any tech/AI article URL
   - Select AI model (ChatGPT or Mistral)
   - Enable web search for enhanced content (Mistral only)
   - Click "Generate Content"

2. **Text Mode**:
   - Enter an optional title
   - Paste your text content
   - Select AI model
   - Click "Generate Content"

3. **Format-Only Mode**:
   - Enter an optional title
   - Paste your text content
   - Click "Format Text Only" (uses Mistral)

4. **Results**:
   - Select from relevant cover images
   - Copy formatted content to clipboard
   - Share directly to WhatsApp

## API Keys

The application uses the following API keys:
- OpenAI API for ChatGPT
- Mistral API for the free model option

## License

This project is licensed under the MIT License - see the LICENSE file for details.
