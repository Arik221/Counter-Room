import streamlit as st
import os
import sys
import time
import mimetypes
from datetime import datetime
from PIL import Image
from io import BytesIO
import json
import tempfile
from typing import List, Dict, Any
from dotenv import load_dotenv
import time

# Load environment variables from .env file
load_dotenv()

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from google import genai
from google.genai import types
from src.courtroom_viz.crew import LegalAnalysisCrew

# ============================================================================
# STREAMLIT PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="CourtroomViz - Legal Evidence Visualizer",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .step-box {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #007bff;
        margin: 1rem 0;
    }
    
    .success-box {
        background: #d4edda;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    
    .warning-box {
        background: #fff3cd;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #ffc107;
        margin: 1rem 0;
    }
    
    .error-box {
        background: #f8d7da;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #dc3545;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# GEMINI CLIENT INITIALIZATION
# ============================================================================

@st.cache_resource
def initialize_gemini_client():
    """Initialize Gemini client with API key"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.error("⚠️ Please add your Gemini API key to the .env file")
        st.info("""
        **Setup Instructions:**
        1. Create a `.env` file in the project root
        2. Add your API key: `GEMINI_API_KEY=your_api_key_here`
        3. Get your free API key at: https://ai.studio/banana
        """)
        st.stop()
    
    try:
        client = genai.Client(api_key=api_key)
        # Test the client
        test_response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Test connection"
        )
        return client
    except Exception as e:
        st.error(f"Failed to initialize Gemini client: {e}")
        st.stop()

# ============================================================================
# GEMINI GENERATION ENGINE
# ============================================================================

class GeminiVisualizationEngine:
    def __init__(self, client):
        self.client = client
        self.model_image = "gemini-2.5-flash-image-preview"
        self.model_text = "gemini-2.5-flash"

    def upload_file_to_gemini(self, file_path: str) -> Any:
        """Upload file to Gemini Files API"""
        try:
            uploaded_file = self.client.files.upload(file=file_path)
            return uploaded_file
        except Exception as e:
            st.error(f"Failed to upload file: {e}")
            return None

    def process_files_with_gemini(self, uploaded_files: List) -> str:
        """Process uploaded files (PDF, TXT) with Gemini"""
        all_content = ""
        
        for uploaded_file in uploaded_files:
            if uploaded_file.type == "application/pdf":
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    tmp_file.write(uploaded_file.read())
                    tmp_file_path = tmp_file.name
                
                try:
                    # Upload to Gemini Files API
                    gemini_file = self.upload_file_to_gemini(tmp_file_path)
                    if gemini_file:
                        # Process with Gemini
                        response = self.client.models.generate_content(
                            model=self.model_text,
                            contents=[
                                "Extract and summarize all relevant information from this legal document. Focus on: 1) Facts and evidence, 2) Timeline of events, 3) People and locations involved, 4) Physical descriptions and measurements, 5) Any technical or forensic details.",
                                gemini_file
                            ]
                        )
                        if response and hasattr(response, 'text'):
                            all_content += f"\n\n--- Document: {uploaded_file.name} ---\n"
                            all_content += response.text
                
                finally:
                    # Clean up temp file
                    os.unlink(tmp_file_path)
            
            elif uploaded_file.type == "text/plain":
                # Process text files directly
                try:
                    # Read text content
                    text_content = uploaded_file.read().decode('utf-8')
                    
                    # Process with Gemini for analysis
                    response = self.client.models.generate_content(
                        model=self.model_text,
                        contents=[
                            "Analyze this legal document text and extract key information. Focus on: 1) Facts and evidence, 2) Timeline of events, 3) People and locations involved, 4) Physical descriptions and measurements, 5) Any technical or forensic details.",
                            text_content
                        ]
                    )
                    if response and hasattr(response, 'text'):
                        all_content += f"\n\n--- Document: {uploaded_file.name} ---\n"
                        all_content += response.text
                
                except Exception as e:
                    st.error(f"Error processing text file {uploaded_file.name}: {e}")
                    # Fallback: use raw text content
                    all_content += f"\n\n--- Document: {uploaded_file.name} (Raw Text) ---\n"
                    all_content += text_content
        
        return all_content

    def generate_scene_visualization(self, scene_analysis: str, style: str = "professional") -> List[str]:
        """Generate crime scene visualizations from scene analysis"""
        
        # Define style prompts for crime scene reconstruction
        style_prompts = {
            "professional": "photorealistic, professional forensic documentation style, high contrast lighting, crime scene reconstruction",
            "technical": "technical forensic diagram style, precise measurements, evidence documentation quality, scientific accuracy",
            "dramatic": "dramatic crime scene lighting, cinematic forensic angles, emotionally compelling but accurate presentation",
            "jury_friendly": "clear, easy to understand crime scene reconstruction, simplified but accurate representation"
        }
        
        base_prompt = f"""
        Create a highly detailed, {style_prompts.get(style, style_prompts['professional'])} crime scene visualization based on this analysis:
        
        {scene_analysis}
        
        Requirements:
        - Photorealistic crime scene reconstruction quality
        - Accurate spatial relationships and proportions  
        - Professional forensic documentation style
        - Clear visual storytelling of the crime scene
        - Maintain factual accuracy of evidence and victim positions
        - Include relevant environmental context
        - Night lighting with flashlight illumination
        - NO courtroom, judge, jury, or legal proceedings
        - This is the actual CRIME SCENE, not a courtroom presentation
        """
        
        try:
            response = self.client.models.generate_content(
                model=self.model_image,
                contents=[base_prompt],
                config=types.GenerateContentConfig(
                    response_modalities=['IMAGE', 'TEXT']
                )
            )
            
            # Extract and save images
            saved_files = self._extract_and_save_images(response, "crime_scene_viz")
            return saved_files
            
        except Exception as e:
            st.error(f"Failed to generate visualization: {e}")
            return []

    def generate_images_from_plan(self, image_generation_plan) -> List[str]:
        """Generate images based on AI-generated image plan"""
        
        if not image_generation_plan:
            st.error("No image generation plan provided")
            return []
        
        # Handle both Pydantic model and dictionary
        if hasattr(image_generation_plan, 'image_specifications'):
            # Pydantic model
            image_specs = image_generation_plan.image_specifications
            total_images = image_generation_plan.total_images
            narrative_flow = image_generation_plan.narrative_flow
            visual_consistency = image_generation_plan.visual_consistency
        else:
            # Dictionary
            if 'image_specifications' not in image_generation_plan:
                st.error("No image specifications found in plan")
                return []
            image_specs = image_generation_plan['image_specifications']
            total_images = len(image_specs)
            narrative_flow = image_generation_plan.get('narrative_flow', '')
            visual_consistency = image_generation_plan.get('visual_consistency', {})
        
        st.info(f"🎬 Generating {total_images} images based on AI analysis...")
        
        # Display the narrative flow
        if narrative_flow:
            st.write("📖 **Narrative Flow:**")
            st.write(narrative_flow)
        
        # Display visual consistency guidelines
        if visual_consistency:
            st.write("🎨 **Visual Consistency Guidelines:**")
            st.write(visual_consistency)
        
        saved_files = []
        
        # Generate all images sequentially (one by one) with retry mechanism
        saved_files = self._generate_images_sequential(image_specs, total_images)
        
        return saved_files

    def _generate_images_sequential(self, image_specs, total_images) -> List[str]:
        """Generate images sequentially (one by one) with retry mechanism"""
        saved_files = []
        
        # Create progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for index, image_spec in enumerate(image_specs):
            try:
                # Handle both Pydantic model and dictionary
                if hasattr(image_spec, 'image_number'):
                    # Pydantic model
                    image_number = image_spec.image_number
                    title = image_spec.title
                    purpose = image_spec.purpose
                    angle_description = image_spec.angle_description
                    focus_elements = image_spec.focus_elements
                    generation_prompt = image_spec.generation_prompt
                else:
                    # Dictionary
                    image_number = image_spec.get('image_number', index+1)
                    title = image_spec.get('title', 'Untitled')
                    purpose = image_spec.get('purpose', 'N/A')
                    angle_description = image_spec.get('angle_description', 'N/A')
                    focus_elements = image_spec.get('focus_elements', [])
                    generation_prompt = image_spec.get('generation_prompt', '')
                
                if not generation_prompt:
                    st.error(f"⚠️ No generation prompt provided for image {image_number}")
                    continue
                
                # Enhance the prompt with police investigation context and image-only request
                enhanced_prompt = f"""POLICE INVESTIGATION VISUALIZATION REQUEST

This is for official police investigation and forensic analysis purposes to help law enforcement understand the case evidence and scene layout.

IMPORTANT: Generate ONLY an image as output. Do not include any text, descriptions, or explanations in your response.

{generation_prompt}

Please provide a detailed, accurate visual representation for investigative purposes. Generate only the image with no accompanying text."""
                
                # Use the correct API format for image generation
                contents = [
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(text=enhanced_prompt),
                        ],
                    ),
                ]
                
                # Retry mechanism with multiple attempts and different prompt styles
                max_retries = 3
                files = []
                
                # Different prompt styles to try
                prompt_styles = [
                    enhanced_prompt,  # Original enhanced prompt
                    f"""FORENSIC ANALYSIS VISUALIZATION

This is for official forensic analysis and evidence documentation purposes.

Generate ONLY an image showing: {title}

Focus on: {', '.join(focus_elements) if focus_elements else 'scene layout and evidence placement'}

Provide a detailed, accurate visual representation for investigative documentation. Generate only the image with no text.""",
                    
                    f"""EVIDENCE DOCUMENTATION REQUEST

For law enforcement evidence analysis and case documentation.

Create an image showing: {title}

Key elements: {', '.join(focus_elements) if focus_elements else 'spatial layout and positioning'}

Generate only the image for official documentation purposes."""
                ]
                
                for attempt in range(max_retries):
                    # Try different prompt styles
                    current_prompt = prompt_styles[attempt % len(prompt_styles)]
                    
                    # Update contents with current prompt style
                    contents = [
                        types.Content(
                            role="user",
                            parts=[
                                types.Part.from_text(text=current_prompt),
                            ],
                        ),
                    ]
                    
                    status_text.text(f"🔄 Generating Image {image_number}: {title} (Attempt {attempt + 1}/{max_retries})")
                    
                    # Try streaming method first (more reliable for image generation)
                    try:
                        files = self._generate_image_streaming(contents, f"image_{image_number}_{title.replace(' ', '_').lower()}")
                        if files and len(files) > 0:
                            st.success(f"✅ Generated Image {image_number} - {len(files)} files (Streaming method, Attempt {attempt + 1})")
                            saved_files.extend(files)
                            break
                        else:
                            st.warning(f"⚠️ No image generated with streaming method for Image {image_number} (Attempt {attempt + 1})")
                    except Exception as e:
                        st.warning(f"⚠️ Streaming method failed for Image {image_number} (Attempt {attempt + 1}): {e}")
                    
                    # Fallback to non-streaming method if streaming failed or returned no files
                    status_text.text(f"🔄 Trying non-streaming method for Image {image_number} (Attempt {attempt + 1})...")
                    
                    try:
                        response = self.client.models.generate_content(
                            model=self.model_image,
                            contents=contents,
                            config=types.GenerateContentConfig(
                                response_modalities=['IMAGE', 'TEXT']
                            )
                        )
                        
                        files = self._extract_and_save_images(response, f"image_{image_number}_{title.replace(' ', '_').lower()}")
                        
                        if files and len(files) > 0:
                            st.success(f"✅ Generated Image {image_number} - {len(files)} files (Fallback method, Attempt {attempt + 1})")
                            saved_files.extend(files)
                            break
                        else:
                            st.warning(f"⚠️ No image generated with fallback method for Image {image_number} (Attempt {attempt + 1})")
                            
                    except Exception as e:
                        st.warning(f"⚠️ Fallback method failed for Image {image_number} (Attempt {attempt + 1}): {e}")
                    
                    # Wait before retry (except for last attempt)
                    if attempt < max_retries - 1:
                        status_text.text(f"⏳ Waiting 2 seconds before retry for Image {image_number}...")
                        time.sleep(2)
                
                # Check if image was successfully generated
                if not files or len(files) == 0:
                    st.error(f"❌ Failed to generate Image {image_number} after {max_retries} attempts")
                
                # Update progress bar
                progress_bar.progress((index + 1) / total_images)
                status_text.text(f"📊 Progress: {index + 1}/{total_images} images completed")
                
            except Exception as e:
                st.error(f"❌ Error processing image {image_number}: {e}")
                # Update progress bar even on error
                progress_bar.progress((index + 1) / total_images)
        
        # Final status update
        status_text.text(f"✅ Completed: {len(saved_files)} images generated successfully")
        progress_bar.progress(1.0)
        
        return saved_files

    def _generate_image_streaming(self, contents, prefix: str = "image") -> List[str]:
        """Generate images using streaming method (more reliable)"""
        saved_files = []
        file_index = 0
        
        try:
            for chunk in self.client.models.generate_content_stream(
                model=self.model_image,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_modalities=['IMAGE', 'TEXT']
                )
            ):
                if (
                    chunk.candidates is None
                    or chunk.candidates[0].content is None
                    or chunk.candidates[0].content.parts is None
                ):
                    continue
                    
                if (chunk.candidates[0].content.parts[0].inline_data and 
                    chunk.candidates[0].content.parts[0].inline_data.data):
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    inline_data = chunk.candidates[0].content.parts[0].inline_data
                    data_buffer = inline_data.data
                    file_extension = mimetypes.guess_extension(inline_data.mime_type) or '.png'
                    filename = f"{prefix}_{timestamp}_{file_index}{file_extension}"
                    
                    try:
                        with open(filename, "wb") as f:
                            f.write(data_buffer)
                        saved_files.append(filename)
                        st.write(f" ✅ **Saved image:** {filename}")
                        file_index += 1
                    except Exception as e:
                        st.error(f"❌ **Failed to save image:** {e}")
                else:
                    # Print any text output
                    if hasattr(chunk, 'text') and chunk.text:
                        st.write(f"📝 **Text output:** {chunk.text}")
                        
        except Exception as e:
            st.error(f"❌ **Streaming generation failed:** {e}")
        
        return saved_files

    def _extract_and_save_images(self, response, prefix: str = "image") -> List[str]:
        """Extract and save images from Gemini response"""
        saved_files = []
        
        if not response:
            st.write("❌ **No response received**")
            return saved_files
        
        st.write(f"🔍 **Analyzing response for images...**")
        st.write(f"**Response type:** {type(response)}")
        
        if hasattr(response, 'candidates') and response.candidates:
            st.write(f"**Candidates found:** {len(response.candidates)}")
            
            for i, candidate in enumerate(response.candidates):
                st.write(f"**Candidate {i}:** {type(candidate)}")
                
                if hasattr(candidate, 'content') and candidate.content:
                    st.write(f"  - Has content: {candidate.content is not None}")
                    
                    if hasattr(candidate.content, 'parts'):
                        st.write(f"  - Parts count: {len(candidate.content.parts)}")
                        
                        for j, part in enumerate(candidate.content.parts):
                            st.write(f"    - Part {j}: {type(part)}")
                            
                            if hasattr(part, 'inline_data') and part.inline_data:
                                st.write(f"      - Has inline_data: {part.inline_data is not None}")
                                
                                if hasattr(part.inline_data, 'data') and part.inline_data.data:
                                    st.write(f"      - Has data: {len(part.inline_data.data)} bytes")
                                    
                                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                    mime_type = getattr(part.inline_data, 'mime_type', 'image/png')
                                    ext = mimetypes.guess_extension(mime_type) or '.png'
                                    filename = f"{prefix}_{timestamp}_{i}_{j}{ext}"
                                    
                                    try:
                                        with open(filename, "wb") as f:
                                            f.write(part.inline_data.data)
                                        
                                        saved_files.append(filename)
                                        st.write(f" ✅ **Saved image:** {filename}")

                                    except Exception as e:
                                        st.error(f"      ❌ **Failed to save image:** {e}")
                                else:
                                    st.write(f"      - No data in inline_data")
                            else:
                                st.write(f"      - No inline_data")
                    else:
                        st.write(f"  - No parts in content")
                else:
                    st.write(f"  - No content in candidate")
        else:
            st.write("❌ **No candidates in response**")
        
        st.write(f"📊 **Total images extracted:** {len(saved_files)}")
        return saved_files

# ============================================================================
# STREAMLIT UI COMPONENTS
# ============================================================================

def render_header():
    """Render the main header"""
    st.markdown("""
    <div class="main-header">
        <h1>🔍 CrimeSceneViz</h1>
        <p>Transform Crime Scene Evidence into Detailed Forensic Visualizations</p>
        <p><em>Powered by Gemini 2.5 Flash Image Preview • Built for the Nano Banana Hackathon</em></p>
    </div>
    """, unsafe_allow_html=True)

def render_sidebar():
    """Render sidebar configuration"""
    with st.sidebar:
        st.header("⚙️ Case Configuration")
        
        case_type = st.selectbox(
            "Case Type",
            ["Traffic Accident", "Crime Scene", "Personal Injury", "Property Dispute", "Medical Malpractice"]
        )
        
        visualization_style = st.selectbox(
            "Crime Scene Style",
            ["professional", "technical", "dramatic", "jury_friendly"],
            help="Choose the forensic documentation style for crime scene reconstruction"
        )
        
        st.info("🤖 **AI will determine the optimal number of images based on case complexity**")
        
        st.divider()
        
        st.subheader("🎯 Generation Settings")
        quality_level = st.slider("Quality Level", 1, 10, 8)
        include_measurements = st.checkbox("Include Forensic Measurements", True)
        expert_review = st.checkbox("Expert Review Mode", False)
        
        return {
            'case_type': case_type,
            'style': visualization_style,
            'quality': quality_level,
            'measurements': include_measurements,
            'expert_review': expert_review
        }

def render_input_section():
    """Render input section with tabs"""
    st.subheader("📋 Case Input")
    
    tab1, tab2, tab3 = st.tabs(["📄 Document Upload", "✏️ Text Input", "🔧 Advanced"])
    
    # Initialize variables
    uploaded_files = None
    raw_text = None
    advanced_config = None
    
    with tab1:
        st.info("Upload PDF reports, text files, images, audio recordings, or video files")
        uploaded_files = st.file_uploader(
            "Upload Case Documents",
            accept_multiple_files=True,
            type=['pdf', 'png', 'jpg', 'jpeg', 'mp3', 'wav', 'mp4', 'doc', 'docx', 'txt'],
            help="Supported formats: PDF, Images (PNG, JPG), Audio (MP3, WAV), Video (MP4), Word docs, Text files"
        )
    
    with tab2:
        st.info("Enter witness testimony, police reports, or case description")
        raw_text = st.text_area(
            "Case Description",
            placeholder="Enter witness testimony, police reports, or detailed case description...",
            height=300,
            help="Be as detailed as possible for better visualizations"
        )
    
    with tab3:
        st.info("Advanced configuration options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            evidence_types = st.multiselect(
                "Evidence Types",
                ["Physical Evidence", "Witness Testimony", "Expert Analysis", "Forensic Data", "Timeline Events"]
            )
        
        with col2:
            focus_areas = st.multiselect(
                "Focus Areas",
                ["Scene Layout", "Character Actions", "Vehicle Movement", "Object Placement", "Timeline Sequence"]
            )
        
        custom_prompt = st.text_area(
            "Custom Generation Instructions",
            placeholder="Add specific instructions for the AI visualization...",
            height=100
        )
        
        advanced_config = {
            'evidence_types': evidence_types,
            'focus_areas': focus_areas,
            'custom_prompt': custom_prompt
        }
        
    return uploaded_files, raw_text, advanced_config

def render_processing_dashboard():
    """Render real-time processing dashboard"""
    st.subheader("⚡ Processing Pipeline")
    
    # Create columns for different processing stages
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="step-box">
            <h4>📄 Document Analysis</h4>
            <p>Processing uploaded files...</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="step-box">
            <h4>🤖 AI Agent Analysis</h4>
            <p>Crew AI analyzing evidence...</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="step-box">
            <h4>🎨 Scene Generation</h4>
            <p>Creating visualizations...</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="step-box">
            <h4>⚖️ Court Ready</h4>
            <p>Final presentation prep...</p>
        </div>
        """, unsafe_allow_html=True)

def render_results_section(generated_images: List[str], analysis_result: Dict[str, Any]):
    """Render results with generated visualizations"""
    st.subheader("📊 Generated Visualizations")
    
    if generated_images:
        # Display images in a grid
        cols = st.columns(2)
        for i, image_path in enumerate(generated_images):
            col = cols[i % 2]
            with col:
                try:
                    image = Image.open(image_path)
                    st.image(image, caption=f"Visualization {i+1}", use_column_width=True)
                    
                    # Download button
                    with open(image_path, 'rb') as f:
                        st.download_button(
                            f"Download Image {i+1}",
                            f.read(),
                            file_name=f"courtroom_viz_{i+1}.png",
                            mime="image/png"
                        )
                except Exception as e:
                    st.error(f"Error displaying image {i+1}: {e}")
    
    # Display analysis results
    if analysis_result and analysis_result.get('success'):
        st.subheader("🔍 AI Analysis Report")
        with st.expander("View Detailed Analysis"):
            st.json(analysis_result)

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    # Initialize components
    render_header()
    
    # Initialize Gemini client
    client = initialize_gemini_client()
    
    # Initialize engines
    crew = LegalAnalysisCrew()
    viz_engine = GeminiVisualizationEngine(client)
    
    # Sidebar configuration
    config = render_sidebar()
    
    # Input section
    uploaded_files, raw_text, advanced_config = render_input_section()
    
    # Process button
    st.divider()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        process_button = st.button(
            "🚀 Generate Crime Scene Visualizations",
            type="primary",
            use_container_width=True
        )
    
    if process_button:
        if not uploaded_files and not raw_text:
            st.error("Please provide either uploaded documents or text input")
            return
        
        # Show processing dashboard
        render_processing_dashboard()
        
        # Initialize session state for results
        if 'generated_images' not in st.session_state:
            st.session_state.generated_images = []
        if 'analysis_result' not in st.session_state:
            st.session_state.analysis_result = {}
        
        try:
            with st.spinner("Processing case data..."):
                # Step 1: Extract content from files or use raw text
                if uploaded_files:
                    case_content = viz_engine.process_files_with_gemini(uploaded_files)
                else:
                    case_content = raw_text
                
                if not case_content:
                    st.error("Failed to extract content from provided input")
                    return
                
                st.success("✅ Case content extracted successfully")
            
            with st.spinner("Analyzing with AI agents..."):
                # Step 2: Analyze with Crew AI
                print("🤖 Starting AI Analysis Process...")
                st.write("🤖 **Case files are analyzing...**")
                
                # Create a progress container for step-by-step logging
                progress_container = st.container()
                
                with progress_container:
                    # Step 1: Forensic Analysis
                    print("📋 Step 1: Forensic Analysis")
                    st.write("📋 **Forensic Analysis**")
                    analysis_result = crew.analyze_case(case_content, advanced_config)
                st.session_state.analysis_result = analysis_result
                
                # Show detailed analysis result
                st.write("🔍 **AI Analysis Complete - Results:**")
                st.write("**Status:**", "✅ Success" if analysis_result.get('success') else "❌ Failed")
                st.write("**Timestamp:**", analysis_result.get('timestamp', 'Unknown'))
                
                if analysis_result.get('success'):
                    st.write("**Analysis Data Available:**", "✅ Yes")
                    if 'validation_passed' in analysis_result:
                        st.write("**Validation:**", "✅ Passed" if analysis_result['validation_passed'] else "❌ Failed")
                else:
                    st.write("**Error:**", analysis_result.get('error', 'Unknown error'))
                
                # Show raw analysis data for debugging
                with st.expander("🔍 **Detailed Analysis Data**"):
                    st.json(analysis_result)
                
                if not analysis_result.get('success'):
                    st.error(f"AI analysis failed: {analysis_result.get('error')}")
                    return
                
                st.success("✅ AI analysis completed successfully!")
            
            with st.spinner("Generating visualizations..."):
                # Step 3: Extract image generation plan from analysis
                print("🎨 Starting Image Generation Process...")
                st.write("🎨 **Generating visualizations...**")
                
                # Get the structured analysis data, not the string representation
                analysis_data = analysis_result.get('structured_analysis', analysis_result.get('analysis', {}))
                
                # Debug: Show the analysis result
                print("📊 Extracting Image Generation Plan...")
                print(f"   - Analysis data type: {type(analysis_data)}")
                with st.expander("🔍 **Raw Analysis Data**"):
                    st.json(analysis_data)
                
                # Extract image generation plan from the visual direction task
                image_generation_plan = None
                print("🔍 Searching for Image Generation Plan...")
                
                # Check if analysis_data is a Pydantic model (VisualDirectionModel)
                if hasattr(analysis_data, 'image_specifications'):
                    print("   - Found VisualDirectionModel Pydantic object")
                    image_generation_plan = analysis_data
                    print("   - Using Pydantic model directly for image generation")
                elif isinstance(analysis_data, dict):
                    print("   - Analysis data is a dictionary")
                    # Try to find image generation plan in the analysis
                    if 'image_generation_plan' in analysis_data:
                        print("   - Found image_generation_plan in analysis data")
                        image_generation_plan = analysis_data['image_generation_plan']
                    elif 'structured_analysis' in analysis_data and analysis_data['structured_analysis']:
                        print("   - Found structured_analysis data")
                        structured_data = analysis_data['structured_analysis']
                        if hasattr(structured_data, 'image_specifications'):
                            print("   - Found VisualDirectionModel in structured data")
                            image_generation_plan = structured_data
                        else:
                            print("   - No VisualDirectionModel in structured data")
                            print("   - Available structured attributes:", dir(structured_data))
                    elif 'raw_result' in analysis_data and hasattr(analysis_data['raw_result'], 'pydantic'):
                        print("   - Found raw_result with pydantic data")
                        pydantic_data = analysis_data['raw_result'].pydantic
                        if hasattr(pydantic_data, 'image_specifications'):
                            print("   - Found VisualDirectionModel in pydantic data")
                            image_generation_plan = pydantic_data
                        else:
                            print("   - No VisualDirectionModel in pydantic data")
                            print("   - Available pydantic attributes:", dir(pydantic_data))
                    else:
                        print("   - No structured data found")
                        print("   - Available keys:", list(analysis_data.keys()))
                else:
                    print("   - Analysis data is not a dictionary or Pydantic model")
                    print("   - Type:", type(analysis_data))
                    # Try to parse as JSON if it's a string
                    if isinstance(analysis_data, str):
                        try:
                            import json
                            parsed_data = json.loads(analysis_data)
                            print("   - Successfully parsed string as JSON")
                            if 'image_specifications' in parsed_data:
                                image_generation_plan = parsed_data
                                print("   - Found image_specifications in parsed JSON")
                        except Exception as e:
                            print(f"   - Could not parse string as JSON: {e}")
                
                if not image_generation_plan:
                    print("❌ No image generation plan found in analysis result")
                    st.error("❌ No image generation plan found in analysis result")
                    st.write("**Troubleshooting:**")
                    st.write("- Check if visual_direction_task completed successfully")
                    st.write("- Verify that image_generation_plan was created")
                    st.write("- Check the detailed analysis data above")
                    return
                
                # Display the AI-generated plan
                print("📋 AI-Generated Image Plan Found!")
                st.write("📋 **Image Plan Ready**")
                
                # Handle both Pydantic model and dictionary
                if hasattr(image_generation_plan, 'total_images'):
                    # Pydantic model
                    total_images = image_generation_plan.total_images
                    image_specs = image_generation_plan.image_specifications
                    print(f"   - Total images: {total_images}")
                    print(f"   - Image specifications: {len(image_specs)} images planned")
                else:
                    # Dictionary
                    total_images = image_generation_plan.get('total_images', 'Unknown')
                    image_specs = image_generation_plan.get('image_specifications', [])
                    print(f"   - Total images: {total_images}")
                    print(f"   - Image specifications: {len(image_specs)} images planned")
                
                st.write("**Total Images:**", total_images)
                
                # Show image specifications
                if image_specs:
                    with st.expander("📸 **Image Specifications Details**"):
                        for i, spec in enumerate(image_specs):
                            if hasattr(spec, 'title'):
                                # Pydantic model
                                title = spec.title
                                purpose = spec.purpose
                                angle = spec.angle_description
                                focus = spec.focus_elements
                            else:
                                # Dictionary
                                title = spec.get('title', 'Untitled')
                                purpose = spec.get('purpose', 'N/A')
                                angle = spec.get('angle_description', 'N/A')
                                focus = spec.get('focus_elements', [])
                            
                            st.write(f"**Image {i+1}:** {title}")
                            st.write(f"  - Purpose: {purpose}")
                            st.write(f"  - Angle: {angle}")
                            st.write(f"  - Focus: {', '.join(focus) if isinstance(focus, list) else focus}")
                
                # Generate images based on the AI plan
                print("🎬 Starting Image Generation...")
                st.write("🎬 **Creating images...**")
                generated_images = viz_engine.generate_images_from_plan(image_generation_plan)
                
                st.session_state.generated_images = generated_images
                
                if generated_images:
                    st.success(f"✅ Generated {len(generated_images)} images based on AI analysis")
                    st.write(f"📁 **Generated Files:** {generated_images}")
                else:
                    st.warning("⚠️ No images were generated")
                    st.error("**Possible causes:**")
                    st.write("- No image specifications in the plan")
                    st.write("- Invalid generation prompts")
                    st.write("- Gemini API issues")
                    st.write("- Image extraction problems")
        
        except Exception as e:
            st.error(f"Processing failed: {e}")
            return
    
    # Display results if available
    if st.session_state.get('generated_images') or st.session_state.get('analysis_result'):
        st.divider()
        render_results_section(
            st.session_state.get('generated_images', []),
            st.session_state.get('analysis_result', {})
        )
    
    # Footer with hackathon info
    st.divider()
    st.markdown("""
    <div style="text-align: center; padding: 2rem; color: #666;">
        <h4>🍌 Built for Nano Banana Hackathon 2025</h4>
        <p>Leveraging Gemini 2.5 Flash Image Preview for revolutionary legal visualization</p>
        <p><strong>Key Features:</strong> PDF Processing • Multi-Agent AI Analysis • Multi-Angle Generation • Character Consistency</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
