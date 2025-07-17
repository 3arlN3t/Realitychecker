"""
Enhanced error messages and user feedback system for Reality Checker.

This module provides improved error handling, contextual feedback, progressive
disclosure, and intelligent error recovery mechanisms.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
import re
import traceback

from app.utils.logging import get_logger
from app.utils.user_experience import UserExperienceLevel, MessageTone

logger = get_logger(__name__)


class FeedbackSeverity(Enum):
    """Severity levels for user feedback."""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class FeedbackContext(Enum):
    """Context categories for feedback messages."""
    ONBOARDING = "onboarding"
    ANALYSIS = "analysis"
    FILE_PROCESSING = "file_processing"
    NETWORK = "network"
    VALIDATION = "validation"
    SYSTEM = "system"
    USER_INPUT = "user_input"
    HELP = "help"


@dataclass
class FeedbackMessage:
    """Structured feedback message with context and actions."""
    severity: FeedbackSeverity
    context: FeedbackContext
    title: str
    message: str
    explanation: Optional[str] = None
    solution: Optional[str] = None
    actions: List[str] = field(default_factory=list)
    related_help: List[str] = field(default_factory=list)
    error_code: Optional[str] = None
    recovery_suggestions: List[str] = field(default_factory=list)
    estimated_fix_time: Optional[str] = None
    user_experience_adapted: bool = False


@dataclass
class UserFeedbackHistory:
    """Track user's interaction with feedback messages."""
    user_phone: str
    recent_errors: List[Dict[str, Any]] = field(default_factory=list)
    error_patterns: Dict[str, int] = field(default_factory=dict)
    successful_recoveries: List[str] = field(default_factory=list)
    last_help_request: Optional[datetime] = None
    feedback_effectiveness: Dict[str, float] = field(default_factory=dict)


