import pytest
from unittest.mock import Mock, MagicMock, patch
from fastapi.testclient import TestClient
from pydantic import ConfigDict, Field
import json
from datetime import datetime

from app.main import app
from app.core.config import Settings
from app.services.llm_inference import LLMInference
from app.models.request_context import (
    RequestContext,
    CharacterDetails,
    StoryOutline,
    WorldbuildingInfo,
    StoryConfiguration,
    SystemPrompts,
    RequestContextMetadata
)



@pytest.fixture(autouse=True)
def patch_settings():
    Settings.model_config = ConfigDict(
        case_sensitive=True,
        env_file = ".env.example")


@pytest.fixture(autouse=True)
def mock_llm():
    """Mock the LLM for all tests"""
    mock_llm_instance = MagicMock(spec=LLMInference)

    # Mock generate method with intelligent responses
    def generate_side_effect(prompt, **kwargs):
        # Character feedback - return JSON
        if "embodying" in prompt.lower() or "character" in prompt.lower() and "actions" in prompt:
            return json.dumps({
                "actions": ["Takes a deep breath", "Looks around carefully", "Steps forward"],
                "dialog": ["This changes everything", "I need to think", "What now?"],
                "physicalSensations": ["Heart racing", "Palms sweating", "Adrenaline pumping"],
                "emotions": ["Anxious", "Determined", "Cautious"],
                "internalMonologue": ["I can do this", "Stay focused", "One step at a time"]
            })

        # Rater feedback - return JSON
        elif "rater" in prompt.lower() or ("opinion" in prompt and "suggestions" in prompt):
            return json.dumps({
                "opinion": "This plot point is engaging and moves the story forward effectively.",
                "suggestions": [
                    "Add more sensory details",
                    "Heighten emotional stakes",
                    "Connect to story arc",
                    "Improve pacing"
                ]
            })

        # Editor review - return JSON
        elif "editor" in prompt.lower() or "review" in prompt.lower():
            return json.dumps({
                "suggestions": [
                    {"issue": "Opening needs work", "suggestion": "Add sensory details", "priority": "high"},
                    {"issue": "Dialogue feels flat", "suggestion": "Make voices distinct", "priority": "medium"},
                    {"issue": "Pacing issues", "suggestion": "Tighten middle section", "priority": "medium"},
                    {"issue": "Weak transitions", "suggestion": "Add scene breaks", "priority": "low"}
                ]
            })

        # Character details - return JSON
        elif "character details" in prompt.lower() or "character concept" in prompt.lower():
            return json.dumps({
                "name": "Alex Morgan",
                "sex": "Female",
                "gender": "Female",
                "sexualPreference": "Bisexual",
                "age": 34,
                "physicalAppearance": "Tall and athletic with dark hair and piercing eyes",
                "usualClothing": "Practical jeans and leather jacket",
                "personality": "Independent, analytical, determined with hidden warmth",
                "motivations": "Seeking truth and justice while proving herself",
                "fears": "Failure, vulnerability, letting others down",
                "relationships": "Struggles with trust but loyal to those who earn it"
            })

        # Chapter outline generation - return JSON array
        elif "chapter outline" in prompt.lower() or ("story structure analyst" in prompt.lower() and "chapter-by-chapter" in prompt.lower()):
            return json.dumps([
                {
                    "title": "The Discovery",
                    "description": "Detective Chen arrives at the crime scene and discovers the first crucial clue. The evidence points to something much larger than a simple murder.",
                    "involved_characters": ["Detective Chen", "Officer Martinez"]
                },
                {
                    "title": "Following Leads",
                    "description": "The investigation deepens as Chen follows the trail of evidence. New suspects emerge and the case becomes more complex.",
                    "involved_characters": ["Detective Chen", "Suspect Williams", "Witness Johnson"]
                },
                {
                    "title": "The Revelation",
                    "description": "A shocking truth is revealed that changes everything Chen thought she knew about the case. The real perpetrator is finally exposed.",
                    "involved_characters": ["Detective Chen", "The Real Killer", "Captain Rodriguez"]
                }
            ])

        # Chapter generation or modification
        elif "chapter" in prompt.lower() or "write" in prompt.lower():
            # Check if this is a modification request (contains "Current chapter:")
            if "Current chapter:" in prompt and "modification request:" in prompt.lower():
                # Extract the current chapter text
                lines = prompt.split('\n')
                current_chapter_start = -1
                current_chapter_end = -1
                
                for i, line in enumerate(lines):
                    if "Current chapter:" in line:
                        current_chapter_start = i + 1
                    elif current_chapter_start != -1 and ("User's modification request:" in line or "modification request:" in line.lower()):
                        current_chapter_end = i
                        break
                
                if current_chapter_start != -1 and current_chapter_end != -1:
                    original_chapter = '\n'.join(lines[current_chapter_start:current_chapter_end]).strip()
                    # Return the original chapter with some modifications to simulate LLM processing
                    return f"{original_chapter}\n\n[Modified based on user request]"
                
            # Default chapter generation
            return """The rain fell hard on the city streets as Detective Chen examined the scene. Every detail mattered now.

She knelt beside the evidence, her trained eye catching what others had missed. The implications were staggering - this case was about to break wide open.

"We need to move fast," she said, her voice steady despite the adrenaline. The pieces were finally coming together, but time was running out."""

        # Flesh out
        elif "expand" in prompt.lower() or "flesh out" in prompt.lower():
            text_to_expand = prompt.split("Text to expand:")[-1].strip() if "Text to expand:" in prompt else "the situation"
            return f"""{text_to_expand}

The atmosphere was thick with tension as the moment unfolded. Every sensory detail heightened the experience - the distant sound of traffic, the smell of rain on pavement, the cool metal of the detective's badge against her chest.

What had seemed simple moments ago now revealed layers of complexity. The characters involved each brought their own perspectives, their own histories that colored how they perceived and reacted to events."""

        # Default
        else:
            return "This is a generated response from the LLM for testing purposes."

    mock_llm_instance.generate.side_effect = generate_side_effect

    # Mock chat_completion with intelligent responses (same logic as generate)
    def chat_completion_side_effect(messages, **kwargs):
        # Extract the combined content from system and user messages
        combined_prompt = "\n".join(msg["content"] for msg in messages)
        # Use the same logic as generate
        return generate_side_effect(combined_prompt, **kwargs)

    mock_llm_instance.chat_completion.side_effect = chat_completion_side_effect

    # Mock chat_completion_stream for streaming endpoints
    def chat_completion_stream_side_effect(messages, **kwargs):
        # Extract the combined content from system and user messages
        combined_prompt = "\n".join(msg["content"] for msg in messages)
        # Generate response using same logic as generate
        response = generate_side_effect(combined_prompt, **kwargs)
        # Yield tokens one by one to simulate streaming
        words = response.split()
        for word in words:
            yield word + " "

    mock_llm_instance.chat_completion_stream.side_effect = chat_completion_stream_side_effect

    # Patch get_llm to return our mock in all endpoint modules
    with patch('app.services.llm_inference.get_llm', return_value=mock_llm_instance):
        with patch('app.api.v1.endpoints.character_feedback.get_llm', return_value=mock_llm_instance):
            with patch('app.api.v1.endpoints.rater_feedback.get_llm', return_value=mock_llm_instance):
                with patch('app.api.v1.endpoints.generate_chapter.get_llm', return_value=mock_llm_instance):
                    with patch('app.api.v1.endpoints.modify_chapter.get_llm', return_value=mock_llm_instance):
                        with patch('app.api.v1.endpoints.editor_review.get_llm', return_value=mock_llm_instance):
                            with patch('app.api.v1.endpoints.flesh_out.get_llm', return_value=mock_llm_instance):
                                with patch('app.api.v1.endpoints.generate_character_details.get_llm', return_value=mock_llm_instance):
                                    with patch('app.api.v1.endpoints.generate_chapter_outlines.get_llm', return_value=mock_llm_instance):
                                        yield mock_llm_instance


