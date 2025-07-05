# RankRight Installation Guide

## System Requirements

- **Python**: 3.11 or higher
- **Operating System**: Windows, macOS, or Linux
- **Memory**: Minimum 512MB RAM available
- **Storage**: 100MB free disk space
- **Network**: Internet connection for Azure OpenAI API

## Core Dependencies

### Required Python Packages

```txt
# Web Application Framework
streamlit>=1.46.1           # Interactive web UI framework

# AI Integration
openai>=1.93.0              # Azure OpenAI client for GPT-4o

# Data Processing
pandas>=2.3.0               # Data analysis and manipulation
plotly>=6.2.0               # Interactive visualizations

# Document Processing
pypdf2>=3.0.1               # PDF text extraction
python-docx>=1.2.0          # Word document processing

# Web Content Extraction
trafilatura>=2.0.0          # Clean web content extraction
requests>=2.32.4            # HTTP client for web requests
```

### Built-in Python Modules (No Installation Required)

- `sqlite3` - Database operations
- `json` - JSON data handling
- `os` - Operating system interface
- `tempfile` - Temporary file management
- `datetime` - Date/time operations
- `typing` - Type annotations
- `urllib.parse` - URL parsing

## Installation Steps

### 1. Clone/Download the Project
```bash
# If using git
git clone <repository-url>
cd rankright

# Or download and extract the ZIP file
```

### 2. Create Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
# Install from the current pyproject.toml
pip install -e .

# OR install packages individually:
pip install streamlit>=1.46.1
pip install openai>=1.93.0
pip install pandas>=2.3.0
pip install plotly>=6.2.0
pip install pypdf2>=3.0.1
pip install python-docx>=1.2.0
pip install trafilatura>=2.0.0
pip install requests>=2.32.4
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
# Required Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment-name
AZURE_OPENAI_API_VERSION=2024-02-01

# Optional: Private Endpoint Configuration
AZURE_OPENAI_USE_PRIVATE_ENDPOINT=false
AZURE_OPENAI_PRIVATE_IP=
AZURE_OPENAI_PRIVATE_FQDN=
```

### 5. Run the Application
```bash
# Start the application
streamlit run app.py --server.port 5000

# The app will be available at: http://localhost:5000
```

## Azure OpenAI Setup

### 1. Create Azure OpenAI Resource
1. Go to [Azure Portal](https://portal.azure.com)
2. Create a new Azure OpenAI resource
3. Note the endpoint URL and API key

### 2. Deploy a Model
1. In your Azure OpenAI resource, go to "Model deployments"
2. Deploy GPT-4o model
3. Name your deployment (e.g., "RankRightAnalyzer")
4. Use this deployment name in your environment variables

### 3. Configure Network Access
- **Public Access**: Set to "All networks" for simple setup
- **Private Endpoint**: Configure VNet and private endpoint if needed

## File Structure

```
rankright/
├── app.py                  # Main Streamlit application
├── azure_openai_client.py  # Azure OpenAI integration
├── database.py             # SQLite database manager
├── document_processor.py   # PDF/DOCX processing
├── evaluation_engine.py    # Document evaluation logic
├── web_scraper.py          # Web content extraction
├── utils.py                # Utility functions
├── config_manager.py       # Configuration management
├── dependencies.txt        # Dependency documentation
├── INSTALLATION.md         # This installation guide
├── replit.md              # Project documentation
└── pyproject.toml         # Python project configuration
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure all packages are installed
   pip list | grep -E "streamlit|openai|pandas"
   ```

2. **Azure OpenAI Connection Issues**
   - Verify endpoint URL and API key
   - Check network/firewall settings
   - Ensure deployment name is correct

3. **Port Already in Use**
   ```bash
   # Use a different port
   streamlit run app.py --server.port 8501
   ```

4. **File Processing Errors**
   - Ensure uploaded files are valid PDF/DOCX/TXT
   - Check file permissions

### Performance Optimization

- **Database**: SQLite works well for single-user setups
- **Memory**: Close unused browser tabs during analysis
- **Network**: Stable internet connection required for AI processing

## Development Setup

For development with additional tools:

```bash
# Install development dependencies
pip install pytest>=7.0.0 black>=22.0.0 flake8>=5.0.0

# Run tests (if available)
pytest

# Format code
black .

# Lint code
flake8 .
```

## Support

For issues with:
- **Application bugs**: Check the logs in the Streamlit interface
- **Azure OpenAI**: Verify your Azure subscription and resource status
- **Dependencies**: Try recreating the virtual environment

## Security Notes

- Keep your Azure OpenAI API key secure
- Use environment variables, never hardcode credentials
- Consider using Azure Key Vault for production deployments
- Enable private endpoints for enhanced security in production