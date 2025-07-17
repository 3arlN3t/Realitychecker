"""
Multi-language support and localization for Reality Checker.

This module provides comprehensive internationalization (i18n) and localization (l10n) 
support for the WhatsApp bot and dashboard interface.
"""

import json
import os
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timezone
import locale

from app.utils.logging import get_logger

logger = get_logger(__name__)


class SupportedLanguage(Enum):
    """Supported languages with their ISO codes."""
    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    PORTUGUESE = "pt"
    GERMAN = "de"
    ITALIAN = "it"
    DUTCH = "nl"
    RUSSIAN = "ru"
    CHINESE_SIMPLIFIED = "zh-CN"
    CHINESE_TRADITIONAL = "zh-TW"
    JAPANESE = "ja"
    KOREAN = "ko"
    ARABIC = "ar"
    HINDI = "hi"
    BENGALI = "bn"
    URDU = "ur"
    FILIPINO = "fil"
    VIETNAMESE = "vi"
    THAI = "th"
    INDONESIAN = "id"
    MALAY = "ms"
    TAMIL = "ta"
    TELUGU = "te"
    GUJARATI = "gu"
    MARATHI = "mr"
    PUNJABI = "pa"
    SWAHILI = "sw"
    YORUBA = "yo"
    IGBO = "ig"
    HAUSA = "ha"
    AMHARIC = "am"


@dataclass
class LocalizationContext:
    """Context for localization including user preferences."""
    language: str
    region: Optional[str] = None
    timezone: Optional[str] = None
    currency: Optional[str] = None
    date_format: Optional[str] = None
    number_format: Optional[str] = None
    rtl: bool = False  # Right-to-left language


