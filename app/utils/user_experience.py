"""
User experience enhancements for the Reality Checker WhatsApp bot.

This module provides improved user interaction flows, onboarding experiences,
personalized messaging, and adaptive user interface components.
"""

import re
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum

from app.models.data_models import JobAnalysisResult, JobClassification
from app.utils.logging import get_logger

logger = get_logger(__name__)


class UserExperienceLevel(Enum):
    """User experience levels for adaptive messaging."""
    NEW_USER = "new_user"
    RETURNING_USER = "returning_user"
    EXPERIENCED_USER = "experienced_user"
    POWER_USER = "power_user"


class MessageTone(Enum):
    """Different message tones for various contexts."""
    FRIENDLY = "friendly"
    PROFESSIONAL = "professional"
    URGENT = "urgent"
    EDUCATIONAL = "educational"
    REASSURING = "reassuring"


@dataclass
class UserContext:
    """Context information about a user for personalized experience."""
    phone_number: str
    experience_level: UserExperienceLevel
    total_interactions: int
    last_interaction: Optional[datetime]
    preferred_language: str = "en"
    has_completed_onboarding: bool = False
    frequently_used_features: List[str] = field(default_factory=list)
    timezone: Optional[str] = None
    interaction_patterns: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationFlow:
    """Represents a conversation flow with branching logic."""
    name: str
    steps: List[Dict[str, Any]]
    current_step: int = 0
    context: Dict[str, Any] = field(default_factory=dict)