@pytest.fixture
def client():
    """Create a test client for FastAPI application"""
    return TestClient(app)


@pytest.fixture
def sample_character_feedback_request():
    """Sample character feedback request using new RequestContext format"""
    # Create a proper RequestContext with all required fields
    request_context = RequestContext(
        configuration=StoryConfiguration(
            system_prompts=SystemPrompts(
                main_prefix="You are a creative writing assistant.",
                main_suffix="Be detailed and authentic.",
                assistant_prompt="Provide helpful character feedback.",
                editor_prompt="Review and improve the character development."
            )
        ),
        worldbuilding=WorldbuildingInfo(
            content="A noir detective story set in 1940s Los Angeles with dark atmosphere and complex mysteries."
        ),
        story_outline=StoryOutline(
            summary="Detective Sarah Chen investigates a murder case in 1940s Los Angeles",
            status="draft",
            content="The story follows Detective Sarah Chen as she uncovers clues in a complex murder case."
        ),
        context_metadata=RequestContextMetadata(
            story_id="noir_detective_001",
            story_title="The Los Angeles Mystery",
            version="1.0",
            created_at=datetime.now(),
            total_characters=1,
            total_chapters=1,
            total_word_count=1000,
            context_size_estimate=500
        ),
        characters=[
            CharacterDetails(
                id="detective_sarah_chen",
                name="Detective Sarah Chen",
                basic_bio="A determined detective working alone in 1940s Los Angeles, haunted by her previous partner's death.",
                creation_source="user",
                last_modified=datetime.now()
            )
        ]
    )
    
    return {
        "request_context": request_context.model_dump(mode='json'),
        "plotPoint": "The detective discovers a crucial clue at the crime scene"
    }


