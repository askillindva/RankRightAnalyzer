# RankRight - Intelligent Document Analyzer

RankRight is an AI-powered document analysis application that evaluates documents and web content against predefined quality criteria. Built with Streamlit and Azure OpenAI, it provides comprehensive scoring, recommendations, and intelligent insights for document improvement.

## Features

- **Multi-format Document Processing**: Supports PDF, DOCX, and TXT files
- **Web Content Analysis**: Direct URL content extraction and analysis
- **AI-Powered Evaluation**: 6 comprehensive criteria assessment using Azure OpenAI
- **Smart Narration**: Audio playback of key insights using text-to-speech
- **Interactive Interface**: Clean, modern Streamlit web interface
- **Session-Based Storage**: No database dependencies - perfect for containerized deployments
- **DevPod Ready**: Optimized for Azure DevPod and containerized environments

## Evaluation Criteria

The application analyzes documents against 6 key criteria:
1. **Clarity & Readability**
2. **Completeness & Coverage**
3. **Accuracy & Reliability**
4. **Structure & Organization**
5. **Compliance & Standards**
6. **Actionability & Usefulness**

## Prerequisites

- Python 3.11 or higher
- Azure OpenAI service access
- DevPod (for containerized deployment)
- Docker (if running locally with containers)

## Azure OpenAI Setup

Before deployment, ensure you have:

1. **Azure OpenAI Resource** deployed in Azure Portal
2. **API Key** from your Azure OpenAI resource
3. **Endpoint URL** (e.g., `https://your-resource.openai.azure.com/`)
4. **Deployment Name** for your GPT-4 model (recommended: `gpt-4o`)

## DevPod Deployment

### Step 1: Create DevPod Workspace

1. **Install DevPod** (if not already installed):
   ```bash
   # For macOS
   brew install devpod
   
   # For Windows (using winget)
   winget install loft-sh.devpod
   
   # For Linux
   curl -L -o devpod "https://github.com/loft-sh/devpod/releases/latest/download/devpod-linux-amd64" && sudo install -c -m 0755 devpod /usr/local/bin
   ```

2. **Create new workspace from repository**:
   ```bash
   devpod up <your-repository-url>
   ```

### Step 2: Environment Configuration

1. **Set up environment variables** in DevPod:
   ```bash
   # Create .env file
   cat > .env << EOF
   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
   AZURE_OPENAI_API_KEY=your-api-key-here
   AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
   AZURE_OPENAI_API_VERSION=2024-02-01
   EOF
   ```

2. **Install dependencies**:
   ```bash
   pip install -r pip-requirements.txt
   ```

### Step 3: Run the Application

1. **Start the Streamlit server**:
   ```bash
   streamlit run app.py --server.port 5000 --server.address 0.0.0.0
   ```

2. **Access the application**:
   - DevPod will automatically expose the port
   - Access via: `http://localhost:5000` or the DevPod-provided URL

### Step 4: Custom DNS Configuration

To run with a specific DNS name in DevPod:

1. **Configure port forwarding** in DevPod:
   ```bash
   devpod ssh <workspace-name> -- -L 5000:localhost:5000
   ```

2. **Set up custom domain** (if using reverse proxy):
   ```bash
   # Example with nginx
   server {
       listen 80;
       server_name your-custom-domain.com;
       
       location / {
           proxy_pass http://localhost:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

## Local Development

### Quick Start

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd rankright
   ```

2. **Install dependencies**:
   ```bash
   pip install -r pip-requirements.txt
   ```

3. **Set environment variables**:
   ```bash
   export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
   export AZURE_OPENAI_API_KEY="your-api-key-here"
   export AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o"
   export AZURE_OPENAI_API_VERSION="2024-02-01"
   ```

4. **Run the application**:
   ```bash
   streamlit run app.py --server.port 5000
   ```

### Using Docker

1. **Create Dockerfile**:
   ```dockerfile
   FROM python:3.11-slim
   
   WORKDIR /app
   
   COPY pip-requirements.txt .
   RUN pip install --no-cache-dir -r pip-requirements.txt
   
   COPY . .
   
   EXPOSE 5000
   
   CMD ["streamlit", "run", "app.py", "--server.port=5000", "--server.address=0.0.0.0"]
   ```

2. **Build and run**:
   ```bash
   docker build -t rankright .
   docker run -p 5000:5000 --env-file .env rankright
   ```

## Project Structure

```
rankright/
├── app.py                    # Main Streamlit application
├── azure_openai_client.py    # Azure OpenAI integration
├── document_processor.py     # Document processing (PDF, DOCX, TXT)
├── evaluation_engine.py      # AI evaluation logic
├── web_scraper.py            # Web content extraction
├── utils.py                  # Utility functions
├── config_manager.py         # Configuration management
├── pip-requirements.txt      # Python dependencies
├── README.md                 # This file
├── replit.md                 # Project documentation
└── .streamlit/
    └── config.toml           # Streamlit configuration
```

## Configuration

### Azure OpenAI Settings

The application supports both public and private Azure OpenAI endpoints:

- **Public Endpoint**: Standard Azure OpenAI resource
- **Private Endpoint**: VNet-integrated Azure OpenAI with custom IP/FQDN

Configuration is managed through the Settings page in the web interface.

### Streamlit Configuration

Key settings in `.streamlit/config.toml`:

```toml
[server]
headless = true
address = "0.0.0.0"
port = 5000
maxUploadSize = 200
```

## Troubleshooting

### Common Issues

1. **Azure OpenAI Connection Issues**:
   - Verify API key and endpoint URL
   - Check firewall settings (set to "All networks" for testing)
   - Ensure deployment name matches your Azure OpenAI model

2. **Port Access Issues**:
   - Ensure port 5000 is available
   - Check firewall settings
   - Verify DevPod port forwarding

3. **Document Processing Errors**:
   - Verify file format support (PDF, DOCX, TXT)
   - Check file size limits (max 200MB)
   - Ensure files are not corrupted

### DevPod Specific Issues

1. **Workspace Creation Fails**:
   ```bash
   devpod delete <workspace-name>
   devpod up <repository-url> --recreate
   ```

2. **Port Forwarding Issues**:
   ```bash
   devpod ssh <workspace-name> -- -L 5000:localhost:5000
   ```

3. **Environment Variables Not Loading**:
   ```bash
   # Check if .env file exists and is readable
   cat .env
   
   # Manually export if needed
   export $(cat .env | xargs)
   ```

## Data Storage

**Important**: This application uses session-based storage only:
- Analysis data is stored in browser memory during the session
- No persistent database or file storage
- Data is cleared when the browser tab is closed or page is reloaded
- Perfect for containerized and DevPod deployments

## Security Considerations

1. **API Keys**: Store securely in environment variables
2. **Network Access**: Configure Azure OpenAI firewall appropriately
3. **File Uploads**: Application processes files temporarily and cleans up automatically
4. **Session Data**: No persistent storage reduces security risks

## Performance Optimization

1. **Memory Usage**: Session data size is displayed in the Analysis History page
2. **File Processing**: Large files are processed in chunks
3. **AI Requests**: Optimized prompts for faster response times
4. **Caching**: Streamlit resource caching for component initialization

## Support

For issues and questions:
1. Check the Settings page connection test
2. Review the troubleshooting section
3. Verify Azure OpenAI configuration
4. Check DevPod logs for deployment issues

## License

This project is designed for enterprise document analysis and improvement workflows.