class MessagePersonalizer:
    """Personalizes messages based on user context and preferences."""
    
    def __init__(self):
        """Initialize message personalizer."""
        self.greeting_templates = {
            UserExperienceLevel.NEW_USER: [
                "👋 Welcome to Reality Checker! I'm here to help you verify job postings.",
                "🌟 Hi there! I'm your job scam detection assistant. Let's get started!",
                "✨ Hello! I'm here to help you stay safe from job scams."
            ],
            UserExperienceLevel.RETURNING_USER: [
                "👋 Hello again! Ready to check another job posting?",
                "🔍 Hi! What job listing would you like me to analyze today?",
                "💼 Welcome back! I'm here to help with job verification."
            ],
            UserExperienceLevel.EXPERIENCED_USER: [
                "🔍 Ready for another analysis?",
                "👋 What can I check for you today?",
                "💼 Let's verify that job posting!"
            ],
            UserExperienceLevel.POWER_USER: [
                "🚀 Ready to analyze?",
                "⚡ What's next?",
                "🔥 Send it over!"
            ]
        }
        
        self.feedback_templates = {
            JobClassification.HIGHLY_LIKELY_SCAM: {
                MessageTone.URGENT: "🚨 **HIGH RISK DETECTED** 🚨\n\nThis job posting shows {confidence}% confidence of being a SCAM.\n\n⚠️ **Do NOT proceed with this opportunity!**",
                MessageTone.EDUCATIONAL: "🎓 **Analysis Complete**\n\nBased on my analysis, this posting has {confidence}% likelihood of being a scam.\n\n📚 **Red flags I found:**\n{reasons}",
                MessageTone.REASSURING: "✅ **Good news - you asked me to check!**\n\nThis posting has concerning elements ({confidence}% scam likelihood).\n\n🛡️ You're being smart by verifying before proceeding."
            },
            JobClassification.LIKELY_SCAM: {
                MessageTone.PROFESSIONAL: "⚠️ **Caution Advised**\n\nThis job posting shows {confidence}% probability of being a scam.\n\n🔍 **Key concerns:**\n{reasons}",
                MessageTone.EDUCATIONAL: "📊 **Analysis Results**\n\nMy assessment indicates {confidence}% likelihood this is a scam.\n\n💡 **What I noticed:**\n{reasons}",
                MessageTone.FRIENDLY: "🤔 **Hmm, I have some concerns...**\n\nThis posting has {confidence}% scam probability.\n\n⚡ **Here's why:**\n{reasons}"
            },
            JobClassification.POTENTIALLY_LEGITIMATE: {
                MessageTone.PROFESSIONAL: "✅ **Generally Positive Assessment**\n\nThis appears to be legitimate with {confidence}% confidence.\n\n📝 **Still, please verify:**\n{reasons}",
                MessageTone.REASSURING: "😊 **Looking good!**\n\nThis seems legitimate ({confidence}% confidence).\n\n💼 **Just double-check:**\n{reasons}",
                MessageTone.FRIENDLY: "👍 **This looks promising!**\n\nI'm {confidence}% confident this is legitimate.\n\n🔍 **Quick tips:**\n{reasons}"
            },
            JobClassification.LIKELY_LEGITIMATE: {
                MessageTone.PROFESSIONAL: "✅ **High Confidence - Appears Legitimate**\n\nThis job posting shows {confidence}% probability of being legitimate.\n\n💼 **Positive indicators:**\n{reasons}",
                MessageTone.FRIENDLY: "🎉 **Great news!**\n\nThis looks legitimate with {confidence}% confidence!\n\n⭐ **What I liked:**\n{reasons}",
                MessageTone.REASSURING: "😊 **You can feel confident!**\n\nThis appears legitimate ({confidence}% confidence).\n\n✨ **Good signs:**\n{reasons}"
            }
        }
        
        self.error_templates = {
            "content_too_short": {
                MessageTone.FRIENDLY: "😅 **Oops! Need more details**\n\nCould you share more information about the job? I need details like:\n• Job title & description\n• Company name\n• Salary/pay\n• Requirements\n\nOr just send 'help' for guidance! 💡",
                MessageTone.EDUCATIONAL: "📚 **More Information Needed**\n\nFor accurate analysis, please include:\n• Complete job description\n• Company details\n• Compensation information\n• Contact details\n\nThis helps me spot red flags more effectively! 🔍",
                MessageTone.PROFESSIONAL: "📋 **Additional Details Required**\n\nPlease provide more comprehensive job information including job description, company details, and compensation for accurate analysis."
            },
            "file_error": {
                MessageTone.FRIENDLY: "😔 **Having trouble with that file**\n\nI can only read PDF files right now. Could you:\n• Send as a PDF, or\n• Copy and paste the text?\n\nI'm here to help! 💪",
                MessageTone.PROFESSIONAL: "📄 **File Format Not Supported**\n\nCurrently, I can only process PDF files. Please send the job posting as a PDF or paste the text directly.",
                MessageTone.EDUCATIONAL: "🎓 **File Tip**\n\nI work best with PDF files or plain text. This ensures I can read all the job details accurately for analysis! 📊"
            }
        }
    
    def create_personalized_greeting(self, user_context: UserContext) -> str:
        """
        Create a personalized greeting based on user context.
        
        Args:
            user_context: User context information
            
        Returns:
            Personalized greeting message
        """
        templates = self.greeting_templates.get(user_context.experience_level, 
                                               self.greeting_templates[UserExperienceLevel.NEW_USER])
        
        # Select template based on time of day or randomization
        import random
        greeting = random.choice(templates)
        
        # Add personalization based on context
        if user_context.total_interactions > 10:
            greeting += f"\n\n📊 You've verified {user_context.total_interactions} job postings with me - great job staying safe!"
        elif user_context.total_interactions > 0:
            greeting += f"\n\n🔄 Welcome back! This is your {user_context.total_interactions + 1}{'st' if user_context.total_interactions == 1 else 'nd' if user_context.total_interactions == 2 else 'rd' if user_context.total_interactions == 3 else 'th'} verification."
        
        return greeting
    
    def create_analysis_response(self, result: JobAnalysisResult, user_context: UserContext, tone: MessageTone = MessageTone.FRIENDLY) -> str:
        """
        Create personalized analysis response.
        
        Args:
            result: Job analysis result
            user_context: User context information
            tone: Desired message tone
            
        Returns:
            Personalized response message
        """
        # Select appropriate template
        classification_templates = self.feedback_templates.get(result.classification, {})
        template = classification_templates.get(tone, list(classification_templates.values())[0] if classification_templates else "Analysis complete.")
        
        # Format reasons for display
        if result.reasons:
            formatted_reasons = "\n".join([f"• {reason}" for reason in result.reasons[:5]])  # Limit to top 5
        else:
            formatted_reasons = "• General assessment based on content analysis"
        
        # Format the message
        message = template.format(
            confidence=int(result.confidence * 100),
            reasons=formatted_reasons
        )
        
        # Add experience-appropriate footer
        footer = self._get_experience_footer(user_context, result)
        if footer:
            message += f"\n\n{footer}"
        
        return message
    
    def create_error_response(self, error_type: str, user_context: UserContext, tone: MessageTone = MessageTone.FRIENDLY) -> str:
        """
        Create personalized error response.
        
        Args:
            error_type: Type of error encountered
            user_context: User context information
            tone: Desired message tone
            
        Returns:
            Personalized error message
        """
        error_templates = self.error_templates.get(error_type, {})
        template = error_templates.get(tone, "I encountered an issue. Please try again or send 'help' for assistance.")
        
        # Add helpful context for new users
        if user_context.experience_level == UserExperienceLevel.NEW_USER:
            template += "\n\n💡 **New here?** Send 'help' to learn how I work!"
        
        return template
    
    def _get_experience_footer(self, user_context: UserContext, result: JobAnalysisResult) -> str:
        """Get experience-appropriate footer message."""
        if user_context.experience_level == UserExperienceLevel.NEW_USER:
            return "🎓 **New to job hunting?** Remember: legitimate companies never ask for money upfront!"
        elif user_context.experience_level == UserExperienceLevel.RETURNING_USER:
            return "💪 **Stay vigilant!** Trust your instincts and verify company details independently."
        elif user_context.experience_level == UserExperienceLevel.EXPERIENCED_USER:
            if result.classification in [JobClassification.HIGHLY_LIKELY_SCAM, JobClassification.LIKELY_SCAM]:
                return "🛡️ **You know the drill** - trust but verify!"
            else:
                return "✅ **Looking good** - proceed with normal due diligence."
        else:  # POWER_USER
            return f"📊 Trust: {result.trust_score:.1f} | Confidence: {result.confidence:.2f}"