class EnhancedFeedbackSystem:
    """Comprehensive feedback and error handling system."""
    
    def __init__(self):
        """Initialize enhanced feedback system."""
        self.feedback_templates = self._create_feedback_templates()
        self.user_feedback_history: Dict[str, UserFeedbackHistory] = {}
        self.error_recovery_strategies = self._create_recovery_strategies()
        self.contextual_help_mapping = self._create_help_mapping()
        
    def _create_feedback_templates(self) -> Dict[str, Dict[str, FeedbackMessage]]:
        """Create comprehensive feedback message templates."""
        return {
            "analysis_errors": {
                "content_too_short": FeedbackMessage(
                    severity=FeedbackSeverity.WARNING,
                    context=FeedbackContext.VALIDATION,
                    title="More Information Needed",
                    message="I need more details to provide an accurate analysis.",
                    explanation="Job postings need sufficient information for me to identify potential red flags and assess legitimacy. Short or vague content makes it difficult to detect scam patterns.",
                    solution="Please include comprehensive job details such as:\n• Complete job title and description\n• Company name and information\n• Salary/compensation details\n• Job requirements and responsibilities\n• Contact information",
                    actions=["send_more_details", "get_help", "see_example"],
                    related_help=["how_to_submit", "what_info_needed"],
                    recovery_suggestions=[
                        "Copy the full job posting from the source",
                        "Include company details from their website",
                        "Add any additional context you have"
                    ],
                    estimated_fix_time="1-2 minutes"
                ),
                "file_processing_failed": FeedbackMessage(
                    severity=FeedbackSeverity.ERROR,
                    context=FeedbackContext.FILE_PROCESSING,
                    title="File Processing Issue",
                    message="I encountered a problem processing your file.",
                    explanation="This could be due to file format, size, or content issues. I work best with clear, text-readable PDF files.",
                    solution="Try these alternatives:\n• Send the job posting as plain text instead\n• Ensure the PDF contains selectable text (not just images)\n• Check that the file size is under 10MB\n• Try saving/exporting the document again",
                    actions=["send_as_text", "try_different_file", "get_help"],
                    related_help=["supported_formats", "file_requirements"],
                    recovery_suggestions=[
                        "Copy and paste the text from the PDF",
                        "Take a screenshot and convert to text",
                        "Save the document in a different format"
                    ],
                    estimated_fix_time="2-3 minutes"
                ),
                "network_error": FeedbackMessage(
                    severity=FeedbackSeverity.ERROR,
                    context=FeedbackContext.NETWORK,
                    title="Connection Issue",
                    message="I'm having trouble connecting to my analysis services.",
                    explanation="This is usually temporary and related to network connectivity or service maintenance.",
                    solution="Please try again in a few moments. If the issue persists, the service may be experiencing high demand or maintenance.",
                    actions=["try_again", "check_status", "get_support"],
                    related_help=["troubleshooting", "service_status"],
                    recovery_suggestions=[
                        "Wait 30 seconds and try again",
                        "Check your internet connection",
                        "Try sending a shorter message first"
                    ],
                    estimated_fix_time="30 seconds - 5 minutes"
                ),
                "analysis_timeout": FeedbackMessage(
                    severity=FeedbackSeverity.WARNING,
                    context=FeedbackContext.ANALYSIS,
                    title="Analysis Taking Longer Than Expected",
                    message="Your job posting is taking longer to analyze than usual.",
                    explanation="Complex or very long job postings sometimes require additional processing time. This is normal for detailed analysis.",
                    solution="I'm still working on your analysis. You can:\n• Wait a bit longer for detailed results\n• Try breaking very long postings into sections\n• Send a shorter version for quick assessment",
                    actions=["wait", "simplify_request", "get_quick_check"],
                    recovery_suggestions=[
                        "Send the most important parts first",
                        "Remove repetitive content",
                        "Focus on the core job description"
                    ],
                    estimated_fix_time="1-3 minutes"
                )
            },
            "user_input_errors": {
                "unclear_request": FeedbackMessage(
                    severity=FeedbackSeverity.INFO,
                    context=FeedbackContext.USER_INPUT,
                    title="I'm Not Sure What You Mean",
                    message="I didn't understand your request.",
                    explanation="I'm designed to analyze job postings and provide scam detection. I can also answer questions about job safety and my features.",
                    solution="Try one of these:\n• Send a job posting to analyze\n• Ask 'help' for assistance\n• Ask specific questions about job postings\n• Send 'demo' for an example",
                    actions=["send_job_posting", "get_help", "see_demo", "ask_question"],
                    related_help=["how_to_use", "available_commands"],
                    recovery_suggestions=[
                        "Be more specific about what you need",
                        "Use simple, clear language", 
                        "Ask one question at a time"
                    ]
                ),
                "language_not_supported": FeedbackMessage(
                    severity=FeedbackSeverity.WARNING,
                    context=FeedbackContext.USER_INPUT,
                    title="Language Support Limitation",
                    message="I detected content in a language I don't fully support yet.",
                    explanation="I work best with English job postings, though I can handle basic content in several languages. For best results, English content is recommended.",
                    solution="For the most accurate analysis:\n• Translate the job posting to English\n• Send key details in English\n• Use translation tools for complex content",
                    actions=["translate_content", "send_english", "get_help"],
                    related_help=["language_support", "translation_tips"],
                    recovery_suggestions=[
                        "Use Google Translate or similar tools",
                        "Focus on the most important details",
                        "Ask someone to help translate"
                    ]
                )
            },
            "success_messages": {
                "analysis_complete": FeedbackMessage(
                    severity=FeedbackSeverity.SUCCESS,
                    context=FeedbackContext.ANALYSIS,
                    title="Analysis Complete",
                    message="I've successfully analyzed your job posting.",
                    solution="Review the trust score, classification, and my detailed reasoning. Feel free to ask questions about any part of the analysis.",
                    actions=["ask_questions", "analyze_another", "get_safety_tips"],
                    related_help=["understanding_results", "trust_scores"]
                ),
                "file_processed": FeedbackMessage(
                    severity=FeedbackSeverity.SUCCESS,
                    context=FeedbackContext.FILE_PROCESSING,
                    title="File Processed Successfully",
                    message="I've extracted the text from your file and completed the analysis.",
                    actions=["review_results", "ask_questions", "send_another"]
                )
            },
            "informational": {
                "first_time_user": FeedbackMessage(
                    severity=FeedbackSeverity.INFO,
                    context=FeedbackContext.ONBOARDING,
                    title="Welcome to Reality Checker!",
                    message="I'm here to help you identify job scams and stay safe while job hunting.",
                    solution="To get started, simply send me a job posting (text or PDF) and I'll analyze it for red flags.",
                    actions=["start_tutorial", "send_job_posting", "get_help"],
                    related_help=["getting_started", "how_to_use"]
                ),
                "analysis_explanation": FeedbackMessage(
                    severity=FeedbackSeverity.INFO,
                    context=FeedbackContext.ANALYSIS,
                    title="How I Analyze Job Postings",
                    message="I examine multiple factors to assess job posting legitimacy.",
                    explanation="My analysis considers:\n• Salary realism and market rates\n• Company verification and legitimacy\n• Communication professionalism\n• Job description clarity and completeness\n• Contact information validity\n• Common scam patterns and red flags",
                    actions=["learn_more", "see_example", "analyze_posting"]
                )
            }
        }
    
    def _create_recovery_strategies(self) -> Dict[str, List[str]]:
        """Create error recovery strategies for common issues."""
        return {
            "file_processing": [
                "Convert PDF to text and send as message",
                "Take screenshot and use OCR tools",
                "Copy text manually from the document",
                "Try a different file format",
                "Reduce file size if too large"
            ],
            "network_issues": [
                "Check internet connection",
                "Wait 30 seconds and retry",
                "Try sending shorter content first",
                "Switch to different network if available",
                "Contact support if persistent"
            ],
            "content_validation": [
                "Include more detailed job information",
                "Add company name and contact details",
                "Provide salary/compensation information",
                "Include job requirements and responsibilities",
                "Send complete job posting without edits"
            ],
            "language_barriers": [
                "Use translation tools (Google Translate)",
                "Send key information in English",
                "Focus on specific concerning elements",
                "Ask for help from English speakers",
                "Use simple, clear language"
            ]
        }
    
    def _create_help_mapping(self) -> Dict[FeedbackContext, List[str]]:
        """Map feedback contexts to relevant help topics."""
        return {
            FeedbackContext.FILE_PROCESSING: [
                "supported_file_formats",
                "file_size_limits", 
                "pdf_requirements",
                "alternative_methods"
            ],
            FeedbackContext.ANALYSIS: [
                "how_analysis_works",
                "trust_scores_explained",
                "understanding_results",
                "analysis_limitations"
            ],
            FeedbackContext.VALIDATION: [
                "what_information_needed",
                "job_posting_requirements",
                "content_guidelines",
                "examples_good_submissions"
            ],
            FeedbackContext.USER_INPUT: [
                "how_to_use_commands",
                "available_features",
                "asking_questions",
                "getting_help"
            ]
        }
    
    def create_feedback(self, 
                       error_type: str, 
                       user_phone: str, 
                       user_experience: UserExperienceLevel = UserExperienceLevel.RETURNING_USER,
                       additional_context: Dict[str, Any] = None) -> FeedbackMessage:
        """
        Create contextual feedback message based on error type and user experience.
        
        Args:
            error_type: Type of error or feedback needed
            user_phone: User's phone number for personalization
            user_experience: User's experience level
            additional_context: Additional context for customization
            
        Returns:
            Customized feedback message
        """
        # Get base feedback message
        feedback = self._get_base_feedback(error_type)
        if not feedback:
            return self._create_generic_feedback(error_type)
        
        # Customize based on user experience
        feedback = self._adapt_for_user_experience(feedback, user_experience)
        
        # Add user-specific context
        feedback = self._personalize_feedback(feedback, user_phone, additional_context)
        
        # Track feedback
        self._track_feedback(user_phone, error_type, feedback)
        
        return feedback
    
    def _get_base_feedback(self, error_type: str) -> Optional[FeedbackMessage]:
        """Get base feedback message for error type."""
        for category in self.feedback_templates.values():
            if error_type in category:
                return category[error_type]
        return None
    
    def _create_generic_feedback(self, error_type: str) -> FeedbackMessage:
        """Create generic feedback for unknown error types."""
        return FeedbackMessage(
            severity=FeedbackSeverity.ERROR,
            context=FeedbackContext.SYSTEM,
            title="Unexpected Issue",
            message="I encountered an unexpected issue while processing your request.",
            solution="Please try again, or contact support if the problem persists.",
            actions=["try_again", "get_help", "contact_support"],
            error_code=error_type
        )
    
    def _adapt_for_user_experience(self, feedback: FeedbackMessage, experience: UserExperienceLevel) -> FeedbackMessage:
        """Adapt feedback message based on user experience level."""
        if experience == UserExperienceLevel.NEW_USER:
            # More detailed explanations for new users
            if not feedback.explanation:
                feedback.explanation = "As a new user, this might be your first time encountering this. Don't worry - it's easily fixable!"
            
            # Add tutorial suggestions
            if "start_tutorial" not in feedback.actions:
                feedback.actions.insert(0, "start_tutorial")
            
            # More encouraging tone
            feedback.message = f"Don't worry! {feedback.message}"
            
        elif experience == UserExperienceLevel.POWER_USER:
            # More concise for experienced users
            feedback.message = feedback.message.split('.')[0] + "."  # First sentence only
            feedback.explanation = None  # Remove basic explanations
            
            # Add advanced options
            if feedback.context == FeedbackContext.FILE_PROCESSING:
                feedback.actions.append("advanced_options")
        
        feedback.user_experience_adapted = True
        return feedback
    
    def _personalize_feedback(self, feedback: FeedbackMessage, user_phone: str, context: Dict[str, Any] = None) -> FeedbackMessage:
        """Personalize feedback based on user history and context."""
        history = self.user_feedback_history.get(user_phone)
        
        if history:
            # Check for repeated errors
            error_count = history.error_patterns.get(feedback.context.value, 0)
            if error_count > 2:
                feedback.message += f"\n\n💡 I notice you've encountered this before. {self._get_persistent_error_help(feedback.context)}"
            
            # Suggest previously successful recoveries
            if feedback.context.value in history.successful_recoveries:
                feedback.recovery_suggestions.insert(0, "Try the method that worked for you before")
        
        # Add context-specific information
        if context:
            if "file_size" in context and context["file_size"] > 5000000:  # 5MB
                feedback.solution += "\n\n📄 Note: Your file is quite large. Consider sending key excerpts as text for faster processing."
            
            if "retry_count" in context and context["retry_count"] > 0:
                feedback.message += f" (Attempt {context['retry_count'] + 1})"
        
        return feedback
    
    def _get_persistent_error_help(self, context: FeedbackContext) -> str:
        """Get help for users experiencing persistent errors."""
        help_text = {
            FeedbackContext.FILE_PROCESSING: "Consider using copy-paste instead of file uploads for more reliable results.",
            FeedbackContext.VALIDATION: "Try including more detailed job information in your submissions.",
            FeedbackContext.NETWORK: "You might want to check your internet connection or try during off-peak hours.",
            FeedbackContext.USER_INPUT: "Send 'tutorial' to review how to use Reality Checker effectively."
        }
        return help_text.get(context, "Send 'help' for personalized assistance.")
    
    def format_feedback_message(self, feedback: FeedbackMessage, include_actions: bool = True) -> str:
        """
        Format feedback message for display to user.
        
        Args:
            feedback: Feedback message to format
            include_actions: Whether to include action buttons/suggestions
            
        Returns:
            Formatted message string
        """
        # Choose emoji based on severity
        emoji_map = {
            FeedbackSeverity.INFO: "💡",
            FeedbackSeverity.SUCCESS: "✅",
            FeedbackSeverity.WARNING: "⚠️",
            FeedbackSeverity.ERROR: "❌",
            FeedbackSeverity.CRITICAL: "🚨"
        }
        
        emoji = emoji_map.get(feedback.severity, "📌")
        
        # Build message
        message_parts = [f"{emoji} **{feedback.title}**\n"]
        message_parts.append(feedback.message)
        
        # Add explanation if present
        if feedback.explanation:
            message_parts.append(f"\n🔍 **Why this happened:**\n{feedback.explanation}")
        
        # Add solution
        if feedback.solution:
            message_parts.append(f"\n💡 **What you can do:**\n{feedback.solution}")
        
        # Add recovery suggestions for errors
        if feedback.severity in [FeedbackSeverity.ERROR, FeedbackSeverity.WARNING] and feedback.recovery_suggestions:
            message_parts.append(f"\n🛠️ **Quick fixes:**")
            for suggestion in feedback.recovery_suggestions[:3]:  # Limit to 3 suggestions
                message_parts.append(f"• {suggestion}")
        
        # Add estimated fix time
        if feedback.estimated_fix_time:
            message_parts.append(f"\n⏱️ **Estimated fix time:** {feedback.estimated_fix_time}")
        
        # Add actions if requested
        if include_actions and feedback.actions:
            action_text = self._format_actions(feedback.actions)
            if action_text:
                message_parts.append(f"\n{action_text}")
        
        return "\n".join(message_parts)
    
    def _format_actions(self, actions: List[str]) -> str:
        """Format action suggestions for user."""
        action_map = {
            "try_again": "🔄 Try again",
            "get_help": "❓ Get help",
            "send_job_posting": "📄 Send job posting",
            "contact_support": "📞 Contact support",
            "start_tutorial": "🎓 Start tutorial",
            "send_as_text": "📝 Send as text",
            "see_example": "👀 See example",
            "analyze_another": "🔍 Analyze another",
            "ask_questions": "❓ Ask questions"
        }
        
        formatted_actions = []
        for action in actions[:4]:  # Limit to 4 actions
            formatted_action = action_map.get(action, action.replace("_", " ").title())
            formatted_actions.append(formatted_action)
        
        if formatted_actions:
            return "**Quick actions:**\n" + "\n".join([f"• {action}" for action in formatted_actions])
        
        return ""
    
    def _track_feedback(self, user_phone: str, error_type: str, feedback: FeedbackMessage) -> None:
        """Track feedback for analytics and personalization."""
        if user_phone not in self.user_feedback_history:
            self.user_feedback_history[user_phone] = UserFeedbackHistory(user_phone=user_phone)
        
        history = self.user_feedback_history[user_phone]
        
        # Track error patterns
        context_key = feedback.context.value
        history.error_patterns[context_key] = history.error_patterns.get(context_key, 0) + 1
        
        # Track recent errors
        error_record = {
            "timestamp": datetime.now(timezone.utc),
            "error_type": error_type,
            "severity": feedback.severity.value,
            "context": feedback.context.value
        }
        
        history.recent_errors.append(error_record)
        
        # Keep only recent errors (last 24 hours)
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
        history.recent_errors = [
            error for error in history.recent_errors 
            if error["timestamp"] > cutoff_time
        ]
    
    def record_successful_recovery(self, user_phone: str, recovery_method: str, context: FeedbackContext) -> None:
        """Record when a user successfully recovers from an error."""
        if user_phone not in self.user_feedback_history:
            self.user_feedback_history[user_phone] = UserFeedbackHistory(user_phone=user_phone)
        
        history = self.user_feedback_history[user_phone]
        
        # Record successful recovery
        recovery_key = f"{context.value}:{recovery_method}"
        history.successful_recoveries.append(recovery_key)
        
        # Update feedback effectiveness
        history.feedback_effectiveness[recovery_key] = history.feedback_effectiveness.get(recovery_key, 0) + 1
        
        logger.info(f"User {user_phone} successfully recovered from {context.value} using {recovery_method}")
    
    def get_contextual_help_suggestions(self, context: FeedbackContext) -> List[str]:
        """Get contextual help suggestions for a given context."""
        return self.contextual_help_mapping.get(context, ["general_help", "contact_support"])
    
    def create_progressive_error_message(self, error_type: str, attempt_number: int, user_phone: str) -> str:
        """Create progressively more helpful error messages."""
        base_feedback = self.create_feedback(error_type, user_phone)
        
        if attempt_number == 1:
            # First attempt - basic message
            return self.format_feedback_message(base_feedback)
        
        elif attempt_number == 2:
            # Second attempt - add more detailed help
            base_feedback.solution += f"\n\n🔧 **Still having trouble?** {self._get_second_attempt_help(error_type)}"
            return self.format_feedback_message(base_feedback)
        
        else:
            # Third+ attempt - offer direct support
            base_feedback.message += "\n\n🤝 **Need personal help?** It looks like you're having persistent difficulties. Consider:"
            base_feedback.actions.extend(["contact_support", "request_callback", "alternative_method"])
            return self.format_feedback_message(base_feedback)
    
    def _get_second_attempt_help(self, error_type: str) -> str:
        """Get additional help for second attempt."""
        help_map = {
            "content_too_short": "Try including the complete job posting with all details visible.",
            "file_processing_failed": "Copy the text from your file and send it as a regular message instead.",
            "network_error": "Check that you have a stable internet connection and try again.",
            "analysis_timeout": "Try sending a shorter version focusing on the main job details."
        }
        return help_map.get(error_type, "Try a different approach or contact support for assistance.")


