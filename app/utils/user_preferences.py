"""
User preferences and settings management for Reality Checker.

This module provides comprehensive user preference management, customizable
settings, adaptive behavior, and personalized experience configuration.
"""

from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from enum import Enum
import json
import asyncio

from app.utils.logging import get_logger
from app.utils.user_experience import MessageTone, UserExperienceLevel

logger = get_logger(__name__)


class NotificationPreference(Enum):
    """User notification preferences."""
    ALL = "all"
    IMPORTANT_ONLY = "important_only"
    CRITICAL_ONLY = "critical_only"
    NONE = "none"


class AnalysisDetailLevel(Enum):
    """Analysis detail level preferences."""
    MINIMAL = "minimal"  # Just score and classification
    STANDARD = "standard"  # Score, classification, main reasons
    DETAILED = "detailed"  # Full analysis with explanations
    EXPERT = "expert"  # Technical details and confidence metrics


class InteractionStyle(Enum):
    """User interaction style preferences."""
    FRIENDLY = "friendly"  # Casual, emoji-rich
    PROFESSIONAL = "professional"  # Formal, business-like
    EDUCATIONAL = "educational"  # Teaching-focused
    CONCISE = "concise"  # Brief, to-the-point


class PrivacyLevel(Enum):
    """Privacy level settings."""
    OPEN = "open"  # Full analytics and personalization
    BALANCED = "balanced"  # Limited analytics, basic personalization
    PRIVATE = "private"  # Minimal data collection
    ANONYMOUS = "anonymous"  # No user tracking


@dataclass
class UserPreferences:
    """Comprehensive user preferences and settings."""
    user_phone: str
    
    # Communication preferences
    language: str = "en"
    interaction_style: InteractionStyle = InteractionStyle.FRIENDLY
    message_tone: MessageTone = MessageTone.FRIENDLY
    notification_preference: NotificationPreference = NotificationPreference.IMPORTANT_ONLY
    
    # Analysis preferences
    analysis_detail_level: AnalysisDetailLevel = AnalysisDetailLevel.STANDARD
    auto_explain_scores: bool = True
    show_confidence_metrics: bool = True
    include_safety_tips: bool = True
    preferred_response_format: str = "structured"  # structured, narrative, bullet_points
    
    # Accessibility preferences
    high_contrast: bool = False
    large_text: bool = False
    reduce_animations: bool = False
    screen_reader_optimized: bool = False
    simplified_language: bool = False
    
    # Privacy and data preferences
    privacy_level: PrivacyLevel = PrivacyLevel.BALANCED
    allow_analytics: bool = True
    allow_personalization: bool = True
    data_retention_days: int = 90
    
    # Behavioral preferences
    enable_proactive_tips: bool = True
    reminder_frequency: str = "weekly"  # never, weekly, monthly
    learning_mode: bool = False  # Enhanced educational content
    expert_mode: bool = False  # Advanced features and technical details
    
    # Time and scheduling preferences
    timezone: Optional[str] = None
    quiet_hours_start: Optional[str] = None  # "22:00"
    quiet_hours_end: Optional[str] = None    # "08:00"
    preferred_contact_times: List[str] = field(default_factory=list)
    
    # Custom preferences
    custom_keywords: List[str] = field(default_factory=list)  # Keywords to watch for
    blocked_content_types: List[str] = field(default_factory=list)
    preferred_examples: List[str] = field(default_factory=list)  # Types of examples user prefers
    
    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: str = "1.0"


