import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
import re
import io
import base64
import tempfile
from database import DatabaseManager
from document_processor import DocumentProcessor
from web_scraper import get_website_text_content
from azure_openai_client import AzureOpenAIClient
from evaluation_engine import EvaluationEngine
from utils import generate_summary_stats, format_timestamp

# Utility function for star ratings
def get_star_rating(score):
    """Convert score to star rating display"""
    stars = int(round(score / 2))  # Convert 0-10 to 0-5 stars
    filled_stars = "⭐" * stars
    empty_stars = "☆" * (5 - stars)
    return f"{filled_stars}{empty_stars}"

def auto_play_summary_audio(summary_text):
    """Generate and auto-play audio summary using pyttsx3"""
    try:
        import pyttsx3
        import subprocess
        
        # Initialize pyttsx3 engine
        engine = pyttsx3.init()
        
        # Configure speech properties
        engine.setProperty('rate', 150)    # Speed of speech
        engine.setProperty('volume', 0.9)  # Volume level (0.0 to 1.0)
        
        # Get available voices and set to a clear one if available
        voices = engine.getProperty('voices')
        if voices:
            # Try to use first available voice (usually system default)
            engine.setProperty('voice', voices[0].id)
        
        # Create temporary WAV file
        wav_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        wav_path = wav_file.name
        wav_file.close()
        
        # Save speech to WAV file
        engine.save_to_file(summary_text, wav_path)
        engine.runAndWait()
        
        try:
            # Try to convert WAV to MP3 using ffmpeg if available
            mp3_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            mp3_path = mp3_file.name
            mp3_file.close()
            
            subprocess.run(['ffmpeg', '-i', wav_path, '-codec:a', 'mp3', mp3_path, '-y'], 
                         check=True, capture_output=True)
            
            # Read MP3 file and encode for playback
            with open(mp3_path, 'rb') as audio_file:
                audio_bytes = audio_file.read()
                audio_base64 = base64.b64encode(audio_bytes).decode()
                
            # Create auto-playing audio HTML with MP3
            audio_html = f"""
            <audio controls autoplay style="width: 100%; margin-top: 10px;">
                <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                Your browser does not support the audio element.
            </audio>
            """
            
            # Clean up files
            os.unlink(mp3_path)
            os.unlink(wav_path)
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback to WAV if MP3 conversion fails
            with open(wav_path, 'rb') as audio_file:
                audio_bytes = audio_file.read()
                audio_base64 = base64.b64encode(audio_bytes).decode()
                
            # Create auto-playing audio HTML with WAV
            audio_html = f"""
            <audio controls autoplay style="width: 100%; margin-top: 10px;">
                <source src="data:audio/wav;base64,{audio_base64}" type="audio/wav">
                Your browser does not support the audio element.
            </audio>
            """
            
            # Clean up WAV file
            os.unlink(wav_path)
            
        st.markdown("🎧 **Auto-playing summary audio:**", unsafe_allow_html=True)
        st.markdown(audio_html, unsafe_allow_html=True)
        
    except ImportError:
        st.warning("Text-to-speech library not available. Please install pyttsx3.")
    except Exception as e:
        st.error(f"Audio generation failed: {str(e)}")
        st.info("Local text-to-speech service encountered an issue.")