class TranslationManager:
    """Manages translations and localized content."""
    
    def __init__(self, translations_dir: str = "app/locales"):
        """
        Initialize translation manager.
        
        Args:
            translations_dir: Directory containing translation files
        """
        self.translations_dir = translations_dir
        self.translations: Dict[str, Dict[str, Any]] = {}
        self.fallback_language = "en"
        self.load_translations()
        
        # RTL languages
        self.rtl_languages = {"ar", "he", "fa", "ur"}
        
        # Language metadata
        self.language_metadata = {
            "en": {"name": "English", "native_name": "English", "region": "US"},
            "es": {"name": "Spanish", "native_name": "Español", "region": "ES"},
            "fr": {"name": "French", "native_name": "Français", "region": "FR"},
            "pt": {"name": "Portuguese", "native_name": "Português", "region": "PT"},
            "de": {"name": "German", "native_name": "Deutsch", "region": "DE"},
            "it": {"name": "Italian", "native_name": "Italiano", "region": "IT"},
            "nl": {"name": "Dutch", "native_name": "Nederlands", "region": "NL"},
            "ru": {"name": "Russian", "native_name": "Русский", "region": "RU"},
            "zh-CN": {"name": "Chinese Simplified", "native_name": "简体中文", "region": "CN"},
            "zh-TW": {"name": "Chinese Traditional", "native_name": "繁體中文", "region": "TW"},
            "ja": {"name": "Japanese", "native_name": "日本語", "region": "JP"},
            "ko": {"name": "Korean", "native_name": "한국어", "region": "KR"},
            "ar": {"name": "Arabic", "native_name": "العربية", "region": "SA"},
            "hi": {"name": "Hindi", "native_name": "हिन्दी", "region": "IN"},
            "bn": {"name": "Bengali", "native_name": "বাংলা", "region": "BD"},
            "ur": {"name": "Urdu", "native_name": "اردو", "region": "PK"},
            "fil": {"name": "Filipino", "native_name": "Filipino", "region": "PH"},
            "vi": {"name": "Vietnamese", "native_name": "Tiếng Việt", "region": "VN"},
            "th": {"name": "Thai", "native_name": "ไทย", "region": "TH"},
            "id": {"name": "Indonesian", "native_name": "Bahasa Indonesia", "region": "ID"},
            "ms": {"name": "Malay", "native_name": "Bahasa Melayu", "region": "MY"},
            "ta": {"name": "Tamil", "native_name": "தமிழ்", "region": "IN"},
            "te": {"name": "Telugu", "native_name": "తెలుగు", "region": "IN"},
            "gu": {"name": "Gujarati", "native_name": "ગુજરાતી", "region": "IN"},
            "mr": {"name": "Marathi", "native_name": "मराठी", "region": "IN"},
            "pa": {"name": "Punjabi", "native_name": "ਪੰਜਾਬੀ", "region": "IN"},
            "sw": {"name": "Swahili", "native_name": "Kiswahili", "region": "KE"},
            "yo": {"name": "Yoruba", "native_name": "Yorùbá", "region": "NG"},
            "ig": {"name": "Igbo", "native_name": "Igbo", "region": "NG"},
            "ha": {"name": "Hausa", "native_name": "Hausa", "region": "NG"},
            "am": {"name": "Amharic", "native_name": "አማርኛ", "region": "ET"},
        }
    
    def load_translations(self) -> None:
        """Load all translation files."""
        try:
            if not os.path.exists(self.translations_dir):
                logger.warning(f"Translations directory not found: {self.translations_dir}")
                self._create_default_translations()
                return
            
            for filename in os.listdir(self.translations_dir):
                if filename.endswith('.json'):
                    lang_code = filename[:-5]  # Remove .json extension
                    file_path = os.path.join(self.translations_dir, filename)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            self.translations[lang_code] = json.load(f)
                        logger.info(f"Loaded translations for {lang_code}")
                    except Exception as e:
                        logger.error(f"Error loading translations for {lang_code}: {e}")
            
            if not self.translations:
                self._create_default_translations()
                
        except Exception as e:
            logger.error(f"Error loading translations: {e}")
            self._create_default_translations()
    
    def _create_default_translations(self) -> None:
        """Create default English translations."""
        self.translations["en"] = {
            "welcome": {
                "new_user": "👋 Welcome to Reality Checker! I'm here to help you verify job postings and stay safe from scams.",
                "returning_user": "👋 Hello again! Ready to check another job posting?",
                "experienced_user": "🔍 Ready for another analysis?",
                "power_user": "🚀 Ready to analyze?"
            },
            "help": {
                "menu": "🆘 **How can I help you?**\n\n1️⃣ How to use Reality Checker\n2️⃣ Understanding trust scores\n3️⃣ What makes a job posting suspicious\n4️⃣ Tips for safe job hunting\n5️⃣ Contact support\n\nSend the number for the topic you want to learn about! 📖",
                "usage": "📚 **Using Reality Checker**\n\nSimply send me:\n• Job posting text (copy & paste)\n• PDF files with job details\n\nI'll analyze and give you a trust score from 0-10!",
                "trust_scores": "📊 **Trust Scores Explained**\n\n🔴 0-3: High risk of scam\n🟡 4-6: Proceed with caution\n🟢 7-10: Likely legitimate\n\nI also explain my reasoning for each score!",
                "red_flags": "🚨 **Red Flags to Watch For**\n\n• Upfront payment requests\n• Too-good-to-be-true salaries\n• Vague job descriptions\n• No company verification\n• Urgent hiring pressure\n• Grammar/spelling errors",
                "tips": "💡 **Safe Job Hunting Tips**\n\n✅ Research companies independently\n✅ Verify contact information\n✅ Never pay upfront fees\n✅ Trust your instincts\n✅ Use Reality Checker for verification!"
            },
            "analysis": {
                "highly_likely_scam": "🚨 **HIGH RISK DETECTED** 🚨\n\nThis job posting shows {confidence}% confidence of being a SCAM.\n\n⚠️ **Do NOT proceed with this opportunity!**",
                "likely_scam": "⚠️ **Caution Advised**\n\nThis job posting shows {confidence}% probability of being a scam.",
                "potentially_legitimate": "✅ **Generally Positive Assessment**\n\nThis appears to be legitimate with {confidence}% confidence.",
                "likely_legitimate": "✅ **High Confidence - Appears Legitimate**\n\nThis job posting shows {confidence}% probability of being legitimate."
            },
            "errors": {
                "content_too_short": "😅 **Oops! Need more details**\n\nCould you share more information about the job? I need details like:\n• Job title & description\n• Company name\n• Salary/pay\n• Requirements",
                "file_error": "😔 **Having trouble with that file**\n\nI can only read PDF files right now. Could you:\n• Send as a PDF, or\n• Copy and paste the text?",
                "network_error": "🌐 **Connection issue**\n\nI'm having trouble connecting to my analysis services. Please try again in a moment.",
                "general_error": "⚠️ I'm experiencing technical difficulties. Please try again later."
            },
            "onboarding": {
                "step1": "🌟 **Welcome to Reality Checker!**\n\nI'm your AI assistant for job scam detection. I can help you verify job postings by analyzing company information, salary claims, and contact details.\n\nReady to learn how I work? 📚",
                "step2": "🎯 **How to use me:**\n\n1️⃣ **Send text**: Copy and paste job posting details\n2️⃣ **Send PDF**: Share job posting as PDF file\n3️⃣ **Get analysis**: I'll analyze and give you a trust score\n\nTry sending me a job posting now! 🚀"
            },
            "common": {
                "yes": "Yes",
                "no": "No",
                "continue": "Continue",
                "skip": "Skip",
                "help": "Help",
                "back": "Back",
                "cancel": "Cancel",
                "done": "Done",
                "loading": "Loading...",
                "error": "Error",
                "success": "Success",
                "warning": "Warning",
                "info": "Information"
            },
            "analysis_results": {
                "trust_score": "Trust Score",
                "confidence": "Confidence",
                "classification": "Classification",
                "reasons": "Analysis Points",
                "recommendation": "Recommendation"
            }
        }
    
    def get_text(self, key: str, language: str = None, **kwargs) -> str:
        """
        Get localized text for a given key.
        
        Args:
            key: Dot-separated key (e.g., 'welcome.new_user')
            language: Language code (defaults to fallback)
            **kwargs: Variables for string formatting
            
        Returns:
            Localized text
        """
        if language is None:
            language = self.fallback_language
        
        # Try requested language first
        text = self._get_nested_value(self.translations.get(language, {}), key)
        
        # Fall back to English if not found
        if text is None and language != self.fallback_language:
            text = self._get_nested_value(self.translations.get(self.fallback_language, {}), key)
        
        # Final fallback
        if text is None:
            logger.warning(f"Translation not found: {key} for language {language}")
            return f"[{key}]"
        
        # Format with provided variables
        try:
            return text.format(**kwargs)
        except KeyError as e:
            logger.warning(f"Missing format variable {e} for key {key}")
            return text
    
    def _get_nested_value(self, data: Dict, key: str) -> Optional[str]:
        """Get nested dictionary value using dot notation."""
        keys = key.split('.')
        value = data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return None
        
        return value if isinstance(value, str) else None
    
    def get_supported_languages(self) -> List[Dict[str, str]]:
        """
        Get list of supported languages.
        
        Returns:
            List of language information dictionaries
        """
        languages = []
        for code, metadata in self.language_metadata.items():
            if code in self.translations:
                languages.append({
                    "code": code,
                    "name": metadata["name"],
                    "native_name": metadata["native_name"],
                    "region": metadata.get("region"),
                    "rtl": code in self.rtl_languages
                })
        return languages
    
    def detect_language_from_text(self, text: str) -> str:
        """
        Attempt to detect language from text content.
        
        Args:
            text: Text to analyze
            
        Returns:
            Detected language code or fallback
        """
        # Simple heuristic-based detection
        text_lower = text.lower()
        
        # Spanish indicators
        if any(word in text_lower for word in ['trabajo', 'empleo', 'empresa', 'salario', 'contrato']):
            return "es"
        
        # French indicators
        if any(word in text_lower for word in ['travail', 'emploi', 'entreprise', 'salaire', 'contrat']):
            return "fr"
        
        # Portuguese indicators
        if any(word in text_lower for word in ['trabalho', 'emprego', 'empresa', 'salário', 'contrato']):
            return "pt"
        
        # German indicators
        if any(word in text_lower for word in ['arbeit', 'stelle', 'unternehmen', 'gehalt', 'vertrag']):
            return "de"
        
        # Arabic indicators (basic)
        if re.search(r'[\u0600-\u06FF]', text):
            return "ar"
        
        # Chinese indicators
        if re.search(r'[\u4e00-\u9fff]', text):
            return "zh-CN"
        
        # Japanese indicators
        if re.search(r'[\u3040-\u309f\u30a0-\u30ff]', text):
            return "ja"
        
        # Korean indicators
        if re.search(r'[\uac00-\ud7af]', text):
            return "ko"
        
        # Default to English
        return self.fallback_language
    
    def create_localization_context(self, language: str, user_preferences: Dict = None) -> LocalizationContext:
        """
        Create localization context for a user.
        
        Args:
            language: User's preferred language
            user_preferences: Additional user preferences
            
        Returns:
            LocalizationContext object
        """
        preferences = user_preferences or {}
        
        # Get language metadata
        metadata = self.language_metadata.get(language, {})
        
        return LocalizationContext(
            language=language,
            region=preferences.get('region', metadata.get('region')),
            timezone=preferences.get('timezone'),
            currency=preferences.get('currency'),
            date_format=preferences.get('date_format'),
            number_format=preferences.get('number_format'),
            rtl=language in self.rtl_languages
        )


