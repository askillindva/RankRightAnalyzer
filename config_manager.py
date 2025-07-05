import os
import json
from typing import Dict, Any, Optional

class ConfigManager:
    """Manages configuration settings for the RankRight application"""
    
    def __init__(self, config_file: str = "config.json"):
        """
        Initialize the configuration manager.
        
        Args:
            config_file: Path to the JSON configuration file
        """
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file, creating default if doesn't exist"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            else:
                # Create default configuration
                default_config = {
                    "azure_openai": {
                        "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT", ""),
                        "api_key": os.getenv("AZURE_OPENAI_API_KEY", ""),
                        "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
                        "deployment_name": os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "RankRightAnalyzer"),
                        "use_private_endpoint": os.getenv("AZURE_OPENAI_USE_PRIVATE_ENDPOINT", "false").lower() == "true",
                        "private_endpoint_ip": os.getenv("AZURE_OPENAI_PRIVATE_IP", ""),
                        "private_endpoint_fqdn": os.getenv("AZURE_OPENAI_PRIVATE_FQDN", "")
                    }
                }
                self._save_config(default_config)
                return default_config
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return {}
    
    def _save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Error saving configuration: {e}")
    
    def get_azure_openai_config(self) -> Dict[str, Any]:
        """Get Azure OpenAI configuration"""
        return self.config.get("azure_openai", {})
    
    def update_azure_openai_config(self, **kwargs) -> None:
        """
        Update Azure OpenAI configuration.
        
        Args:
            **kwargs: Configuration parameters to update
        """
        if "azure_openai" not in self.config:
            self.config["azure_openai"] = {}
        
        for key, value in kwargs.items():
            self.config["azure_openai"][key] = value
        
        self._save_config(self.config)
    
    def get_effective_endpoint(self) -> str:
        """
        Get the effective endpoint URL, considering private endpoint configuration.
        
        Returns:
            The endpoint URL to use for connections
        """
        azure_config = self.get_azure_openai_config()
        
        endpoint = azure_config.get("endpoint", "")
        use_private = azure_config.get("use_private_endpoint", False)
        private_ip = azure_config.get("private_endpoint_ip", "")
        private_fqdn = azure_config.get("private_endpoint_fqdn", "")
        
        if use_private and private_ip:
            # Replace the hostname in the endpoint with the private IP
            import urllib.parse
            parsed = urllib.parse.urlparse(endpoint)
            
            # Build the private endpoint URL
            if private_fqdn:
                # Use custom FQDN if provided
                return f"{parsed.scheme}://{private_fqdn}{parsed.path}"
            else:
                # Use IP address directly
                return f"{parsed.scheme}://{private_ip}{parsed.path}"
        else:
            # Use the standard public endpoint
            return endpoint
    
    def get_connection_summary(self) -> Dict[str, Any]:
        """Get a summary of connection configuration"""
        azure_config = self.get_azure_openai_config()
        
        return {
            "endpoint": azure_config.get("endpoint", ""),
            "effective_endpoint": self.get_effective_endpoint(),
            "use_private_endpoint": azure_config.get("use_private_endpoint", False),
            "private_endpoint_ip": azure_config.get("private_endpoint_ip", ""),
            "private_endpoint_fqdn": azure_config.get("private_endpoint_fqdn", ""),
            "deployment_name": azure_config.get("deployment_name", ""),
            "api_version": azure_config.get("api_version", "2024-02-01")
        }
    
    def export_environment_variables(self) -> Dict[str, str]:
        """
        Export configuration as environment variables format.
        
        Returns:
            Dictionary of environment variable names and values
        """
        azure_config = self.get_azure_openai_config()
        
        env_vars = {}
        
        if azure_config.get("endpoint"):
            env_vars["AZURE_OPENAI_ENDPOINT"] = azure_config["endpoint"]
        if azure_config.get("api_key"):
            env_vars["AZURE_OPENAI_API_KEY"] = azure_config["api_key"]
        if azure_config.get("api_version"):
            env_vars["AZURE_OPENAI_API_VERSION"] = azure_config["api_version"]
        if azure_config.get("deployment_name"):
            env_vars["AZURE_OPENAI_DEPLOYMENT_NAME"] = azure_config["deployment_name"]
        if azure_config.get("use_private_endpoint"):
            env_vars["AZURE_OPENAI_USE_PRIVATE_ENDPOINT"] = str(azure_config["use_private_endpoint"]).lower()
        if azure_config.get("private_endpoint_ip"):
            env_vars["AZURE_OPENAI_PRIVATE_IP"] = azure_config["private_endpoint_ip"]
        if azure_config.get("private_endpoint_fqdn"):
            env_vars["AZURE_OPENAI_PRIVATE_FQDN"] = azure_config["private_endpoint_fqdn"]
        
        return env_vars
    
    def validate_configuration(self) -> tuple[bool, list[str]]:
        """
        Validate the current configuration.
        
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        azure_config = self.get_azure_openai_config()
        
        # Check required fields
        if not azure_config.get("endpoint"):
            issues.append("Azure OpenAI endpoint is missing")
        if not azure_config.get("api_key"):
            issues.append("Azure OpenAI API key is missing")
        if not azure_config.get("deployment_name"):
            issues.append("Azure OpenAI deployment name is missing")
        
        # Check private endpoint configuration
        if azure_config.get("use_private_endpoint", False):
            if not azure_config.get("private_endpoint_ip"):
                issues.append("Private endpoint IP is required when private endpoint is enabled")
        
        return len(issues) == 0, issues