@pytest.fixture
def sample_rater_feedback_request():
    """Sample rater feedback request using new RequestContext format"""
    request_context = RequestContext(
        configuration=StoryConfiguration(
            system_prompts=SystemPrompts(
                main_prefix="You are a story quality rater specializing in narrative analysis.",
                main_suffix="Provide constructive, detailed feedback on story elements.",
                assistant_prompt="Focus on narrative flow, character consistency, and plot development.",
                editor_prompt="Review feedback for clarity and actionable suggestions."
            )
        ),
        worldbuilding=WorldbuildingInfo(
            content="A noir detective story set in 1940s Los Angeles. The atmosphere is dark and moody, with corruption and mystery permeating every corner of the city."
        ),
        story_outline=StoryOutline(
            summary="Detective story involving investigation and discovery of crucial evidence",
            status="draft",
            content="A story where the detective uncovers important clues that advance the investigation and reveal deeper mysteries."
        ),
        context_metadata=RequestContextMetadata(
            story_id="noir_detective_rater_006",
            story_title="Clues and Shadows",
            version="1.0",
            created_at=datetime.now(),
            total_characters=1,
            total_chapters=0,
            total_word_count=0,
            context_size_estimate=400
        ),
        characters=[
            CharacterDetails(
                id="detective_investigator",
                name="Detective",
                basic_bio="A skilled detective investigating mysterious cases in 1940s Los Angeles",
                creation_source="user",
                last_modified=datetime.now()
            )
        ]
    )
    
    return {
        "request_context": request_context.model_dump(mode='json'),
        "raterPrompt": "Evaluate the narrative flow and character consistency",
        "plotPoint": "The detective discovers a crucial clue at the crime scene"
    }