class LocalizedMessaging:
    """Provides localized messaging for different contexts."""
    
    def __init__(self, translation_manager: TranslationManager):
        """
        Initialize localized messaging.
        
        Args:
            translation_manager: Translation manager instance
        """
        self.translator = translation_manager
    
    def get_welcome_message(self, user_experience_level: str, language: str) -> str:
        """
        Get localized welcome message.
        
        Args:
            user_experience_level: User's experience level
            language: User's language
            
        Returns:
            Localized welcome message
        """
        key = f"welcome.{user_experience_level}"
        return self.translator.get_text(key, language)
    
    def get_analysis_message(self, classification: str, confidence: float, reasons: List[str], language: str) -> str:
        """
        Get localized analysis result message.
        
        Args:
            classification: Job classification
            confidence: Confidence score
            reasons: List of analysis reasons
            language: User's language
            
        Returns:
            Localized analysis message
        """
        key = f"analysis.{classification}"
        message = self.translator.get_text(key, language, confidence=int(confidence * 100))
        
        if reasons:
            reasons_text = "\n".join([f"• {reason}" for reason in reasons[:5]])
            message += f"\n\n{reasons_text}"
        
        return message
    
    def get_error_message(self, error_type: str, language: str) -> str:
        """
        Get localized error message.
        
        Args:
            error_type: Type of error
            language: User's language
            
        Returns:
            Localized error message
        """
        key = f"errors.{error_type}"
        return self.translator.get_text(key, language)
    
    def get_help_message(self, help_topic: str, language: str) -> str:
        """
        Get localized help message.
        
        Args:
            help_topic: Help topic
            language: User's language
            
        Returns:
            Localized help message
        """
        key = f"help.{help_topic}"
        return self.translator.get_text(key, language)


