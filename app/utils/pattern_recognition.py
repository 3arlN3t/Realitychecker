"""
Pattern recognition module for advanced analytics in Reality Checker.

This module provides sophisticated pattern recognition capabilities including:
- Time series pattern detection
- Seasonal trend analysis
- Anomaly detection algorithms
- Clustering of user behaviors
- Predictive pattern modeling
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import statistics
from scipy import stats
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import logging

from app.utils.logging import get_logger

logger = get_logger(__name__)


class PatternType(Enum):
    """Types of patterns that can be detected."""
    SEASONAL = "seasonal"
    CYCLICAL = "cyclical"
    TREND = "trend"
    SPIKE = "spike"
    DROP = "drop"
    PLATEAU = "plateau"
    OSCILLATION = "oscillation"
    STEP_CHANGE = "step_change"


@dataclass
class DetectedPattern:
    """A detected pattern in time series data."""
    pattern_type: PatternType
    confidence: float  # 0-1
    start_time: datetime
    end_time: datetime
    magnitude: float
    description: str
    supporting_data: Dict[str, Any]


class PatternRecognitionEngine:
    """Engine for detecting patterns in time series data."""
    
    def __init__(self):
        """Initialize the pattern recognition engine."""
        self.min_data_points = 10
        self.seasonal_periods = [24, 168]  # Hours in day, hours in week
        logger.info("Pattern Recognition Engine initialized")
    
    async def detect_patterns(self, time_series: List[Tuple[datetime, float]], 
                            lookback_days: int = 30) -> List[DetectedPattern]:
        """
        Detect patterns in time series data.
        
        Args:
            time_series: List of (timestamp, value) tuples
            lookback_days: Number of days to analyze
            
        Returns:
            List of detected patterns
        """
        if len(time_series) < self.min_data_points:
            return []
        
        # Convert to pandas DataFrame for easier analysis
        df = pd.DataFrame(time_series, columns=['timestamp', 'value'])
        df = df.sort_values('timestamp')
        
        # Filter by lookback period
        cutoff_time = datetime.now() - timedelta(days=lookback_days)
        df = df[df['timestamp'] >= cutoff_time]
        
        if len(df) < self.min_data_points:
            return []
        
        patterns = []
        
        # Detect different pattern types
        try:
            # Trend detection
            trend_patterns = self._detect_trends(df)
            patterns.extend(trend_patterns)
            
            # Seasonal pattern detection
            seasonal_patterns = self._detect_seasonal_patterns(df)
            patterns.extend(seasonal_patterns)
            
            # Anomaly detection
            anomaly_patterns = self._detect_anomalies(df)
            patterns.extend(anomaly_patterns)
            
            # Step change detection
            step_patterns = self._detect_step_changes(df)
            patterns.extend(step_patterns)
            
        except Exception as e:
            logger.error(f"Error in pattern detection: {e}")
        
        return patterns
    
    def _detect_trends(self, df: pd.DataFrame) -> List[DetectedPattern]:
        """Detect trend patterns in the data."""
        patterns = []
        
        try:
            # Calculate trend using linear regression
            x = np.array(range(len(df))).reshape(-1, 1)
            y = df['value'].values
            
            slope, intercept, r_value, p_value, std_err = stats.linregress(
                range(len(df)), df['value']
            )
            
            # Check if trend is statistically significant
            if p_value < 0.05 and abs(r_value) > 0.5:
                trend_type = PatternType.TREND
                confidence = min(1.0, abs(r_value))
                
                description = f"{'Upward' if slope > 0 else 'Downward'} trend detected"
                magnitude = abs(slope * len(df))
                
                pattern = DetectedPattern(
                    pattern_type=trend_type,
                    confidence=confidence,
                    start_time=df['timestamp'].iloc[0],
                    end_time=df['timestamp'].iloc[-1],
                    magnitude=magnitude,
                    description=description,
                    supporting_data={
                        'slope': slope,
                        'r_squared': r_value**2,
                        'p_value': p_value,
                        'direction': 'up' if slope > 0 else 'down'
                    }
                )
                patterns.append(pattern)
        
        except Exception as e:
            logger.error(f"Error in trend detection: {e}")
        
        return patterns
    
    def _detect_seasonal_patterns(self, df: pd.DataFrame) -> List[DetectedPattern]:
        """Detect seasonal patterns in the data."""
        patterns = []
        
        try:
            # Need sufficient data for seasonal analysis
            if len(df) < 48:  # At least 2 days of hourly data
                return patterns
            
            # Resample to hourly data if timestamps are irregular
            df['hour'] = df['timestamp'].dt.hour
            df['day_of_week'] = df['timestamp'].dt.dayofweek
            
            # Check for daily patterns
            hour_means = df.groupby('hour')['value'].mean()
            hour_std = df.groupby('hour')['value'].std()
            
            # Calculate coefficient of variation to detect seasonality
            cv = hour_std / hour_means
            mean_cv = cv.mean()
            
            if mean_cv > 0.2:  # Significant variation by hour
                # Find peak hours
                peak_hours = hour_means.nlargest(3).index.tolist()
                
                pattern = DetectedPattern(
                    pattern_type=PatternType.SEASONAL,
                    confidence=min(mean_cv, 1.0),
                    start_time=df['timestamp'].iloc[0],
                    end_time=df['timestamp'].iloc[-1],
                    magnitude=hour_means.max() - hour_means.min(),
                    description=f"Daily seasonal pattern detected with peaks at hours {peak_hours}",
                    supporting_data={
                        'peak_hours': peak_hours,
                        'hourly_variation': mean_cv,
                        'period': 24
                    }
                )
                patterns.append(pattern)
            
            # Check for weekly patterns
            if len(df) >= 168:  # At least 1 week of hourly data
                day_means = df.groupby('day_of_week')['value'].mean()
                day_std = df.groupby('day_of_week')['value'].std()
                
                day_cv = day_std / day_means
                mean_day_cv = day_cv.mean()
                
                if mean_day_cv > 0.15:  # Significant variation by day
                    # Find peak days
                    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                    peak_days = [days[i] for i in day_means.nlargest(2).index.tolist()]
                    
                    pattern = DetectedPattern(
                        pattern_type=PatternType.SEASONAL,
                        confidence=min(mean_day_cv * 1.2, 1.0),
                        start_time=df['timestamp'].iloc[0],
                        end_time=df['timestamp'].iloc[-1],
                        magnitude=day_means.max() - day_means.min(),
                        description=f"Weekly seasonal pattern detected with peaks on {', '.join(peak_days)}",
                        supporting_data={
                            'peak_days': peak_days,
                            'daily_variation': mean_day_cv,
                            'period': 7
                        }
                    )
                    patterns.append(pattern)
        
        except Exception as e:
            logger.error(f"Error in seasonal pattern detection: {e}")
        
        return patterns
    
    def _detect_anomalies(self, df: pd.DataFrame) -> List[DetectedPattern]:
        """Detect anomalies in the data."""
        patterns = []
        
        try:
            # Calculate rolling statistics
            window = min(24, max(5, len(df) // 10))
            df['rolling_mean'] = df['value'].rolling(window=window, center=True).mean()
            df['rolling_std'] = df['value'].rolling(window=window, center=True).std()
            
            # Fill NaN values
            df['rolling_mean'] = df['rolling_mean'].fillna(df['value'].mean())
            df['rolling_std'] = df['rolling_std'].fillna(df['value'].std())
            
            # Detect spikes and drops (Z-score method)
            df['z_score'] = (df['value'] - df['rolling_mean']) / df['rolling_std'].replace(0, 1)
            
            # Find anomalies
            spike_threshold = 2.5
            spikes = df[df['z_score'] > spike_threshold]
            drops = df[df['z_score'] < -spike_threshold]
            
            # Create patterns for significant spikes
            for _, spike in spikes.iterrows():
                pattern = DetectedPattern(
                    pattern_type=PatternType.SPIKE,
                    confidence=min(abs(spike['z_score']) / 5.0, 1.0),
                    start_time=spike['timestamp'],
                    end_time=spike['timestamp'] + timedelta(hours=1),
                    magnitude=spike['value'],
                    description=f"Significant spike detected ({spike['z_score']:.2f} standard deviations)",
                    supporting_data={
                        'z_score': spike['z_score'],
                        'expected_value': spike['rolling_mean'],
                        'actual_value': spike['value']
                    }
                )
                patterns.append(pattern)
            
            # Create patterns for significant drops
            for _, drop in drops.iterrows():
                pattern = DetectedPattern(
                    pattern_type=PatternType.DROP,
                    confidence=min(abs(drop['z_score']) / 5.0, 1.0),
                    start_time=drop['timestamp'],
                    end_time=drop['timestamp'] + timedelta(hours=1),
                    magnitude=drop['value'],
                    description=f"Significant drop detected ({drop['z_score']:.2f} standard deviations)",
                    supporting_data={
                        'z_score': drop['z_score'],
                        'expected_value': drop['rolling_mean'],
                        'actual_value': drop['value']
                    }
                )
                patterns.append(pattern)
        
        except Exception as e:
            logger.error(f"Error in anomaly detection: {e}")
        
        return patterns
    
    def _detect_step_changes(self, df: pd.DataFrame) -> List[DetectedPattern]:
        """Detect step changes in the data."""
        patterns = []
        
        try:
            if len(df) < 20:
                return patterns
            
            # Calculate cumulative sum of differences
            df['diff'] = df['value'].diff()
            df['cusum'] = df['diff'].cumsum()
            
            # Use CUSUM to detect change points
            mean_diff = df['diff'].mean()
            std_diff = df['diff'].std()
            
            if std_diff == 0:
                return patterns
            
            # Detect points where the cumulative sum deviates significantly
            threshold = 3 * std_diff
            change_points = df[(df['diff'] - mean_diff).abs() > threshold].index.tolist()
            
            for cp in change_points:
                if cp > 0 and cp < len(df) - 1:
                    before_mean = df.loc[:cp-1, 'value'].mean()
                    after_mean = df.loc[cp:, 'value'].mean()
                    
                    # Only consider significant step changes
                    if abs(after_mean - before_mean) > std_diff * 2:
                        pattern = DetectedPattern(
                            pattern_type=PatternType.STEP_CHANGE,
                            confidence=min(abs(after_mean - before_mean) / (std_diff * 3), 1.0),
                            start_time=df.loc[cp, 'timestamp'],
                            end_time=df.loc[cp, 'timestamp'] + timedelta(hours=1),
                            magnitude=abs(after_mean - before_mean),
                            description=f"Step change detected ({after_mean - before_mean:.2f} units)",
                            supporting_data={
                                'before_mean': before_mean,
                                'after_mean': after_mean,
                                'change_ratio': (after_mean / before_mean) if before_mean != 0 else float('inf')
                            }
                        )
                        patterns.append(pattern)
        
        except Exception as e:
            logger.error(f"Error in step change detection: {e}")
        
        return patterns


class UserBehaviorClusteringEngine:
    """Engine for clustering user behaviors and identifying patterns."""
    
    def __init__(self):
        """Initialize the user behavior clustering engine."""
        self.min_users = 20
        self.default_clusters = 3
        logger.info("User Behavior Clustering Engine initialized")
    
    async def cluster_users(self, user_data: List[Dict[str, Any]], 
                          features: List[str]) -> Dict[str, Any]:
        """
        Cluster users based on behavior features.
        
        Args:
            user_data: List of user data dictionaries
            features: List of feature names to use for clustering
            
        Returns:
            Dictionary with clustering results
        """
        if len(user_data) < self.min_users:
            return {"success": False, "reason": "Insufficient data for clustering"}
        
        try:
            # Extract features
            feature_data = []
            for user in user_data:
                user_features = []
                for feature in features:
                    if feature in user:
                        user_features.append(float(user[feature]))
                    else:
                        user_features.append(0.0)
                feature_data.append(user_features)
            
            # Convert to numpy array
            X = np.array(feature_data)
            
            # Standardize features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Determine optimal number of clusters (simplified)
            n_clusters = min(self.default_clusters, len(user_data) // 10)
            
            # Perform clustering
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            clusters = kmeans.fit_predict(X_scaled)
            
            # Analyze clusters
            cluster_stats = {}
            for i in range(n_clusters):
                cluster_indices = np.where(clusters == i)[0]
                cluster_users = [user_data[idx] for idx in cluster_indices]
                
                # Calculate cluster statistics
                cluster_stats[f"cluster_{i}"] = {
                    "size": len(cluster_users),
                    "percentage": len(cluster_users) / len(user_data) * 100,
                    "centroid": kmeans.cluster_centers_[i].tolist(),
                    "feature_means": {
                        feature: np.mean([user.get(feature, 0) for user in cluster_users])
                        for feature in features
                    }
                }
            
            return {
                "success": True,
                "n_clusters": n_clusters,
                "clusters": clusters.tolist(),
                "cluster_stats": cluster_stats,
                "features_used": features
            }
            
        except Exception as e:
            logger.error(f"Error in user clustering: {e}")
            return {"success": False, "reason": str(e)}
    
    async def identify_user_segments(self, clustering_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify and describe user segments from clustering results.
        
        Args:
            clustering_result: Result from cluster_users method
            
        Returns:
            List of user segment descriptions
        """
        if not clustering_result.get("success", False):
            return []
        
        segments = []
        
        try:
            cluster_stats = clustering_result.get("cluster_stats", {})
            features = clustering_result.get("features_used", [])
            
            for cluster_id, stats in cluster_stats.items():
                # Find distinguishing features
                feature_means = stats.get("feature_means", {})
                
                # Sort features by their values
                sorted_features = sorted(
                    [(f, v) for f, v in feature_means.items()],
                    key=lambda x: x[1],
                    reverse=True
                )
                
                # Get top features
                top_features = sorted_features[:3]
                bottom_features = sorted_features[-3:] if len(sorted_features) > 3 else []
                
                # Create segment description
                segment = {
                    "segment_id": cluster_id,
                    "size": stats["size"],
                    "percentage": stats["percentage"],
                    "key_characteristics": [
                        f"High {f}" for f, v in top_features
                    ],
                    "distinguishing_features": {
                        "high": {f: v for f, v in top_features},
                        "low": {f: v for f, v in bottom_features}
                    },
                    "description": self._generate_segment_description(top_features, bottom_features)
                }
                
                segments.append(segment)
        
        except Exception as e:
            logger.error(f"Error identifying user segments: {e}")
        
        return segments
    
    def _generate_segment_description(self, top_features: List[Tuple[str, float]], 
                                    bottom_features: List[Tuple[str, float]]) -> str:
        """Generate a human-readable segment description."""
        if not top_features:
            return "Undefined segment"
        
        # Create description based on top features
        top_feature_names = [self._humanize_feature_name(f) for f, _ in top_features[:2]]
        
        if len(top_feature_names) > 1:
            description = f"Users with high {top_feature_names[0]} and {top_feature_names[1]}"
        else:
            description = f"Users with high {top_feature_names[0]}"
        
        # Add bottom feature if available
        if bottom_features:
            bottom_feature = self._humanize_feature_name(bottom_features[0][0])
            description += f" but low {bottom_feature}"
        
        return description
    
    def _humanize_feature_name(self, feature_name: str) -> str:
        """Convert feature name to human-readable format."""
        return feature_name.replace('_', ' ')