@pytest.fixture
def sample_generate_chapter_request():
    """Sample chapter generation request using new RequestContext format"""
    request_context = RequestContext(
        configuration=StoryConfiguration(
            system_prompts=SystemPrompts(
                main_prefix="You are a creative writing assistant.",
                main_suffix="Write engaging prose with vivid descriptions.",
                assistant_prompt="Focus on creating compelling narrative scenes.",
                editor_prompt="Review and enhance the chapter content."
            )
        ),
        worldbuilding=WorldbuildingInfo(
            content="A noir detective story set in 1940s Los Angeles with dark atmosphere and rain-soaked streets."
        ),
        story_outline=StoryOutline(
            summary="Detective Sarah Chen investigates a murder case in 1940s Los Angeles",
            status="draft",
            content="The story follows Detective Sarah Chen as she solves crimes in the dark streets of Los Angeles."
        ),
        context_metadata=RequestContextMetadata(
            story_id="noir_detective_002",
            story_title="The Los Angeles Case",
            version="1.0",
            created_at=datetime.now(),
            total_characters=1,
            total_chapters=1,
            total_word_count=1200,
            context_size_estimate=600
        ),
        characters=[
            CharacterDetails(
                id="detective_sarah_chen",
                name="Detective Sarah Chen",
                basic_bio="A determined detective working crime scenes in 1940s Los Angeles, cynical but observant.",
                creation_source="user",
                last_modified=datetime.now()
            )
        ]
    )
    
    return {
        "request_context": request_context.model_dump(mode='json'),
        "plotPoint": "The detective discovers a crucial clue at the crime scene"
    }


@pytest.fixture
def sample_modify_chapter_request():
    """Sample chapter modification request using new RequestContext format"""
    request_context = RequestContext(
        configuration=StoryConfiguration(
            system_prompts=SystemPrompts(
                main_prefix="You are a creative writing assistant.",
                main_suffix="Maintain consistency and apply changes carefully.",
                assistant_prompt="Provide helpful chapter modification suggestions.",
                editor_prompt="Review and improve the chapter modifications."
            )
        ),
        worldbuilding=WorldbuildingInfo(
            content="A noir detective story set in 1940s Los Angeles with dark atmosphere and rain-soaked streets."
        ),
        story_outline=StoryOutline(
            summary="Detective Chen investigates a murder case in 1940s Los Angeles",
            status="draft",
            content="The story follows Detective Chen as she examines crime scenes in the rain-soaked streets of Los Angeles."
        ),
        context_metadata=RequestContextMetadata(
            story_id="noir_detective_001",
            story_title="The Los Angeles Mystery",
            version="1.0",
            created_at=datetime.now(),
            total_characters=1,
            total_chapters=1,
            total_word_count=1000,
            context_size_estimate=500
        ),
        characters=[
            CharacterDetails(
                id="detective_chen",
                name="Detective Chen",
                basic_bio="An experienced detective working crime scenes in 1940s Los Angeles, methodical and observant.",
                creation_source="user",
                last_modified=datetime.now()
            )
        ]
    )
    
    return {
        "request_context": request_context.model_dump(mode='json'),
        "currentChapter": "The rain fell hard on the city streets. Detective Chen examined the crime scene with practiced eyes.",
        "userRequest": "Add more atmospheric details about the weather and setting"
    }


@pytest.fixture
def sample_editor_review_request():
    """Sample editor review request using new RequestContext format"""
    request_context = RequestContext(
        configuration=StoryConfiguration(
            system_prompts=SystemPrompts(
                main_prefix="You are an editor specializing in prose quality and narrative consistency.",
                main_suffix="Provide constructive suggestions for improving writing quality.",
                assistant_prompt="Focus on prose quality, consistency, and narrative flow.",
                editor_prompt="Review text for clarity, style, and structural improvements."
            )
        ),
        worldbuilding=WorldbuildingInfo(
            content="A noir detective story set in 1940s Los Angeles. The atmosphere is dark and moody, with rain-soaked streets and shadowy crime scenes. The setting emphasizes the gritty, atmospheric nature of detective work."
        ),
        story_outline=StoryOutline(
            summary="Detective story involving crime scene investigation in atmospheric 1940s Los Angeles",
            status="draft",
            content="A story where Detective Chen methodically examines crime scenes, using analytical skills to uncover clues in the rain-soaked city."
        ),
        context_metadata=RequestContextMetadata(
            story_id="noir_detective_editor_007",
            story_title="Rain and Investigation",
            version="1.0",
            created_at=datetime.now(),
            total_characters=1,
            total_chapters=0,
            total_word_count=0,
            context_size_estimate=350
        ),
        characters=[
            CharacterDetails(
                id="detective_chen",
                name="Detective Chen",
                basic_bio="A methodical and observant detective investigating cases in 1940s Los Angeles",
                creation_source="user",
                last_modified=datetime.now()
            )
        ]
    )
    
    return {
        "request_context": request_context.model_dump(mode='json'),
        "chapterToReview": "The rain fell hard on the city streets. Detective Chen examined the crime scene."
    }