def generate_ai_revised_document(analysis_data):
    """
    Generate an AI-revised version of the document based on evaluation criteria feedback.
    
    Args:
        analysis_data: Dictionary containing analysis results and evaluation criteria
        
    Returns:
        String containing the revised document content
    """
    try:
        # Get the original content
        original_content = analysis_data.get('content', '')
        evaluation_results = analysis_data.get('evaluation_results', {})
        
        # Create detailed feedback summary for AI revision
        feedback_summary = []
        improvement_areas = []
        
        for criterion, result in evaluation_results.items():
            score = result.get('score', 0)
            ranking = result.get('ranking', 'Unknown')
            feedback = result.get('feedback', 'No feedback available')
            recommendations = result.get('recommendations', [])
            
            # Focus on areas that need improvement (score < 8)
            if score < 8:
                feedback_summary.append(f"""
{criterion} (Score: {score}/10 - {ranking}):
{feedback}
Recommendations: {recommendations if isinstance(recommendations, str) else '; '.join(recommendations)}
""")
                improvement_areas.append(criterion)
        
        # If no areas need improvement, still provide a polished version
        if not feedback_summary:
            feedback_summary.append("Document shows good quality. Focus on minor enhancements for clarity and professionalism.")
        
        feedback_text = "\n".join(feedback_summary)
        
        # Create comprehensive revision prompt for actual content editing
        revision_prompt = f"""
You are an expert document editor. Please EDIT and REVISE the original document content by implementing the specific recommendations provided. 

ORIGINAL DOCUMENT CONTENT:
{original_content}

SPECIFIC AREAS TO IMPROVE AND IMPLEMENT:
{feedback_text}

INSTRUCTIONS:
- Take the original document content and edit it directly
- Implement each recommendation by modifying the actual text
- Restructure paragraphs, sentences, and sections as needed
- Add missing information where recommendations suggest
- Improve clarity by rewriting unclear sections
- Enhance organization by reordering content
- Make the content more actionable by adding specific steps or examples
- Maintain all the original information while improving its presentation

Please provide the COMPLETE REVISED DOCUMENT with all improvements implemented, not a summary. Keep the same document format and structure but with enhanced content quality.
"""
        
        # Use Azure OpenAI client for revision
        ai_client = AzureOpenAIClient()
        revised_content = ai_client.summarize_content(revision_prompt, max_length=2000)
        
        return revised_content
        
    except Exception as e:
        return f"Error generating revised document: {str(e)}"

