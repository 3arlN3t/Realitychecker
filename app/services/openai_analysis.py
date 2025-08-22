"""
OpenAI integration service for job ad scam analysis.

This module provides the OpenAIAnalysisService class that integrates with
OpenAI's GPT-4 API to analyze job advertisements and detect potential scams.
"""

import json
import logging
import time
from typing import Optional
import openai
from openai import AsyncOpenAI

from app.models.data_models import JobAnalysisResult, JobClassification, AppConfig
from app.utils.logging import get_logger, get_correlation_id, log_with_context
from app.utils.security import SecurityValidator
from app.utils.metrics import get_metrics_collector
from app.utils.error_tracking import get_error_tracker, AlertSeverity


logger = get_logger(__name__)


class OpenAIAnalysisService:
    """
    Service for analyzing job advertisements using OpenAI GPT-4.
    
    This service handles the integration with OpenAI's API to analyze job postings
    and determine their legitimacy, providing trust scores, classifications, and reasoning.
    """
    
    def __init__(self, config: AppConfig):
        """
        Initialize the OpenAI analysis service.
        
        Args:
            config: Application configuration containing OpenAI API key and model settings
        """
        self.config = config
        self.client = AsyncOpenAI(api_key=config.openai_api_key)
        self.model = config.openai_model
        
    async def analyze_job_ad(self, job_text: str) -> JobAnalysisResult:
        """
        Analyze a job advertisement for potential scam indicators.
        
        Args:
            job_text: The job advertisement text to analyze
            
        Returns:
            JobAnalysisResult: Analysis result with trust score, classification, and reasons
            
        Raises:
            ValueError: If job_text is empty or invalid
            Exception: If OpenAI API call fails or response is invalid
        """
        if not job_text or not job_text.strip():
            raise ValueError("Job text cannot be empty")
        
        # Sanitize and validate input text for security
        security_validator = SecurityValidator()
        sanitized_text = security_validator.sanitize_text(job_text)
        
        is_valid, validation_error = security_validator.validate_text_content(sanitized_text)
        if not is_valid:
            raise ValueError(f"Invalid job text content: {validation_error}")
        
        correlation_id = get_correlation_id()
        metrics = get_metrics_collector()
        error_tracker = get_error_tracker()
        
        log_with_context(
            logger,
            logging.INFO,
            "Starting job ad analysis",
            model=self.model,
            text_length=len(job_text),
            correlation_id=correlation_id
        )
        
        # Start timing the analysis
        import time
        start_time = time.time()
        
        try:
            prompt = self.build_analysis_prompt(sanitized_text)
            
            log_with_context(
                logger,
                logging.DEBUG,
                "Sending request to OpenAI API",
                model=self.model,
                prompt_length=len(prompt),
                correlation_id=correlation_id
            )
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert job market analyst specializing in identifying employment scams. Analyze job postings carefully and provide structured responses."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for more consistent analysis
                max_tokens=1000,
                timeout=30.0
            )
            
            if not response.choices or not response.choices[0].message.content:
                log_with_context(
                    logger,
                    logging.ERROR,
                    "Empty response from OpenAI API",
                    correlation_id=correlation_id
                )
                raise Exception("Empty response from OpenAI API")
                
            analysis_text = response.choices[0].message.content.strip()
            
            log_with_context(
                logger,
                logging.DEBUG,
                "Received OpenAI response",
                response_length=len(analysis_text),
                correlation_id=correlation_id
            )
            
            result = self.parse_analysis_response(analysis_text)
            
            # Record successful metrics
            duration = time.time() - start_time
            metrics.record_service_call("openai", "analyze_job_ad", True, duration)
            error_tracker.track_service_call("openai", "analyze_job_ad", True, duration)
            
            log_with_context(
                logger,
                logging.INFO,
                "Job ad analysis completed",
                trust_score=result.trust_score,
                classification=result.classification_text,
                confidence=result.confidence,
                duration_seconds=duration,
                correlation_id=correlation_id
            )
            
            return result
            
        except openai.APITimeoutError as e:
            duration = time.time() - start_time
            metrics.record_service_call("openai", "analyze_job_ad", False, duration)
            error_tracker.track_service_call("openai", "analyze_job_ad", False, duration)
            error_tracker.track_error(
                "APITimeoutError",
                str(e),
                "openai_service",
                correlation_id,
                {"duration": duration},
                severity=AlertSeverity.HIGH
            )
            
            log_with_context(
                logger,
                logging.ERROR,
                "OpenAI API timeout",
                error=str(e),
                duration_seconds=duration,
                correlation_id=correlation_id
            )
            raise Exception("Analysis service is currently unavailable. Please try again later.")
            
        except openai.RateLimitError as e:
            duration = time.time() - start_time
            metrics.record_service_call("openai", "analyze_job_ad", False, duration)
            error_tracker.track_service_call("openai", "analyze_job_ad", False, duration)
            error_tracker.track_error(
                "RateLimitError",
                str(e),
                "openai_service",
                correlation_id,
                {"duration": duration},
                severity=AlertSeverity.MEDIUM
            )
            
            log_with_context(
                logger,
                logging.ERROR,
                "OpenAI rate limit exceeded",
                error=str(e),
                duration_seconds=duration,
                correlation_id=correlation_id
            )
            raise Exception("Service is temporarily busy. Please try again in a few minutes.")
            
        except openai.APIError as e:
            duration = time.time() - start_time
            metrics.record_service_call("openai", "analyze_job_ad", False, duration)
            error_tracker.track_service_call("openai", "analyze_job_ad", False, duration)
            error_tracker.track_error(
                "APIError",
                str(e),
                "openai_service",
                correlation_id,
                {"duration": duration},
                severity=AlertSeverity.HIGH
            )
            
            log_with_context(
                logger,
                logging.ERROR,
                "OpenAI API error",
                error=str(e),
                duration_seconds=duration,
                correlation_id=correlation_id
            )
            raise Exception("Unable to analyze the job posting. Please try again.")
            
        except Exception as e:
            duration = time.time() - start_time
            metrics.record_service_call("openai", "analyze_job_ad", False, duration)
            error_tracker.track_service_call("openai", "analyze_job_ad", False, duration)
            
            # Determine severity based on error type
            severity = AlertSeverity.CRITICAL if "Empty response from OpenAI API" in str(e) else AlertSeverity.HIGH
            
            error_tracker.track_error(
                type(e).__name__,
                str(e),
                "openai_service",
                correlation_id,
                {"duration": duration},
                severity=severity
            )
            
            log_with_context(
                logger,
                logging.ERROR,
                "Unexpected error during analysis",
                error=str(e),
                duration_seconds=duration,
                correlation_id=correlation_id
            )
            # Re-raise specific exceptions we want to preserve
            if "Empty response from OpenAI API" in str(e):
                raise e
            raise Exception("An error occurred while analyzing the job posting.")
    
    def build_analysis_prompt(self, job_text: str) -> str:
        """
        Build the analysis prompt for OpenAI GPT-4.
        
        Args:
            job_text: The job advertisement text to analyze
            
        Returns:
            str: Formatted prompt for scam detection analysis
        """
        return f"""
Analyze the following job advertisement for potential scam indicators and provide a structured assessment.

JOB ADVERTISEMENT:
{job_text}

Please analyze this job posting and respond with a JSON object containing exactly these fields:

1. "trust_score": An integer from 0-100 (0 = definitely a scam, 100 = completely legitimate)
2. "classification": One of exactly these three strings: "Legit", "Suspicious", or "Likely Scam"
3. "reasons": An array of exactly 3 specific reasons supporting your classification
4. "confidence": A decimal from 0.0-1.0 indicating your confidence in the analysis

Consider these scam indicators:
- Unrealistic salary promises or "get rich quick" schemes
- Requests for upfront payments, fees, or personal financial information
- Vague job descriptions or responsibilities
- Poor grammar, spelling, or unprofessional communication
- Pressure tactics or urgency without legitimate business reasons
- Requests to work from home immediately without proper vetting
- Contact information that seems unprofessional or suspicious
- Company information that's hard to verify or doesn't exist

Classification guidelines:
- "Legit": 70-100 trust score, legitimate job posting with verifiable details
- "Suspicious": 30-69 trust score, some red flags but could be legitimate
- "Likely Scam": 0-29 trust score, multiple scam indicators present

Respond ONLY with valid JSON in this exact format:
{{
    "trust_score": 85,
    "classification": "Legit",
    "reasons": [
        "Company has verifiable online presence and contact information",
        "Job description is detailed and matches industry standards",
        "Salary range is realistic for the position and location"
    ],
    "confidence": 0.9
}}
"""
    
    def parse_analysis_response(self, response_text: str) -> JobAnalysisResult:
        """
        Parse the OpenAI response and extract analysis results.
        
        Args:
            response_text: Raw response text from OpenAI API
            
        Returns:
            JobAnalysisResult: Parsed analysis result
            
        Raises:
            Exception: If response format is invalid or cannot be parsed
        """
        try:
            # Try to extract JSON from the response
            response_text = response_text.strip()
            
            # Handle cases where response might have extra text around JSON
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON object found in response")
                
            json_text = response_text[start_idx:end_idx]
            data = json.loads(json_text)
            
            # Validate required fields
            required_fields = ['trust_score', 'classification', 'reasons', 'confidence']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                raise ValueError(f"Missing required fields: {missing_fields}")
            
            # Validate and convert classification
            classification_str = data['classification']
            try:
                classification = JobClassification(classification_str)
            except ValueError:
                raise ValueError(f"Invalid classification: {classification_str}")
            
            # Validate trust score
            trust_score = int(data['trust_score'])
            if not (0 <= trust_score <= 100):
                raise ValueError(f"Trust score must be 0-100, got: {trust_score}")
            
            # Validate reasons
            reasons = data['reasons']
            if not isinstance(reasons, list) or len(reasons) != 3:
                raise ValueError("Reasons must be a list of exactly 3 items")
            
            if not all(isinstance(reason, str) and reason.strip() for reason in reasons):
                raise ValueError("All reasons must be non-empty strings")
            
            # Validate confidence
            confidence = float(data['confidence'])
            if not (0.0 <= confidence <= 1.0):
                raise ValueError(f"Confidence must be 0.0-1.0, got: {confidence}")
            
            return JobAnalysisResult(
                trust_score=trust_score,
                classification=classification,
                reasons=reasons,
                confidence=confidence
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response text: {response_text}")
            raise Exception("Invalid response format from analysis service")
            
        except (ValueError, KeyError) as e:
            logger.error(f"Invalid response structure: {e}")
            logger.error(f"Response data: {response_text}")
            raise Exception("Invalid analysis response format")
            
        except Exception as e:
            logger.error(f"Unexpected error parsing response: {e}")
            raise Exception("Failed to process analysis results")
    
    async def health_check(self) -> dict:
        """
        Check the health of the OpenAI service.
        
        Returns:
            dict: Health status information
        """
        try:
            # Check if API key is configured
            if not self.config.openai_api_key or self.config.openai_api_key == "sk":
                return {
                    "status": "unhealthy",
                    "service": "openai",
                    "model": self.model,
                    "api_key_configured": False,
                    "error": "OpenAI API key not configured"
                }
            
            # For now, just check configuration without making API calls
            # API calls will be tested during actual usage
            return {
                "status": "healthy",
                "service": "openai",
                "model": self.model,
                "api_key_configured": True,
                "note": "Configuration validated, API calls will be tested during usage"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "service": "openai",
                "model": self.model,
                "api_key_configured": bool(self.config.openai_api_key),
                "error": str(e)
            }