class ConversationFlowManager:
    """Manages complex conversation flows and user guidance."""
    
    def __init__(self):
        """Initialize conversation flow manager."""
        self.active_flows: Dict[str, ConversationFlow] = {}
        self.flow_templates = {
            "onboarding": {
                "name": "User Onboarding",
                "steps": [
                    {
                        "message": "🌟 **Welcome to Reality Checker!**\n\nI'm your AI assistant for job scam detection. I can help you verify job postings by analyzing:\n• Job descriptions\n• Company information\n• Salary claims\n• Contact details\n\nReady to learn how I work? 📚",
                        "actions": ["continue", "skip"],
                        "responses": {
                            "continue": "Great! Let's start with a quick demo.",
                            "skip": "No problem! Send me a job posting anytime to get started."
                        }
                    },
                    {
                        "message": "🎯 **How to use me:**\n\n1️⃣ **Send text**: Copy and paste job posting details\n2️⃣ **Send PDF**: Share job posting as PDF file\n3️⃣ **Get analysis**: I'll analyze and give you a trust score\n\nTry sending me a job posting now, or send 'demo' for a practice example! 🚀",
                        "actions": ["demo", "job_posting", "skip"],
                        "responses": {
                            "demo": "Here's how I analyze a suspicious posting...",
                            "job_posting": "Perfect! I'll analyze that for you.",
                            "skip": "You're all set! Send me job postings anytime."
                        }
                    }
                ]
            },
            "help_system": {
                "name": "Help and Support",
                "steps": [
                    {
                        "message": "🆘 **How can I help you?**\n\n1️⃣ How to use Reality Checker\n2️⃣ Understanding trust scores\n3️⃣ What makes a job posting suspicious\n4️⃣ Tips for safe job hunting\n5️⃣ Contact support\n\nSend the number for the topic you want to learn about! 📖",
                        "actions": ["1", "2", "3", "4", "5"],
                        "responses": {
                            "1": "📚 **Using Reality Checker**\n\nSimply send me:\n• Job posting text (copy & paste)\n• PDF files with job details\n\nI'll analyze and give you a trust score from 0-10!\n\nAnything else? Send 'help' again.",
                            "2": "📊 **Trust Scores Explained**\n\n🔴 0-3: High risk of scam\n🟡 4-6: Proceed with caution\n🟢 7-10: Likely legitimate\n\nI also explain my reasoning for each score!\n\nMore questions? Send 'help' again.",
                            "3": "🚨 **Red Flags to Watch For**\n\n• Upfront payment requests\n• Too-good-to-be-true salaries\n• Vague job descriptions\n• No company verification\n• Urgent hiring pressure\n• Grammar/spelling errors\n\nNeed more help? Send 'help' again.",
                            "4": "💡 **Safe Job Hunting Tips**\n\n✅ Research companies independently\n✅ Verify contact information\n✅ Never pay upfront fees\n✅ Trust your instincts\n✅ Use Reality Checker for verification!\n\nMore topics? Send 'help' again.",
                            "5": "📞 **Need More Help?**\n\nFor technical issues or feedback:\n• Email: support@realitychecker.com\n• Report issues through our website\n\nI'm also constantly learning and improving!\n\nBack to menu? Send 'help'."
                        }
                    }
                ]
            }
        }
    
    def start_flow(self, user_phone: str, flow_name: str) -> Optional[str]:
        """
        Start a conversation flow for a user.
        
        Args:
            user_phone: User's phone number
            flow_name: Name of the flow to start
            
        Returns:
            Initial message for the flow
        """
        if flow_name not in self.flow_templates:
            return None
        
        template = self.flow_templates[flow_name]
        flow = ConversationFlow(
            name=template["name"],
            steps=template["steps"].copy(),
            current_step=0
        )
        
        self.active_flows[user_phone] = flow
        
        return flow.steps[0]["message"]
    
    def process_flow_response(self, user_phone: str, response: str) -> Optional[str]:
        """
        Process user response in an active flow.
        
        Args:
            user_phone: User's phone number
            response: User's response
            
        Returns:
            Next message in the flow or None if flow completed
        """
        if user_phone not in self.active_flows:
            return None
        
        flow = self.active_flows[user_phone]
        current_step = flow.steps[flow.current_step]
        
        # Check if response matches any actions
        response_lower = response.lower().strip()
        if "actions" in current_step and response_lower in current_step["actions"]:
            # Process the action
            if "responses" in current_step and response_lower in current_step["responses"]:
                response_message = current_step["responses"][response_lower]
                
                # Move to next step or end flow
                flow.current_step += 1
                if flow.current_step >= len(flow.steps):
                    # Flow completed
                    del self.active_flows[user_phone]
                    return response_message + "\n\n✅ **Setup complete!** Send me job postings anytime for analysis."
                else:
                    # Continue to next step
                    next_step_message = flow.steps[flow.current_step]["message"]
                    return f"{response_message}\n\n{next_step_message}"
        
        # If no specific action matched, provide helpful guidance
        return "🤔 I didn't understand that response. Please choose from the available options or send 'help' for assistance."
    
    def is_in_flow(self, user_phone: str) -> bool:
        """Check if user is currently in a conversation flow."""
        return user_phone in self.active_flows
    
    def end_flow(self, user_phone: str) -> None:
        """End conversation flow for user."""
        if user_phone in self.active_flows:
            del self.active_flows[user_phone]


