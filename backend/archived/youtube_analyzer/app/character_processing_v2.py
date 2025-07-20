import json
import logging
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from .models import Character, CharacterAppearance, VideoAnalysis
from .database import SessionLocal

logger = logging.getLogger(__name__)

def process_character_analysis(analysis_id: int, character_traits_json: str) -> None:
    """
    Process character trait analysis and create character appearance records.
    
    Args:
        analysis_id: The video analysis ID
        character_traits_json: JSON string containing character analysis
    """
    db = SessionLocal()
    try:
        # Parse the character analysis JSON
        try:
            character_data = character_traits_json.strip()
            if character_data.startswith("```json"):
                # Clean up markdown formatting
                import re
                match = re.search(r'```json\s*(.*?)\s*```', character_data, re.DOTALL)
                if match:
                    character_data = match.group(1)
            
            character_data = json.loads(character_data)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse character analysis JSON: {e}")
            return
        
        characters = character_data.get('characters', [])
        logger.info(f"Processing {len(characters)} characters from analysis {analysis_id}")
        
        for char_data in characters:
            process_single_character(db, analysis_id, char_data)
        
        db.commit()
        logger.info(f"Successfully processed character data for analysis {analysis_id}")
        
    except Exception as e:
        logger.error(f"Error processing character analysis: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()

def process_single_character(db: Session, analysis_id: int, char_data: Dict) -> None:
    """
    Process a single character's data, creating or finding character identity.
    
    Args:
        db: Database session
        analysis_id: Video analysis ID
        char_data: Character data dictionary
    """
    name = char_data.get('name', '').strip()
    if not name:
        logger.warning("Character data missing name, skipping")
        return
    
    # Find or create character identity (basic info only)
    character = find_or_create_character(db, name, char_data.get('channel_or_brand'))
    
    # Create character appearance record with ALL the analysis data
    create_character_appearance(db, character.id, analysis_id, char_data)
    
    logger.info(f"Processed character appearance: {name} in analysis {analysis_id}")

def find_or_create_character(db: Session, name: str, channel: Optional[str] = None) -> Character:
    """
    Find existing character by name or create new one.
    Character table only stores identity info, not traits.
    """
    # Try to find existing character by name (could add fuzzy matching later)
    existing_character = db.query(Character).filter(Character.name.ilike(f"%{name}%")).first()
    
    if existing_character:
        logger.info(f"Found existing character: {existing_character.name}")
        # Update channel if we have new info
        if channel and not existing_character.channel_name:
            existing_character.channel_name = channel
        return existing_character
    else:
        logger.info(f"Creating new character: {name}")
        character = Character(
            name=name,
            channel_name=channel
        )
        db.add(character)
        db.flush()  # Get the ID
        return character

def create_character_appearance(db: Session, character_id: int, analysis_id: int, char_data: Dict) -> None:
    """
    Create a character appearance record with ALL trait data from this video analysis.
    """
    personality = char_data.get('personality_traits', {})
    speaking = char_data.get('speaking_patterns', {})
    golf_traits = char_data.get('golf_characteristics', {})
    visual = char_data.get('visual_traits', {})
    parody = char_data.get('parody_potential', {})
    
    appearance = CharacterAppearance(
        character_id=character_id,
        video_analysis_id=analysis_id,
        
        # Personality traits from this video's AI analysis
        confidence_level=personality.get('confidence_level'),
        humor_level=personality.get('humor_level'),
        competitiveness=personality.get('competitiveness'),
        trash_talk_frequency=personality.get('trash_talk_frequency'),
        celebration_style=golf_traits.get('celebration_style'),
        
        # Speaking patterns from this video
        catchphrases=json.dumps(speaking.get('catchphrases', [])),
        speaking_style=speaking.get('speaking_style'),
        notable_quotes=json.dumps(speaking.get('notable_quotes', [])),
        profanity_usage=speaking.get('profanity_usage'),
        accent_description=speaking.get('accent_description'),
        
        # Golf characteristics from this video
        skill_level=golf_traits.get('skill_level'),
        playing_style=golf_traits.get('playing_style'),
        reaction_to_bad_shots=golf_traits.get('reaction_to_bad_shots'),
        reaction_to_good_shots=golf_traits.get('reaction_to_good_shots'),
        
        # Visual traits from this video
        appearance_description=visual.get('overall_appearance'),
        clothing_style=visual.get('clothing_style'),
        physical_build=visual.get('physical_build'),
        hair_facial_features=visual.get('hair_facial_features'),
        accessories=visual.get('accessories'),
        equipment_style=visual.get('equipment_style'),
        body_language=visual.get('body_language'),
        
        # Video-specific context
        signature_moments=json.dumps(parody.get('signature_moments', [])),
        comedy_potential=parody.get('comedy_angle')
    )
    
    db.add(appearance)

def get_character_summary(character_id: int) -> Dict:
    """
    Get a comprehensive summary of a character across all appearances with calculated averages.
    """
    db = SessionLocal()
    try:
        character = db.query(Character).filter(Character.id == character_id).first()
        if not character:
            return {}
        
        appearances = db.query(CharacterAppearance).filter(
            CharacterAppearance.character_id == character_id
        ).all()
        
        if not appearances:
            return {'character': {'name': character.name, 'appearances': 0}}
        
        # Calculate average personality traits
        trait_averages = calculate_trait_averages(appearances)
        
        # Compile all quotes and moments
        all_quotes = []
        all_catchphrases = []
        all_moments = []
        
        for appearance in appearances:
            if appearance.notable_quotes:
                quotes = json.loads(appearance.notable_quotes)
                all_quotes.extend(quotes)
            
            if appearance.catchphrases:
                phrases = json.loads(appearance.catchphrases)
                all_catchphrases.extend(phrases)
                
            if appearance.signature_moments:
                moments = json.loads(appearance.signature_moments)
                all_moments.extend(moments)
        
        # Get most recent appearance data for non-numeric traits
        latest_appearance = max(appearances, key=lambda x: x.created_at)
        
        return {
            'character': {
                'id': character.id,
                'name': character.name,
                'channel_name': character.channel_name,
                'appearance_count': len(appearances),
                
                # Averaged personality traits
                'personality_averages': trait_averages,
                
                # Most recent categorical traits
                'latest_traits': {
                    'speaking_style': latest_appearance.speaking_style,
                    'skill_level': latest_appearance.skill_level,
                    'playing_style': latest_appearance.playing_style,
                    'celebration_style': latest_appearance.celebration_style,
                },
                
                # Accumulated data across all videos
                'accumulated_data': {
                    'all_quotes': list(set(all_quotes)),
                    'all_catchphrases': list(set(all_catchphrases)),
                    'all_signature_moments': list(set(all_moments)),
                },
                
                # Latest visual description
                'appearance': {
                    'clothing_style': latest_appearance.clothing_style,
                    'physical_build': latest_appearance.physical_build,
                    'hair_facial_features': latest_appearance.hair_facial_features,
                    'accessories': latest_appearance.accessories,
                    'equipment_style': latest_appearance.equipment_style,
                    'body_language': latest_appearance.body_language,
                }
            }
        }
    finally:
        db.close()

def calculate_trait_averages(appearances: List[CharacterAppearance]) -> Dict:
    """Calculate average numerical traits across all appearances."""
    numeric_traits = [
        'confidence_level', 'humor_level', 'competitiveness', 
        'trash_talk_frequency', 'profanity_usage'
    ]
    
    averages = {}
    for trait in numeric_traits:
        values = [getattr(app, trait) for app in appearances if getattr(app, trait) is not None]
        if values:
            averages[trait] = round(sum(values) / len(values), 1)
            averages[f'{trait}_count'] = len(values)  # How many videos contributed to this average
        else:
            averages[trait] = None
            averages[f'{trait}_count'] = 0
    
    return averages

def get_character_evolution(character_id: int) -> Dict:
    """Get character trait evolution over time (chronological)."""
    db = SessionLocal()
    try:
        appearances = db.query(CharacterAppearance).filter(
            CharacterAppearance.character_id == character_id
        ).order_by(CharacterAppearance.created_at).all()
        
        evolution = []
        for app in appearances:
            video = db.query(VideoAnalysis).filter(VideoAnalysis.id == app.video_analysis_id).first()
            evolution.append({
                'video_analysis_id': app.video_analysis_id,
                'video_url': video.youtube_url if video else None,
                'date': app.created_at.isoformat(),
                'confidence_level': app.confidence_level,
                'humor_level': app.humor_level,
                'competitiveness': app.competitiveness,
                'quotes': json.loads(app.notable_quotes) if app.notable_quotes else [],
                'performance_notes': app.performance_notes
            })
        
        return {'evolution': evolution}
    finally:
        db.close()