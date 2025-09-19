# Pydantic Models for CourtroomViz
# Structured output validation for legal analysis

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class EvidenceItem(BaseModel):
    """Individual evidence item with detailed specifications"""
    type: str = Field(description="Type of evidence (Physical, Digital/Testimonial, Physical/Biological, Physical/Circumstantial, etc.)")
    description: str = Field(description="Detailed description of the evidence")
    location: str = Field(description="Where evidence was found or located")
    measurements: Optional[Dict[str, str]] = Field(description="Physical measurements and dimensions", default=None)
    condition: str = Field(description="Current condition and preservation status")
    relevance: str = Field(description="Relevance to case and legal arguments")
    chain_of_custody: str = Field(description="Chain of custody information")

class SceneLayout(BaseModel):
    """Scene layout and spatial relationships"""
    description: str = Field(description="Overall scene description including body positions, blood evidence, and key locations")
    dimensions: Dict[str, str] = Field(description="Scene dimensions and scale measurements")
    key_elements: List[str] = Field(description="Key visual elements for visualization including evidence items and structures")
    camera_angles: List[str] = Field(description="Recommended camera angles for presentation")
    lighting_conditions: str = Field(description="Lighting conditions and requirements")
    environmental_factors: List[str] = Field(description="Environmental factors affecting the scene")

class CharacterProfile(BaseModel):
    """Character consistency profile for visual generation"""
    name: str = Field(description="Character name or identifier")
    role: str = Field(description="Role in the case (Victim, Suspect/Person of Interest, Witness, Expert Witness, Child, etc.)")
    physical_description: Optional[str] = Field(description="Detailed physical description including age, injuries, condition", default=None)
    clothing: Optional[str] = Field(description="Clothing description if relevant", default=None)
    positioning: Optional[str] = Field(description="Positioning in the scene", default=None)
    actions: List[str] = Field(description="Actions performed by this character")

class TimelineEvent(BaseModel):
    """Timeline event with temporal information"""
    timestamp: str = Field(description="Time or sequence of the event")
    description: str = Field(description="What happened at this time")
    participants: List[str] = Field(description="People involved in this event")
    location: str = Field(description="Where this event occurred")
    evidence_created: List[str] = Field(description="Evidence created or modified at this time")

class ForensicAnalysisModel(BaseModel):
    """Comprehensive forensic analysis output"""
    case_summary: str = Field(description="Brief case summary and context including key facts and circumstances")
    evidence_items: List[EvidenceItem] = Field(description="List of all evidence items found with detailed specifications")
    scene_layout: SceneLayout = Field(description="Scene layout and spatial information including body positions and evidence locations")
    timeline: List[TimelineEvent] = Field(description="Chronological timeline of events with participants and evidence created")
    characters: List[CharacterProfile] = Field(description="People involved in the case with detailed profiles")
    visual_requirements: Dict[str, str] = Field(description="Specific requirements for visual generation including crime scene reconstruction, autopsy diagrams, evidence photos, etc.")
    legal_notes: List[str] = Field(description="Important legal considerations and potential objections")
    technical_specifications: Dict[str, Any] = Field(description="Technical details and measurements including DNA analysis, toxicology, wound analysis, etc.")
    recommendations: List[str] = Field(description="Recommendations for presentation and further analysis")

class SceneReconstructionModel(BaseModel):
    """Scene reconstruction analysis output"""
    spatial_analysis: Dict[str, Any] = Field(description="Detailed spatial relationship analysis including body positions, blood trails, and evidence locations")
    timeline: List[TimelineEvent] = Field(description="Reconstructed timeline of events with detailed spatial context")
    visual_requirements: List[str] = Field(description="Specific visual requirements for reconstruction including 3D models, diagrams, and measurements")
    technical_specifications: Dict[str, Any] = Field(description="Technical specifications for accurate reconstruction including scale, measurements, and forensic details")
    environmental_factors: List[str] = Field(description="Environmental factors that affected the scene and events")

class CharacterConsistencyModel(BaseModel):
    """Character consistency analysis output"""
    character_profiles: List[CharacterProfile] = Field(description="Detailed character profiles with physical descriptions, clothing, positioning, and actions")
    object_specifications: List[Dict[str, str]] = Field(description="Objects and their detailed specifications for consistency including vehicles, weapons, personal belongings, environmental objects")
    visual_consistency: Dict[str, Any] = Field(description="Visual consistency requirements including appearance across multiple angles, lighting, shadows, scale, and proportions")
    legal_accuracy: Dict[str, Any] = Field(description="Legal accuracy considerations for character and object descriptions")

class ImageSpec(BaseModel):
    """Individual image specification for generation"""
    image_number: int = Field(description="Order number in the sequence (1, 2, 3, etc.)")
    title: str = Field(description="Descriptive title for the image")
    angle_description: str = Field(description="Camera angle and perspective description")
    focus_elements: List[str] = Field(description="Key elements to focus on in this image")
    generation_prompt: str = Field(description="Detailed prompt for image generation")
    purpose: str = Field(description="Purpose of this image in the overall narrative")
    lighting_notes: str = Field(description="Specific lighting requirements")
    evidence_highlighted: List[str] = Field(description="Evidence items highlighted in this image")
    scene_context: str = Field(description="Context and background for this specific image")

class ImageGenerationPlan(BaseModel):
    """AI-generated comprehensive image generation plan"""
    total_images: int = Field(description="Total number of images to generate")
    narrative_flow: str = Field(description="How the images tell the complete story in sequence")
    visual_consistency: str = Field(description="Guidelines for maintaining visual consistency across images")
    image_specifications: List[ImageSpec] = Field(description="Detailed specifications for each image")
    overall_style: str = Field(description="Overall visual style and aesthetic approach")
    technical_requirements: List[str] = Field(description="Technical requirements for image generation")

class VisualDirectionModel(BaseModel):
    """Visual direction and presentation plan"""
    total_images: int = Field(description="Total number of images to generate")
    narrative_flow: str = Field(description="How the images tell the complete story in sequence")
    image_specifications: List[ImageSpec] = Field(description="Detailed specifications for each individual image")
    visual_consistency: Dict[str, Any] = Field(description="Guidelines for maintaining visual consistency across all images")
    technical_requirements: Dict[str, Any] = Field(description="Technical requirements for image generation and presentation")
