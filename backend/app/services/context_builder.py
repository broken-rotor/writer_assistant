from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

from app.models.request_context import RequestContext, CharacterDetails, CharacterState
from app.services.token_management import TokenCounter
from app.core.config import settings


class ContextRole(str, Enum):
    SYSTEM = 'system'
    USER = 'user'
    ASSISTANT = 'assistant'


class SummarizationStrategy(str, Enum):
    LITERAL = 'literal'
    SUMMARIZED = 'summarized'
    ROLLING_WINDOW = 'rolling_window'
    SUMMARY_AND_ROLLING_WINDOW = 'summary_and_rolling_window'


@dataclass
class ContextItem:
    tag: Optional[str]
    role: str
    content: str
    token_budget: int
    summarization_strategy: SummarizationStrategy = SummarizationStrategy.LITERAL


class ContextBuilder:
    def __init__(self, request_context: RequestContext):
        self._request_context: RequestContext = request_context
        self._elements: List[ContextItem] = []
        self._tokenizer: TokenCounter = TokenCounter(model_path=settings.MODEL_PATH)

    def build_chat(self) -> List[Dict[str, str]]:
        chat = []
        token_limit = 0
        token_count = 0
        for e in self._elements:
            token_limit += e.token_budget
            content, tokens = self._getContent(e, token_limit - token_count)
            chat.append({'role': e.role, 'content': content})
            token_count += tokens
        return chat

    def build_prompt(self) -> str:
        return '\n'.join([e['content'] for e in self.build_chat()])

    def add_system_prompt(self, prompt: str):
        content = prompt
        if self._request_context.configuration.system_prompts.main_prefix:
            content = f"{self._request_context.configuration.system_prompts.main_prefix}\n{content}"
        if self._request_context.configuration.system_prompts.main_suffix:
            content = f"{content}\n{self._request_context.configuration.system_prompts.main_suffix}"
        content = content + '\n'
        self._elements.append(ContextItem(
            tag=None,
            role=ContextRole.SYSTEM,
            content=content,
            token_budget=2000,
            summarization_strategy=SummarizationStrategy.LITERAL))

    def add_worldbbuilding(self):
        if self._request_context.worldbuilding and self._request_context.worldbuilding.content:
            self._elements.append(ContextItem(
                tag='WORLD_BUILDING',
                role=ContextRole.USER,
                content=self._request_context.worldbuilding.content,
                token_budget=2000,
                summarization_strategy=SummarizationStrategy.SUMMARIZED))

    def add_characters(self):
        def format_character(c: CharacterDetails) -> str:
            return (
                f"- Name: {c.name}\n"
                f"  Basic Bio: {c.basic_bio}\n"
                f"  Sex: {c.sex}\n"
                f"  Gender: {c.gender}\n"
                f"  Sexual Preference: {c.sexual_preference}\n"
                f"  Age: {c.age}\n"
                f"  Physical Appearance: {c.physical_appearance}\n"
                f"  Usual Clothing: {c.usual_clothing}\n"
                f"  Personality: {c.personality}\n"
                f"  Motivations: {c.motivations}\n"
                f"  Fears: {c.fears}\n"
                f"  Relationships: {c.relationships}\n"
            )

        if self._request_context.characters:
            characters = '\n'.join([format_character(c)for c in self._request_context.characters if not c.is_hidden])
            if characters:
                self._elements.append(ContextItem(
                    tag='CHARACTERS',
                    role=ContextRole.USER,
                    content=characters,
                    token_budget=2000,
                    summarization_strategy=SummarizationStrategy.SUMMARIZED))

    def add_story_outline(self):
        if self._request_context.story_outline and self._request_context.story_outline.summary:
            self._elements.append(ContextItem(
                tag='STORY_SUMMARY',
                role=ContextRole.USER,
                content=self._request_context.story_outline.summary,
                token_budget=2000,
                summarization_strategy=SummarizationStrategy.SUMMARIZED))
        if self._request_context.story_outline and self._request_context.story_outline.content:
            self._elements.append(ContextItem(
                tag='STORY_OUTLINE',
                role=ContextRole.USER,
                content=self._request_context.story_outline.content,
                token_budget=2000,
                summarization_strategy=SummarizationStrategy.LITERAL))

    def add_character_states(self):
        def format_list(header: str, items: list[str]) -> str:
            return (f"  {header}:\n" + "".join([f"  - {i}\n" for i in items])) if items else ""

        def format_character_state(c: CharacterState) -> str:
            content = ''.join([
                format_list("Recent Actions", c.recent_actions),
                format_list("Recent Dialog", c.recent_dialog),
                format_list("Recent Physical Sensations", c.physicalSensations),
                format_list("Recent Emotions", c.emotions),
                format_list("Recent Internal Monologue/Thoughts", c.internalMonologue),
                format_list("Current Goals", c.goals),
                format_list("Memories", c.memories)
            ])
            return f"- Name: {c.name}\n{content}" if content else ""

        if self._request_context.character_states:
            character_states = "".join([format_character_state(c) for c in self._request_context.character_states])
            if character_states:
                self._elements.append(ContextItem(
                    tag='CHARACTER_STATES',
                    role=ContextRole.USER,
                    content=character_states,
                    token_budget=2000,
                    summarization_strategy=SummarizationStrategy.SUMMARIZED))

    def add_recent_story(self):
        ## FIXME ##
        content = ''
        if content:
            self._elements.append(ContextItem(
                tag='RECENT_STORY',
                role=ContextRole.USER,
                content=content,
                token_budget=15000,
                summarization_strategy=SummarizationStrategy.SUMMARY_AND_ROLLING_WINDOW))

    def add_agent_instruction(self, prompt: str):
        self._elements.append(ContextItem(
            tag=None,
            role=ContextRole.USER,
            content=prompt,
            token_budget=2000,
            summarization_strategy=SummarizationStrategy.LITERAL))

    def add_chat(self, role: ContextRole, content: str):
        ## FIXME ##
        self._elements.append(ContextItem(
            tag=None,
            role=role,
            content=content,
            token_budget=5000,
            summarization_strategy=SummarizationStrategy.ROLLING_WINDOW))

    def _getContent(self, e: ContextItem, token_budget: int):
        content = f'<{e.tag}>\n{e.content}\n</{e.tag}>\n' if e.tag else e.content
        token_count = self._tokenizer.count_tokens(content)
        if token_count <= token_budget:
            return content, token_count
        ## FIXME ##
        if e.summarization_strategy == SummarizationStrategy.SUMMARIZED:
            pass
        elif e.summarization_strategy == SummarizationStrategy.ROLLING_WINDOW:
            pass
        elif e.summarization_strategy == SummarizationStrategy.SUMMARY_AND_ROLLING_WINDOW:
            pass
        raise ValueError(f"Token budget exceeded {token_count} > {token_budget} for {e.tag} {e.role}")