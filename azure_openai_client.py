import os
import json
import requests
from typing import Dict, List, Any, Optional
import streamlit as st

class AzureOpenAIClient:
    """Client for interacting with Azure OpenAI services via custom API"""
    
    def __init__(self):
        """Initialize Azure OpenAI client with environment variables"""
        
        # Get configuration from environment variables (note the typos in your env file)
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("AZURE_OPENAT_API_KEY")
        self.host = os.getenv("AZURE_OPENAI_HOST")
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME") or os.getenv("AZURE_OPENAT_DEPLOYMENT_NAME")
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
        
        # Build URL from host and deployment name
        if self.host and self.deployment_name:
            self.url = f"https://{self.host}/api/v1/{self.deployment_name}/chat"
        elif self.endpoint:
            self.url = self.endpoint
        else:
            raise ValueError("Either AZURE_OPENAI_HOST and AZURE_OPENAI_DEPLOYMENT_NAME or AZURE_OPENAI_ENDPOINT must be set")
        
        if not self.api_key:
            raise ValueError(
                "Azure OpenAI configuration missing. Please set AZURE_OPENAI_API_KEY environment variable."
            )
        
        # Initialize client
        self.connection_working = False
        self.client = None
        
        try:
            # Test connection with your API structure
            data = {
                "questionContent": [
                    {
                        "type": "text",
                        "value": "Hey Can you tell me if you are working well?"
                    }
                ],
                "chatBotIds": [
                    "faebedce-b075-42aa-9130-bf109d2d8d91"
                ]
            }
            
            response = requests.post(
                self.url, 
                headers={"api-key": self.api_key}, 
                json=data, 
                verify=False
            )
            
            if response.status_code == 200:
                self.connection_working = True
                self.client = response.json()
                print("Azure OpenAI client initialized successfully")
            else:
                raise Exception(f"Request failed with status code: {response.status_code}")
                
        except Exception as e:
            print(f"Azure OpenAI client initialization failed: {str(e)}")
            self.client = None
            self.connection_working = False
    
    def _make_api_request(self, content: str, system_prompt: str = None) -> str:
        """Make API request using your custom format"""
        try:
            # Build request data in your API format
            question_content = [
                {
                    "type": "text",
                    "value": content if not system_prompt else f"{system_prompt}\n\n{content}"
                }
            ]
            
            data = {
                "questionContent": question_content,
                "chatBotIds": [
                    "faebedce-b075-42aa-9130-bf109d2d8d91"
                ]
            }
            
            response = requests.post(
                self.url,
                headers={"api-key": self.api_key},
                json=data,
                verify=False
            )
            
            if response.status_code == 200:
                result = response.json()
                # Extract the response content from your API's response format
                # You may need to adjust this based on your actual response structure
                if isinstance(result, dict) and 'response' in result:
                    return result['response']
                elif isinstance(result, dict) and 'content' in result:
                    return result['content']
                elif isinstance(result, dict) and 'message' in result:
                    return result['message']
                else:
                    # If the structure is different, return the whole response as string
                    return json.dumps(result) if isinstance(result, dict) else str(result)
            else:
                raise Exception(f"API request failed with status code: {response.status_code}")
                
        except Exception as e:
            raise Exception(f"API request failed: {str(e)}")
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get current connection configuration information"""
        return {
            'endpoint': self.url,
            'deployment_name': self.deployment_name,
            'api_version': self.api_version,
            'connection_status': 'Connected' if self.connection_working else 'Disconnected',
            'host': self.host
        }
    
    def summarize_content(self, content: str, max_length: int = 500) -> str:
        """Generate a concise summary of the content"""
        
        system_prompt = f"""You are an expert document analyst. Create a concise summary of the provided content in approximately {max_length} words or less. Focus on the main points, key insights, and essential information."""
        
        prompt = f"""Please provide a comprehensive summary of the following content:

Content:
{content}

Requirements:
- Maximum {max_length} words
- Include key points and main themes
- Maintain clarity and readability
- Focus on actionable insights"""
        
        try:
            return self._make_api_request(prompt, system_prompt)
        except Exception as e:
            return f"Summary generation failed: {str(e)}"
    
    def evaluate_against_criteria(self, content: str, criterion_name: str, criterion_description: str) -> Dict[str, Any]:
        """Evaluate content against a specific criterion"""
        
        system_prompt = f"""You are an expert document evaluator. Evaluate the provided content against the specified criterion and provide a detailed assessment in JSON format."""
        
        prompt = f"""
        Evaluate the following content against this criterion:
        
        Criterion: {criterion_name}
        Description: {criterion_description}
        
        Content:
        {content}
        
        Please provide your evaluation in JSON format:
        {{
            "score": 8,
            "ranking": "Green",
            "explanation": "Detailed explanation of the evaluation",
            "key_findings": ["Finding 1", "Finding 2"],
            "recommendations": ["Recommendation 1", "Recommendation 2"]
        }}
        
        Score scale: 1-10 (1=Very Poor, 10=Excellent)
        Ranking: Green (8-10), Amber (5-7), Red (1-4)
        """
        
        try:
            response = self._make_api_request(prompt, system_prompt)
            
            # Try to parse JSON response
            try:
                result = json.loads(response)
                return self._validate_evaluation_result(result)
            except json.JSONDecodeError:
                # If response is not JSON, extract information manually
                return self._parse_evaluation_response(response, criterion_name)
                
        except Exception as e:
            return {
                "score": 5,
                "ranking": "Amber",
                "explanation": f"Evaluation failed: {str(e)}",
                "key_findings": [],
                "recommendations": ["Please check the AI service connection"]
            }
    
    def _validate_evaluation_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean evaluation result"""
        # Ensure required fields exist
        if 'score' not in result:
            result['score'] = 5
        if 'ranking' not in result:
            score = result.get('score', 5)
            if score >= 8:
                result['ranking'] = 'Green'
            elif score >= 5:
                result['ranking'] = 'Amber'
            else:
                result['ranking'] = 'Red'
        
        # Ensure score is within valid range
        result['score'] = max(1, min(10, result.get('score', 5)))
        
        # Ensure explanation exists
        if 'explanation' not in result:
            result['explanation'] = 'No detailed explanation provided'
        
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
    
    def _parse_evaluation_response(self, response: str, criterion_name: str) -> Dict[str, Any]:
        """Parse non-JSON evaluation response"""
        # Basic parsing logic for when JSON parsing fails
        score = 5  # Default score
        ranking = "Amber"  # Default ranking
        
        # Try to extract score from response
        import re
        score_match = re.search(r'score[:\s]*(\d+)', response.lower())
        if score_match:
            score = int(score_match.group(1))
            score = max(1, min(10, score))
        
        # Determine ranking based on score
        if score >= 8:
            ranking = "Green"
        elif score >= 5:
            ranking = "Amber"
        else:
            ranking = "Red"
        
        return {
            "score": score,
            "ranking": ranking,
            "explanation": response[:500] + "..." if len(response) > 500 else response,
            "key_findings": [],
            "recommendations": [f"Review {criterion_name} based on the analysis provided"]
        }
    
    def test_connection(self) -> tuple[bool, str]:
        """Test the Azure OpenAI connection"""
        
        if not self.connection_working or self.client is None:
            return False, "Client not initialized properly"
        
        try:
            # Test with a simple request
            test_response = self._make_api_request("Test connection - please respond with 'Connection successful'")
            return True, f"Connection successful. Response: {test_response[:100]}..."
        except Exception as e:
            return False, f"Connection test failed: {str(e)}"