@dataclass
class UserBehaviorProfile:
    """Tracks user behavior patterns for adaptive experience."""
    user_phone: str
    
    # Usage patterns
    typical_usage_times: List[str] = field(default_factory=list)  # Hours when user is active
    session_duration_avg: float = 0.0  # Average session length in minutes
    messages_per_session: float = 0.0
    preferred_interaction_frequency: str = "moderate"  # low, moderate, high
    
    # Content patterns
    job_categories_analyzed: Dict[str, int] = field(default_factory=dict)
    scam_types_encountered: Dict[str, int] = field(default_factory=dict)
    help_topics_accessed: Dict[str, int] = field(default_factory=dict)
    
    # Response patterns
    typical_response_time: float = 0.0  # How quickly user responds in seconds
    prefers_immediate_response: bool = True
    reads_full_explanations: bool = True
    uses_suggested_actions: bool = True
    
    # Learning patterns
    improvement_areas: List[str] = field(default_factory=list)
    mastered_concepts: List[str] = field(default_factory=list)
    learning_pace: str = "moderate"  # slow, moderate, fast
    
    # Error patterns
    common_mistakes: Dict[str, int] = field(default_factory=dict)
    recovery_success_rate: float = 0.0
    prefers_detailed_error_help: bool = True
    
    # Engagement metrics
    satisfaction_indicators: Dict[str, float] = field(default_factory=dict)
    feature_usage_frequency: Dict[str, int] = field(default_factory=dict)
    recommendation_follow_rate: float = 0.0
    
    # Adaptive flags
    needs_more_guidance: bool = False
    ready_for_advanced_features: bool = False
    prefers_automation: bool = False
    
    # Metadata
    profile_confidence: float = 0.0  # How confident we are in this profile
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class UserPreferencesManager:
    """Manages user preferences and adaptive behavior."""
    
    def __init__(self):
        """Initialize user preferences manager."""
        self.user_preferences: Dict[str, UserPreferences] = {}
        self.behavior_profiles: Dict[str, UserBehaviorProfile] = {}
        self.preference_templates = self._create_preference_templates()
        self.adaptive_rules = self._create_adaptive_rules()
        
    def _create_preference_templates(self) -> Dict[str, UserPreferences]:
        """Create preference templates for different user types."""
        return {
            "new_user": UserPreferences(
                user_phone="template",
                interaction_style=InteractionStyle.EDUCATIONAL,
                analysis_detail_level=AnalysisDetailLevel.DETAILED,
                auto_explain_scores=True,
                include_safety_tips=True,
                learning_mode=True,
                enable_proactive_tips=True
            ),
            "experienced_user": UserPreferences(
                user_phone="template",
                interaction_style=InteractionStyle.PROFESSIONAL,
                analysis_detail_level=AnalysisDetailLevel.STANDARD,
                auto_explain_scores=False,
                include_safety_tips=False,
                learning_mode=False,
                enable_proactive_tips=False
            ),
            "expert_user": UserPreferences(
                user_phone="template",
                interaction_style=InteractionStyle.CONCISE,
                analysis_detail_level=AnalysisDetailLevel.EXPERT,
                auto_explain_scores=False,
                show_confidence_metrics=True,
                expert_mode=True,
                preferred_response_format="technical"
            ),
            "accessibility_focused": UserPreferences(
                user_phone="template",
                high_contrast=True,
                large_text=True,
                screen_reader_optimized=True,
                simplified_language=True,
                reduce_animations=True,
                preferred_response_format="simple_text"
            ),
            "privacy_conscious": UserPreferences(
                user_phone="template",
                privacy_level=PrivacyLevel.PRIVATE,
                allow_analytics=False,
                allow_personalization=False,
                data_retention_days=30,
                notification_preference=NotificationPreference.CRITICAL_ONLY
            )
        }
    
    def _create_adaptive_rules(self) -> Dict[str, Any]:
        """Create rules for adaptive behavior based on user patterns."""
        return {
            "interaction_frequency": {
                "high_usage": {
                    "condition": lambda profile: profile.messages_per_session > 10,
                    "adaptations": {
                        "interaction_style": InteractionStyle.CONCISE,
                        "analysis_detail_level": AnalysisDetailLevel.MINIMAL,
                        "auto_explain_scores": False
                    }
                },
                "low_usage": {
                    "condition": lambda profile: profile.messages_per_session < 3,
                    "adaptations": {
                        "analysis_detail_level": AnalysisDetailLevel.DETAILED,
                        "include_safety_tips": True,
                        "enable_proactive_tips": True
                    }
                }
            },
            "error_patterns": {
                "frequent_errors": {
                    "condition": lambda profile: profile.recovery_success_rate < 0.5,
                    "adaptations": {
                        "prefers_detailed_error_help": True,
                        "simplified_language": True,
                        "learning_mode": True
                    }
                }
            },
            "expertise_level": {
                "becoming_expert": {
                    "condition": lambda profile: len(profile.mastered_concepts) > 5 and profile.recommendation_follow_rate > 0.8,
                    "adaptations": {
                        "expert_mode": True,
                        "analysis_detail_level": AnalysisDetailLevel.EXPERT,
                        "interaction_style": InteractionStyle.PROFESSIONAL
                    }
                }
            },
            "engagement_level": {
                "highly_engaged": {
                    "condition": lambda profile: profile.satisfaction_indicators.get("overall", 0) > 0.8,
                    "adaptations": {
                        "enable_proactive_tips": True,
                        "reminder_frequency": "weekly"
                    }
                },
                "low_engagement": {
                    "condition": lambda profile: profile.satisfaction_indicators.get("overall", 0) < 0.4,
                    "adaptations": {
                        "interaction_style": InteractionStyle.FRIENDLY,
                        "include_safety_tips": False,
                        "reminder_frequency": "never"
                    }
                }
            }
        }
    
    async def get_user_preferences(self, user_phone: str) -> UserPreferences:
        """
        Get user preferences, creating defaults if needed.
        
        Args:
            user_phone: User's phone number
            
        Returns:
            User preferences object
        """
        if user_phone not in self.user_preferences:
            # Create default preferences
            preferences = UserPreferences(user_phone=user_phone)
            self.user_preferences[user_phone] = preferences
            await self._save_preferences(user_phone)
        
        return self.user_preferences[user_phone]
    
    async def update_preferences(self, user_phone: str, updates: Dict[str, Any]) -> UserPreferences:
        """
        Update user preferences.
        
        Args:
            user_phone: User's phone number
            updates: Dictionary of preference updates
            
        Returns:
            Updated preferences object
        """
        preferences = await self.get_user_preferences(user_phone)
        
        # Update preferences
        for key, value in updates.items():
            if hasattr(preferences, key):
                setattr(preferences, key, value)
        
        preferences.updated_at = datetime.now(timezone.utc)
        
        await self._save_preferences(user_phone)
        logger.info(f"Updated preferences for user {user_phone}")
        
        return preferences
    
    async def apply_template(self, user_phone: str, template_name: str) -> UserPreferences:
        """
        Apply a preference template to a user.
        
        Args:
            user_phone: User's phone number
            template_name: Name of template to apply
            
        Returns:
            Updated preferences object
        """
        if template_name not in self.preference_templates:
            raise ValueError(f"Template '{template_name}' not found")
        
        template = self.preference_templates[template_name]
        current_preferences = await self.get_user_preferences(user_phone)
        
        # Apply template while preserving user-specific data
        template_data = asdict(template)
        del template_data["user_phone"]  # Don't overwrite user phone
        del template_data["created_at"]  # Preserve creation time
        
        await self.update_preferences(user_phone, template_data)
        
        logger.info(f"Applied template '{template_name}' to user {user_phone}")
        return self.user_preferences[user_phone]
    
    async def get_behavior_profile(self, user_phone: str) -> UserBehaviorProfile:
        """
        Get user behavior profile, creating default if needed.
        
        Args:
            user_phone: User's phone number
            
        Returns:
            User behavior profile
        """
        if user_phone not in self.behavior_profiles:
            profile = UserBehaviorProfile(user_phone=user_phone)
            self.behavior_profiles[user_phone] = profile
        
        return self.behavior_profiles[user_phone]
    
    async def update_behavior_profile(self, user_phone: str, interaction_data: Dict[str, Any]) -> None:
        """
        Update user behavior profile based on interaction data.
        
        Args:
            user_phone: User's phone number
            interaction_data: Data from user interaction
        """
        profile = await self.get_behavior_profile(user_phone)
        
        # Update usage patterns
        if "timestamp" in interaction_data:
            hour = interaction_data["timestamp"].hour
            if str(hour) not in profile.typical_usage_times:
                profile.typical_usage_times.append(str(hour))
        
        # Update content patterns
        if "job_category" in interaction_data:
            category = interaction_data["job_category"]
            profile.job_categories_analyzed[category] = profile.job_categories_analyzed.get(category, 0) + 1
        
        if "scam_type_detected" in interaction_data:
            scam_type = interaction_data["scam_type_detected"]
            profile.scam_types_encountered[scam_type] = profile.scam_types_encountered.get(scam_type, 0) + 1
        
        # Update response patterns
        if "response_time" in interaction_data:
            current_avg = profile.typical_response_time
            new_time = interaction_data["response_time"]
            profile.typical_response_time = (current_avg + new_time) / 2 if current_avg > 0 else new_time
        
        # Update engagement metrics
        if "satisfaction_score" in interaction_data:
            current_satisfaction = profile.satisfaction_indicators.get("overall", 0.5)
            new_score = interaction_data["satisfaction_score"]
            profile.satisfaction_indicators["overall"] = (current_satisfaction + new_score) / 2
        
        # Update learning patterns
        if "concept_mastered" in interaction_data:
            concept = interaction_data["concept_mastered"]
            if concept not in profile.mastered_concepts:
                profile.mastered_concepts.append(concept)
        
        if "mistake_made" in interaction_data:
            mistake = interaction_data["mistake_made"]
            profile.common_mistakes[mistake] = profile.common_mistakes.get(mistake, 0) + 1
        
        profile.last_updated = datetime.now(timezone.utc)
        profile.profile_confidence = min(1.0, profile.profile_confidence + 0.1)
        
        # Apply adaptive rules
        await self._apply_adaptive_rules(user_phone)
    
    async def _apply_adaptive_rules(self, user_phone: str) -> None:
        """Apply adaptive rules based on behavior profile."""
        profile = await self.get_behavior_profile(user_phone)
        preferences = await self.get_user_preferences(user_phone)
        
        adaptations = {}
        
        # Check each adaptive rule
        for category, rules in self.adaptive_rules.items():
            for rule_name, rule in rules.items():
                if rule["condition"](profile):
                    adaptations.update(rule["adaptations"])
                    logger.info(f"Applied adaptive rule '{rule_name}' for user {user_phone}")
        
        # Apply adaptations
        if adaptations:
            await self.update_preferences(user_phone, adaptations)
    
    def get_preference_suggestions(self, user_phone: str) -> List[Dict[str, Any]]:
        """
        Get preference suggestions for user based on their usage patterns.
        
        Args:
            user_phone: User's phone number
            
        Returns:
            List of preference suggestions
        """
        suggestions = []
        
        if user_phone in self.behavior_profiles:
            profile = self.behavior_profiles[user_phone]
            
            # Suggest expert mode if user is advanced
            if (len(profile.mastered_concepts) > 5 and 
                profile.recommendation_follow_rate > 0.8 and
                not self.user_preferences.get(user_phone, UserPreferences(user_phone="")).expert_mode):
                suggestions.append({
                    "type": "feature_upgrade",
                    "title": "Enable Expert Mode",
                    "description": "You seem to be getting comfortable with Reality Checker. Expert mode provides more technical details and advanced features.",
                    "action": "enable_expert_mode",
                    "benefit": "More detailed analysis with confidence metrics and technical insights"
                })
            
            # Suggest accessibility features if needed
            if profile.recovery_success_rate < 0.5:
                suggestions.append({
                    "type": "accessibility",
                    "title": "Simplify Language",
                    "description": "Having trouble with some responses? I can use simpler language and provide more detailed explanations.",
                    "action": "enable_simplified_language",
                    "benefit": "Clearer, easier-to-understand responses"
                })
            
            # Suggest notification adjustments
            if profile.satisfaction_indicators.get("interruption", 0) < 0.3:
                suggestions.append({
                    "type": "notifications",
                    "title": "Reduce Notifications",
                    "description": "I notice you might prefer fewer notifications. I can limit them to only critical alerts.",
                    "action": "reduce_notifications",
                    "benefit": "Less interruption, only important alerts"
                })
        
        return suggestions
    
    async def _save_preferences(self, user_phone: str) -> None:
        """Save user preferences to storage."""
        # In production, this would save to database
        logger.debug(f"Saved preferences for user {user_phone}")
    
    def export_user_preferences(self, user_phone: str) -> Dict[str, Any]:
        """
        Export user preferences for backup or transfer.
        
        Args:
            user_phone: User's phone number
            
        Returns:
            Dictionary with user preferences and behavior profile
        """
        preferences = self.user_preferences.get(user_phone)
        profile = self.behavior_profiles.get(user_phone)
        
        export_data = {
            "user_phone": user_phone,
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "preferences": asdict(preferences) if preferences else None,
            "behavior_profile": asdict(profile) if profile else None,
            "version": "1.0"
        }
        
        return export_data
    
    async def import_user_preferences(self, import_data: Dict[str, Any]) -> bool:
        """
        Import user preferences from backup.
        
        Args:
            import_data: Exported preference data
            
        Returns:
            True if import successful
        """
        try:
            user_phone = import_data["user_phone"]
            
            if "preferences" in import_data and import_data["preferences"]:
                prefs_data = import_data["preferences"]
                preferences = UserPreferences(**prefs_data)
                self.user_preferences[user_phone] = preferences
            
            if "behavior_profile" in import_data and import_data["behavior_profile"]:
                profile_data = import_data["behavior_profile"]
                profile = UserBehaviorProfile(**profile_data)
                self.behavior_profiles[user_phone] = profile
            
            logger.info(f"Imported preferences for user {user_phone}")
            return True
            
        except Exception as e:
            logger.error(f"Error importing preferences: {e}")
            return False
    
    def get_preference_summary(self, user_phone: str) -> str:
        """
        Get a human-readable summary of user preferences.
        
        Args:
            user_phone: User's phone number
            
        Returns:
            Formatted preference summary
        """
        preferences = self.user_preferences.get(user_phone)
        if not preferences:
            return "No preferences set."
        
        summary = f"**Your Reality Checker Preferences**\n\n"
        summary += f"🗣️ **Language:** {preferences.language}\n"
        summary += f"💬 **Style:** {preferences.interaction_style.value}\n"
        summary += f"📊 **Analysis Level:** {preferences.analysis_detail_level.value}\n"
        summary += f"🔔 **Notifications:** {preferences.notification_preference.value}\n"
        summary += f"🛡️ **Privacy:** {preferences.privacy_level.value}\n"
        
        if preferences.expert_mode:
            summary += f"🎓 **Expert Mode:** Enabled\n"
        
        if preferences.learning_mode:
            summary += f"📚 **Learning Mode:** Enabled\n"
        
        if preferences.high_contrast or preferences.large_text or preferences.screen_reader_optimized:
            summary += f"♿ **Accessibility:** Enhanced features enabled\n"
        
        summary += f"\n*Last updated: {preferences.updated_at.strftime('%Y-%m-%d')}*"
        
        return summary


