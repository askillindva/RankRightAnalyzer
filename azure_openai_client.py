import os
import json
import requests
from typing import Dict, List, Any, Optional
import streamlit as st

# Azure OpenAI client
try:
    from openai import AzureOpenAI
except ImportError:
    AzureOpenAI = None

class AzureOpenAIClient:
    """Client for interacting with Azure OpenAI services"""
    
    def __init__(self):
        """Initialize Azure OpenAI client with environment variables"""
        
        if AzureOpenAI is None:
            raise ImportError("openai library is required for Azure OpenAI integration")
        
        # Get configuration from environment variables
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "RankRightAnalyzer")
        
        # Private endpoint configuration
        self.use_private_endpoint = os.getenv("AZURE_OPENAI_USE_PRIVATE_ENDPOINT", "false").lower() == "true"
        self.private_endpoint_ip = os.getenv("AZURE_OPENAI_PRIVATE_IP", "")
        self.private_endpoint_fqdn = os.getenv("AZURE_OPENAI_PRIVATE_FQDN", "")
        
        if not self.endpoint or not self.api_key:
            raise ValueError(
                "Azure OpenAI configuration missing. Please set AZURE_OPENAI_ENDPOINT "
                "and AZURE_OPENAI_API_KEY environment variables."
            )
        
        # Initialize client with private endpoint support
        try:
            # Configure endpoint for private endpoint if enabled
            endpoint_url = self._get_effective_endpoint()
            
            self.client = AzureOpenAI(
                azure_endpoint=endpoint_url,
                api_key=self.api_key,
                api_version=self.api_version
            )
            self.connection_working = True
        except Exception as e:
            st.warning(f"Azure OpenAI client initialization failed: {str(e)}")
            self.connection_working = False
            self.client = None
    
    def _get_effective_endpoint(self) -> str:
        """
        Get the effective endpoint URL, considering private endpoint configuration.
        
        Returns:
            The endpoint URL to use for connections
        """
        if self.use_private_endpoint and self.private_endpoint_ip:
            # Replace the hostname in the endpoint with the private IP
            import urllib.parse
            parsed = urllib.parse.urlparse(self.endpoint)
            
            # Build the private endpoint URL
            if self.private_endpoint_fqdn:
                # Use custom FQDN if provided
                private_endpoint = f"{parsed.scheme}://{self.private_endpoint_fqdn}{parsed.path}"
            else:
                # Use IP address directly
                private_endpoint = f"{parsed.scheme}://{self.private_endpoint_ip}{parsed.path}"
            
            return private_endpoint
        else:
            # Use the standard public endpoint
            return self.endpoint
    
    def get_connection_info(self) -> Dict[str, Any]:
        """
        Get current connection configuration information.
        
        Returns:
            Dictionary containing connection details
        """
        return {
            "endpoint": self.endpoint,
            "effective_endpoint": self._get_effective_endpoint(),
            "use_private_endpoint": self.use_private_endpoint,
            "private_endpoint_ip": self.private_endpoint_ip,
            "private_endpoint_fqdn": self.private_endpoint_fqdn,
            "api_version": self.api_version,
            "deployment_name": self.deployment_name,
            "connection_working": self.connection_working
        }
    
    def summarize_content(self, content: str, max_length: int = 500) -> str:
        """
        Generate a concise summary of the content.
        
        Args:
            content: Text content to summarize
            max_length: Maximum length of summary in words
            
        Returns:
            Generated summary
        """
        
        if not self.connection_working or self.client is None:
            raise Exception(
                "Azure OpenAI connection not available. Please check your firewall settings:\n\n"
                "1. Go to your Azure OpenAI resource in Azure Portal\n"
                "2. Navigate to 'Networking' section\n"
                "3. Either:\n"
                "   - Add your current IP address to allowed IPs, OR\n"
                "   - Change from 'Selected networks' to 'All networks'\n"
                "4. Save the changes and wait a few minutes\n\n"
                "Error: Connection blocked by Virtual Network/Firewall rules"
            )
        
        prompt = f"""
        Create a very concise summary of this document in simple, everyday language. Keep it under {max_length} words. Replace Key purpose or goal with the purpose of the document and Areas of improvement in the document with Suggested improvments in the document. Do not include ** in the headers. 
        Focus on:
        - Key purpose or goal, keep it under 100 words.
        - Areas of improvement in the document. keep it under 100 words.
        
        Write in plain language that anyone can understand. Avoid technical jargon.
        
        Content:
        {content}
        
        Summary:
        """
        
        try:
            if self.client is None:
                raise Exception("Client not initialized")
                
            response = self.client.chat.completions.create(
                model=self.deployment_name,  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert document analyst. Provide clear, concise summaries that capture the essence of the content."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            content = response.choices[0].message.content or ""
            return content.strip() if content else "Summary could not be generated"
            
        except Exception as e:
            error_msg = str(e)
            if "Virtual Network is configured" in error_msg:
                raise Exception(
                    "Virtual Network Configuration Issue:\n\n"
                    "Your Azure OpenAI resource is configured with a Virtual Network, which requires a specific VNet endpoint.\n\n"
                    "To fix this:\n"
                    "1. Go to Azure Portal → Your OpenAI Resource → Networking\n"
                    "2. Under 'Public network access':\n"
                    "   - Change from 'Disabled' to 'Enabled from all networks'\n"
                    "   - OR change from 'Enabled from selected virtual networks and IP addresses' to 'Enabled from all networks'\n"
                    "3. Click 'Save' and wait 5-10 minutes\n"
                    "4. Try again\n\n"
                    "Alternative: If you need to keep VNet restrictions, you'll need to deploy this application within the same Azure VNet.\n\n"
                    f"Technical error: {error_msg}"
                )
            elif "403" in error_msg and ("Virtual Network" in error_msg or "Firewall" in error_msg):
                raise Exception(
                    "Access denied due to Azure firewall rules. To fix this:\n\n"
                    "1. Go to your Azure OpenAI resource in Azure Portal\n"
                    "2. Click on 'Networking' in the left menu\n"
                    "3. Under 'Firewalls and virtual networks':\n"
                    "   - Change from 'Selected networks' to 'All networks', OR\n"
                    "   - Add your current IP address to the allowed list\n"
                    "4. Click 'Save' and wait 2-3 minutes for changes to take effect\n"
                    "5. Try the analysis again\n\n"
                    f"Technical error: {error_msg}"
                )
            else:
                raise Exception(f"Failed to generate summary: {str(e)}")
    
    def evaluate_against_criteria(self, content: str, criterion_name: str, 
                                criterion_description: str) -> Dict[str, Any]:
        """
        Evaluate content against a specific criterion.
        
        Args:
            content: Text content to evaluate
            criterion_name: Name of the evaluation criterion
            criterion_description: Description of what the criterion measures
            
        Returns:
            Dictionary containing evaluation results
        """
        
        prompt = f"""
        You are an expert document analyst. Evaluate the following content against the specified criterion and provide a detailed analysis.

        Criterion: {criterion_name}
        Description: {criterion_description}

        Content to evaluate:
        {content}

        Please provide your evaluation in JSON format with the following structure:
        {{
            "ranking": "Green|Amber|Red",
            "score": 7.5,
            "explanation": "Detailed explanation of the evaluation",
            "key_findings": ["Finding 1", "Finding 2", "Finding 3"],
            "recommendations": ["Recommendation 1", "Recommendation 2"]
        }}

        Ranking criteria:
        - Green: Excellent performance (8-10 points) - meets or exceeds expectations
        - Amber: Good performance with room for improvement (5-7 points) - partially meets expectations
        - Red: Poor performance requiring significant improvement (1-4 points) - does not meet expectations

        Score should be between 1-10 where 10 is excellent and 1 is very poor.
        """
        
        try:
            if self.client is None:
                raise Exception("Client not initialized")
                
            response = self.client.chat.completions.create(
                model=self.deployment_name,  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert document evaluator. Provide objective, detailed analysis in the exact JSON format requested."
                    },
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                max_tokens=1500,
                temperature=0.2
            )
            
            content = response.choices[0].message.content
            if not content:
                raise Exception("No response content received")
            result = json.loads(content)
            
            # Validate and clean the result
            validated_result = self._validate_evaluation_result(result)
            
            return validated_result
            
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse evaluation response as JSON: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to evaluate content: {str(e)}")
    
    def _validate_evaluation_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean evaluation result"""
        
        # Ensure required fields exist
        required_fields = ['ranking', 'score', 'explanation']
        for field in required_fields:
            if field not in result:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate ranking
        valid_rankings = ['Green', 'Amber', 'Red']
        if result['ranking'] not in valid_rankings:
            # Try to map common variations
            ranking_lower = result['ranking'].lower()
            if ranking_lower in ['green', 'good', 'excellent']:
                result['ranking'] = 'Green'
            elif ranking_lower in ['amber', 'yellow', 'warning', 'moderate']:
                result['ranking'] = 'Amber'
            elif ranking_lower in ['red', 'poor', 'bad', 'critical']:
                result['ranking'] = 'Red'
            else:
                result['ranking'] = 'Amber'  # Default fallback
        
        # Validate score
        try:
            score = float(result['score'])
            result['score'] = max(1.0, min(10.0, score))  # Clamp between 1-10
        except (ValueError, TypeError):
            result['score'] = 5.0  # Default fallback
        
        # Ensure explanation is a string
        if not isinstance(result['explanation'], str):
            result['explanation'] = str(result['explanation'])
        
        # Ensure key_findings is a list
        if 'key_findings' not in result:
            result['key_findings'] = []
        elif not isinstance(result['key_findings'], list):
            result['key_findings'] = [str(result['key_findings'])]
        
        # Ensure recommendations is a list
        if 'recommendations' not in result:
            result['recommendations'] = []
        elif not isinstance(result['recommendations'], list):
            result['recommendations'] = [str(result['recommendations'])]
        
        return result
    
    def analyze_content_structure(self, content: str) -> Dict[str, Any]:
        """
        Analyze the structure and organization of content.
        
        Args:
            content: Text content to analyze
            
        Returns:
            Dictionary containing structure analysis
        """
        
        prompt = f"""
        Analyze the structure and organization of the following content. 
        Provide insights about document quality, readability, and organization.

        Content:
        {content}

        Please provide your analysis in JSON format:
        {{
            "word_count": 1500,
            "readability_score": "Good|Fair|Poor",
            "structure_quality": "Excellent|Good|Fair|Poor",
            "key_topics": ["Topic 1", "Topic 2"],
            "document_type": "Report|Manual|Policy|Other",
            "organization_notes": "Brief notes about how well the content is organized"
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
                messages=[
                    {
                        "role": "system",
                        "content": "You are a document structure analyst. Provide objective analysis of document organization and quality."
                    },
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                max_tokens=800,
                temperature=0.1
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            # Return basic analysis if AI call fails
            word_count = len(content.split()) if content else 0
            return {
                "word_count": word_count,
                "readability_score": "Unknown",
                "structure_quality": "Unknown",
                "key_topics": [],
                "document_type": "Unknown",
                "organization_notes": f"Analysis failed: {str(e)}"
            }
    
    def test_connection(self) -> tuple[bool, str]:
        """Test the Azure OpenAI connection"""
        
        if not self.connection_working or self.client is None:
            return False, "Client not initialized properly"
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[{"role": "user", "content": "Hello, this is a connection test."}],
                max_tokens=10
            )
            return True, "Connection successful"
        except Exception as e:
            return False, str(e)
