"""
Enhanced AI analysis service for job ad scam detection.

This module extends the base OpenAIAnalysisService with advanced capabilities:
- Analysis result validation and fallback mechanisms
- Confidence scoring and uncertainty quantification
- Analysis history tracking and learning from results
- Multiple AI model support and comparison
- Custom analysis templates and rule-based detection
- Feedback loop for improving analysis accuracy
- Batch processing for large-scale analysis
- Real-time analysis result streaming
"""

import logging
import json
import asyncio
import time
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime
import statistics
from collections import defaultdict
import re

from openai import AsyncOpenAI
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.models.data_models import JobAnalysisResult, JobClassification, AppConfig
from app.services.openai_analysis import OpenAIAnalysisService
from app.utils.logging import get_logger, get_correlation_id, log_with_context
from app.utils.metrics import get_metrics_collector
from app.utils.error_tracking import get_error_tracker, AlertSeverity


logger = get_logger(__name__)


class EnhancedAIAnalysisService(OpenAIAnalysisService):
    """
    Enhanced service for analyzing job advertisements using multiple AI models.
    
    This service extends the base OpenAIAnalysisService with advanced capabilities:
    - Analysis result validation and fallback mechanisms
    - Confidence scoring and uncertainty quantification
    - Analysis history tracking and learning from results
    - Multiple AI model support and comparison
    - Custom analysis templates and rule-based detection
    - Feedback loop for improving analysis accuracy
    - Batch processing for large-scale analysis
    - Real-time analysis result streaming
    """
    
    def __init__(self, config: AppConfig):
        """
        Initialize the enhanced AI analysis service.
        
        Args:
            config: Application configuration containing API keys and model settings
        """
        super().__init__(config)
        
        # Initialize additional models if configured
        self.models = {
            "primary": self.model,
            "fallback": config.openai_fallback_model if hasattr(config, "openai_fallback_model") else "gpt-3.5-turbo"
        }
        
        # Initialize analysis history cache
        self.analysis_history: Dict[str, List[JobAnalysisResult]] = {}
        self.analysis_history_max_size = 1000  # Maximum number of job ads to keep in history
        
        # Initialize rule-based detection patterns
        self.scam_patterns = self._initialize_scam_patterns()
        
        # Initialize vectorizer for similarity detection
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.vectorizer_fitted = False
        self.job_ad_vectors = {}
        
        # Initialize feedback tracking
        self.feedback_data = defaultdict(list)
        
        logger.info("EnhancedAIAnalysisService initialized with multiple model support")    

    async def analyze_job_ad(self, job_text: str) -> JobAnalysisResult:
        """
        Analyze a job advertisement with enhanced capabilities.
        
        Args:
            job_text: The job advertisement text to analyze
            
        Returns:
            JobAnalysisResult: Analysis result with trust score, classification, and reasons
            
        Raises:
            ValueError: If job_text is empty or invalid
            Exception: If analysis fails
        """
        correlation_id = get_correlation_id()
        metrics = get_metrics_collector()
        error_tracker = get_error_tracker()
        
        # Start timing the analysis
        start_time = time.time()
        
        try:
            # Check for similar job ads in history first
            similar_result = await self._check_similar_job_ads(job_text)
            if similar_result:
                log_with_context(
                    logger,
                    logging.INFO,
                    "Using cached analysis for similar job ad",
                    similarity_score=similar_result[1],
                    correlation_id=correlation_id
                )
                
                # Record metrics for cached analysis
                duration = time.time() - start_time
                metrics.record_service_call("openai", "analyze_job_ad_cached", True, duration)
                
                # Return the cached result with adjusted confidence
                cached_result = similar_result[0]
                return JobAnalysisResult(
                    trust_score=cached_result.trust_score,
                    classification=cached_result.classification,
                    reasons=cached_result.reasons,
                    confidence=cached_result.confidence * 0.9  # Slightly reduce confidence for cached results
                )
            
            # Apply rule-based pre-analysis
            rule_based_result = self._apply_rule_based_detection(job_text)
            
            # If rule-based detection has high confidence, use it directly
            if rule_based_result and rule_based_result.confidence > 0.9:
                log_with_context(
                    logger,
                    logging.INFO,
                    "Using rule-based analysis result",
                    trust_score=rule_based_result.trust_score,
                    classification=rule_based_result.classification_text,
                    confidence=rule_based_result.confidence,
                    correlation_id=correlation_id
                )
                
                # Record metrics for rule-based analysis
                duration = time.time() - start_time
                metrics.record_service_call("rule_based", "analyze_job_ad", True, duration)
                
                # Add to history
                self._add_to_analysis_history(job_text, rule_based_result)
                
                return rule_based_result
            
            # Proceed with AI analysis
            log_with_context(
                logger,
                logging.INFO,
                "Starting enhanced AI analysis",
                model=self.model,
                text_length=len(job_text),
                correlation_id=correlation_id
            )
            
            # Try primary model first
            try:
                result = await self._analyze_with_model(job_text, self.models["primary"])
                
                # Validate the result
                if not self._validate_analysis_result(result):
                    log_with_context(
                        logger,
                        logging.WARNING,
                        "Primary model result validation failed, trying fallback model",
                        model=self.models["primary"],
                        correlation_id=correlation_id
                    )
                    result = await self._analyze_with_model(job_text, self.models["fallback"])
            except Exception as e:
                log_with_context(
                    logger,
                    logging.ERROR,
                    "Primary model analysis failed, trying fallback model",
                    model=self.models["primary"],
                    error=str(e),
                    correlation_id=correlation_id
                )
                result = await self._analyze_with_model(job_text, self.models["fallback"])
            
            # If we have a rule-based result, combine it with AI result
            if rule_based_result:
                result = self._combine_analysis_results(result, rule_based_result)
            
            # Add to analysis history
            self._add_to_analysis_history(job_text, result)
            
            # Record successful metrics
            duration = time.time() - start_time
            metrics.record_service_call("openai", "analyze_job_ad_enhanced", True, duration)
            
            log_with_context(
                logger,
                logging.INFO,
                "Enhanced job ad analysis completed",
                trust_score=result.trust_score,
                classification=result.classification_text,
                confidence=result.confidence,
                duration_seconds=duration,
                correlation_id=correlation_id
            )
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            metrics.record_service_call("openai", "analyze_job_ad_enhanced", False, duration)
            error_tracker.track_service_call("openai", "analyze_job_ad_enhanced", False, duration)
            
            # Try fallback mechanisms
            try:
                fallback_result = await self._get_fallback_analysis(job_text, str(e))
                if fallback_result:
                    log_with_context(
                        logger,
                        logging.WARNING,
                        "Using fallback analysis result",
                        trust_score=fallback_result.trust_score,
                        classification=fallback_result.classification_text,
                        confidence=fallback_result.confidence,
                        original_error=str(e),
                        correlation_id=correlation_id
                    )
                    return fallback_result
            except Exception as fallback_error:
                log_with_context(
                    logger,
                    logging.ERROR,
                    "Fallback analysis also failed",
                    original_error=str(e),
                    fallback_error=str(fallback_error),
                    correlation_id=correlation_id
                )
            
            # Re-raise the original exception if all fallbacks fail
            raise    
    
    async def analyze_job_ads_batch(self, job_texts: List[str]) -> List[JobAnalysisResult]:
        """
        Analyze multiple job advertisements in batch.
        
        Args:
            job_texts: List of job advertisement texts to analyze
            
        Returns:
            List[JobAnalysisResult]: List of analysis results
        """
        correlation_id = get_correlation_id()
        
        log_with_context(
            logger,
            logging.INFO,
            "Starting batch analysis",
            batch_size=len(job_texts),
            correlation_id=correlation_id
        )
        
        # Create tasks for concurrent analysis
        tasks = [self.analyze_job_ad(text) for text in job_texts]
        
        # Execute analyses concurrently with rate limiting
        results = []
        batch_size = 5  # Process 5 at a time to avoid rate limits
        
        for i in range(0, len(tasks), batch_size):
            batch_tasks = tasks[i:i+batch_size]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    # Create a placeholder result for failed analyses
                    results.append(JobAnalysisResult(
                        trust_score=50,
                        classification=JobClassification.SUSPICIOUS,
                        reasons=["Analysis failed", "Could not determine legitimacy", "Manual review recommended"],
                        confidence=0.1
                    ))
                else:
                    results.append(result)
            
            # Add a small delay between batches to avoid rate limits
            if i + batch_size < len(tasks):
                await asyncio.sleep(1)
        
        log_with_context(
            logger,
            logging.INFO,
            "Batch analysis completed",
            successful_analyses=sum(1 for r in results if r.confidence > 0.5),
            total_analyses=len(results),
            correlation_id=correlation_id
        )
        
        return results
    
    async def analyze_job_ad_streaming(self, job_text: str, callback):
        """
        Analyze a job advertisement with streaming results.
        
        Args:
            job_text: The job advertisement text to analyze
            callback: Function to call with partial results
            
        Returns:
            JobAnalysisResult: Final analysis result
        """
        correlation_id = get_correlation_id()
        
        log_with_context(
            logger,
            logging.INFO,
            "Starting streaming analysis",
            text_length=len(job_text),
            correlation_id=correlation_id
        )
        
        # First send a preliminary rule-based result
        rule_based_result = self._apply_rule_based_detection(job_text)
        if rule_based_result:
            await callback({
                "type": "preliminary",
                "result": {
                    "trust_score": rule_based_result.trust_score,
                    "classification": rule_based_result.classification_text,
                    "reasons": rule_based_result.reasons,
                    "confidence": rule_based_result.confidence
                }
            })
        
        # Then check for similar job ads
        similar_result = await self._check_similar_job_ads(job_text)
        if similar_result:
            await callback({
                "type": "similar",
                "result": {
                    "trust_score": similar_result[0].trust_score,
                    "classification": similar_result[0].classification_text,
                    "reasons": similar_result[0].reasons,
                    "confidence": similar_result[0].confidence * 0.9,
                    "similarity_score": similar_result[1]
                }
            })
        
        # Start the actual analysis
        try:
            # Create the analysis prompt
            prompt = self.build_analysis_prompt(job_text)
            
            # Stream the response
            stream = await asyncio.wait_for(
                self.client.chat.completions.create(
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
                    temperature=0.3,
                    max_tokens=1000,
                    stream=True,
                    timeout=8.0
                ),
                timeout=10.0
            )
            
            collected_chunks = []
            collected_messages = []
            
            # Process the stream
            async for chunk in stream:
                collected_chunks.append(chunk)
                chunk_message = chunk.choices[0].delta.content
                if chunk_message is not None:
                    collected_messages.append(chunk_message)
                    
                    # Try to parse partial results
                    try:
                        partial_text = "".join(collected_messages)
                        if "{" in partial_text and "}" in partial_text:
                            json_start = partial_text.find("{")
                            json_end = partial_text.rfind("}") + 1
                            json_str = partial_text[json_start:json_end]
                            
                            partial_data = json.loads(json_str)
                            if all(k in partial_data for k in ["trust_score", "classification", "reasons"]):
                                await callback({
                                    "type": "partial",
                                    "result": partial_data
                                })
                    except:
                        # Ignore parsing errors for partial results
                        pass
            
            # Process the complete response
            full_response = "".join(collected_messages)
            final_result = self.parse_analysis_response(full_response)
            
            # Add to history
            self._add_to_analysis_history(job_text, final_result)
            
            # Send the final result
            await callback({
                "type": "final",
                "result": {
                    "trust_score": final_result.trust_score,
                    "classification": final_result.classification_text,
                    "reasons": final_result.reasons,
                    "confidence": final_result.confidence
                }
            })
            
            return final_result
            
        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                "Streaming analysis failed",
                error=str(e),
                correlation_id=correlation_id
            )
            
            # Try to get a fallback result
            fallback_result = await self._get_fallback_analysis(job_text, str(e))
            if fallback_result:
                await callback({
                    "type": "fallback",
                    "result": {
                        "trust_score": fallback_result.trust_score,
                        "classification": fallback_result.classification_text,
                        "reasons": fallback_result.reasons,
                        "confidence": fallback_result.confidence,
                        "error": str(e)
                    }
                })
                return fallback_result
            
            # If all fails, raise the exception
            raise    

    async def record_feedback(self, job_text: str, analysis_result: JobAnalysisResult, 
                            user_feedback: Dict[str, Any]) -> bool:
        """
        Record user feedback for an analysis result to improve future analyses.
        
        Args:
            job_text: The analyzed job advertisement text
            analysis_result: The original analysis result
            user_feedback: User feedback data including correct classification
            
        Returns:
            bool: True if feedback was successfully recorded
        """
        correlation_id = get_correlation_id()
        
        try:
            # Extract feedback data
            correct_classification = user_feedback.get("correct_classification")
            correct_trust_score = user_feedback.get("correct_trust_score")
            feedback_comment = user_feedback.get("comment", "")
            
            log_with_context(
                logger,
                logging.INFO,
                "Recording analysis feedback",
                original_classification=analysis_result.classification_text,
                correct_classification=correct_classification,
                original_trust_score=analysis_result.trust_score,
                correct_trust_score=correct_trust_score,
                correlation_id=correlation_id
            )
            
            # Store feedback for learning
            feedback_entry = {
                "job_text": job_text[:1000],  # Limit text size
                "original_result": {
                    "trust_score": analysis_result.trust_score,
                    "classification": analysis_result.classification_text,
                    "reasons": analysis_result.reasons,
                    "confidence": analysis_result.confidence
                },
                "correct_classification": correct_classification,
                "correct_trust_score": correct_trust_score,
                "feedback_comment": feedback_comment,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Add to feedback data
            self.feedback_data[analysis_result.classification_text].append(feedback_entry)
            
            # Update analysis history with corrected result if available
            if correct_classification and correct_trust_score is not None:
                try:
                    # Create corrected result
                    corrected_result = JobAnalysisResult(
                        trust_score=correct_trust_score,
                        classification=JobClassification(correct_classification),
                        reasons=analysis_result.reasons,  # Keep original reasons
                        confidence=1.0  # Human feedback has perfect confidence
                    )
                    
                    # Update history
                    self._add_to_analysis_history(job_text, corrected_result, is_feedback=True)
                    
                except Exception as e:
                    log_with_context(
                        logger,
                        logging.ERROR,
                        "Failed to update analysis history with feedback",
                        error=str(e),
                        correlation_id=correlation_id
                    )
            
            return True
            
        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                "Failed to record analysis feedback",
                error=str(e),
                correlation_id=correlation_id
            )
            return False
    
    def get_analysis_templates(self) -> List[Dict[str, Any]]:
        """
        Get available analysis templates for custom analysis.
        
        Returns:
            List[Dict[str, Any]]: List of available templates
        """
        return [
            {
                "id": "standard",
                "name": "Standard Job Analysis",
                "description": "Comprehensive analysis for general job postings",
                "model": self.models["primary"]
            },
            {
                "id": "remote_work",
                "name": "Remote Work Analysis",
                "description": "Specialized analysis for remote job opportunities",
                "model": self.models["primary"]
            },
            {
                "id": "high_salary",
                "name": "High Salary Job Analysis",
                "description": "Focused analysis for high-paying job offers",
                "model": self.models["primary"]
            },
            {
                "id": "quick",
                "name": "Quick Analysis",
                "description": "Faster analysis with slightly lower accuracy",
                "model": self.models["fallback"]
            }
        ] 
   
    async def analyze_with_template(self, job_text: str, template_id: str) -> JobAnalysisResult:
        """
        Analyze a job advertisement using a specific template.
        
        Args:
            job_text: The job advertisement text to analyze
            template_id: ID of the template to use
            
        Returns:
            JobAnalysisResult: Analysis result
            
        Raises:
            ValueError: If template_id is invalid
        """
        correlation_id = get_correlation_id()
        
        # Find the template
        templates = self.get_analysis_templates()
        template = next((t for t in templates if t["id"] == template_id), None)
        
        if not template:
            raise ValueError(f"Invalid template ID: {template_id}")
        
        log_with_context(
            logger,
            logging.INFO,
            "Analyzing job ad with template",
            template_id=template_id,
            template_name=template["name"],
            correlation_id=correlation_id
        )
        
        # Customize analysis based on template
        if template_id == "remote_work":
            # Use specialized prompt for remote work
            prompt = self._build_remote_work_prompt(job_text)
            model = template["model"]
        elif template_id == "high_salary":
            # Use specialized prompt for high salary jobs
            prompt = self._build_high_salary_prompt(job_text)
            model = template["model"]
        elif template_id == "quick":
            # Use fallback model for quick analysis
            prompt = self.build_analysis_prompt(job_text)
            model = self.models["fallback"]
        else:
            # Use standard analysis
            prompt = self.build_analysis_prompt(job_text)
            model = self.models["primary"]
        
        # Perform the analysis
        try:
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=model,
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
                    temperature=0.3,
                    max_tokens=1000,
                    timeout=8.0
                ),
                timeout=10.0
            )
            
            if not response.choices or not response.choices[0].message.content:
                raise Exception("Empty response from OpenAI API")
                
            analysis_text = response.choices[0].message.content.strip()
            result = self.parse_analysis_response(analysis_text)
            
            # Add template info to result (not stored in JobAnalysisResult but returned in dict)
            result_dict = {
                "trust_score": result.trust_score,
                "classification": result.classification_text,
                "reasons": result.reasons,
                "confidence": result.confidence,
                "template": {
                    "id": template_id,
                    "name": template["name"]
                }
            }
            
            log_with_context(
                logger,
                logging.INFO,
                "Template analysis completed",
                template_id=template_id,
                trust_score=result.trust_score,
                classification=result.classification_text,
                correlation_id=correlation_id
            )
            
            # Add to history
            self._add_to_analysis_history(job_text, result)
            
            return result
            
        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                "Template analysis failed",
                template_id=template_id,
                error=str(e),
                correlation_id=correlation_id
            )
            raise
    
    def get_analysis_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about analysis history and performance.
        
        Returns:
            Dict[str, Any]: Analysis statistics
        """
        # Count classifications
        classifications = {"Legit": 0, "Suspicious": 0, "Likely Scam": 0}
        confidence_by_class = {"Legit": [], "Suspicious": [], "Likely Scam": []}
        trust_scores = []
        
        for job_text, results in self.analysis_history.items():
            if results:
                latest = results[-1]
                classifications[latest.classification_text] += 1
                confidence_by_class[latest.classification_text].append(latest.confidence)
                trust_scores.append(latest.trust_score)
        
        # Calculate average confidence by classification
        avg_confidence = {}
        for cls, values in confidence_by_class.items():
            avg_confidence[cls] = statistics.mean(values) if values else 0
        
        # Calculate trust score distribution
        trust_score_ranges = {
            "0-20": 0,
            "21-40": 0,
            "41-60": 0,
            "61-80": 0,
            "81-100": 0
        }
        
        for score in trust_scores:
            if score <= 20:
                trust_score_ranges["0-20"] += 1
            elif score <= 40:
                trust_score_ranges["21-40"] += 1
            elif score <= 60:
                trust_score_ranges["41-60"] += 1
            elif score <= 80:
                trust_score_ranges["61-80"] += 1
            else:
                trust_score_ranges["81-100"] += 1
        
        # Calculate feedback statistics
        feedback_stats = {
            "total_feedback": sum(len(items) for items in self.feedback_data.values()),
            "agreement_rate": self._calculate_feedback_agreement_rate(),
            "feedback_by_class": {cls: len(items) for cls, items in self.feedback_data.items()}
        }
        
        return {
            "total_analyses": len(self.analysis_history),
            "classifications": classifications,
            "average_confidence": avg_confidence,
            "trust_score_distribution": trust_score_ranges,
            "feedback": feedback_stats
        }    

    # Private helper methods
    
    async def _analyze_with_model(self, job_text: str, model: str) -> JobAnalysisResult:
        """
        Analyze job ad with a specific model.
        
        Args:
            job_text: The job advertisement text to analyze
            model: The model to use for analysis
            
        Returns:
            JobAnalysisResult: Analysis result
        """
        correlation_id = get_correlation_id()
        
        log_with_context(
            logger,
            logging.INFO,
            "Analyzing with specific model",
            model=model,
            text_length=len(job_text),
            correlation_id=correlation_id
        )
        
        prompt = self.build_analysis_prompt(job_text)
        
        response = await asyncio.wait_for(
            self.client.chat.completions.create(
                model=model,
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
                temperature=0.3,
                max_tokens=800,  # Reduced from 1000 for faster response
                timeout=6.0      # Reduced from 8.0 seconds
            ),
            timeout=8.0          # Reduced from 10.0 seconds
        )
        
        if not response.choices or not response.choices[0].message.content:
            raise Exception(f"Empty response from model: {model}")
            
        analysis_text = response.choices[0].message.content.strip()
        result = self.parse_analysis_response(analysis_text)
        
        log_with_context(
            logger,
            logging.INFO,
            "Model analysis completed",
            model=model,
            trust_score=result.trust_score,
            classification=result.classification_text,
            confidence=result.confidence,
            correlation_id=correlation_id
        )
        
        return result
    
    def _validate_analysis_result(self, result: JobAnalysisResult) -> bool:
        """
        Validate analysis result for consistency and quality.
        
        Args:
            result: Analysis result to validate
            
        Returns:
            bool: True if result is valid
        """
        # Check confidence threshold
        if result.confidence < 0.5:
            logger.warning(f"Low confidence result: {result.confidence}")
            return False
        
        # Check consistency between trust score and classification
        if result.classification == JobClassification.LEGIT and result.trust_score < 65:
            logger.warning(f"Inconsistent LEGIT classification with trust score: {result.trust_score}")
            return False
        
        if result.classification == JobClassification.LIKELY_SCAM and result.trust_score > 35:
            logger.warning(f"Inconsistent LIKELY_SCAM classification with trust score: {result.trust_score}")
            return False
        
        # Check reason quality (ensure they're not too short or generic)
        for reason in result.reasons:
            if len(reason) < 10 or reason in ["Good job posting", "Legitimate job", "Scam job posting"]:
                logger.warning(f"Low quality reason: {reason}")
                return False
        
        return True
    
    async def _get_fallback_analysis(self, job_text: str, error_message: str) -> Optional[JobAnalysisResult]:
        """
        Get fallback analysis when primary analysis fails.
        
        Args:
            job_text: The job advertisement text to analyze
            error_message: Error message from the failed analysis
            
        Returns:
            Optional[JobAnalysisResult]: Fallback analysis result or None
        """
        correlation_id = get_correlation_id()
        
        # Try rule-based detection first
        rule_based_result = self._apply_rule_based_detection(job_text)
        if rule_based_result and rule_based_result.confidence > 0.7:
            log_with_context(
                logger,
                logging.INFO,
                "Using rule-based fallback",
                trust_score=rule_based_result.trust_score,
                classification=rule_based_result.classification_text,
                confidence=rule_based_result.confidence,
                correlation_id=correlation_id
            )
            return rule_based_result
        
        # Try similar job ads
        similar_result = await self._check_similar_job_ads(job_text)
        if similar_result and similar_result[1] > 0.8:  # High similarity threshold for fallback
            log_with_context(
                logger,
                logging.INFO,
                "Using similar job fallback",
                similarity_score=similar_result[1],
                correlation_id=correlation_id
            )
            return similar_result[0]
        
        # Try fallback model if different from primary
        if self.models["fallback"] != self.models["primary"]:
            try:
                log_with_context(
                    logger,
                    logging.INFO,
                    "Trying fallback model",
                    model=self.models["fallback"],
                    correlation_id=correlation_id
                )
                return await self._analyze_with_model(job_text, self.models["fallback"])
            except Exception as e:
                log_with_context(
                    logger,
                    logging.ERROR,
                    "Fallback model also failed",
                    model=self.models["fallback"],
                    error=str(e),
                    correlation_id=correlation_id
                )
        
        # If all else fails, create a conservative "suspicious" result
        log_with_context(
            logger,
            logging.WARNING,
            "Using default suspicious fallback",
            correlation_id=correlation_id
        )
        
        return JobAnalysisResult(
            trust_score=50,
            classification=JobClassification.SUSPICIOUS,
            reasons=[
                "Analysis encountered technical difficulties",
                "Unable to verify job legitimacy with confidence",
                "Recommend manual review or resubmission"
            ],
            confidence=0.5
        )
    
    def _initialize_scam_patterns(self) -> Dict[str, Any]:
        """
        Initialize rule-based scam detection patterns.
        
        Returns:
            Dict[str, Any]: Dictionary of scam patterns and their weights
        """
        return {
            "high_risk_indicators": [
                # Unrealistic salary promises
                {"pattern": r"\$\d{2,3},\d{3}\+?\s*(?:per\s+week|weekly|/week)", "weight": 0.8, "description": "Unrealistic weekly salary"},
                {"pattern": r"\$\d{3,4}\+?\s*(?:per\s+day|daily|/day)", "weight": 0.9, "description": "Unrealistic daily salary"},
                {"pattern": r"earn\s+\$\d{3,4}\+?\s*(?:per\s+hour|hourly|/hour)", "weight": 0.7, "description": "Unrealistic hourly wage"},
                
                # Work from home red flags
                {"pattern": r"(?:work\s+from\s+home|remote).{0,50}(?:no\s+experience|entry\s+level).{0,50}\$\d{3,4}", "weight": 0.6, "description": "High-paying remote work with no experience"},
                {"pattern": r"(?:make\s+money|earn\s+cash).{0,30}(?:from\s+home|remotely)", "weight": 0.5, "description": "Generic money-making claims"},
                
                # Urgency and pressure tactics
                {"pattern": r"(?:urgent|immediate|asap|right\s+away|start\s+today)", "weight": 0.4, "description": "Excessive urgency"},
                {"pattern": r"(?:limited\s+time|act\s+now|don't\s+miss|hurry)", "weight": 0.4, "description": "Pressure tactics"},
                
                # Vague job descriptions
                {"pattern": r"(?:data\s+entry|typing|customer\s+service).{0,50}(?:no\s+experience|easy\s+work)", "weight": 0.3, "description": "Vague job description"},
                {"pattern": r"(?:flexible\s+schedule|work\s+when\s+you\s+want|be\s+your\s+own\s+boss)", "weight": 0.3, "description": "Too-good-to-be-true flexibility"},
                
                # Payment and fee red flags
                {"pattern": r"(?:pay\s+fee|upfront\s+cost|investment\s+required|starter\s+kit)", "weight": 0.9, "description": "Upfront payment required"},
                {"pattern": r"(?:training\s+fee|processing\s+fee|background\s+check\s+fee)", "weight": 0.8, "description": "Training or processing fees"},
                
                # Contact and communication red flags
                {"pattern": r"(?:text\s+only|no\s+phone\s+calls|email\s+only)", "weight": 0.4, "description": "Limited communication methods"},
                {"pattern": r"(?:whatsapp|telegram|signal)\s+(?:only|preferred)", "weight": 0.5, "description": "Unusual communication platforms"},
                
                # Grammatical and spelling issues (common in scams)
                {"pattern": r"(?:recieve|recive|seperate|seprate|definately|definatly)", "weight": 0.2, "description": "Poor spelling/grammar"},
                {"pattern": r"(?:alot|a\s+lot\s+of\s+money|guarenteed|guarentee)", "weight": 0.2, "description": "Poor spelling/grammar"},
            ],
            
            "medium_risk_indicators": [
                # Generic company names
                {"pattern": r"(?:global|international|worldwide|universal)\s+(?:company|corporation|inc|llc)", "weight": 0.3, "description": "Generic company name"},
                
                # Unusual benefits
                {"pattern": r"(?:free\s+car|company\s+car|travel\s+benefits|housing\s+provided)", "weight": 0.4, "description": "Unusual benefits for entry-level"},
                
                # MLM indicators
                {"pattern": r"(?:build\s+your\s+team|recruit\s+others|network\s+marketing|multi\s*level)", "weight": 0.6, "description": "MLM indicators"},
                
                # Cryptocurrency/investment related
                {"pattern": r"(?:bitcoin|crypto|forex|trading|investment).{0,50}(?:training|opportunity)", "weight": 0.5, "description": "Cryptocurrency/investment schemes"},
            ],
            
            "positive_indicators": [
                # Legitimate job indicators
                {"pattern": r"(?:bachelor|degree|certification|license)\s+(?:required|preferred)", "weight": -0.3, "description": "Education requirements"},
                {"pattern": r"(?:benefits|health\s+insurance|401k|pto|vacation)", "weight": -0.2, "description": "Standard benefits"},
                {"pattern": r"(?:interview|references|background\s+check|drug\s+test)", "weight": -0.3, "description": "Standard hiring process"},
                {"pattern": r"(?:job\s+description|responsibilities|qualifications|requirements)", "weight": -0.2, "description": "Structured job posting"},
                
                # Legitimate company indicators
                {"pattern": r"(?:equal\s+opportunity|eeo|diversity|inclusion)", "weight": -0.2, "description": "EEO statements"},
                {"pattern": r"(?:www\.|https?://)[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "weight": -0.1, "description": "Company website"},
            ]
        }
    
    def _apply_rule_based_detection(self, job_text: str) -> Optional[JobAnalysisResult]:
        """
        Apply rule-based detection patterns to analyze job text.
        
        Args:
            job_text: The job advertisement text to analyze
            
        Returns:
            Optional[JobAnalysisResult]: Rule-based analysis result or None
        """
        if not job_text or len(job_text.strip()) < 20:
            return None
        
        text_lower = job_text.lower()
        total_score = 0.0
        matched_patterns = []
        
        # Check high-risk indicators
        for pattern_info in self.scam_patterns["high_risk_indicators"]:
            if re.search(pattern_info["pattern"], text_lower, re.IGNORECASE):
                total_score += pattern_info["weight"]
                matched_patterns.append(pattern_info["description"])
        
        # Check medium-risk indicators
        for pattern_info in self.scam_patterns["medium_risk_indicators"]:
            if re.search(pattern_info["pattern"], text_lower, re.IGNORECASE):
                total_score += pattern_info["weight"]
                matched_patterns.append(pattern_info["description"])
        
        # Check positive indicators
        for pattern_info in self.scam_patterns["positive_indicators"]:
            if re.search(pattern_info["pattern"], text_lower, re.IGNORECASE):
                total_score += pattern_info["weight"]
                matched_patterns.append(pattern_info["description"])
        
        # Normalize score and determine classification
        if total_score >= 0.8:
            classification = JobClassification.LIKELY_SCAM
            trust_score = max(5, 35 - int(total_score * 30))
            confidence = min(0.95, 0.7 + (total_score - 0.8) * 0.5)
        elif total_score >= 0.4:
            classification = JobClassification.SUSPICIOUS
            trust_score = max(25, 50 - int(total_score * 25))
            confidence = min(0.8, 0.6 + (total_score - 0.4) * 0.25)
        elif total_score <= -0.3:
            classification = JobClassification.LEGIT
            trust_score = min(95, 75 + int(abs(total_score) * 20))
            confidence = min(0.85, 0.5 + abs(total_score) * 0.5)
        else:
            # Not enough evidence for rule-based classification
            return None
        
        # Build reasons from matched patterns
        reasons = []
        if matched_patterns:
            if classification == JobClassification.LIKELY_SCAM:
                reasons = [
                    "Multiple scam indicators detected",
                    f"Detected patterns: {', '.join(matched_patterns[:3])}",
                    "High risk of fraudulent job posting"
                ]
            elif classification == JobClassification.SUSPICIOUS:
                reasons = [
                    "Some concerning patterns detected",
                    f"Warning signs: {', '.join(matched_patterns[:3])}",
                    "Exercise caution and verify independently"
                ]
            else:
                reasons = [
                    "Legitimate job posting indicators present",
                    f"Positive signs: {', '.join(matched_patterns[:3])}",
                    "Appears to follow standard job posting practices"
                ]
        else:
            reasons = [
                "Analysis based on job posting patterns",
                "Recommend additional verification",
                "Consider other factors before applying"
            ]
        
        return JobAnalysisResult(
            trust_score=trust_score,
            classification=classification,
            reasons=reasons[:3],  # Ensure exactly 3 reasons
            confidence=confidence
        )
    
    async def _check_similar_job_ads(self, job_text: str) -> Optional[Tuple[JobAnalysisResult, float]]:
        """
        Check for similar job ads in analysis history.
        
        Args:
            job_text: The job advertisement text to check
            
        Returns:
            Optional[Tuple[JobAnalysisResult, float]]: Tuple of (similar_result, similarity_score) or None
        """
        if not self.analysis_history or len(job_text.strip()) < 50:
            return None
        
        try:
            # Prepare texts for comparison
            texts = [job_text]
            results = []
            
            # Add historical job texts
            for historical_text, analysis_results in self.analysis_history.items():
                if analysis_results:
                    texts.append(historical_text)
                    results.append(analysis_results[-1])  # Get latest result
            
            if len(texts) < 2:
                return None
            
            # Vectorize texts using TF-IDF
            if not self.vectorizer_fitted:
                # Fit vectorizer with all available texts
                self.vectorizer.fit(texts)
                self.vectorizer_fitted = True
            
            # Transform texts to vectors
            vectors = self.vectorizer.transform(texts)
            
            # Calculate similarity between new job and historical jobs
            similarity_scores = cosine_similarity(vectors[0:1], vectors[1:]).flatten()
            
            # Find most similar job
            max_similarity_idx = np.argmax(similarity_scores)
            max_similarity = similarity_scores[max_similarity_idx]
            
            # Return result if similarity is high enough
            if max_similarity > 0.75:  # 75% similarity threshold
                return (results[max_similarity_idx], max_similarity)
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking similar job ads: {e}")
            return None
    
    def _add_to_analysis_history(self, job_text: str, result: JobAnalysisResult, is_feedback: bool = False) -> None:
        """
        Add analysis result to history for future similarity checking.
        
        Args:
            job_text: The analyzed job advertisement text
            result: The analysis result
            is_feedback: Whether this is a feedback-corrected result
        """
        try:
            # Create a hash key for the job text (first 1000 chars)
            text_key = job_text[:1000]
            
            # Initialize list if not exists
            if text_key not in self.analysis_history:
                self.analysis_history[text_key] = []
            
            # Add result to history
            self.analysis_history[text_key].append(result)
            
            # If this is feedback, mark it as the preferred result
            if is_feedback:
                # Move feedback result to end (most recent)
                feedback_result = self.analysis_history[text_key].pop()
                self.analysis_history[text_key].append(feedback_result)
            
            # Limit history size to prevent memory issues
            if len(self.analysis_history) > self.analysis_history_max_size:
                # Remove oldest entry
                oldest_key = next(iter(self.analysis_history))
                del self.analysis_history[oldest_key]
                
                # Mark vectorizer as needing refit
                self.vectorizer_fitted = False
                
        except Exception as e:
            logger.error(f"Error adding to analysis history: {e}")
    
    def _combine_analysis_results(self, ai_result: JobAnalysisResult, rule_result: JobAnalysisResult) -> JobAnalysisResult:
        """
        Combine AI and rule-based analysis results.
        
        Args:
            ai_result: Result from AI analysis
            rule_result: Result from rule-based analysis
            
        Returns:
            JobAnalysisResult: Combined analysis result
        """
        # Weight the results based on confidence
        ai_weight = ai_result.confidence * 0.7  # AI gets 70% weight
        rule_weight = rule_result.confidence * 0.3  # Rules get 30% weight
        
        total_weight = ai_weight + rule_weight
        
        if total_weight == 0:
            return ai_result  # Fallback to AI result
        
        # Calculate weighted trust score
        combined_trust_score = int(
            (ai_result.trust_score * ai_weight + rule_result.trust_score * rule_weight) / total_weight
        )
        
        # Determine classification based on combined trust score
        if combined_trust_score >= 65:
            classification = JobClassification.LEGIT
        elif combined_trust_score >= 35:
            classification = JobClassification.SUSPICIOUS
        else:
            classification = JobClassification.LIKELY_SCAM
        
        # Combine reasons (prefer AI reasons but include rule-based insights)
        combined_reasons = ai_result.reasons.copy()
        
        # Add rule-based insights if different classification
        if rule_result.classification != ai_result.classification:
            if len(combined_reasons) < 3:
                combined_reasons.append(f"Rule-based analysis suggests {rule_result.classification_text.lower()}")
            else:
                combined_reasons[2] = f"Rule-based analysis suggests {rule_result.classification_text.lower()}"
        
        # Calculate combined confidence
        combined_confidence = min(0.95, (ai_result.confidence + rule_result.confidence) / 2)
        
        return JobAnalysisResult(
            trust_score=combined_trust_score,
            classification=classification,
            reasons=combined_reasons[:3],  # Ensure exactly 3 reasons
            confidence=combined_confidence
        )
    
    def _build_remote_work_prompt(self, job_text: str) -> str:
        """
        Build specialized prompt for remote work analysis.
        
        Args:
            job_text: The job advertisement text
            
        Returns:
            str: Specialized prompt for remote work analysis
        """
        base_prompt = self.build_analysis_prompt(job_text)
        
        remote_work_addendum = """
        