class CulturalAdapter:
    """Adapts content and behavior based on cultural context."""
    
    def __init__(self):
        """Initialize cultural adapter."""
        self.cultural_preferences = {
            # Greeting styles
            "formal_greetings": ["de", "ja", "ko", "ar"],
            "emoji_friendly": ["en", "es", "pt", "fil"],
            "direct_communication": ["de", "nl", "en"],
            "indirect_communication": ["ja", "ko", "th"],
            
            # Trust indicators
            "authority_focused": ["ja", "ko", "de", "ar"],
            "community_focused": ["es", "pt", "fil", "th"],
            "individual_focused": ["en", "nl", "de"],
            
            # Risk communication
            "high_context": ["ja", "ko", "ar", "th"],
            "low_context": ["en", "de", "nl"],
        }
    
    def adapt_message_style(self, message: str, language: str, context: str) -> str:
        """
        Adapt message style based on cultural preferences.
        
        Args:
            message: Original message
            language: Target language
            context: Message context (greeting, warning, etc.)
            
        Returns:
            Culturally adapted message
        """
        # Formal greetings for certain cultures
        if context == "greeting" and language in self.cultural_preferences["formal_greetings"]:
            message = message.replace("Hi!", "Good day,").replace("Hey", "Hello")
        
        # Adjust emoji usage
        if language not in self.cultural_preferences["emoji_friendly"]:
            # Reduce emoji usage for cultures that prefer more formal communication
            message = re.sub(r'[😀-🙏]{2,}', lambda m: m.group(0)[:1], message)
        
        # Adjust directness of warnings
        if context == "warning" and language in self.cultural_preferences["high_context"]:
            # Make warnings less direct for high-context cultures
            message = message.replace("Do NOT", "It would be advisable not to")
            message = message.replace("SCAM", "potentially fraudulent opportunity")
        
        return message
    
    def get_cultural_trust_indicators(self, language: str) -> List[str]:
        """
        Get culturally relevant trust indicators.
        
        Args:
            language: User's language
            
        Returns:
            List of trust indicators relevant to the culture
        """
        if language in self.cultural_preferences["authority_focused"]:
            return [
                "Government registration verification",
                "Official company documentation",
                "Regulatory compliance certificates",
                "Professional licenses and credentials"
            ]
        elif language in self.cultural_preferences["community_focused"]:
            return [
                "Employee testimonials and reviews",
                "Community reputation and references",
                "Local business registration",
                "Word-of-mouth recommendations"
            ]
        else:  # individual_focused
            return [
                "Transparent hiring process",
                "Clear job responsibilities",
                "Competitive market rates",
                "Professional communication standards"
            ]


