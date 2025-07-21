"""
Extensions for the analytics service to support web uploads.

This module provides additional analytics functionality for web uploads.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from app.models.data_models import UserDetails, UserInteraction


async def get_source_breakdown(users: List[UserDetails], date_range: Optional[tuple] = None) -> Dict[str, int]:
    """
    Calculate breakdown of interactions by source (WhatsApp vs Web).
    
    Args:
        users: List of user details
        date_range: Optional tuple of (start_date, end_date)
        
    Returns:
        Dict with counts by source
    """
    source_counts = {"whatsapp": 0, "web": 0}
    
    for user in users:
        for interaction in user.interaction_history:
            # Apply date filter if provided
            if date_range:
                start_date, end_date = date_range
                if not (start_date <= interaction.timestamp <= end_date):
                    continue
            
            source = interaction.source if hasattr(interaction, 'source') else "whatsapp"
            source_counts[source] = source_counts.get(source, 0) + 1
    
    return source_counts


async def get_source_success_rates(users: List[UserDetails], date_range: Optional[tuple] = None) -> Dict[str, float]:
    """
    Calculate success rates by source (WhatsApp vs Web).
    
    Args:
        users: List of user details
        date_range: Optional tuple of (start_date, end_date)
        
    Returns:
        Dict with success rates by source
    """
    source_totals = {"whatsapp": 0, "web": 0}
    source_successes = {"whatsapp": 0, "web": 0}
    
    for user in users:
        for interaction in user.interaction_history:
            # Apply date filter if provided
            if date_range:
                start_date, end_date = date_range
                if not (start_date <= interaction.timestamp <= end_date):
                    continue
            
            source = interaction.source if hasattr(interaction, 'source') else "whatsapp"
            source_totals[source] = source_totals.get(source, 0) + 1
            
            if interaction.was_successful:
                source_successes[source] = source_successes.get(source, 0) + 1
    
    # Calculate success rates
    success_rates = {}
    for source, total in source_totals.items():
        if total > 0:
            success_rates[source] = round((source_successes[source] / total) * 100, 2)
        else:
            success_rates[source] = 0.0
    
    return success_rates


async def get_source_response_times(users: List[UserDetails], date_range: Optional[tuple] = None) -> Dict[str, float]:
    """
    Calculate average response times by source (WhatsApp vs Web).
    
    Args:
        users: List of user details
        date_range: Optional tuple of (start_date, end_date)
        
    Returns:
        Dict with average response times by source
    """
    source_times = {"whatsapp": [], "web": []}
    
    for user in users:
        for interaction in user.interaction_history:
            # Apply date filter if provided
            if date_range:
                start_date, end_date = date_range
                if not (start_date <= interaction.timestamp <= end_date):
                    continue
            
            if interaction.response_time > 0:
                source = interaction.source if hasattr(interaction, 'source') else "whatsapp"
                source_times[source].append(interaction.response_time)
    
    # Calculate average response times
    avg_times = {}
    for source, times in source_times.items():
        if times:
            avg_times[source] = round(sum(times) / len(times), 2)
        else:
            avg_times[source] = 0.0
    
    return avg_times


async def get_source_daily_trends(users: List[UserDetails], date_range: tuple) -> Dict[str, List[Dict[str, Any]]]:
    """
    Calculate daily trends by source (WhatsApp vs Web).
    
    Args:
        users: List of user details
        date_range: Tuple of (start_date, end_date)
        
    Returns:
        Dict with daily trends by source
    """
    start_date, end_date = date_range
    daily_counts = {"whatsapp": defaultdict(int), "web": defaultdict(int)}
    
    for user in users:
        for interaction in user.interaction_history:
            if start_date <= interaction.timestamp <= end_date:
                date_str = interaction.timestamp.date().isoformat()
                source = interaction.source if hasattr(interaction, 'source') else "whatsapp"
                daily_counts[source][date_str] += 1
    
    # Convert to list format
    result = {"whatsapp": [], "web": []}
    current_date = start_date.date()
    end_date = end_date.date()
    
    while current_date <= end_date:
        date_str = current_date.isoformat()
        
        for source in ["whatsapp", "web"]:
            result[source].append({
                "date": date_str,
                "count": daily_counts[source].get(date_str, 0)
            })
        
        current_date += timedelta(days=1)
    
    return result