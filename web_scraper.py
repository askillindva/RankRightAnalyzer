import trafilatura
import requests
from typing import Optional
import streamlit as st

def get_website_text_content(url: str) -> str:
    """
    Extract main text content from a website URL.
    
    Args:
        url: The URL to scrape content from
        
    Returns:
        Extracted text content from the website
        
    Raises:
        Exception: If content extraction fails
    """
    
    if not url:
        raise ValueError("URL cannot be empty")
    
    # Ensure URL has proper protocol
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        # Fetch the webpage
        downloaded = trafilatura.fetch_url(url)
        
        if downloaded is None:
            raise Exception(f"Failed to fetch content from URL: {url}")
        
        # Extract text content
        text = trafilatura.extract(
            downloaded,
            include_comments=False,
            include_tables=True,
            include_formatting=False,
            favor_precision=True
        )
        
        if not text or not text.strip():
            raise Exception("No text content could be extracted from the webpage")
        
        return text.strip()
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"Network error while fetching URL: {str(e)}")
    except Exception as e:
        raise Exception(f"Error extracting content from URL: {str(e)}")

def validate_url(url: str) -> tuple[bool, str]:
    """
    Validate if URL is accessible and can be scraped.
    
    Args:
        url: The URL to validate
        
    Returns:
        Tuple of (is_valid, message)
    """
    
    if not url:
        return False, "URL cannot be empty"
    
    # Ensure URL has proper protocol
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        # Quick HEAD request to check if URL is accessible
        response = requests.head(url, timeout=10, allow_redirects=True)
        
        if response.status_code == 200:
            return True, "URL is accessible"
        elif response.status_code == 405:
            # Some servers don't support HEAD, try GET
            response = requests.get(url, timeout=10, stream=True)
            if response.status_code == 200:
                return True, "URL is accessible"
            else:
                return False, f"HTTP {response.status_code}: {response.reason}"
        else:
            return False, f"HTTP {response.status_code}: {response.reason}"
            
    except requests.exceptions.Timeout:
        return False, "Request timed out - URL may be slow to respond"
    except requests.exceptions.ConnectionError:
        return False, "Connection error - check if URL is correct"
    except requests.exceptions.RequestException as e:
        return False, f"Request error: {str(e)}"
    except Exception as e:
        return False, f"Validation error: {str(e)}"

def get_confluence_content(url: str) -> str:
    """
    Specialized function for extracting Confluence page content.
    
    Args:
        url: Confluence page URL
        
    Returns:
        Extracted content optimized for Confluence pages
    """
    
    try:
        # Download the page
        downloaded = trafilatura.fetch_url(url)
        
        if downloaded is None:
            raise Exception("Failed to fetch Confluence page")
        
        # Extract with settings optimized for Confluence
        text = trafilatura.extract(
            downloaded,
            include_comments=False,
            include_tables=True,
            include_formatting=True,  # Keep some formatting for better structure
            favor_precision=True,
            deduplicate=True
        )
        
        if not text or not text.strip():
            raise Exception("No content could be extracted from Confluence page")
        
        return text.strip()
        
    except Exception as e:
        raise Exception(f"Error extracting Confluence content: {str(e)}")

def extract_metadata(url: str) -> dict:
    """
    Extract metadata from a webpage.
    
    Args:
        url: The URL to extract metadata from
        
    Returns:
        Dictionary containing metadata
    """
    
    try:
        downloaded = trafilatura.fetch_url(url)
        
        if downloaded is None:
            return {}
        
        metadata = trafilatura.extract_metadata(downloaded)
        
        return {
            'title': metadata.title if metadata else None,
            'author': metadata.author if metadata else None,
            'date': metadata.date if metadata else None,
            'description': metadata.description if metadata else None,
            'sitename': metadata.sitename if metadata else None,
            'url': metadata.url if metadata else url
        }
        
    except Exception as e:
        st.warning(f"Could not extract metadata: {str(e)}")
        return {}
