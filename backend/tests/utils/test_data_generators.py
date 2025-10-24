"""
Test Data Generators for Context Management Testing

This module provides realistic test data generators for various story lengths,
character complexities, and context management scenarios to enable comprehensive
testing of the Writer Assistant's context management system.
"""

import random
import string
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from app.services.context_manager import ContextItem, ContextType
from app.services.token_management import LayerType


class StoryComplexity(Enum):
    """Story complexity levels for test data generation."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    EPIC = "epic"


class ContentLength(Enum):
    """Content length categories for test generation."""
    SHORT = "short"      # 100-500 tokens
    MEDIUM = "medium"    # 500-2000 tokens
    LONG = "long"        # 2000-8000 tokens
    VERY_LONG = "very_long"  # 8000+ tokens


@dataclass
class TestStoryData:
    """Container for generated test story data."""
    title: str
    genre: str
    characters: List[Dict[str, Any]]
    plot_outline: str
    chapters: List[str]
    world_building: str
    total_tokens: int
    complexity: StoryComplexity


@dataclass
class TestContextScenario:
    """Container for test context management scenarios."""
    name: str
    description: str
    context_items: List[ContextItem]
    expected_token_usage: Dict[LayerType, int]
    should_trigger_overflow: bool
    complexity: StoryComplexity


class StoryDataGenerator:
    """Generates realistic story content for testing."""
    
    GENRES = [
        "Fantasy", "Science Fiction", "Mystery", "Romance", "Thriller",
        "Historical Fiction", "Literary Fiction", "Horror", "Adventure"
    ]
    
    CHARACTER_TRAITS = [
        "brave", "cunning", "wise", "impulsive", "loyal", "mysterious",
        "ambitious", "compassionate", "stubborn", "charismatic"
    ]
    
    PLOT_ELEMENTS = [
        "ancient prophecy", "hidden treasure", "forbidden love", "dark secret",
        "mysterious stranger", "lost memory", "betrayal", "redemption",
        "coming of age", "revenge quest"
    ]

    def __init__(self, seed: Optional[int] = None):
        """Initialize generator with optional seed for reproducible results."""
        if seed is not None:
            random.seed(seed)
    
    def generate_story(self, complexity: StoryComplexity = StoryComplexity.MODERATE) -> TestStoryData:
        """Generate a complete test story based on complexity level."""
        genre = random.choice(self.GENRES)
        title = self._generate_title(genre)
        
        # Generate characters based on complexity
        num_characters = self._get_character_count(complexity)
        characters = [self._generate_character() for _ in range(num_characters)]
        
        # Generate plot outline
        plot_outline = self._generate_plot_outline(complexity, genre)
        
        # Generate chapters
        num_chapters = self._get_chapter_count(complexity)
        chapters = [self._generate_chapter(i + 1, complexity) for i in range(num_chapters)]
        
        # Generate world building
        world_building = self._generate_world_building(complexity, genre)
        
        # Calculate total tokens (rough estimate)
        total_tokens = self._estimate_tokens(plot_outline, chapters, world_building, characters)
        
        return TestStoryData(
            title=title,
            genre=genre,
            characters=characters,
            plot_outline=plot_outline,
            chapters=chapters,
            world_building=world_building,
            total_tokens=total_tokens,
            complexity=complexity
        )
    
    def _generate_title(self, genre: str) -> str:
        """Generate a story title based on genre."""
        title_patterns = {
            "Fantasy": ["The {} of {}", "Chronicles of {}", "The {} Prophecy"],
            "Science Fiction": ["Beyond {}", "The {} Protocol", "Quantum {}"],
            "Mystery": ["The {} Mystery", "Death in {}", "The {} Conspiracy"],
            "Romance": ["Love in {}", "The {} Heart", "Passion's {}"],
            "Thriller": ["The {} Hunt", "Deadly {}", "The {} Gambit"]
        }
        
        pattern = random.choice(title_patterns.get(genre, ["The {} Story"]))
        word1 = random.choice(["Crystal", "Shadow", "Golden", "Lost", "Hidden", "Ancient"])
        word2 = random.choice(["Kingdom", "Tower", "Valley", "Secret", "Dawn", "Storm"])
        
        return pattern.format(word1, word2)
    
    def _generate_character(self) -> Dict[str, Any]:
        """Generate a character with traits and background."""
        names = ["Alex", "Morgan", "Jordan", "Casey", "Riley", "Avery", "Quinn", "Sage"]
        
        return {
            "name": random.choice(names),
            "age": random.randint(18, 65),
            "traits": random.sample(self.CHARACTER_TRAITS, k=random.randint(2, 4)),
            "background": self._generate_character_background(),
            "goals": self._generate_character_goals(),
            "relationships": {}
        }
    
    def _generate_character_background(self) -> str:
        """Generate character background story."""
        backgrounds = [
            "Grew up in a small village, always dreaming of adventure beyond the mountains.",
            "Former soldier turned scholar, haunted by memories of past battles.",
            "Orphaned at a young age, learned to survive on the streets through wit and cunning.",
            "Noble-born but rejected their family's expectations to pursue their own path.",
            "Mysterious past shrouded in secrets, with skills that hint at hidden training."
        ]
        return random.choice(backgrounds)
    
    def _generate_character_goals(self) -> str:
        """Generate character goals and motivations."""
        goals = [
            "Seeking to uncover the truth about their mysterious heritage.",
            "Determined to protect their loved ones from an ancient threat.",
            "Pursuing knowledge that could change the world forever.",
            "Trying to redeem themselves for past mistakes.",
            "Fighting to restore balance to a world in chaos."
        ]
        return random.choice(goals)
    
    def _generate_plot_outline(self, complexity: StoryComplexity, genre: str) -> str:
        """Generate plot outline based on complexity and genre."""
        base_plots = {
            "Fantasy": "A young hero discovers they have magical powers and must save the realm from an ancient evil.",
            "Science Fiction": "Humanity faces extinction from an alien threat, and only advanced technology can save them.",
            "Mystery": "A detective investigates a series of murders that reveal a deeper conspiracy.",
            "Romance": "Two people from different worlds fall in love despite the obstacles keeping them apart.",
            "Thriller": "A protagonist races against time to prevent a catastrophic event."
        }
        
        base_plot = base_plots.get(genre, "A character faces challenges and grows through their journey.")
        
        if complexity == StoryComplexity.SIMPLE:
            return base_plot
        elif complexity == StoryComplexity.MODERATE:
            return f"{base_plot} Along the way, they discover hidden truths about themselves and must make difficult choices."
        elif complexity == StoryComplexity.COMPLEX:
            return f"{base_plot} The story weaves together multiple plotlines involving political intrigue, personal relationships, and moral dilemmas that challenge everything the protagonist believes."
        else:  # EPIC
            return f"{base_plot} This epic tale spans multiple generations and locations, featuring an ensemble cast whose interconnected stories reveal the true scope of the threat facing their world."
    
    def _generate_chapter(self, chapter_num: int, complexity: StoryComplexity) -> str:
        """Generate chapter content based on complexity."""
        base_length = {
            StoryComplexity.SIMPLE: 200,
            StoryComplexity.MODERATE: 500,
            StoryComplexity.COMPLEX: 1000,
            StoryComplexity.EPIC: 2000
        }
        
        length = base_length[complexity] + random.randint(-100, 200)
        
        # Generate realistic chapter content
        chapter_start = f"Chapter {chapter_num}\n\n"
        content = self._generate_prose(length)
        
        return chapter_start + content
    
    def _generate_prose(self, target_length: int) -> str:
        """Generate prose-like text of approximately target_length characters."""
        sentences = [
            "The morning sun cast long shadows across the ancient courtyard.",
            "She could hear footsteps echoing in the distance, growing closer.",
            "The old book contained secrets that had been hidden for centuries.",
            "His heart raced as he approached the mysterious door.",
            "The wind whispered through the trees, carrying an ominous message.",
            "Time seemed to slow as the moment of truth arrived.",
            "The artifact glowed with an otherworldly light.",
            "Memories of the past came flooding back in vivid detail.",
            "The choice before them would determine the fate of many.",
            "In the silence, they could hear the sound of their own breathing."
        ]
        
        content = ""
        while len(content) < target_length:
            sentence = random.choice(sentences)
            content += sentence + " "
            
            # Add paragraph breaks occasionally
            if random.random() < 0.3:
                content += "\n\n"
        
        return content[:target_length].strip()
    
    def _generate_world_building(self, complexity: StoryComplexity, genre: str) -> str:
        """Generate world building content."""
        base_worlds = {
            "Fantasy": "A magical realm where ancient powers still influence the modern world.",
            "Science Fiction": "A future where humanity has spread across the galaxy, encountering new civilizations.",
            "Mystery": "A contemporary city with hidden depths and dark secrets.",
            "Romance": "A charming small town where everyone knows everyone else's business.",
            "Thriller": "An urban landscape where danger lurks around every corner."
        }
        
        base_world = base_worlds.get(genre, "A world much like our own, but with hidden mysteries.")
        
        complexity_additions = {
            StoryComplexity.SIMPLE: "",
            StoryComplexity.MODERATE: " The world has a rich history that affects current events.",
            StoryComplexity.COMPLEX: " Multiple cultures and societies interact in complex ways, each with their own customs, beliefs, and conflicts.",
            StoryComplexity.EPIC: " The world spans multiple continents and dimensions, with intricate political systems, ancient histories, and cosmic forces at play."
        }
        
        return base_world + complexity_additions[complexity]
    
    def _get_character_count(self, complexity: StoryComplexity) -> int:
        """Get number of characters based on complexity."""
        counts = {
            StoryComplexity.SIMPLE: random.randint(2, 4),
            StoryComplexity.MODERATE: random.randint(4, 7),
            StoryComplexity.COMPLEX: random.randint(7, 12),
            StoryComplexity.EPIC: random.randint(12, 20)
        }
        return counts[complexity]
    
    def _get_chapter_count(self, complexity: StoryComplexity) -> int:
        """Get number of chapters based on complexity."""
        counts = {
            StoryComplexity.SIMPLE: random.randint(3, 8),
            StoryComplexity.MODERATE: random.randint(8, 15),
            StoryComplexity.COMPLEX: random.randint(15, 25),
            StoryComplexity.EPIC: random.randint(25, 50)
        }
        return counts[complexity]
    
    def _estimate_tokens(self, plot_outline: str, chapters: List[str], 
                        world_building: str, characters: List[Dict]) -> int:
        """Rough token estimation (4 characters ≈ 1 token)."""
        total_chars = len(plot_outline) + len(world_building)
        total_chars += sum(len(chapter) for chapter in chapters)
        total_chars += sum(len(str(char)) for char in characters)
        
        return total_chars // 4


class ContextDataGenerator:
    """Generates context items and scenarios for testing."""
    
    def __init__(self, seed: Optional[int] = None):
        """Initialize generator with optional seed."""
        if seed is not None:
            random.seed(seed)
    
    def generate_context_scenario(self, name: str, complexity: StoryComplexity) -> TestContextScenario:
        """Generate a complete context management test scenario."""
        story_gen = StoryDataGenerator(seed=42)  # Use fixed seed for consistency
        story_data = story_gen.generate_story(complexity)
        
        context_items = []
        
        # Generate system context
        system_context = ContextItem(
            content="You are a creative writing assistant helping to craft an engaging story.",
            context_type=ContextType.SYSTEM,
            priority=10,
            layer_type=LayerType.WORKING_MEMORY,
            metadata={"source": "system", "immutable": True}
        )
        context_items.append(system_context)
        
        # Generate story context items
        for i, chapter in enumerate(story_data.chapters[:3]):  # Use first 3 chapters
            chapter_context = ContextItem(
                content=chapter,
                context_type=ContextType.STORY,
                priority=8 - i,  # Recent chapters have higher priority
                layer_type=LayerType.EPISODIC_MEMORY,
                metadata={"chapter": i + 1, "type": "chapter"}
            )
            context_items.append(chapter_context)
        
        # Generate character context items
        for char in story_data.characters[:5]:  # Use first 5 characters
            char_context = ContextItem(
                content=f"Character: {char['name']}, Age: {char['age']}, Traits: {', '.join(char['traits'])}, Background: {char['background']}",
                context_type=ContextType.CHARACTER,
                priority=random.randint(5, 8),
                layer_type=LayerType.SEMANTIC_MEMORY,
                metadata={"character_name": char['name'], "type": "character"}
            )
            context_items.append(char_context)
        
        # Generate world building context
        world_context = ContextItem(
            content=story_data.world_building,
            context_type=ContextType.WORLD,
            priority=6,
            layer_type=LayerType.SEMANTIC_MEMORY,
            metadata={"type": "world_building"}
        )
        context_items.append(world_context)
        
        # Calculate expected token usage
        expected_usage = self._calculate_expected_usage(context_items, complexity)
        
        # Determine if this should trigger overflow
        total_expected = sum(expected_usage.values())
        should_overflow = total_expected > 30000  # Assuming 32k limit with 2k buffer
        
        return TestContextScenario(
            name=name,
            description=f"Test scenario with {complexity.value} story complexity",
            context_items=context_items,
            expected_token_usage=expected_usage,
            should_trigger_overflow=should_overflow,
            complexity=complexity
        )
    
    def _calculate_expected_usage(self, context_items: List[ContextItem], 
                                 complexity: StoryComplexity) -> Dict[LayerType, int]:
        """Calculate expected token usage by layer."""
        usage = {layer: 0 for layer in LayerType}
        
        for item in context_items:
            # Rough token estimation
            tokens = len(item.content) // 4
            usage[item.layer_type] += tokens
        
        return usage


class TokenTestDataGenerator:
    """Generates test data specifically for token management testing."""
    
    def __init__(self, seed: Optional[int] = None):
        """Initialize generator with optional seed."""
        if seed is not None:
            random.seed(seed)
    
    def generate_token_stress_test(self, target_tokens: int) -> List[ContextItem]:
        """Generate context items that target a specific token count."""
        items = []
        current_tokens = 0
        
        while current_tokens < target_tokens:
            remaining = target_tokens - current_tokens
            item_size = min(remaining, random.randint(100, 2000))
            
            content = self._generate_content(item_size * 4)  # 4 chars ≈ 1 token
            
            item = ContextItem(
                content=content,
                context_type=random.choice(list(ContextType)),
                priority=random.randint(1, 10),
                layer_type=random.choice(list(LayerType)),
                metadata={"generated": True, "target_tokens": item_size}
            )
            
            items.append(item)
            current_tokens += item_size
        
        return items
    
    def _generate_content(self, target_length: int) -> str:
        """Generate content of approximately target_length characters."""
        words = ["the", "quick", "brown", "fox", "jumps", "over", "lazy", "dog", "and", "runs", "through", "forest"]
        content = ""
        
        while len(content) < target_length:
            word = random.choice(words)
            content += word + " "
        
        return content[:target_length].strip()


# Convenience functions for quick test data generation
def generate_test_story_content(complexity: StoryComplexity = StoryComplexity.MODERATE) -> TestStoryData:
    """Quick function to generate test story content."""
    generator = StoryDataGenerator()
    return generator.generate_story(complexity)


def generate_test_character_data(count: int = 5) -> List[Dict[str, Any]]:
    """Quick function to generate test character data."""
    generator = StoryDataGenerator()
    return [generator._generate_character() for _ in range(count)]


def generate_test_context_items(scenario_name: str = "default", 
                               complexity: StoryComplexity = StoryComplexity.MODERATE) -> List[ContextItem]:
    """Quick function to generate test context items."""
    generator = ContextDataGenerator()
    scenario = generator.generate_context_scenario(scenario_name, complexity)
    return scenario.context_items
