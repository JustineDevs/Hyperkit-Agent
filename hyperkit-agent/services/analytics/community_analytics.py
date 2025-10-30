"""
Analytics and Quality Scoring for Community Artifacts

Tracks Community upload metrics, implements quality scoring,
and provides analytics for RAG prioritization.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import json
from collections import defaultdict

logger = logging.getLogger(__name__)


class CommunityAnalytics:
    """
    Analytics system for Community uploads.
    
    Features:
    - Upload metrics tracking
    - Quality scoring
    - Usage analytics
    - RAG prioritization data
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize analytics system"""
        self.config = config or {}
        self.analytics_data: Dict[str, Any] = {
            'uploads': [],
            'quality_scores': {},
            'usage_stats': {},
            'popular_artifacts': {},
            'time_series': defaultdict(list)
        }
        
        # Load analytics data
        self._load_analytics_data()
    
    def _load_analytics_data(self):
        """Load analytics data from disk"""
        try:
            analytics_file = Path("data/analytics/community_analytics.json")
            if analytics_file.exists():
                with open(analytics_file, 'r') as f:
                    self.analytics_data = json.load(f)
        except Exception as e:
            logger.warning(f"Could not load analytics data: {e}")
    
    def _save_analytics_data(self):
        """Save analytics data to disk"""
        try:
            analytics_dir = Path("data/analytics")
            analytics_dir.mkdir(parents=True, exist_ok=True)
            
            analytics_file = analytics_dir / "community_analytics.json"
            with open(analytics_file, 'w') as f:
                json.dump(self.analytics_data, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save analytics data: {e}")
    
    def record_upload(
        self,
        artifact_id: str,
        artifact_type: str,
        user_id: Optional[str] = None,
        metadata: Dict[str, Any] = None
    ):
        """Record an upload event"""
        upload_event = {
            'artifact_id': artifact_id,
            'artifact_type': artifact_type,
            'user_id': user_id,
            'timestamp': datetime.utcnow().isoformat(),
            'metadata': metadata or {}
        }
        
        self.analytics_data['uploads'].append(upload_event)
        
        # Track time series
        date_key = datetime.utcnow().strftime('%Y-%m-%d')
        self.analytics_data['time_series'][date_key].append({
            'type': 'upload',
            'artifact_id': artifact_id
        })
        
        self._save_analytics_data()
    
    def record_usage(self, artifact_id: str, usage_type: str = 'retrieve'):
        """Record artifact usage (retrieval, download, etc.)"""
        if artifact_id not in self.analytics_data['usage_stats']:
            self.analytics_data['usage_stats'][artifact_id] = {
                'retrievals': 0,
                'downloads': 0,
                'last_used': None
            }
        
        stats = self.analytics_data['usage_stats'][artifact_id]
        stats['last_used'] = datetime.utcnow().isoformat()
        
        if usage_type == 'retrieve':
            stats['retrievals'] += 1
        elif usage_type == 'download':
            stats['downloads'] += 1
        
        # Track in time series
        date_key = datetime.utcnow().strftime('%Y-%m-%d')
        self.analytics_data['time_series'][date_key].append({
            'type': usage_type,
            'artifact_id': artifact_id
        })
        
        self._save_analytics_data()
    
    def calculate_quality_score(self, artifact_id: str, metadata: Dict[str, Any]) -> float:
        """
        Calculate quality score for an artifact.
        
        Factors:
        - Compilation success
        - Audit results
        - Usage frequency
        - Upvotes/flags
        - Age (older = more trusted)
        """
        score = 0.5  # Base score
        
        # Compilation success
        if metadata.get('compilation_success'):
            score += 0.15
        
        # Audit severity
        audit_severity = metadata.get('audit_severity', 'unknown')
        if audit_severity == 'low':
            score += 0.15
        elif audit_severity == 'medium':
            score += 0.08
        
        # Usage frequency
        usage_stats = self.analytics_data['usage_stats'].get(artifact_id, {})
        total_usage = usage_stats.get('retrievals', 0) + usage_stats.get('downloads', 0)
        if total_usage > 10:
            score += 0.1
        elif total_usage > 5:
            score += 0.05
        
        # Upvotes (if available)
        upvotes = metadata.get('upvotes', 0)
        if upvotes > 5:
            score += 0.1
        elif upvotes > 0:
            score += 0.05
        
        # Age bonus (older artifacts slightly more trusted)
        timestamp = metadata.get('timestamp')
        if timestamp:
            try:
                upload_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                age_days = (datetime.utcnow() - upload_date.replace(tzinfo=None)).days
                if age_days > 30:
                    score += 0.05
            except Exception:
                pass
        
        # Store score
        self.analytics_data['quality_scores'][artifact_id] = score
        self._save_analytics_data()
        
        return max(0.0, min(1.0, score))
    
    def get_popular_artifacts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most popular artifacts"""
        # Sort by usage frequency
        sorted_artifacts = sorted(
            self.analytics_data['usage_stats'].items(),
            key=lambda x: x[1]['retrievals'] + x[1]['downloads'],
            reverse=True
        )
        
        return [
            {
                'artifact_id': artifact_id,
                'usage_stats': stats,
                'quality_score': self.analytics_data['quality_scores'].get(artifact_id, 0.5)
            }
            for artifact_id, stats in sorted_artifacts[:limit]
        ]
    
    def get_analytics_summary(self) -> Dict[str, Any]:
        """Get analytics summary"""
        total_uploads = len(self.analytics_data['uploads'])
        
        # Uploads by type
        uploads_by_type = defaultdict(int)
        for upload in self.analytics_data['uploads']:
            uploads_by_type[upload['artifact_type']] += 1
        
        # Time range stats
        last_7_days = datetime.utcnow() - timedelta(days=7)
        recent_uploads = [
            u for u in self.analytics_data['uploads']
            if datetime.fromisoformat(u['timestamp'].replace('Z', '+00:00')).replace(tzinfo=None) > last_7_days
        ]
        
        return {
            'total_uploads': total_uploads,
            'uploads_by_type': dict(uploads_by_type),
            'recent_uploads_7d': len(recent_uploads),
            'total_artifacts_tracked': len(self.analytics_data['usage_stats']),
            'average_quality_score': sum(self.analytics_data['quality_scores'].values()) / len(self.analytics_data['quality_scores']) if self.analytics_data['quality_scores'] else 0.0,
            'top_artifacts': self.get_popular_artifacts(5)
        }