@pytest.fixture
def sample_flesh_out_request():
    """Sample flesh out request using new RequestContext format"""
    request_context = RequestContext(
        configuration=StoryConfiguration(
            system_prompts=SystemPrompts(
                main_prefix="You are a creative writing assistant specializing in detailed scene expansion.",
                main_suffix="Expand text with relevant detail while maintaining narrative consistency.",
                assistant_prompt="Focus on adding atmospheric details and character insights.",
                editor_prompt="Review expanded text for flow and narrative coherence."
            )
        ),
        worldbuilding=WorldbuildingInfo(
            content="A noir detective story set in 1940s Los Angeles. The city is shrouded in shadows and mystery, with corruption lurking around every corner. Post-war atmosphere with returning veterans and changing social dynamics."
        ),
        story_outline=StoryOutline(
            summary="Detective story involving mysterious evidence and corruption in 1940s Los Angeles",
            status="draft",
            content="A story where the detective discovers crucial evidence that leads deeper into a web of mystery and corruption."
        ),
        context_metadata=RequestContextMetadata(
            story_id="noir_detective_flesh_005",
            story_title="Shadows and Evidence",
            version="1.0",
            created_at=datetime.now(),
            total_characters=1,
            total_chapters=0,
            total_word_count=0,
            context_size_estimate=500
        ),
        characters=[
            CharacterDetails(
                id="detective_protagonist",
                name="Detective",
                basic_bio="A seasoned detective investigating mysterious cases in 1940s Los Angeles",
                creation_source="user",
                last_modified=datetime.now()
            )
        ]
    )
    
    return {
        "request_context": request_context.model_dump(mode='json'),
        "textToFleshOut": "The detective finds a mysterious photograph"
    }


@pytest.fixture
def sample_generate_character_request():
    """Sample generate character details request using new RequestContext format"""
    request_context = RequestContext(
        configuration=StoryConfiguration(
            system_prompts=SystemPrompts(
                main_prefix="You are a character creator specializing in noir fiction.",
                main_suffix="Create believable, complex characters with depth and authenticity.",
                assistant_prompt="Focus on developing compelling character backgrounds and motivations.",
                editor_prompt="Review character details for consistency and narrative potential."
            )
        ),
        worldbuilding=WorldbuildingInfo(
            content="A noir detective story set in 1940s Los Angeles. The city is filled with corruption, shadows, and moral ambiguity. Post-war atmosphere with returning veterans, changing social dynamics."
        ),
        story_outline=StoryOutline(
            summary="Detective story involving corruption and mystery in 1940s Los Angeles",
            status="draft",
            content="A story requiring a tough but fair detective character with a mysterious past to navigate the corrupt underworld."
        ),
        context_metadata=RequestContextMetadata(
            story_id="noir_detective_character_004",
            story_title="Shadows and Secrets",
            version="1.0",
            created_at=datetime.now(),
            total_characters=0,
            total_chapters=0,
            total_word_count=0,
            context_size_estimate=600
        ),
        characters=[]  # Empty since we're generating new characters
    )
    
    return {
        "request_context": request_context.model_dump(mode='json'),
        "basicBio": "A tough but fair detective with a mysterious past",
        "existingCharacters": []
    }