# Global instance
_enhanced_feedback_system: Optional[EnhancedFeedbackSystem] = None


def get_enhanced_feedback_system() -> EnhancedFeedbackSystem:
    """Get global enhanced feedback system instance."""
    global _enhanced_feedback_system
    if _enhanced_feedback_system is None:
        _enhanced_feedback_system = EnhancedFeedbackSystem()
    return _enhanced_feedback_system


def create_user_friendly_error(error: Exception, context: Dict[str, Any], user_phone: str) -> str:
    """
    Create user-friendly error message from system exception.
    
    Args:
        error: System exception
        context: Error context information
        user_phone: User's phone number
        
    Returns:
        User-friendly error message
    """
    feedback_system = get_enhanced_feedback_system()
    
    # Map system errors to user-friendly types
    error_type_mapping = {
        "ConnectionError": "network_error",
        "TimeoutError": "analysis_timeout", 
        "FileNotFoundError": "file_processing_failed",
        "ValueError": "content_too_short",
        "UnicodeDecodeError": "file_processing_failed"
    }
    
    error_type = error_type_mapping.get(type(error).__name__, "general_error")
    
    # Add error details to context
    context.update({
        "error_message": str(error),
        "error_type": type(error).__name__,
        "traceback": traceback.format_exc()
    })
    
    feedback = feedback_system.create_feedback(error_type, user_phone, additional_context=context)
    return feedback_system.format_feedback_message(feedback)


def log_user_feedback_interaction(user_phone: str, feedback_type: str, user_response: str) -> None:
    """
    Log user interaction with feedback messages.
    
    Args:
        user_phone: User's phone number
        feedback_type: Type of feedback provided
        user_response: User's response to feedback
    """
    feedback_system = get_enhanced_feedback_system()
    
    # Analyze user response to determine if recovery was successful
    positive_responses = ["thanks", "thank you", "worked", "fixed", "solved", "better", "good"]
    negative_responses = ["still", "not working", "same error", "help", "problem"]
    
    user_response_lower = user_response.lower()
    
    if any(word in user_response_lower for word in positive_responses):
        # User indicates success
        recovery_method = "feedback_guidance"
        context = FeedbackContext.SYSTEM  # Default context
        feedback_system.record_successful_recovery(user_phone, recovery_method, context)
        
    elif any(word in user_response_lower for word in negative_responses):
        # User still having issues - may need escalated help
        logger.info(f"User {user_phone} still experiencing issues after feedback for {feedback_type}")
    
    logger.info(f"User feedback interaction: {user_phone} responded '{user_response}' to {feedback_type}")