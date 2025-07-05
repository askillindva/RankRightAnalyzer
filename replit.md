# RankRight - Document Analyzer

## Overview

RankRight is an AI-powered document analysis application built with Streamlit that evaluates documents and web content against predefined quality criteria. The system leverages Azure OpenAI for intelligent analysis and provides comprehensive scoring and recommendations for document improvement.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit web application with multi-page navigation
- **UI Components**: 
  - Main analysis interface for document upload and URL input
  - History page for viewing past analyses
  - Settings page for configuration
- **State Management**: Streamlit session state for maintaining analysis status and current analysis ID

### Backend Architecture
- **Application Layer**: Python-based modular architecture with specialized components
- **AI Integration**: Azure OpenAI client for content summarization and evaluation
- **Data Layer**: SQLite database for persistent storage of analyses and results
- **Document Processing**: Support for PDF, DOCX, and TXT file formats
- **Web Scraping**: Trafilatura-based content extraction from web URLs

## Key Components

### Core Modules

1. **DatabaseManager** (`database.py`)
   - SQLite database operations with two main tables:
     - `analyses`: Stores analysis metadata and results
     - `criteria_results`: Detailed criterion-specific evaluations
   - Handles storage and retrieval of analysis data

2. **DocumentProcessor** (`document_processor.py`)
   - Multi-format document processing (PDF, DOCX, TXT)
   - Uses PyPDF2/pypdf for PDF extraction
   - Uses python-docx for Word document processing
   - Temporary file handling for uploaded documents

3. **AzureOpenAIClient** (`azure_openai_client.py`)
   - Integration with Azure OpenAI services
   - Content summarization capabilities
   - Environment variable configuration for API credentials

4. **EvaluationEngine** (`evaluation_engine.py`)
   - Implements 6 predefined evaluation criteria:
     - Clarity & Readability
     - Completeness & Coverage
     - Accuracy & Reliability
     - Structure & Organization
     - Compliance & Standards
     - Actionability & Usefulness
   - AI-powered evaluation with scoring and recommendations

5. **WebScraper** (`web_scraper.py`)
   - Trafilatura-based web content extraction
   - Handles URL validation and content cleaning
   - Supports both HTTP and HTTPS protocols

6. **Utils** (`utils.py`)
   - Timestamp formatting utilities
   - Summary statistics generation
   - Data processing helpers

## Data Flow

1. **Input Processing**:
   - User uploads document or provides URL
   - Content extraction via DocumentProcessor or WebScraper
   - Text preprocessing and validation

2. **AI Analysis**:
   - Content summarization using Azure OpenAI
   - Evaluation against 6 criteria using EvaluationEngine
   - Scoring and recommendation generation

3. **Data Storage**:
   - Analysis results stored in SQLite database
   - Detailed criterion results maintained separately
   - Timestamp tracking for historical analysis

4. **Result Presentation**:
   - Streamlit interface displays scores and recommendations
   - Historical analysis browsing and comparison
   - Visual charts and statistics

## External Dependencies

### AI Services
- **Azure OpenAI**: Content analysis and summarization
  - Requires: AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY
  - Default model: GPT-4o
  - API version: 2024-02-01

### Python Libraries
- **Streamlit**: Web application framework
- **Plotly Express**: Data visualization
- **Pandas**: Data manipulation
- **Trafilatura**: Web content extraction
- **PyPDF2/pypdf**: PDF document processing
- **python-docx**: Word document processing
- **sqlite3**: Database operations

### File Processing
- **Supported Formats**: PDF, DOCX, TXT
- **Upload Method**: Streamlit file uploader with temporary file handling
- **Web Content**: Direct URL content extraction

## Deployment Strategy

### Local Development
- SQLite database for data persistence
- Environment variable configuration for Azure OpenAI
- Streamlit development server

### Production Considerations
- Database: Currently SQLite (suitable for single-user deployment)
- Scalability: Consider PostgreSQL migration for multi-user scenarios
- Security: Environment-based credential management
- Caching: Streamlit resource caching for component initialization

### Configuration Requirements
```
AZURE_OPENAI_ENDPOINT=<your-endpoint>
AZURE_OPENAI_API_KEY=<your-api-key>
AZURE_OPENAI_API_VERSION=2024-02-01
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
```

## Recent Changes

### July 01, 2025
- Initial RankRight application setup completed
- Added comprehensive error handling for Azure OpenAI firewall issues
- Implemented user-friendly error messages with fix instructions
- Added connection testing functionality in Settings page
- All core components operational: document processing, web scraping, database storage, AI evaluation

### July 02, 2025
- Added private endpoint support for Azure OpenAI connections
- Implemented configurable IP address settings in Settings page
- Created ConfigManager for persistent configuration storage
- Enhanced connection testing to show private endpoint status
- Updated Azure OpenAI client to support both public and private endpoints

### Known Issues & Solutions
- **Azure OpenAI 403 Firewall Error**: Common issue when Azure OpenAI has network restrictions
  - **Option 1**: Change Azure OpenAI networking from "Selected networks" to "All networks" in Azure Portal
  - **Option 2**: Add current IP address (34.9.104.227) to allowed list (temporary - IP changes on restart)
  - **Option 3**: Use Azure Service Tags for more secure access
  - **Production**: Deploy to Azure infrastructure for static IPs and private endpoints
  - Fix instructions integrated into error messages throughout the application

### Network Security Recommendations
- **Development**: Use IP whitelisting with current dynamic IP
- **Production**: Deploy to Azure App Service with VNet integration
- **Enterprise**: Implement private endpoints and Azure Front Door
- Replit does not provide static IPs or private endpoints

## Changelog

```
Changelog:
- July 01, 2025. Initial setup and Azure integration completed
```

## User Preferences

```
Preferred communication style: Simple, everyday language.
```