@pytest.fixture
def sample_structured_context_container():
    """Sample structured context container for testing"""
    from app.models.generation_models import (
        StructuredContextContainer,
        PlotElement,
        CharacterContext,
        UserRequest,
        SystemInstruction,
        ContextMetadata
    )
    from datetime import datetime
    
    return StructuredContextContainer(
        plot_elements=[
            PlotElement(
                id="scene_001",
                type="scene",
                content="The detective arrives at the crime scene on a rainy night",
                priority="high",
                tags=["current_scene", "investigation", "weather"],
                metadata={"location": "crime_scene", "time": "night", "weather": "rain"}
            ),
            PlotElement(
                id="setup_001",
                type="setup",
                content="A noir detective story set in 1940s Los Angeles",
                priority="medium",
                tags=["setting", "genre", "background"],
                metadata={"era": "1940s", "location": "los_angeles", "genre": "noir"}
            )
        ],
        character_contexts=[
            CharacterContext(
                character_id="detective_sarah_chen",
                character_name="Detective Sarah Chen",
                current_state={
                    "emotion": "focused",
                    "location": "crime_scene",
                    "mental_state": "analytical",
                    "physical_state": "alert"
                },
                recent_actions=["Arrived at scene", "Examining evidence", "Taking notes"],
                relationships={"partner": "works_alone", "suspects": "suspicious"},
                goals=["Solve the murder case", "Find justice", "Protect the innocent"],
                memories=["Previous partner's death", "Similar cases", "Training"],
                personality_traits=["cynical", "determined", "observant", "methodical"]
            )
        ],
        user_requests=[
            UserRequest(
                id="req_001",
                type="general",
                content="Focus on atmospheric details and character development",
                priority="medium",
                context="story_enhancement",
                timestamp=datetime.now()
            )
        ],
        system_instructions=[
            SystemInstruction(
                id="inst_001",
                type="behavior",
                content="You are a creative writing assistant focused on noir storytelling",
                scope="global",
                priority="high",
                metadata={"genre": "noir", "style": "atmospheric"}
            ),
            SystemInstruction(
                id="inst_002",
                type="style",
                content="Use vivid descriptions and maintain consistent tone",
                scope="chapter",
                priority="medium"
            )
        ],
        metadata=ContextMetadata(
            total_elements=6,
            processing_applied=True,
            processing_mode="structured",
            optimization_level="light",
            compression_ratio=0.85,
            filtered_elements={"plot": 2, "character": 1, "user": 1, "system": 2},
            processing_time_ms=150.5,
            created_at=datetime.now().isoformat(),
            version="1.0"
        )
    )


@pytest.fixture
def sample_legacy_context_request():
    """Sample legacy context request for backward compatibility testing"""
    return {
        "context_mode": "structured",
        "systemPrompts": {
            "mainPrefix": "You are a creative writing assistant.",
            "mainSuffix": "Be detailed and authentic."
        },
        "worldbuilding": "A noir detective story set in 1940s Los Angeles",
        "storySummary": "A detective investigates a mysterious murder case",
        "previousChapters": [],
        "character": {
            "name": "Detective Sarah Chen",
            "basicBio": "A hardboiled detective with a troubled past",
            "sex": "Female",
            "gender": "Female",
            "sexualPreference": "Heterosexual",
            "age": 35,
            "physicalAppearance": "Tall, athletic, with sharp eyes",
            "usualClothing": "Trench coat and fedora",
            "personality": "Cynical but determined",
            "motivations": "Seeking justice and redemption",
            "fears": "Losing another partner",
            "relationships": "Works alone, trusts few people"
        },
        "plotPoint": "The detective discovers a crucial clue at the crime scene"
    }


