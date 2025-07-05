from datetime import datetime
from typing import Dict, Any, List
import streamlit as st

def format_timestamp(timestamp_str: str) -> str:
    """
    Format timestamp string for display.
    
    Args:
        timestamp_str: Timestamp string from database
        
    Returns:
        Formatted timestamp string
    """
    try:
        # Parse the timestamp
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        
        # Format for display
        return dt.strftime("%Y-%m-%d %H:%M:%S")
        
    except Exception:
        return timestamp_str

def generate_summary_stats(analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate summary statistics from analysis data.
    
    Args:
        analyses: List of analysis dictionaries
        
    Returns:
        Dictionary containing summary statistics
    """
    
    if not analyses:
        return {
            "total_analyses": 0,
            "avg_score": 0.0,
            "ranking_distribution": {"Green": 0, "Amber": 0, "Red": 0},
            "most_common_issues": []
        }
    
    total_analyses = len(analyses)
    all_scores = []
    ranking_counts = {"Green": 0, "Amber": 0, "Red": 0}
    all_recommendations = []
    
    for analysis in analyses:
        evaluation_results = analysis.get('evaluation_results', {})
        
        for criterion_result in evaluation_results.values():
            all_scores.append(criterion_result.get('score', 0))
            ranking = criterion_result.get('ranking', 'Amber')
            if ranking in ranking_counts:
                ranking_counts[ranking] += 1
            
            # Collect recommendations
            recommendations = criterion_result.get('recommendations', [])
            all_recommendations.extend(recommendations)
    
    # Calculate average score
    avg_score = sum(all_scores) / len(all_scores) if all_scores else 0.0
    
    # Find most common recommendations/issues
    recommendation_counts = {}
    for rec in all_recommendations:
        recommendation_counts[rec] = recommendation_counts.get(rec, 0) + 1
    
    most_common_issues = sorted(
        recommendation_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]  # Top 5 most common issues
    
    return {
        "total_analyses": total_analyses,
        "avg_score": round(avg_score, 2),
        "ranking_distribution": ranking_counts,
        "most_common_issues": [issue[0] for issue in most_common_issues]
    }

def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Truncate text to specified length with ellipsis.
    
    Args:
        text: Text to truncate
        max_length: Maximum length before truncation
        
    Returns:
        Truncated text with ellipsis if needed
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - 3] + "..."

def get_ranking_color(ranking: str) -> str:
    """
    Get color code for ranking visualization.
    
    Args:
        ranking: Ranking value (Green, Amber, Red)
        
    Returns:
        Color code for visualization
    """
    color_map = {
        'Green': '#2E8B57',  # Sea Green
        'Amber': '#FF8C00',  # Dark Orange
        'Red': '#DC143C'     # Crimson
    }
    
    return color_map.get(ranking, '#808080')  # Gray as fallback

def get_ranking_emoji(ranking: str) -> str:
    """
    Get emoji for ranking display.
    
    Args:
        ranking: Ranking value (Green, Amber, Red)
        
    Returns:
        Emoji representing the ranking
    """
    emoji_map = {
        'Green': '🟢',
        'Amber': '🟡',
        'Red': '🔴'
    }
    
    return emoji_map.get(ranking, '⚪')

def validate_analysis_data(analysis_data: Dict[str, Any]) -> bool:
    """
    Validate analysis data structure.
    
    Args:
        analysis_data: Analysis data dictionary
        
    Returns:
        True if data structure is valid
    """
    required_fields = ['id', 'content', 'source_info', 'summary', 'evaluation_results', 'timestamp']
    
    for field in required_fields:
        if field not in analysis_data:
            return False
    
    # Validate evaluation_results structure
    evaluation_results = analysis_data['evaluation_results']
    if not isinstance(evaluation_results, dict):
        return False
    
    for criterion_result in evaluation_results.values():
        if not isinstance(criterion_result, dict):
            return False
        
        required_criterion_fields = ['ranking', 'score', 'explanation']
        for field in required_criterion_fields:
            if field not in criterion_result:
                return False
    
    return True

def export_analysis_to_text(analysis_data: Dict[str, Any]) -> str:
    """
    Export analysis data to formatted text.
    
    Args:
        analysis_data: Analysis data dictionary
        
    Returns:
        Formatted text representation of analysis
    """
    
    if not validate_analysis_data(analysis_data):
        return "Invalid analysis data"
    
    text_lines = []
    text_lines.append("=== RANKRIGHT ANALYSIS REPORT ===")
    text_lines.append(f"Analysis ID: {analysis_data['id']}")
    text_lines.append(f"Timestamp: {format_timestamp(analysis_data['timestamp'])}")
    text_lines.append(f"Source: {analysis_data['source_info']}")
    text_lines.append("")
    
    text_lines.append("SUMMARY:")
    text_lines.append(analysis_data['summary'])
    text_lines.append("")
    
    text_lines.append("EVALUATION RESULTS:")
    text_lines.append("-" * 50)
    
    for criterion_name, result in analysis_data['evaluation_results'].items():
        text_lines.append(f"\n{criterion_name.upper()}:")
        text_lines.append(f"Ranking: {get_ranking_emoji(result['ranking'])} {result['ranking']}")
        text_lines.append(f"Score: {result['score']}/10")
        text_lines.append(f"Explanation: {result['explanation']}")
        
        if result.get('key_findings'):
            text_lines.append("Key Findings:")
            for finding in result['key_findings']:
                text_lines.append(f"  • {finding}")
        
        if result.get('recommendations'):
            text_lines.append("Recommendations:")
            for recommendation in result['recommendations']:
                text_lines.append(f"  • {recommendation}")
        
        text_lines.append("")
    
    return "\n".join(text_lines)

def create_download_button(analysis_data: Dict[str, Any], button_text: str = "Download Report") -> None:
    """
    Create a download button for analysis report.
    
    Args:
        analysis_data: Analysis data dictionary
        button_text: Text for the download button
    """
    
    if not validate_analysis_data(analysis_data):
        st.error("Cannot download: Invalid analysis data")
        return
    
    report_text = export_analysis_to_text(analysis_data)
    filename = f"rankright_analysis_{analysis_data['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    st.download_button(
        label=button_text,
        data=report_text,
        file_name=filename,
        mime="text/plain",
        help="Download the complete analysis report as a text file"
    )
