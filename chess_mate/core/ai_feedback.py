import os
from openai import OpenAI
from typing import Dict, List, Any, Optional, TypedDict, Union, Literal
import logging

logger = logging.getLogger(__name__)

class FeedbackSection(TypedDict):
    analysis: str
    suggestions: List[str]

class StudyPlan(TypedDict):
    focus_areas: List[str]
    exercises: List[str]

class FeedbackData(TypedDict):
    opening: FeedbackSection
    tactics: FeedbackSection
    strategy: FeedbackSection
    time_management: FeedbackSection
    endgame: FeedbackSection
    study_plan: StudyPlan

SectionType = Literal["opening", "tactics", "strategy", "time_management", "endgame"]

class AIFeedbackGenerator:
    """Class to handle AI-powered feedback generation for chess games."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the feedback generator with OpenAI API key."""
        self.client = None
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OpenAI API key not set. AI feedback will be disabled.")
        else:
            self.client = OpenAI(api_key=api_key)

    def generate_personalized_feedback(
        self,
        game_analysis: List[Dict[str, Any]],
        player_profile: Dict[str, Any]
    ) -> FeedbackData:
        """
        Generate personalized feedback using OpenAI's GPT model.
        
        Args:
            game_analysis: List of move analysis data
            player_profile: Dictionary containing player information
            
        Returns:
            Dictionary containing structured feedback
        """
        try:
            if not self.client:
                logger.warning("OpenAI client not initialized. Using fallback feedback.")
                return self._generate_fallback_feedback(game_analysis)

            # Prepare the analysis summary
            analysis_summary = self._prepare_analysis_summary(game_analysis)
            
            # Create the prompt
            prompt = self._create_analysis_prompt(analysis_summary, player_profile)
            
            # Generate feedback using OpenAI
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a chess analysis expert providing specific, actionable feedback to help players improve their game."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            # Parse and structure the response
            content = response.choices[0].message.content
            if not content:
                logger.warning("Empty response from OpenAI API")
                return self._generate_fallback_feedback(game_analysis)
                
            feedback = self._parse_ai_response(content)
            return feedback
            
        except Exception as e:
            logger.error("Error generating AI feedback: %s", str(e))
            return self._generate_fallback_feedback(game_analysis)

    def _prepare_analysis_summary(self, game_analysis: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Prepare a summary of the game analysis for the AI prompt."""
        summary: Dict[str, Union[int, List[Dict[str, Any]]]] = {
            "total_moves": len(game_analysis),
            "critical_moves": [],
            "mistakes": [],
            "positional_notes": [],
            "time_management": []
        }
        
        for move in game_analysis:
            if move.get("is_critical"):
                critical_moves = summary.get("critical_moves", [])
                if isinstance(critical_moves, list):
                    critical_moves.append({
                        "move_number": move["move_number"],
                        "move": move["move"],
                        "evaluation": move["score"]
                    })
            
            if move.get("is_mistake"):
                mistakes = summary.get("mistakes", [])
                if isinstance(mistakes, list):
                    mistakes.append({
                        "move_number": move["move_number"],
                        "move": move["move"],
                        "evaluation_drop": move.get("evaluation_drop", 0)
                    })
            
            if move.get("time_spent", 0) > 60:  # More than 60 seconds spent
                time_management = summary.get("time_management", [])
                if isinstance(time_management, list):
                    time_management.append({
                        "move_number": move["move_number"],
                        "time_spent": move["time_spent"]
                    })
        
        return summary

    def _create_analysis_prompt(
        self,
        analysis_summary: Dict[str, Any],
        player_profile: Dict[str, Any]
    ) -> str:
        """Create a detailed prompt for the AI based on analysis and player profile."""
        prompt = f"""
Analyze this chess game for {player_profile.get('username', 'Anonymous')} (Rating: {player_profile.get('rating', 'Unrated')})
Total games played: {player_profile.get('total_games', 0)}
Preferred openings: {', '.join(player_profile.get('preferred_openings', ['Not specified']))}

Game Summary:
- Total moves: {analysis_summary['total_moves']}
- Critical positions: {len(analysis_summary.get('critical_moves', []))}
- Mistakes: {len(analysis_summary.get('mistakes', []))}
- Time management issues: {len(analysis_summary.get('time_management', []))}

Please provide specific, actionable feedback in the following areas:
1. Opening preparation and improvements
2. Tactical awareness and calculation
3. Strategic understanding and positional play
4. Time management
5. Endgame technique
6. Specific exercises or study recommendations

Focus on the most critical aspects and provide concrete suggestions for improvement.
"""
        return prompt

    def _parse_ai_response(self, response_text: str) -> FeedbackData:
        """Parse and structure the AI's response into organized feedback."""
        feedback: FeedbackData = {
            "opening": {"analysis": "", "suggestions": []},
            "tactics": {"analysis": "", "suggestions": []},
            "strategy": {"analysis": "", "suggestions": []},
            "time_management": {"analysis": "", "suggestions": []},
            "endgame": {"analysis": "", "suggestions": []},
            "study_plan": {"focus_areas": [], "exercises": []}
        }
        
        # Simple parsing based on common patterns
        current_section: Optional[Union[SectionType, Literal["study_plan"]]] = None
        for line in response_text.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            # Identify sections
            if "opening" in line.lower():
                current_section = "opening"
            elif "tactical" in line.lower():
                current_section = "tactics"
            elif "strategic" in line.lower() or "positional" in line.lower():
                current_section = "strategy"
            elif "time" in line.lower():
                current_section = "time_management"
            elif "endgame" in line.lower():
                current_section = "endgame"
            elif "study" in line.lower() or "exercise" in line.lower():
                current_section = "study_plan"
            
            # Add content to appropriate section
            if current_section and current_section != "study_plan" and line.startswith('-'):
                section = feedback[current_section] if current_section in ["opening", "tactics", "strategy", "time_management", "endgame"] else feedback["opening"]
                section["suggestions"].append(line[1:].strip())
            elif current_section == "study_plan" and line.startswith('-'):
                if "exercise" in line.lower():
                    feedback["study_plan"]["exercises"].append(line[1:].strip())
                else:
                    feedback["study_plan"]["focus_areas"].append(line[1:].strip())
            elif current_section and current_section != "study_plan":
                section = feedback[current_section] if current_section in ["opening", "tactics", "strategy", "time_management", "endgame"] else feedback["opening"]
                section["analysis"] += line + " "
        
        return feedback

    def _generate_fallback_feedback(self, game_analysis: List[Dict[str, Any]]) -> FeedbackData:
        """Generate basic feedback when AI generation fails."""
        feedback: FeedbackData = {
            "opening": {
                "analysis": "Analysis unavailable",
                "suggestions": ["Review your opening preparation"]
            },
            "tactics": {
                "analysis": "Analysis unavailable",
                "suggestions": ["Practice tactical puzzles daily"]
            },
            "strategy": {
                "analysis": "Analysis unavailable",
                "suggestions": ["Study positional chess concepts"]
            },
            "time_management": {
                "analysis": "Analysis unavailable",
                "suggestions": ["Practice time management in online games"]
            },
            "endgame": {
                "analysis": "Analysis unavailable",
                "suggestions": ["Study basic endgame principles"]
            },
            "study_plan": {
                "focus_areas": ["Tactics", "Time Management"],
                "exercises": ["Solve puzzles", "Play practice games"]
            }
        }
        return feedback 