@pytest.fixture
def sample_chapter_outline_request():
    """Sample chapter outline generation request using new RequestContext format"""
    request_context = RequestContext(
        configuration=StoryConfiguration(
            system_prompts=SystemPrompts(
                main_prefix="You are a creative writing assistant specializing in story structure.",
                main_suffix="Create compelling chapter outlines with clear narrative progression.",
                assistant_prompt="Focus on developing engaging plot points and character arcs.",
                editor_prompt="Review chapter outlines for pacing and story coherence."
            )
        ),
        worldbuilding=WorldbuildingInfo(
            content="1940s Los Angeles - a city of dreams and nightmares, where corruption runs deep and everyone has secrets. The noir atmosphere permeates every street corner."
        ),
        story_outline=StoryOutline(
            summary="A noir detective story set in 1940s Los Angeles. Detective Sarah Chen investigates a mysterious murder that leads her into a web of corruption and deceit. As she follows the clues, she discovers that the case is connected to her own past and must confront her demons to solve it.",
            status="draft",
            content="Detective Sarah Chen receives a new murder case that initially appears straightforward but quickly reveals layers of corruption and personal connection to her past."
        ),
        context_metadata=RequestContextMetadata(
            story_id="noir_detective_outlines_003",
            story_title="Shadows of the Past",
            version="1.0",
            created_at=datetime.now(),
            total_characters=2,
            total_chapters=0,
            total_word_count=0,
            context_size_estimate=800
        ),
        characters=[
            CharacterDetails(
                id="detective_sarah_chen",
                name="Detective Sarah Chen",
                basic_bio="A hardboiled detective with a troubled past and a reputation for getting results. Cynical but determined to find justice.",
                creation_source="user",
                last_modified=datetime.now()
            ),
            CharacterDetails(
                id="captain_rodriguez",
                name="Captain Rodriguez",
                basic_bio="Sarah's boss, a veteran cop trying to keep his department clean while dealing with political pressures.",
                creation_source="user",
                last_modified=datetime.now()
            )
        ]
    )
    
    return {
        "request_context": request_context.model_dump(mode='json'),
        "generation_preferences": {
            "chapter_count_preference": "8-12",
            "pacing": "steady",
            "focus": "character_development"
        }
    }


@pytest.fixture
def sample_chapter_outline_request_with_system_prompts():
    """Sample chapter outline generation request with system prompts using new RequestContext format"""
    request_context = RequestContext(
        configuration=StoryConfiguration(
            system_prompts=SystemPrompts(
                main_prefix="Always maintain character consistency and emotional coherence throughout the story.",
                main_suffix="Ensure each chapter ends with a compelling hook for the next chapter.",
                assistant_prompt="You are a noir fiction specialist.",
                editor_prompt="Focus on atmospheric descriptions."
            )
        ),
        worldbuilding=WorldbuildingInfo(
            content="1940s Los Angeles - a city of dreams and nightmares, where corruption runs deep and everyone has secrets. The noir atmosphere permeates every street corner."
        ),
        story_outline=StoryOutline(
            summary="A noir detective story set in 1940s Los Angeles. Detective Sarah Chen investigates a mysterious murder that leads her into a web of corruption and deceit. As she follows the clues, she discovers that the case is connected to her own past and must confront her demons to solve it.",
            status="draft",
            content="Detective Sarah Chen receives a new murder case that initially appears straightforward but quickly reveals layers of corruption and personal connection to her past."
        ),
        context_metadata=RequestContextMetadata(
            story_id="noir_detective_outlines_with_prompts_008",
            story_title="Shadows of the Past",
            version="1.0",
            created_at=datetime.now(),
            total_characters=1,
            total_chapters=0,
            total_word_count=0,
            context_size_estimate=900
        ),
        characters=[
            CharacterDetails(
                id="detective_sarah_chen",
                name="Detective Sarah Chen",
                basic_bio="A hardboiled detective with a troubled past and a reputation for getting results. Cynical but determined to find justice.",
                creation_source="user",
                last_modified=datetime.now()
            )
        ]
    )
    
    return {
        "request_context": request_context.model_dump(mode='json'),
        "generation_preferences": {
            "chapter_count_preference": "8-12",
            "pacing": "steady",
            "focus": "character_development"
        }
    }