# Global instances
_translation_manager: Optional[TranslationManager] = None
_localized_messaging: Optional[LocalizedMessaging] = None
_cultural_adapter: Optional[CulturalAdapter] = None


def get_translation_manager() -> TranslationManager:
    """Get global translation manager instance."""
    global _translation_manager
    if _translation_manager is None:
        _translation_manager = TranslationManager()
    return _translation_manager


def get_localized_messaging() -> LocalizedMessaging:
    """Get global localized messaging instance."""
    global _localized_messaging
    if _localized_messaging is None:
        _localized_messaging = LocalizedMessaging(get_translation_manager())
    return _localized_messaging


def get_cultural_adapter() -> CulturalAdapter:
    """Get global cultural adapter instance."""
    global _cultural_adapter
    if _cultural_adapter is None:
        _cultural_adapter = CulturalAdapter()
    return _cultural_adapter


def localize_datetime(dt: datetime, language: str, timezone_str: str = None) -> str:
    """
    Localize datetime formatting based on language and timezone.
    
    Args:
        dt: Datetime to format
        language: Language code
        timezone_str: Timezone string
        
    Returns:
        Localized datetime string
    """
    try:
        # Basic localization - in production, use proper datetime libraries
        formats = {
            "en": "%B %d, %Y at %I:%M %p",
            "es": "%d de %B de %Y a las %H:%M",
            "fr": "%d %B %Y à %H:%M",
            "de": "%d. %B %Y um %H:%M",
            "ja": "%Y年%m月%d日 %H:%M",
            "ko": "%Y년 %m월 %d일 %H:%M",
            "ar": "%d %B %Y في %H:%M",
            "zh-CN": "%Y年%m月%d日 %H:%M",
        }
        
        format_str = formats.get(language, formats["en"])
        return dt.strftime(format_str)
        
    except Exception as e:
        logger.error(f"Error localizing datetime: {e}")
        return dt.isoformat()


def localize_number(number: float, language: str, number_type: str = "decimal") -> str:
    """
    Localize number formatting based on language.
    
    Args:
        number: Number to format
        language: Language code
        number_type: Type of number (decimal, currency, percentage)
        
    Returns:
        Localized number string
    """
    try:
        # Basic number localization
        if language in ["de", "fr", "es", "pt", "it"]:
            # European style: 1.234,56
            if number_type == "percentage":
                return f"{number:.1f}%".replace(".", ",")
            else:
                return f"{number:,.2f}".replace(",", " ").replace(".", ",")
        else:
            # US/UK style: 1,234.56
            if number_type == "percentage":
                return f"{number:.1f}%"
            else:
                return f"{number:,.2f}"
                
    except Exception as e:
        logger.error(f"Error localizing number: {e}")
        return str(number)