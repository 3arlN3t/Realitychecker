"""
User onboarding and help system for Reality Checker.

This module provides comprehensive onboarding experiences, interactive tutorials,
contextual help, and progressive user guidance.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
import json

from app.utils.logging import get_logger
from app.utils.user_experience import UserExperienceLevel, UserContext

logger = get_logger(__name__)


class OnboardingStage(Enum):
    """Different stages of user onboarding."""
    NOT_STARTED = "not_started"
    WELCOME = "welcome"
    FEATURES_INTRO = "features_intro"
    FIRST_ANALYSIS = "first_analysis"
    UNDERSTANDING_RESULTS = "understanding_results"
    ADVANCED_FEATURES = "advanced_features"
    COMPLETED = "completed"


class HelpCategory(Enum):
    """Categories of help content."""
    GETTING_STARTED = "getting_started"
    ANALYSIS_FEATURES = "analysis_features"
    UNDERSTANDING_RESULTS = "understanding_results"
    TROUBLESHOOTING = "troubleshooting"
    SAFETY_TIPS = "safety_tips"
    ADVANCED_USAGE = "advanced_usage"


@dataclass
class OnboardingStep:
    """Individual step in the onboarding process."""
    id: str
    title: str
    description: str
    message: str
    actions: List[str] = field(default_factory=list)
    next_steps: Dict[str, str] = field(default_factory=dict)
    completion_criteria: Optional[str] = None
    estimated_time: Optional[int] = None  # in seconds
    interactive: bool = True
    media_url: Optional[str] = None


@dataclass
class OnboardingProgress:
    """Tracks user's onboarding progress."""
    user_phone: str
    current_stage: OnboardingStage
    completed_steps: List[str] = field(default_factory=list)
    skipped_steps: List[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_interaction: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completion_percentage: float = 0.0
    user_feedback: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HelpTopic:
    """Individual help topic with content and examples."""
    id: str
    category: HelpCategory
    title: str
    description: str
    content: str
    examples: List[str] = field(default_factory=list)
    related_topics: List[str] = field(default_factory=list)
    difficulty_level: str = "beginner"  # beginner, intermediate, advanced
    estimated_read_time: int = 60  # in seconds
    tags: List[str] = field(default_factory=list)


class OnboardingSystem:
    """Comprehensive user onboarding system."""
    
    def __init__(self):
        """Initialize onboarding system."""
        self.onboarding_flows = self._create_onboarding_flows()
        self.user_progress: Dict[str, OnboardingProgress] = {}
        self.help_content = self._create_help_content()
        
    def _create_onboarding_flows(self) -> Dict[OnboardingStage, List[OnboardingStep]]:
        """Create structured onboarding flows."""
        return {
            OnboardingStage.WELCOME: [
                OnboardingStep(
                    id="welcome_intro",
                    title="Welcome to Reality Checker",
                    description="Introduction to the service",
                    message="🌟 **Welcome to Reality Checker!**\n\nI'm your AI-powered job scam detection assistant. I help job seekers like you stay safe by analyzing job postings for red flags and suspicious content.\n\n🛡️ **What I do:**\n• Analyze job descriptions for scam indicators\n• Check company legitimacy\n• Verify salary claims\n• Identify common fraud patterns\n\nReady to learn how to use me? 🚀",
                    actions=["yes", "skip", "learn_more"],
                    next_steps={
                        "yes": "features_intro",
                        "skip": "quick_start",
                        "learn_more": "detailed_intro"
                    },
                    estimated_time=30
                ),
                OnboardingStep(
                    id="detailed_intro",
                    title="Why Reality Checker Exists",
                    description="Background on job scams and our mission",
                    message="📊 **The Problem We Solve**\n\nJob scams cost victims billions annually:\n• 💰 Average loss: $2,000 per victim\n• 📈 300% increase in job scams since 2020\n• 🎯 Most targeted: Entry-level job seekers\n\n✨ **How I Help:**\n• Instant analysis of job postings\n• Red flag detection using AI\n• Educational guidance on safe job hunting\n• 24/7 availability when you need it\n\nLet's keep you safe! Continue? 💪",
                    actions=["continue", "skip"],
                    next_steps={"continue": "features_intro", "skip": "quick_start"},
                    estimated_time=45
                )
            ],
            
            OnboardingStage.FEATURES_INTRO: [
                OnboardingStep(
                    id="how_to_use",
                    title="How to Use Reality Checker",
                    description="Basic usage instructions",
                    message="🎯 **How to Use Me - It's Easy!**\n\n**Method 1: Send Text** 📝\n• Copy job posting details\n• Paste and send to me\n• Get instant analysis\n\n**Method 2: Send PDF** 📄\n• Screenshot or save job posting as PDF\n• Send the file to me\n• I'll extract and analyze the text\n\n**What I Need:**\n• Job title and description\n• Company name\n• Salary/compensation\n• Contact information\n\nReady to try? Send 'demo' for a practice example! 🚀",
                    actions=["demo", "real_job", "continue"],
                    next_steps={
                        "demo": "demo_analysis",
                        "real_job": "first_analysis", 
                        "continue": "trust_scores"
                    },
                    estimated_time=60
                ),
                OnboardingStep(
                    id="demo_analysis",
                    title="Demo Analysis",
                    description="Practice with a sample job posting",
                    message="🎭 **Practice with This Fake Job Posting:**\n\n---\n**URGENT: Make $5000/week working from home!**\n\nNo experience needed! Just pay $200 registration fee to get started. Contact John at johnscammer@email.com immediately!\n\nGuaranteed income! Work only 2 hours per day!\n---\n\n🤔 What do you think? Does this look legitimate to you?\n\nSend your guess: 'scam' or 'legit', then I'll show you my analysis! 🔍",
                    actions=["scam", "legit"],
                    next_steps={"scam": "demo_results_correct", "legit": "demo_results_learning"},
                    estimated_time=90,
                    interactive=True
                ),
                OnboardingStep(
                    id="demo_results_correct",
                    title="Great Job!",
                    description="User correctly identified the scam",
                    message="🎉 **Excellent!** You spotted the scam!\n\n🚨 **My Analysis: HIGH RISK SCAM (95% confidence)**\n\n**Red Flags I Found:**\n• 💰 Unrealistic income promise ($5000/week)\n• 💳 Upfront payment required ($200 fee)\n• ⏰ Urgent/pressure tactics\n• 📧 Unprofessional email address\n• 🔍 Vague job description\n• ✨ \"Too good to be true\" claims\n\nYou're already thinking like a scam detector! 🕵️\n\nReady to learn about trust scores? 📊",
                    actions=["continue", "another_demo"],
                    next_steps={"continue": "trust_scores", "another_demo": "demo_analysis_2"},
                    estimated_time=60
                ),
                OnboardingStep(
                    id="demo_results_learning", 
                    title="Learning Moment",
                    description="Educational response for incorrect guess",
                    message="📚 **Learning Opportunity!**\n\nThis was actually a scam! Let me show you why:\n\n🚨 **My Analysis: HIGH RISK SCAM (95% confidence)**\n\n**Major Red Flags:**\n• 💰 Unrealistic promises ($5000/week for 2hrs work)\n• 💳 Upfront payment required\n• ⏰ Pressure tactics (\"URGENT\", \"immediately\")\n• 📧 Unprofessional contact info\n• 🎯 Targets desperation\n\n💡 **Remember:** If it sounds too good to be true, it probably is!\n\nDon't worry - spotting scams takes practice. That's why I'm here to help! 🛡️\n\nReady to learn about trust scores? 📊",
                    actions=["continue", "another_demo"],
                    next_steps={"continue": "trust_scores", "another_demo": "demo_analysis_2"},
                    estimated_time=75
                ),
                OnboardingStep(
                    id="trust_scores",
                    title="Understanding Trust Scores", 
                    description="Explanation of the scoring system",
                    message="📊 **Trust Scores Explained**\n\nI rate every job posting on a scale of 0-10:\n\n🔴 **0-3: High Risk**\n• Likely scam - avoid completely\n• Multiple red flags detected\n• Do NOT proceed\n\n🟡 **4-6: Proceed with Caution**\n• Some concerning elements\n• Research company thoroughly\n• Ask detailed questions\n\n🟢 **7-10: Likely Legitimate**\n• Positive indicators found\n• Normal due diligence recommended\n• Proceed with confidence\n\n💡 **Plus:** I always explain my reasoning so you can learn to spot patterns yourself!\n\nReady to try analyzing a real job posting? 🎯",
                    actions=["yes", "more_examples", "questions"],
                    next_steps={
                        "yes": "first_analysis",
                        "more_examples": "more_demos", 
                        "questions": "faq"
                    },
                    estimated_time=90
                )
            ],
            
            OnboardingStage.FIRST_ANALYSIS: [
                OnboardingStep(
                    id="first_real_analysis",
                    title="Your First Real Analysis",
                    description="Guide user through their first analysis",
                    message="🎯 **Time for Your First Real Analysis!**\n\nSend me a job posting you'd like me to check. This could be:\n• A posting you found online\n• An email you received\n• A text message offer\n• A social media job ad\n\nJust copy and paste the text, or send a PDF/screenshot!\n\n💡 **Tip:** Include as much detail as possible for the most accurate analysis.\n\nI'm ready when you are! 🚀",
                    actions=["job_posting"],
                    completion_criteria="user_sends_job_posting",
                    estimated_time=120,
                    interactive=True
                )
            ],
            
            OnboardingStage.UNDERSTANDING_RESULTS: [
                OnboardingStep(
                    id="results_explanation",
                    title="Understanding Your Results",
                    description="Help user understand analysis results",
                    message="🎓 **Understanding Your Analysis Results**\n\nGreat job sending your first posting! Here's how to read my analysis:\n\n📊 **Trust Score:** The overall rating (0-10)\n📈 **Confidence:** How certain I am about my assessment\n🔍 **Classification:** Risk level category\n📝 **Analysis Points:** Specific things I noticed\n💡 **Recommendation:** What you should do next\n\n🤔 **Questions about your results?**\n• Ask me to clarify anything\n• Send 'explain [topic]' for more details\n• I'm here to help you understand!\n\nWant to learn about advanced features? 🚀",
                    actions=["advanced", "questions", "another"],
                    next_steps={
                        "advanced": "advanced_features",
                        "questions": "qa_session",
                        "another": "first_analysis"
                    },
                    estimated_time=90
                )
            ],
            
            OnboardingStage.ADVANCED_FEATURES: [
                OnboardingStep(
                    id="advanced_tips",
                    title="Advanced Features & Tips",
                    description="Advanced usage guidance",
                    message="🚀 **Advanced Features & Pro Tips**\n\n**🔍 Deep Analysis:**\n• Send multiple postings for comparison\n• Ask for specific red flag explanations\n• Request industry-specific insights\n\n**💬 Interactive Help:**\n• Send 'help' anytime for assistance\n• Ask 'explain trust score' for details\n• Say 'tips' for job hunting safety advice\n\n**🛡️ Stay Protected:**\n• Always verify companies independently\n• Never pay upfront fees\n• Trust your instincts\n• Use me as one tool in your toolkit\n\n**🎯 Quick Commands:**\n• 'help' - Get assistance\n• 'tips' - Safety advice\n• 'demo' - Practice examples\n\nYou're now a Reality Checker expert! 🎉",
                    actions=["finish", "practice_more"],
                    next_steps={"finish": "completion", "practice_more": "first_analysis"},
                    estimated_time=120
                )
            ]
        }
    
    def _create_help_content(self) -> Dict[HelpCategory, List[HelpTopic]]:
        """Create comprehensive help content."""
        return {
            HelpCategory.GETTING_STARTED: [
                HelpTopic(
                    id="what_is_reality_checker",
                    category=HelpCategory.GETTING_STARTED,
                    title="What is Reality Checker?",
                    description="Overview of the Reality Checker service",
                    content="Reality Checker is an AI-powered job scam detection service that helps job seekers verify the legitimacy of job postings. I analyze job descriptions, company information, salary claims, and contact details to identify potential scams and protect you from fraud.",
                    examples=[
                        "Analyze text-based job postings",
                        "Process PDF job advertisements", 
                        "Identify common scam patterns",
                        "Provide safety recommendations"
                    ],
                    related_topics=["how_to_use", "trust_scores"],
                    tags=["basics", "overview", "intro"]
                ),
                HelpTopic(
                    id="how_to_use",
                    category=HelpCategory.GETTING_STARTED,
                    title="How to Use Reality Checker",
                    description="Step-by-step usage instructions",
                    content="Using Reality Checker is simple:\n\n1. **Send Text**: Copy and paste job posting details directly to me\n2. **Send PDF**: Share job posting files for analysis\n3. **Get Results**: Receive instant analysis with trust score and explanations\n4. **Ask Questions**: Request clarification on any part of the analysis\n\nI can analyze job titles, descriptions, company information, salary details, requirements, and contact information.",
                    examples=[
                        "Copy job posting from Indeed and paste it",
                        "Screenshot LinkedIn job and send as image",
                        "Forward suspicious job email text",
                        "Send PDF attachment from job board"
                    ],
                    related_topics=["trust_scores", "file_formats"],
                    difficulty_level="beginner",
                    tags=["usage", "instructions", "basics"]
                )
            ],
            
            HelpCategory.ANALYSIS_FEATURES: [
                HelpTopic(
                    id="trust_scores",
                    category=HelpCategory.ANALYSIS_FEATURES,
                    title="Understanding Trust Scores",
                    description="How trust scores work and what they mean",
                    content="Trust scores range from 0-10 and indicate the likelihood that a job posting is legitimate:\n\n🔴 **0-3: High Risk** - Strong indicators of scam, avoid completely\n🟡 **4-6: Proceed with Caution** - Some red flags, research thoroughly\n🟢 **7-10: Likely Legitimate** - Positive indicators, normal caution advised\n\nThe score considers factors like realistic salary ranges, professional communication, company verification, job description clarity, and contact information legitimacy.",
                    examples=[
                        "Score 2: 'Make $5000/week from home, pay $200 to start'",
                        "Score 5: Vague description but legitimate company",
                        "Score 8: Clear role at verified company with realistic pay",
                        "Score 9: Detailed posting from known employer"
                    ],
                    related_topics=["red_flags", "analysis_factors"],
                    difficulty_level="beginner",
                    tags=["scoring", "analysis", "results"]
                ),
                HelpTopic(
                    id="red_flags",
                    category=HelpCategory.ANALYSIS_FEATURES,
                    title="Common Red Flags",
                    description="Warning signs that indicate potential scams",
                    content="🚨 **Major Red Flags:**\n\n💰 **Financial Red Flags:**\n• Upfront payment required\n• Unrealistic income promises\n• 'Easy money' claims\n• Payment processing roles\n\n📝 **Content Red Flags:**\n• Poor grammar/spelling\n• Vague job descriptions\n• Excessive urgency\n• Too-good-to-be-true offers\n\n🏢 **Company Red Flags:**\n• No verifiable company info\n• Generic email addresses\n• No physical address\n• Fake testimonials\n\n📞 **Contact Red Flags:**\n• Only text/WhatsApp contact\n• Refuses phone calls\n• Won't provide references\n• Avoids direct questions",
                    examples=[
                        "'Pay $500 for training materials'",
                        "'Earn $10,000 your first month!'",
                        "'URGENT: Apply within 24 hours!'",
                        "'Work 2 hours, earn $500 daily'"
                    ],
                    related_topics=["trust_scores", "safety_tips"],
                    difficulty_level="intermediate",
                    tags=["red_flags", "scams", "warning_signs"]
                )
            ],
            
            HelpCategory.SAFETY_TIPS: [
                HelpTopic(
                    id="job_hunting_safety",
                    category=HelpCategory.SAFETY_TIPS,
                    title="Safe Job Hunting Practices",
                    description="Best practices for safe job searching",
                    content="🛡️ **Essential Safety Tips:**\n\n✅ **Before Applying:**\n• Research company independently\n• Verify company website and contact info\n• Check company reviews on multiple sites\n• Look up company registration/licensing\n\n✅ **During Communication:**\n• Ask detailed questions about the role\n• Request specific company information\n• Verify interviewer's identity\n• Keep records of all communications\n\n✅ **Never Do This:**\n• Pay upfront fees or 'deposits'\n• Share bank account or SSN early\n• Send money for 'equipment'\n• Accept checks then wire money back\n\n✅ **Trust Your Instincts:**\n• If something feels off, investigate\n• Don't rush important decisions\n• Seek second opinions\n• Use Reality Checker for verification",
                    examples=[
                        "Google '[Company Name] reviews scam'",
                        "Check Better Business Bureau ratings",
                        "Verify address on Google Street View",
                        "Ask for employee LinkedIn profiles"
                    ],
                    related_topics=["red_flags", "verification_methods"],
                    difficulty_level="intermediate",
                    tags=["safety", "tips", "best_practices"]
                )
            ]
        }
    
    def start_onboarding(self, user_phone: str, user_context: UserContext = None) -> Tuple[str, OnboardingProgress]:
        """
        Start onboarding process for a new user.
        
        Args:
            user_phone: User's phone number
            user_context: Optional user context information
            
        Returns:
            Tuple of (welcome_message, onboarding_progress)
        """
        # Create new onboarding progress
        progress = OnboardingProgress(
            user_phone=user_phone,
            current_stage=OnboardingStage.WELCOME
        )
        
        self.user_progress[user_phone] = progress
        
        # Get first onboarding step
        first_step = self.onboarding_flows[OnboardingStage.WELCOME][0]
        
        # Customize welcome message based on user context
        if user_context and user_context.experience_level != UserExperienceLevel.NEW_USER:
            # Offer abbreviated onboarding for returning users
            message = f"{first_step.message}\n\n💡 **Returning user?** Send 'skip' to go straight to job analysis!"
        else:
            message = first_step.message
        
        logger.info(f"Started onboarding for user {user_phone}")
        return message, progress
    
    def process_onboarding_response(self, user_phone: str, response: str) -> Optional[str]:
        """
        Process user response during onboarding.
        
        Args:
            user_phone: User's phone number
            response: User's response
            
        Returns:
            Next onboarding message or None if completed
        """
        if user_phone not in self.user_progress:
            return None
        
        progress = self.user_progress[user_phone]
        current_steps = self.onboarding_flows.get(progress.current_stage, [])
        
        if not current_steps:
            return None
        
        # Find current step
        current_step_index = len(progress.completed_steps)
        if current_step_index >= len(current_steps):
            # Move to next stage
            return self._advance_onboarding_stage(user_phone)
        
        current_step = current_steps[current_step_index]
        response_lower = response.lower().strip()
        
        # Check if response matches any actions
        if response_lower in current_step.actions:
            # Mark step as completed
            progress.completed_steps.append(current_step.id)
            progress.last_interaction = datetime.now(timezone.utc)
            
            # Handle next step based on response
            if response_lower in current_step.next_steps:
                next_step_id = current_step.next_steps[response_lower]
                
                # Find next step
                for step in current_steps:
                    if step.id == next_step_id:
                        return step.message
                
                # If not found in current stage, might be in another stage
                return self._handle_cross_stage_navigation(user_phone, next_step_id)
            else:
                # Continue to next step in sequence
                return self._get_next_sequential_step(user_phone)
        
        # Handle special responses
        if response_lower in ['skip', 'skip onboarding']:
            return self._skip_onboarding(user_phone)
        elif response_lower in ['help', 'help me']:
            return self._get_contextual_help(user_phone)
        elif response_lower in ['back', 'previous']:
            return self._go_back_onboarding(user_phone)
        
        # Invalid response - provide guidance
        return f"🤔 I didn't understand '{response}'. Please choose from: {', '.join(current_step.actions)}\n\nOr send 'help' for assistance!"
    
    def _advance_onboarding_stage(self, user_phone: str) -> Optional[str]:
        """Advance user to the next onboarding stage."""
        progress = self.user_progress[user_phone]
        
        # Determine next stage
        stage_order = [
            OnboardingStage.WELCOME,
            OnboardingStage.FEATURES_INTRO,
            OnboardingStage.FIRST_ANALYSIS,
            OnboardingStage.UNDERSTANDING_RESULTS,
            OnboardingStage.ADVANCED_FEATURES,
            OnboardingStage.COMPLETED
        ]
        
        current_index = stage_order.index(progress.current_stage)
        if current_index < len(stage_order) - 1:
            next_stage = stage_order[current_index + 1]
            progress.current_stage = next_stage
            
            if next_stage == OnboardingStage.COMPLETED:
                return self._complete_onboarding(user_phone)
            
            # Get first step of next stage
            next_steps = self.onboarding_flows.get(next_stage, [])
            if next_steps:
                return next_steps[0].message
        
        return self._complete_onboarding(user_phone)
    
    def _complete_onboarding(self, user_phone: str) -> str:
        """Complete the onboarding process."""
        progress = self.user_progress[user_phone]
        progress.current_stage = OnboardingStage.COMPLETED
        progress.completion_percentage = 100.0
        
        completion_message = """🎉 **Onboarding Complete!**

Congratulations! You're now ready to use Reality Checker effectively.

🎯 **What You've Learned:**
• How to send job postings for analysis
• Understanding trust scores and classifications
• Recognizing common red flags
• Safe job hunting practices

💪 **You're Ready To:**
• Analyze any job posting instantly
• Make informed decisions about opportunities
• Stay protected from job scams
• Help others stay safe too!

🚀 **Get Started:**
Send me any job posting to analyze, or:
• Send 'help' for assistance
• Send 'tips' for safety advice
• Send 'demo' for practice examples

Welcome to safer job hunting! 🛡️"""

        logger.info(f"Completed onboarding for user {user_phone}")
        return completion_message
    
    def get_help_content(self, category: HelpCategory = None, topic_id: str = None) -> str:
        """
        Get help content for a specific category or topic.
        
        Args:
            category: Help category to browse
            topic_id: Specific topic ID to get
            
        Returns:
            Formatted help content
        """
        if topic_id:
            # Find specific topic
            for cat_topics in self.help_content.values():
                for topic in cat_topics:
                    if topic.id == topic_id:
                        return self._format_help_topic(topic)
            return "Help topic not found. Send 'help' for available topics."
        
        if category:
            # Get topics for category
            topics = self.help_content.get(category, [])
            if not topics:
                return "No topics found for this category."
            
            content = f"📚 **{category.value.replace('_', ' ').title()} Help**\n\n"
            for i, topic in enumerate(topics, 1):
                content += f"{i}️⃣ **{topic.title}**\n{topic.description}\n\n"
            
            content += "Send the number to read a specific topic, or 'help' for main menu."
            return content
        
        # Main help menu
        return self._get_main_help_menu()
    
    def _format_help_topic(self, topic: HelpTopic) -> str:
        """Format a help topic for display."""
        content = f"📖 **{topic.title}**\n\n{topic.content}\n\n"
        
        if topic.examples:
            content += "💡 **Examples:**\n"
            for example in topic.examples:
                content += f"• {example}\n"
            content += "\n"
        
        if topic.related_topics:
            content += f"🔗 **Related:** {', '.join(topic.related_topics)}\n\n"
        
        content += "Send 'help' to return to main menu."
        return content
    
    def _get_main_help_menu(self) -> str:
        """Get the main help menu."""
        return """🆘 **Reality Checker Help**

**Quick Start:**
1️⃣ Getting Started - Basic usage and setup
2️⃣ Analysis Features - Understanding results and scores  
3️⃣ Safety Tips - Best practices for job hunting
4️⃣ Troubleshooting - Common issues and solutions

**Quick Commands:**
• 'demo' - Practice with example job postings
• 'tips' - Get safety advice
• 'tutorial' - Restart onboarding
• 'support' - Contact human support

Send the number for a help category, or type a specific question! 💬"""
    
    def is_in_onboarding(self, user_phone: str) -> bool:
        """Check if user is currently in onboarding."""
        if user_phone not in self.user_progress:
            return False
        
        progress = self.user_progress[user_phone]
        return progress.current_stage != OnboardingStage.COMPLETED
    
    def get_onboarding_progress(self, user_phone: str) -> Optional[OnboardingProgress]:
        """Get user's onboarding progress."""
        return self.user_progress.get(user_phone)
    
    def skip_to_analysis(self, user_phone: str) -> str:
        """Skip onboarding and go directly to analysis mode."""
        if user_phone in self.user_progress:
            progress = self.user_progress[user_phone]
            progress.current_stage = OnboardingStage.COMPLETED
            progress.completion_percentage = 100.0
            progress.skipped_steps = ["full_onboarding"]
        
        return """⚡ **Onboarding Skipped**

No problem! You can always get help later.

🎯 **Quick Start:**
• Send me job posting text to analyze
• Send PDF files for analysis
• Send 'help' anytime for assistance
• Send 'tips' for safety advice

Ready to analyze your first job posting! 🚀"""


# Global instance
_onboarding_system: Optional[OnboardingSystem] = None


def get_onboarding_system() -> OnboardingSystem:
    """Get global onboarding system instance."""
    global _onboarding_system
    if _onboarding_system is None:
        _onboarding_system = OnboardingSystem()
    return _onboarding_system