class AdaptiveMessaging:
    """Provides adaptive messaging based on user behavior and context."""
    
    def __init__(self):
        """Initialize adaptive messaging system."""
        self.message_personalizer = MessagePersonalizer()
        self.flow_manager = ConversationFlowManager()
    
    def determine_user_experience_level(self, total_interactions: int, last_interaction: Optional[datetime]) -> UserExperienceLevel:
        """
        Determine user experience level based on usage patterns.
        
        Args:
            total_interactions: Total number of interactions
            last_interaction: Last interaction timestamp
            
        Returns:
            User experience level
        """
        if total_interactions == 0:
            return UserExperienceLevel.NEW_USER
        elif total_interactions < 5:
            return UserExperienceLevel.RETURNING_USER
        elif total_interactions < 20:
            return UserExperienceLevel.EXPERIENCED_USER
        else:
            return UserExperienceLevel.POWER_USER
    
    def determine_message_tone(self, result: JobAnalysisResult, user_context: UserContext) -> MessageTone:
        """
        Determine appropriate message tone based on result and context.
        
        Args:
            result: Analysis result
            user_context: User context
            
        Returns:
            Appropriate message tone
        """
        # High-risk scams should always be urgent for new users
        if (result.classification == JobClassification.HIGHLY_LIKELY_SCAM and 
            user_context.experience_level == UserExperienceLevel.NEW_USER):
            return MessageTone.URGENT
        
        # Educational tone for users still learning
        if user_context.experience_level in [UserExperienceLevel.NEW_USER, UserExperienceLevel.RETURNING_USER]:
            return MessageTone.EDUCATIONAL
        
        # Professional tone for experienced users
        if user_context.experience_level == UserExperienceLevel.EXPERIENCED_USER:
            return MessageTone.PROFESSIONAL
        
        # Friendly tone as default
        return MessageTone.FRIENDLY
    
    def should_start_onboarding(self, user_context: UserContext) -> bool:
        """
        Determine if user should go through onboarding.
        
        Args:
            user_context: User context
            
        Returns:
            True if onboarding should be started
        """
        return (user_context.experience_level == UserExperienceLevel.NEW_USER and 
                not user_context.has_completed_onboarding and
                user_context.total_interactions == 0)
    
    def get_contextual_help_message(self, user_context: UserContext, error_context: Optional[str] = None) -> str:
        """
        Get contextual help message based on user needs.
        
        Args:
            user_context: User context
            error_context: Optional error context
            
        Returns:
            Contextual help message
        """
        if user_context.experience_level == UserExperienceLevel.NEW_USER:
            return self.flow_manager.start_flow(user_context.phone_number, "onboarding") or "Welcome! Send me a job posting to analyze."
        else:
            return self.flow_manager.start_flow(user_context.phone_number, "help_system") or "How can I help you today?"


# Global instances
_message_personalizer: Optional[MessagePersonalizer] = None
_flow_manager: Optional[ConversationFlowManager] = None
_adaptive_messaging: Optional[AdaptiveMessaging] = None


def get_message_personalizer() -> MessagePersonalizer:
    """Get global message personalizer instance."""
    global _message_personalizer
    if _message_personalizer is None:
        _message_personalizer = MessagePersonalizer()
    return _message_personalizer


def get_flow_manager() -> ConversationFlowManager:
    """Get global conversation flow manager instance."""
    global _flow_manager
    if _flow_manager is None:
        _flow_manager = ConversationFlowManager()
    return _flow_manager


def get_adaptive_messaging() -> AdaptiveMessaging:
    """Get global adaptive messaging instance."""
    global _adaptive_messaging
    if _adaptive_messaging is None:
        _adaptive_messaging = AdaptiveMessaging()
    return _adaptive_messaging