import os
import logging
import requests
import time
from typing import Optional, Dict, Any, List
from pathlib import Path
from collections import deque
from .config import MODEL_CONFIGS, API_CONFIG

class ModelManager:
    _instance = None
    _api_key: Optional[str] = None
    _request_times: deque = deque(maxlen=60)  # Store last 60 request times
    _min_request_interval = 1.0  # Minimum time between requests in seconds
    _rpm_limit = 60  # Together.AI's rate limit
    _last_progress_update = 0
    _progress_callback = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.api_key = os.getenv("TOGETHER_API_KEY")
        if not self.api_key:
            raise ValueError("TOGETHER_API_KEY environment variable is not set")
        
        self.base_url = API_CONFIG["together"]["base_url"]
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def set_progress_callback(self, callback):
        """Set a callback function for progress updates."""
        self._progress_callback = callback

    def _update_progress(self, message: str, progress: float = None):
        """Update progress if callback is set."""
        current_time = time.time()
        if (self._progress_callback and 
            current_time - self._last_progress_update >= 0.5):  # Update at most every 0.5 seconds
            self._progress_callback(message, progress)
            self._last_progress_update = current_time

    def _wait_for_rate_limit(self):
        """Wait if necessary to respect rate limits using a sliding window approach."""
        current_time = time.time()
        
        # Remove timestamps older than 1 minute
        while self._request_times and current_time - self._request_times[0] > 60:
            self._request_times.popleft()
        
        # If we've made 60 requests in the last minute, wait
        if len(self._request_times) >= self._rpm_limit:
            wait_time = 60 - (current_time - self._request_times[0])
            if wait_time > 0:
                self._update_progress(f"Rate limit reached, waiting {wait_time:.1f} seconds...")
                time.sleep(wait_time)
        
        # Ensure minimum interval between requests
        if self._request_times and current_time - self._request_times[-1] < self._min_request_interval:
            sleep_time = self._min_request_interval - (current_time - self._request_times[-1])
            if sleep_time > 0.1:  # Only sleep if more than 0.1 seconds needed
                time.sleep(sleep_time)
        
        self._request_times.append(time.time())

    def _handle_api_error(self, response: requests.Response) -> None:
        """Handle API errors with appropriate messages."""
        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 60))
            self._update_progress(f"Rate limit exceeded. Waiting {retry_after} seconds...")
            # Clear the request times queue to reset rate limiting
            self._request_times.clear()
            time.sleep(retry_after)
            raise Exception("Rate limit exceeded. Please try again in a moment.")
        elif response.status_code == 401:
            raise Exception("Invalid API key. Please check your TOGETHER_API_KEY.")
        elif response.status_code == 400:
            raise Exception(f"Invalid request: {response.text}")
        else:
            raise Exception(f"API request failed with status {response.status_code}: {response.text}")

    def _make_api_request(self, model_type: str, prompt: str) -> str:
        """Make a request to the Together.AI API with rate limiting."""
        if model_type not in MODEL_CONFIGS:
            raise ValueError(f"Unknown model type: {model_type}")

        config = MODEL_CONFIGS[model_type]
        model_name = API_CONFIG["together"]["models"][model_type]

        payload = {
            "model": model_name,
            "prompt": prompt,
            "max_tokens": API_CONFIG["together"]["max_tokens"],
            "temperature": config["temperature"],
            "top_p": config["top_p"],
            "repetition_penalty": config["repetition_penalty"],
            "stop": ["</s>", "Human:", "Assistant:"]
        }

        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                self._wait_for_rate_limit()
                self._update_progress("Making API request...")
                
                response = requests.post(
                    f"{self.base_url}/completions",
                    headers=self.headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    return response.json()["choices"][0]["text"].strip()
                else:
                    self._handle_api_error(response)
                    
            except requests.exceptions.RequestException as e:
                retry_count += 1
                if retry_count == max_retries:
                    self.logger.error(f"Failed to make API request after {max_retries} retries: {str(e)}")
                    raise
                wait_time = 2 ** retry_count  # Exponential backoff
                self._update_progress(f"Request failed, retrying in {wait_time} seconds...")
                time.sleep(wait_time)

    def get_model(self, model_type: str) -> tuple:
        """
        Get a model for inference.
        
        Args:
            model_type (str): Type of model to use ("summarizer", "level_adapter", or "flashcard_gen")
            
        Returns:
            tuple: (model, None) - The model is actually a function that makes API calls
        """
        if model_type not in MODEL_CONFIGS:
            raise ValueError(f"Unknown model type: {model_type}")

        def model_fn(text: str) -> str:
            return self._make_api_request(model_type, text)

        return model_fn, None

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the API configuration.
        
        Returns:
            Dict[str, Any]: Dictionary containing API information
        """
        info = {
            "api_provider": "Together.AI",
            "base_url": self.base_url,
            "available_models": list(MODEL_CONFIGS.keys()),
            "model_configs": MODEL_CONFIGS,
            "rate_limit": f"{self._rpm_limit} requests per minute"
        }
        return info 