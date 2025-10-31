"""
Context-aware follow-up question generation for worldbuilding conversations.
Analyzes conversation history and generates relevant follow-up questions.
"""
from typing import List, Dict, Set
from app.models.worldbuilding_models import (
    WorldbuildingTopic, FollowupQuestion, TopicContext, WorldbuildingChatContext
)
from app.models.generation_models import ConversationMessage


class WorldbuildingFollowupGenerator:
    """Generates context-aware follow-up questions for worldbuilding conversations."""

    def __init__(self):
        self.topic_question_templates = self._initialize_question_templates()
        self.context_analyzers = self._initialize_context_analyzers()
        self.gap_detectors = self._initialize_gap_detectors()

    def _initialize_question_templates(self) -> Dict[WorldbuildingTopic, Dict[str, List[str]]]:
        """Initialize question templates categorized by type for each topic."""
        return {
            'geography': {
                'exploration': [
                    "What lies beyond {location}?",
                    "How do people travel from {place1} to {place2}?",
                    "What natural resources can be found in {region}?",
                    "What dangers or challenges exist in {area}?"
                ],
                'detail': [
                    "What does {location} look, sound, and smell like?",
                    "What's the weather like in {region} during different seasons?",
                    "How has {geographical_feature} shaped the local culture?",
                    "What legends or stories are told about {landmark}?"
                ],
                'connection': [
                    "How does the geography of {region} affect its politics?",
                    "What trade routes connect {location} to other areas?",
                    "How do the people of {place} adapt to their environment?",
                    "What conflicts arise from geographical boundaries or resources?"
                ],
                'consequence': [
                    "What would happen if {geographical_feature} changed?",
                    "How do natural disasters affect {region}?",
                    "What happens when outsiders try to settle in {area}?",
                    "How does the isolation/accessibility of {place} affect its development?"
                ]
            },
            'culture': {
                'exploration': [
                    "What are the most important cultural values in {society}?",
                    "How do {group} celebrate important life events?",
                    "What taboos or forbidden practices exist in {culture}?",
                    "What does hospitality look like in {society}?"
                ],
                'detail': [
                    "What would a typical day look like for a {social_class} in {society}?",
                    "How do {people} dress for different occasions?",
                    "What foods are considered delicacies or staples in {culture}?",
                    "What art forms or entertainment are most valued?"
                ],
                'connection': [
                    "How do {culture1} and {culture2} interact or conflict?",
                    "What happens when someone breaks a major cultural norm?",
                    "How does {cultural_practice} affect political or economic life?",
                    "What cultural exchanges occur through trade or diplomacy?"
                ],
                'consequence': [
                    "How do cultural differences lead to misunderstandings or conflicts?",
                    "What happens to cultural traditions during times of change?",
                    "How do outsiders adapt to or challenge local customs?",
                    "What cultural practices are changing and why?"
                ]
            },
            'magic_system': {
                'exploration': [
                    "What different schools or types of magic exist?",
                    "How do magical abilities first manifest in people?",
                    "What magical creatures or entities exist in this world?",
                    "What ancient magical knowledge has been lost or forbidden?"
                ],
                'detail': [
                    "What does it feel like to cast {spell_type}?",
                    "What components or tools are needed for {magical_practice}?",
                    "How long does it take to master {magical_skill}?",
                    "What are the visible signs that someone is using magic?"
                ],
                'connection': [
                    "How does magic interact with technology in this world?",
                    "What role do magical practitioners play in politics?",
                    "How does the availability of magic affect economic systems?",
                    "What conflicts arise between magical and non-magical people?"
                ],
                'consequence': [
                    "What happens when magic goes wrong or is misused?",
                    "How do magical accidents or disasters affect society?",
                    "What are the long-term effects of using magic regularly?",
                    "How would society change if magic suddenly disappeared?"
                ]
            },
            'politics': {
                'exploration': [
                    "What are the major political factions or parties?",
                    "How do different regions or territories relate to the central government?",
                    "What succession laws or leadership selection processes exist?",
                    "What diplomatic relationships exist with neighboring powers?"
                ],
                'detail': [
                    "What does a typical political ceremony or court session look like?",
                    "How are political decisions actually made behind the scenes?",
                    "What symbols, titles, or regalia represent political authority?",
                    "How do ordinary citizens interact with or petition the government?"
                ],
                'connection': [
                    "How do economic interests influence political decisions?",
                    "What role does religion play in governance and law?",
                    "How do cultural differences create political tensions?",
                    "What happens when political and magical authorities conflict?"
                ],
                'consequence': [
                    "What would happen if the current government fell?",
                    "How do political purges or power struggles affect society?",
                    "What are the consequences of political corruption or abuse?",
                    "How do wars or external threats change political structures?"
                ]
            },
            'history': {
                'exploration': [
                    "What major historical periods or eras can be identified?",
                    "What historical mysteries or lost knowledge intrigue scholars?",
                    "What cyclical patterns or recurring themes exist in history?",
                    "What historical figures are revered, feared, or controversial?"
                ],
                'detail': [
                    "What was daily life like during {historical_period}?",
                    "How is {historical_event} remembered and commemorated?",
                    "What artifacts or ruins remain from {ancient_civilization}?",
                    "What different versions exist of {historical_story}?"
                ],
                'connection': [
                    "How do historical grievances affect current politics?",
                    "What historical precedents guide current decisions?",
                    "How have past magical or technological discoveries shaped society?",
                    "What historical alliances or enmities still matter today?"
                ],
                'consequence': [
                    "What lessons have been learned or ignored from {historical_event}?",
                    "How do historical injustices continue to affect society?",
                    "What would happen if historical secrets were revealed?",
                    "How do different groups interpret the same historical events?"
                ]
            }
        }

    def _initialize_context_analyzers(self) -> Dict[str, callable]:
        """Initialize functions to analyze conversation context for different patterns."""
        return {
            'mentioned_entities': self._extract_mentioned_entities,
            'topic_depth': self._analyze_topic_depth,
            'conversation_gaps': self._identify_conversation_gaps,
            'user_interests': self._analyze_user_interests,
            'connection_opportunities': self._find_connection_opportunities
        }

    def _initialize_gap_detectors(self) -> Dict[WorldbuildingTopic, List[str]]:
        """Initialize gap detection criteria for each topic."""
        return {
            'geography': [
                'climate_patterns', 'natural_resources', 'major_locations',
                'travel_methods', 'geographical_hazards', 'unique_features'
            ],
            'culture': [
                'core_values', 'social_structure', 'traditions', 'arts_entertainment',
                'daily_life', 'cultural_conflicts', 'belief_systems'
            ],
            'magic_system': [
                'magic_rules', 'magic_users', 'magic_costs', 'magic_types',
                'social_impact', 'magical_creatures', 'magical_locations'
            ],
            'politics': [
                'government_type', 'leadership', 'laws_enforcement', 'political_conflicts',
                'international_relations', 'power_structures', 'citizen_rights'
            ],
            'history': [
                'major_events', 'historical_figures', 'cultural_memory', 'historical_impact',
                'lost_knowledge', 'historical_conflicts', 'timeline'
            ]
        }

    def generate_followup_questions(
        self,
        context: WorldbuildingChatContext,
        recent_messages: List[ConversationMessage],
        max_questions: int = 5
    ) -> List[FollowupQuestion]:
        """Generate context-aware follow-up questions."""

        # Analyze conversation context
        analysis = self._analyze_conversation_context(context, recent_messages)

        # Generate questions based on different strategies
        questions = []

        # 1. Topic-specific questions based on current focus
        questions.extend(self._generate_topic_specific_questions(
            context.current_topic, analysis, max_questions // 2
        ))

        # 2. Gap-filling questions for incomplete areas
        questions.extend(self._generate_gap_filling_questions(
            context, analysis, max_questions // 3
        ))

        # 3. Connection questions linking different topics
        questions.extend(self._generate_connection_questions(
            context, analysis, max_questions // 4
        ))

        # 4. Exploration questions for new areas
        questions.extend(self._generate_exploration_questions(
            context, analysis, max_questions // 4
        ))

        # Sort by priority and return top questions
        questions.sort(key=lambda q: q.priority, reverse=True)
        return questions[:max_questions]

    def _analyze_conversation_context(
        self,
        context: WorldbuildingChatContext,
        recent_messages: List[ConversationMessage]
    ) -> Dict[str, any]:
        """Analyze conversation context to inform question generation."""

        analysis = {
            'mentioned_entities': set(),
            'topic_depth': {},
            'conversation_gaps': [],
            'user_interests': [],
            'recent_topics': [],
            'message_count': len(recent_messages)
        }

        # Analyze recent messages
        for message in recent_messages[-10:]:  # Look at last 10 messages
            if message.role == 'user':
                # Extract entities and topics mentioned
                analysis['mentioned_entities'].update(
                    self._extract_mentioned_entities(message.content)
                )

                # Identify user interests based on what they ask about
                analysis['user_interests'].extend(
                    self._analyze_user_interests(message.content)
                )

        # Analyze topic depth for each active topic
        for topic in context.active_topics:
            if topic in context.topic_contexts:
                topic_context = context.topic_contexts[topic]
                analysis['topic_depth'][topic] = topic_context.completeness_score

        # Identify gaps in worldbuilding coverage
        analysis['conversation_gaps'] = self._identify_conversation_gaps(context)

        return analysis

    def _generate_topic_specific_questions(
        self,
        topic: WorldbuildingTopic,
        analysis: Dict[str, any],
        max_questions: int
    ) -> List[FollowupQuestion]:
        """Generate questions specific to the current topic."""

        questions = []
        if topic not in self.topic_question_templates:
            return questions

        templates = self.topic_question_templates[topic]
        entities = analysis['mentioned_entities']

        # Generate questions for each question type
        for question_type, question_templates in templates.items():
            for template in question_templates[:2]:  # Limit per type
                # Try to fill template with mentioned entities
                filled_question = self._fill_question_template(template, entities)
                if filled_question:
                    priority = self._calculate_question_priority(
                        question_type, topic, analysis
                    )
                    questions.append(FollowupQuestion(
                        question=filled_question,
                        topic=topic,
                        priority=priority,
                        context_dependent=True,
                        reasoning=f"Explores {question_type} aspects of {topic}"
                    ))

        return questions[:max_questions]

    def _generate_gap_filling_questions(
        self,
        context: WorldbuildingChatContext,
        analysis: Dict[str, any],
        max_questions: int
    ) -> List[FollowupQuestion]:
        """Generate questions to fill gaps in worldbuilding coverage."""

        questions = []
        gaps = analysis['conversation_gaps']

        gap_questions = {
            'geography': [
                "What's the climate like in your world?",
                "What are the major geographical features?",
                "How do people travel between different locations?",
                "What natural resources are important?"
            ],
            'culture': [
                "What are the core values of this society?",
                "How is the social structure organized?",
                "What important traditions or customs exist?",
                "How do people express themselves culturally?"
            ],
            'magic_system': [
                "How does magic work in your world?",
                "Who can use magic and how do they learn?",
                "What are the limitations of magic?",
                "How does society view magical practitioners?"
            ],
            'politics': [
                "What type of government exists?",
                "Who holds political power?",
                "How are laws made and enforced?",
                "What are the major political conflicts?"
            ],
            'history': [
                "What are the most important historical events?",
                "How was this world or civilization founded?",
                "What legends or myths shape cultural memory?",
                "How does the past influence the present?"
            ]
        }

        for gap_topic in gaps[:max_questions]:
            if gap_topic in gap_questions:
                question_text = gap_questions[gap_topic][0]  # Use first question
                questions.append(FollowupQuestion(
                    question=question_text,
                    topic=gap_topic,
                    priority=0.8,  # High priority for filling gaps
                    context_dependent=False,
                    reasoning=f"Addresses gap in {gap_topic} coverage"
                ))

        return questions

    def _generate_connection_questions(
        self,
        context: WorldbuildingChatContext,
        analysis: Dict[str, any],
        max_questions: int
    ) -> List[FollowupQuestion]:
        """Generate questions that connect different worldbuilding topics."""

        questions = []
        active_topics = context.active_topics

        connection_templates = [
            "How does {topic1} influence {topic2} in your world?",
            "What happens when {topic1} conflicts with {topic2}?",
            "How do the {topic1} aspects affect {topic2}?",
            "What connections exist between {topic1} and {topic2}?"
        ]

        # Generate connections between active topics
        for i, topic1 in enumerate(active_topics):
            for topic2 in active_topics[i + 1:]:
                if len(questions) >= max_questions:
                    break

                template = connection_templates[len(questions) % len(connection_templates)]
                question_text = template.format(topic1=topic1, topic2=topic2)

                questions.append(FollowupQuestion(
                    question=question_text,
                    topic='general',  # Connection questions are general
                    priority=0.6,
                    context_dependent=True,
                    reasoning=f"Explores connections between {topic1} and {topic2}"
                ))

        return questions[:max_questions]

    def _generate_exploration_questions(
        self,
        context: WorldbuildingChatContext,
        analysis: Dict[str, any],
        max_questions: int
    ) -> List[FollowupQuestion]:
        """Generate questions to explore new or underdeveloped areas."""

        questions = []
        all_topics = list(self.topic_question_templates.keys())
        unexplored_topics = [t for t in all_topics if t not in context.active_topics]

        exploration_starters = {
            'geography': "What does the physical landscape of your world look like?",
            'culture': "Tell me about the people and societies in your world.",
            'magic_system': "Does magic exist in your world, and if so, how does it work?",
            'politics': "What kind of governments or power structures exist?",
            'history': "What important events from the past shape your world?",
            'technology': "What level of technology exists in your world?",
            'economy': "How do people make their living and trade with each other?",
            'religion': "What spiritual beliefs or religions exist?",
            'characters': "Who are the most important or influential people?",
            'languages': "What languages are spoken in your world?",
            'conflicts': "What major conflicts or tensions exist?",
            'organizations': "What important groups or institutions exist?"
        }

        for topic in unexplored_topics[:max_questions]:
            if topic in exploration_starters:
                questions.append(FollowupQuestion(
                    question=exploration_starters[topic],
                    topic=topic,
                    priority=0.4,  # Lower priority for exploration
                    context_dependent=False,
                    reasoning=f"Introduces unexplored topic: {topic}"
                ))

        return questions

    def _extract_mentioned_entities(self, text: str) -> Set[str]:
        """Extract mentioned entities (places, people, concepts) from text."""
        # Simple entity extraction - could be enhanced with NLP
        entities = set()

        # Look for capitalized words (potential proper nouns)
        import re
        capitalized_words = re.findall(r'\b[A-Z][a-z]+\b', text)
        entities.update(capitalized_words)

        # Look for quoted terms
        quoted_terms = re.findall(r'"([^"]*)"', text)
        entities.update(quoted_terms)

        return entities

    def _analyze_topic_depth(self, context: WorldbuildingChatContext) -> Dict[WorldbuildingTopic, float]:
        """Analyze how deeply each topic has been explored."""
        depth_scores = {}

        for topic, topic_context in context.topic_contexts.items():
            # Base score on completeness score and content length
            content_score = min(len(topic_context.accumulated_content) / 1000, 1.0)
            element_score = min(len(topic_context.key_elements) / 10, 1.0)
            question_score = min(len(topic_context.questions_asked) / 5, 1.0)

            depth_scores[topic] = (content_score + element_score + question_score) / 3

        return depth_scores

    def _identify_conversation_gaps(self, context: WorldbuildingChatContext) -> List[WorldbuildingTopic]:
        """Identify topics that haven't been adequately covered."""
        gaps = []
        all_topics = list(self.gap_detectors.keys())

        for topic in all_topics:
            if topic not in context.active_topics:
                gaps.append(topic)
            elif topic in context.topic_contexts:
                topic_context = context.topic_contexts[topic]
                if topic_context.completeness_score < 0.3:  # Less than 30% complete
                    gaps.append(topic)

        return gaps

    def _analyze_user_interests(self, message: str) -> List[str]:
        """Analyze user message to identify their interests and focus areas."""
        interests = []
        message_lower = message.lower()

        # Look for question patterns that indicate interest
        if any(word in message_lower for word in ['tell me about', 'what about', 'how does']):
            interests.append('detail_seeking')

        if any(word in message_lower for word in ['why', 'how', 'what causes']):
            interests.append('explanation_seeking')

        if any(word in message_lower for word in ['example', 'instance', 'specific']):
            interests.append('example_seeking')

        return interests

    def _find_connection_opportunities(self, context: WorldbuildingChatContext) -> List[tuple]:
        """Find opportunities to connect different worldbuilding topics."""
        connections = []
        active_topics = context.active_topics

        # Define natural connections between topics
        natural_connections = {
            ('geography', 'culture'): "How does the environment shape cultural practices?",
            ('politics', 'magic_system'): "How do magical abilities affect political power?",
            ('history', 'conflicts'): "What historical events led to current conflicts?",
            ('economy', 'geography'): "How do natural resources affect trade and wealth?",
            ('religion', 'politics'): "What role does faith play in governance?",
            ('culture', 'languages'): "How do different languages reflect cultural diversity?"
        }

        for (topic1, topic2), question in natural_connections.items():
            if topic1 in active_topics and topic2 in active_topics:
                connections.append((topic1, topic2, question))

        return connections

    def _fill_question_template(self, template: str, entities: Set[str]) -> str:
        """Fill question template with mentioned entities."""
        # Simple template filling - could be enhanced
        import re

        # Find template variables
        variables = re.findall(r'\{([^}]+)\}', template)

        if not variables:
            return template

        # Try to fill with available entities
        filled_template = template
        entity_list = list(entities)

        for i, var in enumerate(variables):
            if i < len(entity_list):
                filled_template = filled_template.replace(f'{{{var}}}', entity_list[i])
            else:
                # Use generic placeholder
                placeholder = var.replace('_', ' ')
                filled_template = filled_template.replace(f'{{{var}}}', f"[{placeholder}]")

        return filled_template

    def _calculate_question_priority(
        self,
        question_type: str,
        topic: WorldbuildingTopic,
        analysis: Dict[str, any]
    ) -> float:
        """Calculate priority score for a question."""
        base_priority = {
            'exploration': 0.7,
            'detail': 0.6,
            'connection': 0.8,
            'consequence': 0.5
        }.get(question_type, 0.5)

        # Boost priority based on topic depth (less explored = higher priority)
        topic_depth = analysis['topic_depth'].get(topic, 0.0)
        depth_boost = (1.0 - topic_depth) * 0.3

        # Boost priority if user has shown interest in this area
        interest_boost = 0.2 if 'detail_seeking' in analysis['user_interests'] else 0.0

        return min(base_priority + depth_boost + interest_boost, 1.0)
