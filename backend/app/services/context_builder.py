from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Set

from app.models.request_context import RequestContext, CharacterDetails, CharacterState
from app.services.llm_inference import LLMInference


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

    def structured_content(self):
        return f'<{self.tag}>\n{self.content.strip()}\n</{self.tag}>\n' if self.tag else self.content


class ContextBuilder:
    def __init__(self, request_context: RequestContext, model: LLMInference):
        self._request_context: RequestContext = request_context
        self._elements: List[ContextItem] = []
        self._model: LLMInference = model

    def build_messages(self) -> List[Dict[str, str]]:
        chat = []
        token_limit = 0
        token_count = 0
        for e in self._elements:
            token_limit += e.token_budget
            content, tokens = self._get_content(e, token_limit - token_count)
            chat.append({'role': e.role, 'content': content.strip()})
            token_count += tokens
        return chat

    def build_prompt(self) -> str:
        return '\n'.join([e['content'] for e in self.build_messages()])

    def add_long_term_elements(self, system_prompt: str):
        self.add_system_prompt(system_prompt)
        self.add_worldbuilding()
        self.add_characters()
        self.add_story_outline()

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

    def add_worldbuilding(self):
        if self._request_context.worldbuilding and self._request_context.worldbuilding.content:
            self._elements.append(ContextItem(
                tag='WORLD_BUILDING',
                role=ContextRole.USER,
                content=self._request_context.worldbuilding.content,
                token_budget=2000,
                summarization_strategy=SummarizationStrategy.SUMMARIZED))

    def add_characters(self, tag: str = 'CHARACTERS', exclude_characters: Set[str] = {}, include_characters: Set[str] = {}):
        def add_item(title: str, element) -> str:
            return f"  {title}: {element}\n" if element else ""

        def format_character(c: CharacterDetails) -> str:
            content = ''
            content += add_item("Basic Bio", c.basic_bio)
            content += add_item("Sex", c.sex)
            content += add_item("Gender", c.gender)
            content += add_item("Sexual Preference", c.sexual_preference)
            content += add_item("Age", c.age)
            content += add_item("Physical Appearance", c.physical_appearance)

            content += add_item("Usual Clothing", c.usual_clothing)
            content += add_item("Personality", c.personality)
            content += add_item("Motivations", c.motivations)
            content += add_item("Fears", c.fears)
            content += add_item("Relationships", c.relationships)
            return f"- Name: {c.name}\n{content}" if content else ""

        if self._request_context.characters:
            characters = '\n'.join(
                [format_character(c)
                 for c in self._request_context.characters
                 if (not c.is_hidden and
                     c.name not in exclude_characters and
                     (not include_characters or c.name in include_characters))])
            if characters:
                self._elements.append(ContextItem(
                    tag=tag,
                    role=ContextRole.USER,
                    content=characters,
                    token_budget=2000,
                    summarization_strategy=SummarizationStrategy.SUMMARIZED))

    def add_story_outline(self):
        if self._request_context.context_metadata.story_title:
            self._elements.append(ContextItem(
                tag='STORY_TITLE',
                role=ContextRole.USER,
                content=self._request_context.context_metadata.story_title,
                token_budget=2000,
                summarization_strategy=SummarizationStrategy.LITERAL))
        if self._request_context.story_outline and self._request_context.story_outline.summary:
            self._elements.append(ContextItem(
                tag='STORY_SUMMARY',
                role=ContextRole.USER,
                content=self._request_context.story_outline.summary,
                token_budget=2000,
                summarization_strategy=SummarizationStrategy.LITERAL))
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

    def add_recent_story(self, include_up_to: Optional[int] = None):
        ## FIXME ##
        content = ''
        if content:
            self._elements.append(ContextItem(
                tag='RECENT_STORY',
                role=ContextRole.USER,
                content=content,
                token_budget=15000,
                summarization_strategy=SummarizationStrategy.SUMMARY_AND_ROLLING_WINDOW))

    def add_recent_story_summary(self):
        ## FIXME ##
        content = ''
        if content:
            self._elements.append(ContextItem(
                tag='RECENT_STORY_SUMMARY',
                role=ContextRole.USER,
                content=content,
                token_budget=5000,
                summarization_strategy=SummarizationStrategy.SUMMARIZED))

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

    def _get_content(self, e: ContextItem, token_budget: int) -> (str, int):
        content = e.structured_content()

        content_truncation = self._model.truncate_to_tokens(content, token_budget)
        if content_truncation.head is None:
            return content_truncation.tail, content_truncation.tail_token_count

        if e.summarization_strategy == SummarizationStrategy.SUMMARIZED:
            return self._summarize(content)
        elif e.summarization_strategy == SummarizationStrategy.ROLLING_WINDOW:
            return content_truncation.tail, content_truncation.tail_token_count
        elif e.summarization_strategy == SummarizationStrategy.SUMMARY_AND_ROLLING_WINDOW:
            content_truncation = self._model.truncate_to_tokens(content, int(token_budget * 0.60))
            summary, summary_count = self._summarize(content_truncation.head)
            return f"{summary}\n{content_truncation.tail}", summary_count + content_truncation.tail_token_count
        else:
            raise ValueError(f"Token budget exceeded {content_truncation.tail_token_count} > {token_budget} for {e.tag} {e.role}")

    def _summarize(self, content: str) -> (str, int):
        ## FIXME ##
        return '', 0