# Settings management for quick access
class QuickSettings:
    """Quick settings for common preference changes."""
    
    def __init__(self, preferences_manager: UserPreferencesManager):
        """Initialize with preferences manager."""
        self.preferences_manager = preferences_manager
    
    async def toggle_expert_mode(self, user_phone: str) -> Tuple[bool, str]:
        """Toggle expert mode on/off."""
        preferences = await self.preferences_manager.get_user_preferences(user_phone)
        new_state = not preferences.expert_mode
        
        await self.preferences_manager.update_preferences(user_phone, {
            "expert_mode": new_state,
            "analysis_detail_level": AnalysisDetailLevel.EXPERT if new_state else AnalysisDetailLevel.STANDARD,
            "show_confidence_metrics": new_state
        })
        
        status = "enabled" if new_state else "disabled"
        message = f"🎓 Expert mode {status}. You'll now receive {'detailed technical analysis' if new_state else 'standard analysis'}."
        
        return new_state, message
    
    async def set_language(self, user_phone: str, language: str) -> str:
        """Set user language preference."""
        await self.preferences_manager.update_preferences(user_phone, {"language": language})
        return f"🌍 Language set to {language}. Future messages will be in this language."
    
    async def adjust_detail_level(self, user_phone: str, level: str) -> str:
        """Adjust analysis detail level."""
        level_map = {
            "minimal": AnalysisDetailLevel.MINIMAL,
            "standard": AnalysisDetailLevel.STANDARD, 
            "detailed": AnalysisDetailLevel.DETAILED,
            "expert": AnalysisDetailLevel.EXPERT
        }
        
        if level not in level_map:
            return f"❌ Invalid detail level. Choose from: {', '.join(level_map.keys())}"
        
        await self.preferences_manager.update_preferences(user_phone, {
            "analysis_detail_level": level_map[level]
        })
        
        return f"📊 Analysis detail level set to {level}. Your next analysis will reflect this change."
    
    async def toggle_accessibility(self, user_phone: str, feature: str) -> Tuple[bool, str]:
        """Toggle accessibility features."""
        feature_map = {
            "high_contrast": "High contrast mode",
            "large_text": "Large text mode",
            "simple_language": "Simplified language",
            "screen_reader": "Screen reader optimization"
        }
        
        if feature not in feature_map:
            return False, f"❌ Unknown accessibility feature. Available: {', '.join(feature_map.keys())}"
        
        preferences = await self.preferences_manager.get_user_preferences(user_phone)
        current_state = getattr(preferences, feature, False)
        new_state = not current_state
        
        await self.preferences_manager.update_preferences(user_phone, {feature: new_state})
        
        status = "enabled" if new_state else "disabled"
        message = f"♿ {feature_map[feature]} {status}."
        
        return new_state, message


# Global instances
_preferences_manager: Optional[UserPreferencesManager] = None
_quick_settings: Optional[QuickSettings] = None


def get_preferences_manager() -> UserPreferencesManager:
    """Get global user preferences manager instance."""
    global _preferences_manager
    if _preferences_manager is None:
        _preferences_manager = UserPreferencesManager()
    return _preferences_manager


def get_quick_settings() -> QuickSettings:
    """Get global quick settings instance."""
    global _quick_settings
    if _quick_settings is None:
        _quick_settings = QuickSettings(get_preferences_manager())
    return _quick_settings