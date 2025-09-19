# CourtroomViz Crew Implementation
# Legal Analysis Crew using CrewAI framework

from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List, Dict, Any
import os
from datetime import datetime
from .models import (
    ForensicAnalysisModel, 
    SceneReconstructionModel, 
    CharacterConsistencyModel, 
    VisualDirectionModel
)

@CrewBase
class LegalAnalysisCrew:
    """Legal Analysis Crew for Courtroom Visualization"""

    agents: List[BaseAgent]
    tasks: List[Task]

    def __init__(self):
        # Initialize Gemini LLM for CrewAI
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        self.llm = LLM(
            model="gemini/gemini-2.5-flash",
            temperature=0.1
        )

    @agent
    def forensic_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['forensic_analyst'], # type: ignore[index]
            llm=self.llm,
            verbose=True
        )

    @agent
    def scene_reconstructor(self) -> Agent:
        return Agent(
            config=self.agents_config['scene_reconstructor'], # type: ignore[index]
            llm=self.llm,
            verbose=True
        )

    @agent
    def character_profiler(self) -> Agent:
        return Agent(
            config=self.agents_config['character_profiler'], # type: ignore[index]
            llm=self.llm,
            verbose=True
        )

    @agent
    def visual_director(self) -> Agent:
        return Agent(
            config=self.agents_config['visual_director'], # type: ignore[index]
            llm=self.llm,
            verbose=True
        )

    @task
    def forensic_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['forensic_analysis_task'], # type: ignore[index]
            output_pydantic=ForensicAnalysisModel,
            agent=self.forensic_analyst()
        )

    @task
    def scene_reconstruction_task(self) -> Task:
        return Task(
            config=self.tasks_config['scene_reconstruction_task'], # type: ignore[index]
            output_pydantic=SceneReconstructionModel,
            agent=self.scene_reconstructor()
        )

    @task
    def character_consistency_task(self) -> Task:
        return Task(
            config=self.tasks_config['character_consistency_task'], # type: ignore[index]
            output_pydantic=CharacterConsistencyModel,
            agent=self.character_profiler()
        )

    @task
    def visual_direction_task(self) -> Task:
        return Task(
            config=self.tasks_config['visual_direction_task'], # type: ignore[index]
            output_pydantic=VisualDirectionModel,
            agent=self.visual_director()
        )

    @crew
    def crew(self) -> Crew:
        """Creates the legal analysis crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            memory=False,  # Disable memory system (causing excessive API calls)
            planning=False,  # Disable planning system (causing errors)
            # planning_llm=self.llm,  # Disabled due to planning system issues
            embedder={
                "provider": "google",  # Use Google embeddings
                "config": {
                    "api_key": os.getenv("GEMINI_API_KEY"),
                    "model": "text-embedding-004"
                }
            },
            verbose=True,
            output_log_file="courtroom_viz_analysis.log"
        )

    def analyze_case(self, case_data: str, advanced_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze case data using crew AI with enhanced configuration"""
        # Build enhanced descriptions based on advanced config
        evidence_focus = ""
        focus_areas = ""
        custom_instructions = ""
        
        if advanced_config:
            if advanced_config.get('evidence_types'):
                evidence_focus = f" Focus on these evidence types: {', '.join(advanced_config['evidence_types'])}."
            
            if advanced_config.get('focus_areas'):
                focus_areas = f" Pay special attention to: {', '.join(advanced_config['focus_areas'])}."
            
            if advanced_config.get('custom_prompt'):
                custom_instructions = f" Additional instructions: {advanced_config['custom_prompt']}"
        
        # Prepare inputs for the crew
        inputs = {
            'case_data': case_data,
            'evidence_focus': evidence_focus,
            'focus_areas': focus_areas,
            'custom_instructions': custom_instructions
        }
        
        try:
            # Execute crew with enhanced error handling
            result = self.crew().kickoff(inputs=inputs)
            
            # Validate the result
            validation_result = self.validate_analysis_output(result)
            if not validation_result[0]:
                return {
                    'success': False,
                    'error': f"Analysis validation failed: {validation_result[1]}",
                    'timestamp': datetime.now().isoformat()
                }
            
            # Extract the actual analysis content - prioritize Pydantic model
            analysis_content = ""
            structured_data = None
            
            if hasattr(result, 'pydantic') and result.pydantic:
                # Use Pydantic model as primary source
                structured_data = result.pydantic
                analysis_content = str(result.pydantic)
                print(f"✅ Using Pydantic model output (type: {type(result.pydantic)})")
            elif hasattr(result, 'raw') and result.raw:
                analysis_content = result.raw
                print(f"⚠️ Using raw output (length: {len(result.raw)} chars)")
                # Try to parse as JSON if it looks like structured data
                try:
                    import json
                    if analysis_content.strip().startswith('{') and analysis_content.strip().endswith('}'):
                        structured_data = json.loads(analysis_content)
                        print("✅ Successfully parsed raw output as JSON")
                except Exception as e:
                    print(f"⚠️ Could not parse raw output as JSON: {e}")
            else:
                analysis_content = str(result)
                print(f"⚠️ Using string representation of result")
            
            return {
                'success': True,
                'analysis': analysis_content,
                'structured_analysis': structured_data,  # Include structured data for context passing
                'raw_result': result,
                'timestamp': datetime.now().isoformat(),
                'validation_passed': True
            }
        except Exception as e:
            # Enhanced error handling with specific error types
            error_type = type(e).__name__
            error_message = str(e)
            
            # Log the error for debugging
            with open("courtroom_viz_errors.log", "a") as f:
                f.write(f"{datetime.now().isoformat()} - {error_type}: {error_message}\n")
            
            return {
                'success': False,
                'error': f"{error_type}: {error_message}",
                'error_type': error_type,
                'timestamp': datetime.now().isoformat()
            }
    
    def validate_analysis_output(self, result) -> tuple[bool, Any]:
        """Validate the analysis output for completeness and quality"""
        try:
            # Check if result exists and has content
            if not result:
                return (False, "Analysis result is empty or None")
            
            # Check if result has raw output
            if hasattr(result, 'raw') and result.raw:
                if len(result.raw.strip()) < 100:
                    return (False, "Analysis output too short or insufficient detail")
            
            # Check if result has pydantic output (structured data)
            if hasattr(result, 'pydantic') and result.pydantic:
                pydantic_data = result.pydantic
                
                # Validate forensic analysis model
                if hasattr(pydantic_data, 'evidence_items'):
                    if not pydantic_data.evidence_items or len(pydantic_data.evidence_items) == 0:
                        return (False, "No evidence items found in analysis")
                
                if hasattr(pydantic_data, 'scene_layout'):
                    if not pydantic_data.scene_layout:
                        return (False, "Scene layout information missing")
            
            # Check for key content indicators
            content_indicators = ['evidence', 'scene', 'timeline', 'character', 'visual']
            if hasattr(result, 'raw') and result.raw:
                content_lower = result.raw.lower()
                found_indicators = [indicator for indicator in content_indicators if indicator in content_lower]
                if len(found_indicators) < 2:
                    return (False, f"Insufficient content depth. Found only: {found_indicators}")
            
            return (True, result)
            
        except Exception as e:
            return (False, f"Validation error: {str(e)}")
