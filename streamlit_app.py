"""
Streamlit UI for DocMind-AI Document Extraction.

This web interface provides:
- Document upload (PDF, DOCX, PPTX)
- Real-time extraction progress
- Multiple output format display
- Document preview and metadata
"""

import streamlit as st
import requests
import time
import json
from pathlib import Path
from typing import Optional, Dict, Any
import base64

# Configuration
st.set_page_config(
    page_title="DocMind-AI",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_URL = st.sidebar.text_input(
    "API URL",
    value="http://localhost:8001",
    help="FastAPI backend URL"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
    }
</style>
""", unsafe_allow_html=True)


def check_api_health() -> bool:
    """Check if API is accessible."""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


def upload_document(
    file: Any,
    output_format: str = "markdown",
    enable_vision: bool = True,
    preserve_hierarchy: bool = True
) -> Optional[str]:
    """Upload document to API and get job ID."""
    try:
        files = {"file": (file.name, file.getvalue(), file.type)}
        params = {
            "output_format": output_format,
            "enable_vision": enable_vision,
            "preserve_hierarchy": preserve_hierarchy
        }

        response = requests.post(
            f"{API_URL}/extract",
            files=files,
            params=params,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            return result.get("job_id")
        else:
            st.error(f"❌ Error: {response.status_code} {response.reason}")
            if response.text:
                st.error(f"Details: {response.text}")
            return None

    except requests.exceptions.ConnectionError:
        st.error(f"❌ Cannot connect to API at {API_URL}")
        st.info("Make sure the FastAPI backend is running on port 8001")
        return None
    except Exception as e:
        st.error(f"❌ Upload failed: {str(e)}")
        return None


def get_job_status(job_id: str) -> Optional[Dict[str, Any]]:
    """Get job status from API."""
    try:
        response = requests.get(f"{API_URL}/jobs/{job_id}", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"❌ Failed to get job status: {str(e)}")
        return None


def get_job_result(job_id: str) -> Optional[Dict[str, Any]]:
    """Get job result from API."""
    try:
        response = requests.get(f"{API_URL}/jobs/{job_id}/result", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"❌ Failed to get result: {str(e)}")
        return None


def display_metadata(metadata: Dict[str, Any]):
    """Display document metadata."""
    st.subheader("📋 Document Metadata")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"**Title:** {metadata.get('title', 'N/A')}")
        st.markdown(f"**Format:** {metadata.get('format', 'N/A').upper()}")

    with col2:
        st.markdown(f"**Pages:** {metadata.get('total_pages', 'N/A')}")
        st.markdown(f"**File Size:** {metadata.get('file_size_bytes', 0) / 1024:.2f} KB")

    with col3:
        if metadata.get('author'):
            st.markdown(f"**Author:** {metadata['author']}")
        if metadata.get('created_date'):
            st.markdown(f"**Created:** {metadata['created_date']}")


def display_processing_stats(result: Dict[str, Any]):
    """Display processing statistics."""
    st.subheader("📊 Processing Statistics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        duration = result.get('processing_time_seconds', 0)
        st.metric("Processing Time", f"{duration:.2f}s")

    with col2:
        cost = result.get('total_cost_usd', 0)
        st.metric("Total Cost", f"${cost:.4f}")

    with col3:
        pages = result.get('pages_processed', 0)
        st.metric("Pages Processed", pages)

    with col4:
        strategy_counts = result.get('strategy_counts', {})
        total_strategies = sum(strategy_counts.values())
        st.metric("Processing Strategies", total_strategies)

    # Strategy breakdown
    if strategy_counts:
        st.markdown("**Strategy Breakdown:**")
        strategy_cols = st.columns(len(strategy_counts))
        for idx, (strategy, count) in enumerate(strategy_counts.items()):
            with strategy_cols[idx]:
                st.markdown(f"*{strategy}*: {count}")


def display_extracted_content(content: str, format: str):
    """Display extracted content based on format."""
    st.subheader("📄 Extracted Content")

    if format == "markdown":
        st.markdown(content)
    elif format == "json":
        try:
            json_obj = json.loads(content)
            st.json(json_obj)
        except:
            st.code(content, language="json")
    elif format == "text":
        st.text(content)
    else:
        st.code(content)

    # Download button
    st.download_button(
        label=f"📥 Download {format.upper()}",
        data=content,
        file_name=f"extracted_content.{format}",
        mime="text/plain"
    )


def display_page_analyses(analyses: list):
    """Display page-by-page analysis."""
    if not analyses:
        return

    st.subheader("🔍 Page Analysis")

    with st.expander("View detailed page analysis", expanded=False):
        for analysis in analyses:
            page_num = analysis.get('page_number', 'Unknown')
            strategy = analysis.get('recommended_strategy', 'Unknown')
            cost = analysis.get('estimated_cost_usd', 0)

            st.markdown(f"**Page {page_num}** - Strategy: `{strategy}` - Cost: ${cost:.4f}")

            # Component details
            components = analysis.get('components', {})
            if components:
                cols = st.columns(4)
                with cols[0]:
                    st.caption(f"Text blocks: {components.get('text_blocks', 0)}")
                with cols[1]:
                    st.caption(f"Images: {components.get('images', 0)}")
                with cols[2]:
                    st.caption(f"Tables: {components.get('tables', 0)}")
                with cols[3]:
                    st.caption(f"Charts: {components.get('charts', 0)}")

            st.divider()


def main():
    """Main Streamlit application."""

    # Header
    st.markdown('<h1 class="main-header">📄 DocMind-AI</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p style="text-align: center; font-size: 1.2rem; color: #666;">Intelligent Document Extraction with Multimodal AI</p>',
        unsafe_allow_html=True
    )

    st.divider()

    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")

        # API Health Check
        if check_api_health():
            st.success("✅ API Connected")
        else:
            st.error("❌ API Not Connected")
            st.info("Start the API with:\n```bash\npython run_api.py --port 8001 --reload\n```")

        st.divider()

        # Extraction Settings
        st.subheader("Extraction Settings")

        output_format = st.selectbox(
            "Output Format",
            ["markdown", "json", "text"],
            help="Choose output format for extracted content"
        )

        enable_vision = st.checkbox(
            "Enable Vision Processing",
            value=True,
            help="Use multimodal AI for images, charts, and complex layouts"
        )

        preserve_hierarchy = st.checkbox(
            "Preserve Document Hierarchy",
            value=True,
            help="Maintain document structure (headings, sections, etc.)"
        )

        st.divider()

        st.caption("[API Docs](http://localhost:8001/docs)")
        st.caption("[ReDoc](http://localhost:8001/redoc)")

    # Main content area
    tab1, tab2 = st.tabs(["📤 Upload & Extract", "📊 Job History"])

    with tab1:
        # File Upload
        st.subheader("Upload Document")

        uploaded_file = st.file_uploader(
            "Choose a document",
            type=["pdf", "docx", "pptx"],
            help="Supported formats: PDF, DOCX, PPTX"
        )

        if uploaded_file is not None:
            # Display file info
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info(f"**Filename:** {uploaded_file.name}")
            with col2:
                st.info(f"**Size:** {uploaded_file.size / 1024:.2f} KB")
            with col3:
                st.info(f"**Type:** {uploaded_file.type}")

            st.divider()

            # Extract button
            if st.button("🚀 Start Extraction", type="primary", use_container_width=True):
                with st.spinner("Uploading document..."):
                    job_id = upload_document(
                        uploaded_file,
                        output_format=output_format,
                        enable_vision=enable_vision,
                        preserve_hierarchy=preserve_hierarchy
                    )

                if job_id:
                    st.success(f"✅ Job created: `{job_id}`")

                    # Progress tracking
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    max_wait = 300  # 5 minutes
                    start_time = time.time()

                    while time.time() - start_time < max_wait:
                        status = get_job_status(job_id)

                        if not status:
                            st.error("❌ Failed to get job status")
                            break

                        job_status = status.get('status', 'unknown')
                        progress = status.get('progress', 0)

                        progress_bar.progress(progress / 100)
                        status_text.text(f"Status: {job_status.upper()} - {progress}%")

                        if job_status == "completed":
                            status_text.success("✅ Extraction completed!")

                            # Get and display result
                            result = get_job_result(job_id)

                            if result:
                                st.divider()

                                # Display metadata
                                if result.get('metadata'):
                                    display_metadata(result['metadata'])
                                    st.divider()

                                # Display processing stats
                                display_processing_stats(result)
                                st.divider()

                                # Display page analyses
                                if result.get('page_analyses'):
                                    display_page_analyses(result['page_analyses'])
                                    st.divider()

                                # Display extracted content
                                if result.get('content'):
                                    display_extracted_content(result['content'], output_format)

                            break

                        elif job_status == "failed":
                            error_msg = status.get('error', 'Unknown error')
                            st.error(f"❌ Job failed: {error_msg}")
                            break

                        time.sleep(2)

                    else:
                        st.warning("⏱️ Job timeout - check status later")

    with tab2:
        st.subheader("Recent Jobs")
        st.info("Job history feature coming soon!")
        st.markdown("""
        In the future, this tab will show:
        - List of all extraction jobs
        - Job status and results
        - Ability to download past results
        - Job management (delete, retry, etc.)
        """)


if __name__ == "__main__":
    main()