def create_word_document(content, analysis_id):
    """
    Create a Word document from the revised content.
    
    Args:
        content: The revised document content
        analysis_id: The analysis ID for the document
        
    Returns:
        Bytes of the Word document
    """
    try:
        from docx import Document
        import io
        
        # Create a new Document
        doc = Document()
        
        # Add title
        title = doc.add_heading('Revised Document', 0)
        
        # Add analysis info
        doc.add_paragraph(f'Analysis ID: {analysis_id}')
        doc.add_paragraph(f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        doc.add_paragraph('')  # Empty line
        
        # Add the revised content
        # Split content into paragraphs and add them
        paragraphs = content.split('\n\n')
        for paragraph in paragraphs:
            if paragraph.strip():
                doc.add_paragraph(paragraph.strip())
        
        # Save to bytes
        doc_io = io.BytesIO()
        doc.save(doc_io)
        doc_io.seek(0)
        
        return doc_io.getvalue()
        
    except ImportError:
        # Fallback to text file if python-docx is not available
        return content.encode('utf-8')
    except Exception as e:
        # Fallback to text file on any error
        return content.encode('utf-8')

# Page configuration
st.set_page_config(
    page_title="RankRight - Document Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize components
@st.cache_resource
def init_components():
    db_manager = DatabaseManager()
    doc_processor = DocumentProcessor()
    ai_client = AzureOpenAIClient()
    eval_engine = EvaluationEngine(ai_client)
    return db_manager, doc_processor, ai_client, eval_engine

# Initialize global components
try:
    db_manager, doc_processor, ai_client, eval_engine = init_components()
    # Verify eval_engine has the required method
    if not hasattr(eval_engine, 'calculate_overall_ranking'):
        st.error("Evaluation engine initialization issue detected. Reinitializing...")
        st.cache_resource.clear()
        db_manager, doc_processor, ai_client, eval_engine = init_components()
except Exception as e:
    st.error(f"Component initialization failed: {e}")
    # Manual initialization as fallback
    db_manager = DatabaseManager()
    doc_processor = DocumentProcessor()
    ai_client = AzureOpenAIClient()
    eval_engine = EvaluationEngine(ai_client)

# Session state initialization
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False
if 'current_analysis_id' not in st.session_state:
    st.session_state.current_analysis_id = None

def main():
    # Remove top padding and add compact layout CSS
    st.markdown(
        """
        <style>
        .main > div {
            padding-top: 1rem;
        }
        .block-container {
            padding-top: 1rem;
        }
        .logo-container {
            margin-top: -10px;
            margin-left: -15px;
            padding: 0;
        }
        .main-title {
            margin-top: -10px;
            margin-bottom: 0px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    # Add company logo at the top left corner - compact layout
    col1, col2 = st.columns([1.3, 3.7])
    
    with col1:
        try:
            # Larger logo with custom container
            st.markdown('<div class="logo-container">', unsafe_allow_html=True)
            st.image("attached_assets/AskiTech2_1751736122642.png", width=220)
            st.markdown('</div>', unsafe_allow_html=True)
        except FileNotFoundError:
            st.write("**AskiTech**")  # Fallback text if logo not found
    
    with col2:
        st.markdown('<div class="main-title">', unsafe_allow_html=True)
        st.title("🎯 RankRight - Intelligent Document Analyzer")
        st.markdown("Analyze documents and Confluence pages with AI-powered insights")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Add separator line
    st.divider()
    
    # Sidebar for navigation
    with st.sidebar:
        st.header("Navigation")
        page = st.radio("Select Page", ["Home", "Analysis History", "Settings"])
    
    if page == "Home":
        show_home_page()
    elif page == "Analysis History":
        show_history_page()
    elif page == "Settings":
        show_settings_page()

def show_home_page():
    st.header("Document Analysis")
    
    # Input methods
    input_method = st.radio("Choose input method:", ["Upload Documents", "Confluence URL"])
    
    # Clear previous session state when switching methods
    if 'current_input_method' not in st.session_state:
        st.session_state.current_input_method = input_method
    elif st.session_state.current_input_method != input_method:
        # User switched methods, clear analysis state and cached content
        st.session_state.analysis_complete = False
        st.session_state.current_analysis_id = None
        st.session_state.current_input_method = input_method
        # Clear URL content when switching to document upload
        if 'url_content' in st.session_state:
            del st.session_state.url_content
        if 'url_source' in st.session_state:
            del st.session_state.url_source
    
    content_text = ""
    source_info = ""
    
    if input_method == "Upload Documents":
        uploaded_files = st.file_uploader(
            "Upload documents",
            type=['pdf', 'docx', 'txt'],
            accept_multiple_files=True,
            help="Supported formats: PDF, DOCX, TXT"
        )
        
        if uploaded_files:
            content_text = ""
            source_info = f"Uploaded files: {', '.join([f.name for f in uploaded_files])}"
            
            for uploaded_file in uploaded_files:
                try:
                    file_content = doc_processor.process_file(uploaded_file)
                    content_text += f"\n\n--- Content from {uploaded_file.name} ---\n{file_content}"
                except Exception as e:
                    st.error(f"Error processing {uploaded_file.name}: {str(e)}")
                    
    else:  # Confluence URL
        url = st.text_input("Enter Confluence page URL:")
        
        if url and st.button("Fetch Content"):
            try:
                with st.spinner("Fetching content from URL..."):
                    url_content = get_website_text_content(url)
                    # Store URL content in session state to prevent mixing with document content
                    st.session_state.url_content = url_content
                    st.session_state.url_source = f"URL: {url}"
                    st.success("Content fetched successfully!")
            except Exception as e:
                st.error(f"Error fetching content: {str(e)}")
        
        # Use URL content from session state if available
        if 'url_content' in st.session_state and st.session_state.url_content:
            content_text = st.session_state.url_content
            source_info = st.session_state.url_source
            
            # Add clear content button
            if st.button("Clear URL Content"):
                del st.session_state.url_content
                del st.session_state.url_source
                st.session_state.analysis_complete = False
                st.session_state.current_analysis_id = None
                st.rerun()
    
    # Analysis section
    if content_text:
        st.subheader("Content Preview")
        with st.expander("View extracted content", expanded=False):
            st.text_area("Content", content_text[:1000] + "..." if len(content_text) > 1000 else content_text, height=200, disabled=True)
        
        # Analysis button
        if st.button("🔍 Analyze Document", type="primary", use_container_width=True):
            perform_analysis(content_text, source_info)
    
    # Show analysis results if available
    if st.session_state.analysis_complete and st.session_state.current_analysis_id:
        show_analysis_results(st.session_state.current_analysis_id)

def perform_analysis(content_text, source_info):
    """Perform comprehensive document analysis"""
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Step 1: Generate summary
        status_text.text("Generating document summary...")
        progress_bar.progress(20)
        
        summary = ai_client.summarize_content(content_text)
        
        # Step 2: Run evaluation criteria
        status_text.text("Evaluating against criteria...")
        progress_bar.progress(40)
        
        evaluation_results = eval_engine.evaluate_content(content_text)
        
        # Step 3: Store results in database
        status_text.text("Storing analysis results...")
        progress_bar.progress(80)
        
        analysis_id = db_manager.store_analysis(
            content=content_text,
            source_info=source_info,
            summary=summary,
            evaluation_results=evaluation_results
        )
        
        # Complete
        progress_bar.progress(100)
        status_text.text("Analysis completed successfully!")
        
        # Update session state
        st.session_state.analysis_complete = True
        st.session_state.current_analysis_id = analysis_id
        
        st.success("✅ Analysis completed! Results are displayed below.")
        st.rerun()
        
    except Exception as e:
        error_msg = str(e)
        progress_bar.empty()
        status_text.empty()
        
        # Check for Azure firewall/networking issues
        if "403" in error_msg and ("Virtual Network" in error_msg or "Firewall" in error_msg):
            st.error("🚫 Azure OpenAI Access Blocked")
            
            with st.expander("🔧 Quick Fix Instructions", expanded=True):
                st.markdown("""
                **Your Azure OpenAI service has firewall rules blocking this connection.**
                
                ### Option 1: Allow All Networks (Simplest)
                1. Go to **Azure Portal** (portal.azure.com)
                2. Find your **Azure OpenAI resource**
                3. Click **"Networking"** in the left sidebar
                4. Change from "Selected networks" to **"All networks"**
                5. Click **"Save"** and wait 2-3 minutes
                
                ### Option 2: Add Current IP (Temporary)
                - Add IP: `34.9.104.227` to your allowed list
                - Note: This IP changes when Replit restarts
                
                ### Option 3: Check Virtual Network Settings
                - Your error suggests VNet is configured
                - Go to Networking → Public network access
                - Change to "Enabled from all networks"
                """)
                
            st.info("After fixing the Azure settings, try uploading and analyzing your document again.")
            
        else:
            st.error(f"Analysis failed: {error_msg}")

def show_analysis_results(analysis_id):
    """Display analysis results in tabs"""
    
    # Get analysis data
    analysis_data = db_manager.get_analysis(analysis_id)
    if not analysis_data:
        st.error("Analysis data not found")
        return
    
    # Calculate overall ranking - with fallback method
    try:
        # Try using the evaluation engine method
        overall_ranking = eval_engine.calculate_overall_ranking(analysis_data['evaluation_results'])
    except Exception as e:
        # Fallback: Calculate overall ranking manually
        evaluation_results = analysis_data['evaluation_results']
        ranking_counts = {"Green": 0, "Amber": 0, "Red": 0}
        total_score = 0
        criterion_count = 0
        
        for criterion_name, result in evaluation_results.items():
            ranking = result.get("ranking", "Red")
            score = result.get("score", 0)
            ranking_counts[ranking] += 1
            total_score += score
            criterion_count += 1
        
        average_score = total_score / criterion_count if criterion_count > 0 else 0
        total_criteria = len(evaluation_results)
        green_percentage = (ranking_counts["Green"] / total_criteria) * 100
        red_percentage = (ranking_counts["Red"] / total_criteria) * 100
        
        # Determine overall ranking
        if red_percentage >= 50:
            overall_ranking_value = "Red"
        elif green_percentage >= 70:
            overall_ranking_value = "Green"
        elif red_percentage == 0 and ranking_counts["Green"] >= ranking_counts["Amber"]:
            overall_ranking_value = "Green"
        else:
            overall_ranking_value = "Amber"
        
        # Generate summary
        if overall_ranking_value == "Green":
            summary = f"Excellent document quality with {ranking_counts['Green']}/{total_criteria} criteria rated Green"
        elif overall_ranking_value == "Amber":
            summary = f"Good document quality with room for improvement in {ranking_counts['Amber'] + ranking_counts['Red']} areas"
        else:
            summary = f"Document needs significant improvement with {ranking_counts['Red']} critical issues identified"
        
        overall_ranking = {
            "overall_ranking": overall_ranking_value,
            "overall_score": round(average_score, 1),
            "ranking_breakdown": ranking_counts,
            "summary": summary,
            "green_percentage": round(green_percentage, 1),
            "amber_percentage": round((ranking_counts["Amber"] / total_criteria) * 100, 1),
            "red_percentage": round(red_percentage, 1)
        }
    
    # Overall ranking section in table format
    st.subheader("🎯 Overall Ranking")
    
    # Create overall ranking table
    ranking_colors = {'Green': '🟢', 'Amber': '🟡', 'Red': '🔴'}
    ranking_shape = ranking_colors.get(overall_ranking['overall_ranking'], '⚪')
    
    # Make the rank symbol bigger (use multiple symbols for bigger appearance)
    big_ranking_shape = ranking_shape * 3  # Triple the symbol for bigger appearance
    
    # Get summary text from Document Summary section
    summary_text = analysis_data['summary']
    if len(summary_text) > 500:
        # Truncate to 500 words while preserving readability
        words = summary_text.split()[:75]  # Approximately 500 characters
        summary_text = ' '.join(words) + "..."
    
    # Create table data
    overall_ranking_data = [{
        'Ranking': big_ranking_shape,
        'Summary': summary_text
    }]
    
    overall_ranking_df = pd.DataFrame(overall_ranking_data)
    
    # Display the table without headers using HTML for better control
    st.markdown("""
    <style>
    .ranking-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 16px;
    }
    .ranking-table td {
        padding: 15px;
        border: none;
        vertical-align: top;
    }
    .ranking-symbol {
        font-size: 48px;
        text-align: center;
        width: 100px;
    }
    .ranking-summary {
        font-size: 16px;
        line-height: 1.5;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Create custom HTML table
    table_html = f"""
    <table class="ranking-table">
        <tr>
            <td class="ranking-symbol" title="Average Score: {overall_ranking['overall_score']:.1f}/10">
                {ranking_shape}
            </td>
            <td class="ranking-summary">
                {summary_text}
            </td>
        </tr>
    </table>
    """
    
    st.markdown(table_html, unsafe_allow_html=True)
    
    # Auto-play summary audio after analysis completion
    audio_key = f"audio_played_{analysis_id}"
    if audio_key not in st.session_state:
        st.session_state[audio_key] = False
    
    if not st.session_state[audio_key]:
        st.session_state[audio_key] = True
        # Add a small delay and then auto-play the summary
        st.markdown("---")
        auto_play_summary_audio(summary_text)
    
    # Evaluation results in star rating table
    st.subheader("📊 Evaluation Results")
    
    # Create evaluation summary table
    evaluation_data = []
    for criterion_name, result in analysis_data['evaluation_results'].items():
        evaluation_data.append({
            'Criterion': criterion_name,
            'Rating': get_star_rating(result['score']),
            'Score': f"{result['score']:.1f}/10"
        })
    
    evaluation_df = pd.DataFrame(evaluation_data)
    
    # Display the table
    st.dataframe(
        evaluation_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Criterion": st.column_config.TextColumn("Evaluation Criteria", width="medium"),
            "Rating": st.column_config.TextColumn("Star Rating", width="medium"),
            "Score": st.column_config.TextColumn("Score", width="small")
        }
    )
    
    # Detailed analysis in accordion format
    st.subheader("🔍 Detailed Analysis")
    
    for criterion_name, result in analysis_data['evaluation_results'].items():
        with st.expander(f"➕ {criterion_name} - {result['ranking']} ({result['score']:.1f}/10)"):
            # Display detailed analysis
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.metric("Star Rating", get_star_rating(result['score']))
                st.metric("Ranking", f"{result['ranking']}")
                st.metric("Score", f"{result['score']:.1f}/10")
                
            with col2:
                st.write("**Analysis:**")
                st.write(result.get('analysis', 'No detailed analysis available'))
                
                if 'recommendations' in result:
                    st.write("**Recommendations:**")
                    recommendations = result['recommendations']
                    if isinstance(recommendations, list):
                        for rec in recommendations:
                            st.write(f"• {rec}")
                    else:
                        st.write(recommendations)
    
    # Conclusion Section
    st.subheader("🎯 Final Conclusion")
    
    # Define colors and overall ranking
    ranking_colors = {'Green': '🟢', 'Amber': '🟡', 'Red': '🔴'}
    ranking_color = overall_ranking['overall_ranking']
    
    if ranking_color == 'Green':
        st.success(f"""
        **🎉 Excellent Document Quality**
        
        Overall Ranking: {ranking_colors[ranking_color]} **{ranking_color}**
        
        {overall_ranking['summary']}
        
        **Key Metrics:**
        - Average Score: **{overall_ranking['overall_score']}/10**
        - Green Criteria: **{overall_ranking['ranking_breakdown']['Green']}/{len(analysis_data['evaluation_results'])}**
        - Areas for Improvement: **{overall_ranking['ranking_breakdown']['Amber'] + overall_ranking['ranking_breakdown']['Red']}**
        """)
    elif ranking_color == 'Amber':
        st.warning(f"""
        **⚠️ Good Document with Room for Improvement**
        
        Overall Ranking: {ranking_colors[ranking_color]} **{ranking_color}**
        
        {overall_ranking['summary']}
        
        **Key Metrics:**
        - Average Score: **{overall_ranking['overall_score']}/10**
        - Green Criteria: **{overall_ranking['ranking_breakdown']['Green']}/{len(analysis_data['evaluation_results'])}**
        - Areas Needing Attention: **{overall_ranking['ranking_breakdown']['Amber'] + overall_ranking['ranking_breakdown']['Red']}**
        """)
    else:  # Red
        st.error(f"""
        **🚨 Document Requires Significant Improvement**
        
        Overall Ranking: {ranking_colors[ranking_color]} **{ranking_color}**
        
        {overall_ranking['summary']}
        
        **Key Metrics:**
        - Average Score: **{overall_ranking['overall_score']}/10**
        - Critical Issues: **{overall_ranking['ranking_breakdown']['Red']}**
        - Total Areas for Improvement: **{overall_ranking['ranking_breakdown']['Amber'] + overall_ranking['ranking_breakdown']['Red']}**
        """)
    
    # Action recommendations
    st.subheader("🎯 Recommended Next Steps")
    if ranking_color == 'Green':
        st.info("✅ This document meets high quality standards. Consider minor refinements based on individual criterion feedback.")
    elif ranking_color == 'Amber':
        st.info("📈 Focus on improving Amber and Red criteria. Prioritize the Red issues first for maximum impact.")
    else:
        st.info("🔧 Immediate action required. Address all Red criteria before proceeding. Consider comprehensive document revision.")
    
    # Auto-generate AI-revised document
    revised_document_key = f'revised_document_{analysis_id}'
    if revised_document_key not in st.session_state:
        with st.spinner("Generating AI-revised document based on evaluation feedback..."):
            try:
                revised_document = generate_ai_revised_document(analysis_data)
                st.session_state[revised_document_key] = revised_document
            except Exception as e:
                st.error(f"Failed to generate revised document: {str(e)}")
                st.session_state[revised_document_key] = "Error generating revised document. Please try again."
    
    # Display AI-revised document
    st.subheader("📄 AI-Revised Document")
    st.markdown("*Based on the evaluation criteria feedback, here's an improved version of your document:*")
    
    revised_content = st.session_state.get(revised_document_key, "")
    
    # Display in expandable text area
    with st.expander("View AI-Revised Document", expanded=True):
        st.text_area("Revised Content", revised_content, height=400, disabled=True, key=f"revised_text_{analysis_id}")
    
    # Download button for revised document as Word file
    col1, col2 = st.columns([1, 2])
    with col1:
        # Create Word document
        word_doc_bytes = create_word_document(revised_content, analysis_id)
        st.download_button(
            label="📥 Download Revised Document (Word)",
            data=word_doc_bytes,
            file_name=f"revised_document_{analysis_id}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )
    with col2:
        st.markdown("*The revised document addresses all feedback points from the evaluation criteria.*")

def show_history_page():
    """Display analysis history"""
    st.header("📚 Analysis History")
    
    # Get all analyses
    analyses = db_manager.get_all_analyses()
    
    if not analyses:
        st.info("No analyses found. Start by analyzing a document on the Home page.")
        return
    
    # Create summary table
    df_data = []
    for analysis in analyses:
        df_data.append({
            'ID': analysis['id'],
            'Source': analysis['source_info'][:50] + "..." if len(analysis['source_info']) > 50 else analysis['source_info'],
            'Timestamp': format_timestamp(analysis['timestamp']),
            'Summary': analysis['summary'][:100] + "..." if len(analysis['summary']) > 100 else analysis['summary']
        })
    
    df = pd.DataFrame(df_data)
    
    # Display table with selection
    selected_indices = st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row"
    )
    
    # Show detailed view for selected analysis
    if selected_indices['selection']['rows']:
        selected_idx = selected_indices['selection']['rows'][0]
        selected_id = df.iloc[selected_idx]['ID']
        
        st.divider()
        st.subheader(f"Analysis Details - ID: {selected_id}")
        show_analysis_results(selected_id)

def show_settings_page():
    """Display settings and configuration"""
    st.header("⚙️ Settings")
    
    # API Configuration
    st.subheader("API Configuration")
    
    # Azure OpenAI settings
    with st.expander("Azure OpenAI Configuration"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Basic Configuration**")
            endpoint = st.text_input("Azure OpenAI Endpoint", value=os.getenv("AZURE_OPENAI_ENDPOINT", ""))
            api_key = st.text_input("API Key", type="password", value="***" if os.getenv("AZURE_OPENAI_API_KEY") else "")
            api_version = st.text_input("API Version", value=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"))
            deployment_name = st.text_input("Deployment Name", value=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "RankRightAnalyzer"))
        
        with col2:
            st.markdown("**Private Endpoint Configuration**")
            use_private_endpoint = st.checkbox(
                "Use Private Endpoint", 
                value=os.getenv("AZURE_OPENAI_USE_PRIVATE_ENDPOINT", "false").lower() == "true",
                help="Enable to connect via private endpoint instead of public internet"
            )
            
            private_ip = st.text_input(
                "Private Endpoint IP", 
                value=os.getenv("AZURE_OPENAI_PRIVATE_IP", ""),
                disabled=not use_private_endpoint,
                help="IP address of the private endpoint"
            )
            
            private_fqdn = st.text_input(
                "Private Endpoint FQDN (Optional)", 
                value=os.getenv("AZURE_OPENAI_PRIVATE_FQDN", ""),
                disabled=not use_private_endpoint,
                help="Custom FQDN for private endpoint (leave empty to use IP directly)"
            )
        
        # Save configuration button
        if st.button("💾 Save Configuration", key="save_config"):
            try:
                from config_manager import ConfigManager
                config_mgr = ConfigManager()
                
                # Update configuration
                config_mgr.update_azure_openai_config(
                    endpoint=endpoint,
                    api_version=api_version,
                    deployment_name=deployment_name,
                    use_private_endpoint=use_private_endpoint,
                    private_endpoint_ip=private_ip,
                    private_endpoint_fqdn=private_fqdn
                )
                
                st.success("✅ Configuration saved successfully!")
                st.info("""
                **Next Steps:**
                1. Restart the application to apply changes
                2. Test the connection using the button below
                3. If using private endpoint, ensure network connectivity to the private IP
                """)
                
            except Exception as e:
                st.error(f"❌ Failed to save configuration: {str(e)}")
        
        # Configuration check
        st.subheader("Configuration Status")
        
        # Show connection information
        try:
            from azure_openai_client import AzureOpenAIClient
            client = AzureOpenAIClient()
            conn_info = client.get_connection_info()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Basic Configuration**")
                if conn_info["endpoint"]:
                    st.info(f"✅ Endpoint: {conn_info['endpoint']}")
                else:
                    st.error("❌ Azure OpenAI Endpoint is missing")
                    
                if os.getenv("AZURE_OPENAI_API_KEY"):
                    st.info("✅ API Key is configured")
                else:
                    st.error("❌ Azure OpenAI API Key is missing")
                    
                if conn_info["deployment_name"]:
                    st.info(f"✅ Deployment: {conn_info['deployment_name']}")
                else:
                    st.error("❌ Deployment Name is missing")
            
            with col2:
                st.markdown("**Connection Information**")
                if conn_info["use_private_endpoint"]:
                    st.info("🔒 Private Endpoint: Enabled")
                    st.info(f"📍 Effective Endpoint: {conn_info['effective_endpoint']}")
                    if conn_info["private_endpoint_ip"]:
                        st.info(f"🌐 Private IP: {conn_info['private_endpoint_ip']}")
                    if conn_info["private_endpoint_fqdn"]:
                        st.info(f"🏷️ Private FQDN: {conn_info['private_endpoint_fqdn']}")
                else:
                    st.info("🌐 Private Endpoint: Disabled (Using public endpoint)")
                    
        except Exception as e:
            st.error(f"❌ Configuration check failed: {str(e)}")
            
        config_issues = []
        if not endpoint:
            config_issues.append("❌ Azure OpenAI Endpoint is missing")
        if not os.getenv("AZURE_OPENAI_API_KEY"):
            config_issues.append("❌ Azure OpenAI API Key is missing")
        if not deployment_name:
            config_issues.append("❌ Deployment Name is missing")
        if use_private_endpoint and not private_ip:
            config_issues.append("❌ Private Endpoint IP is required when private endpoint is enabled")
            
        if config_issues:
            for issue in config_issues:
                st.error(issue)
        
        if st.button("🔍 Test Connection"):
            with st.spinner("Testing Azure OpenAI connection..."):
                try:
                    test_client = AzureOpenAIClient()
                    conn_info = test_client.get_connection_info()
                    
                    # Show connection details
                    st.info(f"🔗 Testing connection to: {conn_info['effective_endpoint']}")
                    if conn_info['use_private_endpoint']:
                        st.info(f"🔒 Using private endpoint via IP: {conn_info['private_endpoint_ip']}")
                    
                    success, message = test_client.test_connection()
                    
                    if success:
                        st.success("✅ Connection successful! Azure OpenAI is working perfectly.")
                        st.balloons()
                    else:
                        st.error(f"❌ Connection failed: {message}")
                        
                except Exception as e:
                    st.error(f"❌ Connection test failed: {str(e)}")
    
    # Network Information
    st.subheader("Network Information")
    with st.expander("Current Network Details"):
        try:
            import requests
            current_ip = requests.get('https://ifconfig.me', timeout=5).text.strip()
            st.info(f"**Current IP Address**: {current_ip}")
            st.warning("⚠️ This IP is dynamic and changes when Replit restarts")
            
            st.markdown(f"""
            **To whitelist this IP in Azure OpenAI:**
            1. Go to Azure Portal → Your OpenAI Resource → Networking
            2. Select "Selected networks"
            3. Add IP address: `{current_ip}`
            4. Click Save and wait 2-3 minutes
            
            **Note**: You'll need to update this when the IP changes.
            """)
        except Exception as e:
            st.error(f"Could not detect current IP: {str(e)}")
    
    # Database settings
    st.subheader("Database")
    with st.expander("Database Information"):
        st.info("Using SQLite database for local storage")
        
        # Database stats
        analyses_count = len(db_manager.get_all_analyses())
        st.metric("Total Analyses", analyses_count)
        
        if st.button("Clear All Data", type="secondary"):
            if st.warning("This will delete all analysis data. Are you sure?"):
                db_manager.clear_all_data()
                st.success("All data cleared!")
                st.rerun()
    
    # Evaluation Criteria
    st.subheader("Evaluation Criteria")
    criteria = eval_engine.get_criteria_descriptions()
    
    for i, (name, description) in enumerate(criteria.items(), 1):
        with st.expander(f"Criterion {i}: {name}"):
            st.write(description)

if __name__ == "__main__":
    main()
