# Islamic Guidance AI

An AI-powered application for providing Islamic guidance based on Quran and Hadith, with a modern web interface featuring dark mode and comprehensive testing.

## ✨ Features

- **Natural Language Understanding**: Users can ask questions in natural language
- **Quran & Hadith Search**: Searches for relevant verses and hadiths via Python backend
- **AI-Powered Guidance**: Uses Google Gemini AI to provide contextual Islamic guidance
- **Dark Mode**: Toggle between light and dark themes
- **API Key Management**: Save and load API keys from settings
- **Comprehensive Testing**: Backend (pytest) and frontend UI tests included

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Google Gemini API Key ([Get one here](https://ai.google.dev/))
- Node.js 16+ (optional, for TypeScript compilation)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/haseeb-heaven/islamic-guidance-ai
   cd islamic-guidance-ai
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   
   Create a `.env` file in the root directory:
   ```env
   GEMINI_API_KEY=your_api_key_here
   ```
   
   Or set it via the Settings page in the UI after starting the server.

### Running the Application

#### Backend (FastAPI Server)

```bash
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

The server will start at `http://127.0.0.1:8000`

#### Frontend

The frontend is served automatically by the FastAPI server as static files. Simply navigate to:

```
http://127.0.0.1:8000
```

**Pages:**
- **Home**: `http://127.0.0.1:8000/` - Main search interface
- **Settings**: `http://127.0.0.1:8000/settings.html` - Configure API key and theme

### Using Docker

#### Build and run with Docker

```bash
docker build -t islamic-guidance-ai .
docker run -p 8000:8000 -e GEMINI_API_KEY=your_key_here islamic-guidance-ai
```

#### Using Docker Compose

```bash
# Set your API key in .env first
docker-compose up
```

## 🧪 Testing

### Backend Tests (pytest)

Run all backend API tests:

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests
pytest tests/backend -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

### Frontend Tests

Open the test page in your browser:

```
http://127.0.0.1:8000/tests/frontend/test_ui_components.html
```

Or open the file directly:

```bash
# Windows
start tests/frontend/test_ui_components.html

# Mac/Linux
open tests/frontend/test_ui_components.html
```

### Test Coverage

- ✅ Quran search (valid/invalid inputs)
- ✅ Hadith search (multiple books, topics)
- ✅ API key management (get/save)
- ✅ Guidance endpoint (valid/invalid queries)
- ✅ Frontend components (dark mode, input validation)
- ✅ Static file serving

## 📁 Project Structure

```
islamic-guidance-ai/
├── main.py                 # FastAPI backend server
├── api_parsers.py          # Quran and Hadith API parsers
├── api_tester.py           # API testing utilities
├── index.html              # Main frontend page
├── settings.html           # Settings page
├── script.js               # Frontend logic
├── settings.js             # Settings page logic
├── styles.css              # Styling
├── src/                    # TypeScript source (optional)
│   ├── services/          # Service modules
│   └── routes/            # Route handlers
├── tests/                  # Test suite
│   ├── backend/           # Backend API tests
│   ├── frontend/          # Frontend UI tests
│   ├── integration/       # Integration tests
│   └── conftest.py        # Pytest configuration
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Docker Compose setup
├── requirements.txt        # Python dependencies
├── requirements-test.txt   # Test dependencies
└── pytest.ini             # Pytest settings
```

## 🔧 API Endpoints

### Backend API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/quran/search` | GET | Search Quran verses by keyword |
| `/api/hadith/search` | GET | Search Hadiths by topic and book |
| `/api/guidance` | POST | Get AI-powered Islamic guidance |
| `/api/get-api-key` | GET | Retrieved stored API key |
| `/api/save-api-key` | POST | Save API key to .env file |

### Example API Calls

**Search Quran:**
```bash
curl "http://127.0.0.1:8000/api/quran/search?keyword=patience"
```

**Search Hadith:**
```bash
curl "http://127.0.0.1:8000/api/hadith/search?topic=prayer&book=bukhari"
```

**Get Guidance:**
```bash
curl -X POST http://127.0.0.1:8000/api/guidance \
  -H "Content-Type: application/json" \
  -d '{"query": "I am feeling anxious about my future"}'
```

## 🎨 Features Detail

### Dark Mode
- Toggle button in top-right corner
- Persists preference in localStorage
- Applies to all pages

### API Key Management
- Load from .env file automatically
- Save via Settings page
- Password field with visibility toggle (eye icon)
- Backup storage in localStorage

### Search
- Minimum 10 character validation
- Real-time feedback
- Results include citations with links

## 🔐 Security Notes

> **WARNING**: The `/api/save-api-key` endpoint writes to the `.env` file and is intended for **development use only**. In production, manage API keys through environment variables or secure secret management systems.

## 📝 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Contact

For questions or issues, please open an issue on GitHub.
