import os
import json
import requests
from typing import Dict, List, Any, Optional
import streamlit as st
import logging
import traceback
from datetime import datetime

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
        
        # Initialize client and debugging
        self.connection_working = False
        self.client = None
        self.debug_logs = []
        self.last_request_info = {}
        
        self._log_debug("Azure OpenAI Client Initialization", {
            "url": self.url,
            "has_api_key": bool(self.api_key),
            "api_key_prefix": self.api_key[:8] + "..." if self.api_key else "None",
            "host": self.host,
            "deployment_name": self.deployment_name,
            "api_version": self.api_version
        })
        
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
            
            self._log_debug("Sending test request", {
                "url": self.url,
                "headers": {"api-key": f"{self.api_key[:8]}..." if self.api_key else "None"},
                "data": data
            })
            
            response = requests.post(
                self.url, 
                headers={"api-key": self.api_key}, 
                json=data, 
                verify=False,
                timeout=30
            )
            
            self._log_debug("Response received", {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "response_text": response.text[:500] + "..." if len(response.text) > 500 else response.text
            })
            
            if response.status_code == 200:
                self.connection_working = True
                self.client = response.json()
                self._log_debug("Connection successful", {"response": self.client})
                print("Azure OpenAI client initialized successfully")
            else:
                error_msg = f"Request failed with status code: {response.status_code}, Response: {response.text}"
                self._log_debug("Connection failed", {"error": error_msg})
                raise Exception(error_msg)
                
        except Exception as e:
            error_details = {
                "error": str(e),
                "traceback": traceback.format_exc(),
                "url": self.url,
                "has_api_key": bool(self.api_key)
            }
            self._log_debug("Initialization failed", error_details)
            print(f"Azure OpenAI client initialization failed: {str(e)}")
            self.client = None
            self.connection_working = False
    
    def _log_debug(self, action: str, details: Dict[str, Any]) -> None:
        """Log debug information with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "action": action,
            "details": details
        }
        self.debug_logs.append(log_entry)
        
        # Keep only last 20 logs to prevent memory issues
        if len(self.debug_logs) > 20:
            self.debug_logs = self.debug_logs[-20:]
    
    def get_debug_logs(self) -> List[Dict[str, Any]]:
        """Get debug logs for troubleshooting"""
        return self.debug_logs
    
    def _make_api_request(self, content: str, system_prompt: str = None) -> str:
        """Make API request using your custom format"""
        request_id = datetime.now().strftime("%H:%M:%S.%f")
        
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
            
            # Log request details
            self._log_debug(f"API Request {request_id}", {
                "url": self.url,
                "content_length": len(content),
                "has_system_prompt": bool(system_prompt),
                "system_prompt_length": len(system_prompt) if system_prompt else 0,
                "data": data,
                "headers": {"api-key": f"{self.api_key[:8]}..." if self.api_key else "None"}
            })
            
            # Store request info for debugging
            self.last_request_info = {
                "request_id": request_id,
                "timestamp": datetime.now().isoformat(),
                "url": self.url,
                "data": data
            }
            
            response = requests.post(
                self.url,
                headers={"api-key": self.api_key},
                json=data,
                verify=False,
                timeout=60
            )
            
            # Log response details
            self._log_debug(f"API Response {request_id}", {
                "status_code": response.status_code,
                "response_headers": dict(response.headers),
                "response_length": len(response.text),
                "response_text": response.text[:1000] + "..." if len(response.text) > 1000 else response.text
            })
            
            if response.status_code == 200:
                result = response.json()
                
                self._log_debug(f"Response Parsed {request_id}", {
                    "result_type": type(result).__name__,
                    "result_keys": list(result.keys()) if isinstance(result, dict) else "Not a dict",
                    "result_structure": str(result)[:500] + "..." if len(str(result)) > 500 else str(result)
                })
                
                # Extract the response content from your API's response format
                extracted_content = None
                
                # Try different possible response structures
                if isinstance(result, dict):
                    # Try common response field names
                    for field in ['response', 'content', 'message', 'answer', 'text', 'result', 'data']:
                        if field in result:
                            extracted_content = result[field]
                            self._log_debug(f"Content Extracted {request_id}", {
                                "field_used": field,
                                "content_type": type(extracted_content).__name__,
                                "content_preview": str(extracted_content)[:200] + "..." if len(str(extracted_content)) > 200 else str(extracted_content)
                            })
                            break
                    
                    # If no common field found, try to find text content in nested structures
                    if extracted_content is None:
                        if 'choices' in result and len(result['choices']) > 0:
                            choice = result['choices'][0]
                            if 'message' in choice and 'content' in choice['message']:
                                extracted_content = choice['message']['content']
                            elif 'text' in choice:
                                extracted_content = choice['text']
                        
                        if extracted_content:
                            self._log_debug(f"Content From Choices {request_id}", {
                                "content_preview": str(extracted_content)[:200] + "..." if len(str(extracted_content)) > 200 else str(extracted_content)
                            })
                
                # If still no content found, return the whole response
                if extracted_content is None:
                    extracted_content = json.dumps(result) if isinstance(result, dict) else str(result)
                    self._log_debug(f"Using Full Response {request_id}", {
                        "reason": "No standard content field found",
                        "content_preview": str(extracted_content)[:200] + "..." if len(str(extracted_content)) > 200 else str(extracted_content)
                    })
                
                return str(extracted_content)
            else:
                error_msg = f"API request failed with status code: {response.status_code}, Response: {response.text}"
                self._log_debug(f"Request Failed {request_id}", {
                    "status_code": response.status_code,
                    "response_text": response.text,
                    "error": error_msg
                })
                raise Exception(error_msg)
                
        except Exception as e:
            error_details = {
                "error": str(e),
                "traceback": traceback.format_exc(),
                "request_id": request_id,
                "url": self.url,
                "has_api_key": bool(self.api_key)
            }
            self._log_debug(f"Request Exception {request_id}", error_details)
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
        
        self._log_debug("Connection Test Started", {
            "connection_working": self.connection_working,
            "has_client": self.client is not None
        })
        
        if not self.connection_working or self.client is None:
            return False, "Client not initialized properly"
        
        try:
            # Test with a simple request
            test_response = self._make_api_request("Test connection - please respond with 'Connection successful'")
            
            self._log_debug("Connection Test Completed", {
                "success": True,
                "response_length": len(test_response),
                "response_preview": test_response[:100] + "..." if len(test_response) > 100 else test_response
            })
            
            return True, f"Connection successful. Response: {test_response[:100]}..."
        except Exception as e:
            self._log_debug("Connection Test Failed", {
                "error": str(e),
                "traceback": traceback.format_exc()
            })
            return False, f"Connection test failed: {str(e)}"
    
    def get_debug_summary(self) -> str:
        """Get a formatted debug summary for troubleshooting"""
        summary = []
        summary.append("=== Azure OpenAI Client Debug Summary ===")
        summary.append(f"Connection Status: {'Connected' if self.connection_working else 'Disconnected'}")
        summary.append(f"URL: {self.url}")
        summary.append(f"Host: {self.host}")
        summary.append(f"Deployment: {self.deployment_name}")
        summary.append(f"API Key: {'Set' if self.api_key else 'Missing'} ({self.api_key[:8]}... if set)")
        summary.append(f"Total Debug Logs: {len(self.debug_logs)}")
        
        if self.last_request_info:
            summary.append(f"\nLast Request: {self.last_request_info.get('timestamp', 'Unknown')}")
            summary.append(f"Request ID: {self.last_request_info.get('request_id', 'Unknown')}")
        
        summary.append("\n=== Recent Debug Logs ===")
        for log in self.debug_logs[-5:]:  # Show last 5 logs
            summary.append(f"[{log['timestamp']}] {log['action']}")
            if isinstance(log['details'], dict):
                for key, value in log['details'].items():
                    if key not in ['traceback', 'response_text']:  # Skip verbose details
                        summary.append(f"  {key}: {str(value)[:100]}...")
        
        return "\n".join(summary)