Pay special attention to these remote work red flags:
        - Unrealistic salary promises for remote work
        - Vague job descriptions with "work from home" emphasis
        - Requests for upfront payments or equipment purchases
        - Limited communication methods or contact information
        - Promises of immediate start without proper vetting
        - "Too good to be true" benefits for entry-level remote work
        - Emphasis on "easy money" or "no experience required"
        - Use of non-standard communication platforms only
        
        Consider these positive indicators for legitimate remote work:
        - Clear job responsibilities and requirements
        - Standard hiring process (interviews, references)
        - Realistic salary ranges for the role and location
        - Proper company information and website
        - Standard benefits package
        - Clear equipment and workspace policies
        """
        
        return base_prompt + remote_work_addendum
    
    def _build_high_salary_prompt(self, job_text: str) -> str:
        """
        Build specialized prompt for high salary job analysis.
        
        Args:
            job_text: The job advertisement text
            
        Returns:
            str: Specialized prompt for high salary analysis
        """
        base_prompt = self.build_analysis_prompt(job_text)
        
        high_salary_addendum = """
        
Pay special attention to these high salary job red flags:
        - Salary significantly above market rate for the role
        - High pay with minimal qualifications or experience required
        - Emphasis on earning potential rather than job responsibilities
        - Vague job descriptions with focus on compensation
        - Promises of quick advancement or bonuses
        - "Get rich quick" language or unrealistic income claims
        - Pay structure that seems too good to be true
        - Commission-only or MLM-style compensation
        
        Consider these indicators for legitimate high-paying jobs:
        - Salary appropriate for specialized skills or experience
        - Clear qualification requirements justifying the salary
        - Detailed job responsibilities and expectations
        - Transparent company information and industry context
        - Standard benefits commensurate with the role level
        - Professional job posting format and language
        """
        
        return base_prompt + high_salary_addendum
    
    def _calculate_feedback_agreement_rate(self) -> float:
        """
        Calculate the rate at which user feedback agrees with original analysis.
        
        Returns:
            float: Agreement rate between 0.0 and 1.0
        """
        if not self.feedback_data:
            return 0.0
        
        total_feedback = 0
        agreements = 0
        
        for classification, feedback_items in self.feedback_data.items():
            for item in feedback_items:
                total_feedback += 1
                original_class = item["original_result"]["classification"]
                correct_class = item["correct_classification"]
                
                if original_class == correct_class:
                    agreements += 1
        
        return agreements / total_feedback if total_feedback > 0 else 0.0
    
    async def cleanup(self):
        """
        Clean up resources used by the Enhanced AI Analysis service.
        
        This method handles graceful cleanup of any resources, connections,
        HTTP clients, cached data, and background tasks used by the service.
        """
        correlation_id = get_correlation_id()
        
        try:
            log_with_context(
                logger,
                logging.INFO,
                "Cleaning up Enhanced AI Analysis service resources",
                analysis_history_size=len(self.analysis_history),
                feedback_data_size=sum(len(items) for items in self.feedback_data.values()),
                correlation_id=correlation_id
            )
            
            # Close the OpenAI client if it has a close method
            if hasattr(self.client, 'close'):
                try:
                    await self.client.close()
                except Exception as e:
                    logger.warning(f"Could not close OpenAI client: {e}")
            
            # Clear analysis history cache to free memory
            if self.analysis_history:
                self.analysis_history.clear()
                logger.info("Cleared analysis history cache")
            
            # Clear feedback data
            if self.feedback_data:
                self.feedback_data.clear()
                logger.info("Cleared feedback data cache")
            
            # Clear job ad vectors cache
            if self.job_ad_vectors:
                self.job_ad_vectors.clear()
                logger.info("Cleared job ad vectors cache")
            
            # Reset vectorizer state
            self.vectorizer_fitted = False
            
            # Clear any references to prevent memory leaks
            self.client = None
            self.vectorizer = None
            
            log_with_context(
                logger,
                logging.INFO,
                "Enhanced AI Analysis service cleanup completed successfully",
                correlation_id=correlation_id
            )
            
        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                "Error during Enhanced AI Analysis service cleanup",
                error=str(e),
                correlation_id=correlation_id
            )