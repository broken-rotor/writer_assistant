"""
Topic classification service for worldbuilding conversations.
Classifies user messages into worldbuilding topics and suggests transitions.
"""
import re
from typing import List, Dict, Set
from app.models.worldbuilding_models import (
    WorldbuildingTopic, TopicClassificationResult, TopicTransition
)


class WorldbuildingTopicClassifier:
    """Classifies messages into worldbuilding topics using keyword matching and patterns."""

    def __init__(self):
        self.topic_keywords = self._initialize_topic_keywords()
        self.topic_patterns = self._initialize_topic_patterns()
        self.transition_triggers = self._initialize_transition_triggers()

    def _initialize_topic_keywords(self) -> Dict[WorldbuildingTopic, Set[str]]:
        """Initialize keyword sets for each worldbuilding topic."""
        return {
            'geography': {
                'mountain', 'river', 'ocean', 'forest', 'desert', 'city', 'town', 'village',
                'continent', 'island', 'valley', 'plain', 'hill', 'lake', 'sea', 'coast',
                'terrain', 'landscape', 'region', 'territory', 'border', 'climate', 'weather',
                'location', 'place', 'map', 'distance', 'travel', 'journey', 'path', 'road'
            },
            'culture': {
                'culture', 'society', 'tradition', 'custom', 'ritual', 'ceremony', 'festival',
                'belief', 'value', 'norm', 'practice', 'lifestyle', 'art', 'music', 'dance',
                'food', 'cuisine', 'clothing', 'fashion', 'architecture', 'building', 'house',
                'family', 'families', 'marriage', 'education', 'social', 'community', 'tribe', 'clan',
                'organize', 'organization', 'structure', 'hierarchy', 'relationship', 'kinship'
            },
            'magic_system': {
                'magic', 'spell', 'wizard', 'mage', 'sorcerer', 'enchantment', 'potion',
                'artifact', 'rune', 'crystal', 'power', 'ability', 'supernatural', 'mystical',
                'arcane', 'divine', 'elemental', 'energy', 'force', 'charm', 'curse',
                'ritual', 'incantation', 'wand', 'staff', 'tome', 'grimoire', 'familiar'
            },
            'politics': {
                'government', 'king', 'queen', 'emperor', 'ruler', 'lord', 'noble', 'court',
                'kingdom', 'empire', 'republic', 'democracy', 'monarchy', 'council', 'senate',
                'law', 'rule', 'decree', 'policy', 'alliance', 'treaty', 'war', 'peace',
                'diplomacy', 'ambassador', 'minister', 'official', 'authority', 'power',
                'throne', 'crown', 'succession', 'rebellion', 'revolution', 'coup'
            },
            'history': {
                'history', 'past', 'ancient', 'old', 'legend', 'myth', 'story', 'tale',
                'chronicle', 'record', 'event', 'war', 'battle', 'conquest', 'founding',
                'creation', 'origin', 'beginning', 'age', 'era', 'period', 'time',
                'ancestor', 'predecessor', 'heritage', 'legacy', 'tradition', 'relic',
                'artifact', 'ruins', 'monument', 'memorial', 'timeline', 'chronology'
            },
            'technology': {
                'technology', 'invention', 'tool', 'weapon', 'armor', 'machine', 'device',
                'craft', 'skill', 'technique', 'method', 'process', 'material', 'metal',
                'forge', 'smith', 'engineer', 'builder', 'construction', 'transportation',
                'communication', 'medicine', 'healing', 'alchemy', 'science', 'knowledge',
                'discovery', 'innovation', 'advancement', 'progress', 'development',
                'ship', 'ships', 'vessel', 'vehicle', 'flying', 'powered', 'engine'
            },
            'economy': {
                'trade', 'merchant', 'market', 'shop', 'store', 'goods', 'product', 'service',
                'money', 'coin', 'currency', 'gold', 'silver', 'wealth', 'rich', 'poor',
                'price', 'cost', 'value', 'exchange', 'barter', 'commerce', 'business',
                'guild', 'craft', 'profession', 'job', 'work', 'labor', 'resource',
                'mining', 'farming', 'agriculture', 'industry', 'production', 'export', 'import'
            },
            'religion': {
                'god', 'goddess', 'deity', 'divine', 'holy', 'sacred', 'temple', 'shrine',
                'church', 'priest', 'cleric', 'monk', 'nun', 'prophet', 'oracle', 'faith',
                'belief', 'worship', 'prayer', 'ritual', 'ceremony', 'blessing', 'curse',
                'heaven', 'hell', 'afterlife', 'soul', 'spirit', 'angel', 'demon',
                'religion', 'mythology', 'pantheon', 'scripture', 'doctrine', 'dogma'
            },
            'characters': {
                'character', 'person', 'people', 'individual', 'hero', 'villain', 'protagonist',
                'antagonist', 'leader', 'follower', 'friend', 'enemy', 'ally', 'rival',
                'family', 'relative', 'parent', 'child', 'sibling', 'spouse', 'lover',
                'mentor', 'student', 'teacher', 'master', 'apprentice', 'companion',
                'personality', 'trait', 'characteristic', 'behavior', 'motivation', 'goal'
            },
            'languages': {
                'language', 'tongue', 'dialect', 'accent', 'speech', 'word', 'phrase',
                'vocabulary', 'grammar', 'syntax', 'writing', 'script', 'alphabet',
                'letter', 'symbol', 'rune', 'text', 'book', 'document', 'communication',
                'translation', 'interpreter', 'scholar', 'scribe', 'literature', 'poetry',
                'song', 'chant', 'spell', 'incantation', 'name', 'naming', 'etymology'
            },
            'conflicts': {
                'war', 'battle', 'fight', 'conflict', 'struggle', 'dispute', 'argument',
                'disagreement', 'tension', 'rivalry', 'competition', 'enemy', 'opponent',
                'threat', 'danger', 'crisis', 'problem', 'challenge', 'obstacle',
                'invasion', 'attack', 'defense', 'siege', 'campaign', 'strategy', 'tactics',
                'victory', 'defeat', 'surrender', 'truce', 'ceasefire', 'peace'
            },
            'organizations': {
                'organization', 'group', 'faction', 'party', 'guild', 'order', 'society',
                'club', 'association', 'brotherhood', 'sisterhood', 'company', 'corporation',
                'institution', 'establishment', 'council', 'committee', 'board', 'assembly',
                'alliance', 'coalition', 'union', 'league', 'confederation', 'federation',
                'army', 'military', 'guard', 'police', 'force', 'unit', 'squad', 'team'
            },
            'general': {
                'world', 'setting', 'universe', 'realm', 'dimension', 'plane', 'reality',
                'creation', 'existence', 'life', 'nature', 'environment', 'atmosphere',
                'mood', 'tone', 'theme', 'concept', 'idea', 'vision', 'inspiration'
            }
        }

    def _initialize_topic_patterns(self) -> Dict[WorldbuildingTopic, List[str]]:
        """Initialize regex patterns for topic detection."""
        return {
            'geography': [
                r'\b(?:where|location|place|situated|located|positioned)\b',
                r'\b(?:north|south|east|west|center|middle)\b.*\b(?:of|from)\b',
                r'\b(?:miles|kilometers|distance|far|near|close)\b',
                r'\b(?:climate|weather|season|temperature|rain|snow)\b'
            ],
            'culture': [
                r'\b(?:people|folk|inhabitants|citizens|residents)\b.*\b(?:do|practice|believe)\b',
                r'\b(?:tradition|custom|ritual|ceremony|festival)\b',
                r'\b(?:art|music|dance|food|clothing|architecture)\b',
                r'\b(?:social|society|community|family|marriage)\b'
            ],
            'magic_system': [
                r'\b(?:how|what|why)\b.*\b(?:magic|spell|power|ability)\b',
                r'\b(?:cast|casting|channel|channeling|invoke|invoking)\b',
                r'\b(?:mana|energy|force|essence|source)\b',
                r'\b(?:learn|learning|study|studying|master|mastering)\b.*\b(?:magic|spells)\b'
            ],
            'politics': [
                r'\b(?:who|what)\b.*\b(?:rules|governs|leads|controls)\b',
                r'\b(?:government|political|politics|power|authority)\b',
                r'\b(?:law|legal|illegal|crime|justice|court)\b',
                r'\b(?:alliance|treaty|war|peace|diplomacy)\b'
            ],
            'history': [
                r'\b(?:what|when|how)\b.*\b(?:happened|occurred|began|started|founded|created)\b',
                r'\b(?:ago|past|ancient|old|historical|history)\b',
                r'\b(?:legend|myth|story|tale|chronicle)\b',
                r'\b(?:before|after|during|since)\b.*\b(?:war|age|era|period)\b'
            ]
        }

    def _initialize_transition_triggers(self) -> Dict[str, WorldbuildingTopic]:
        """Initialize phrases that suggest topic transitions."""
        return {
            'tell me about': 'general',
            'what about': 'general',
            'how about': 'general',
            'speaking of': 'general',
            'that reminds me': 'general',
            'on another note': 'general',
            'changing topics': 'general',
            'moving on': 'general'
        }

    def classify_message(self, message: str, current_topic: WorldbuildingTopic = 'general') -> TopicClassificationResult:
        """Classify a message into worldbuilding topics."""
        message_lower = message.lower()
        topic_scores = {}
        keywords_found = []

        # Score each topic based on keyword matches
        for topic, keywords in self.topic_keywords.items():
            score = 0
            topic_keywords = []

            for keyword in keywords:
                if keyword in message_lower:
                    score += 1
                    topic_keywords.append(keyword)

            # Apply pattern matching bonus
            if topic in self.topic_patterns:
                for pattern in self.topic_patterns[topic]:
                    if re.search(pattern, message_lower):
                        score += 2  # Pattern matches are weighted higher

            # Apply contextual bonuses for better classification
            score = self._apply_contextual_bonuses(message_lower, topic, score)

            if score > 0:
                topic_scores[topic] = score
                keywords_found.extend(topic_keywords)

        # Determine primary topic
        if not topic_scores:
            primary_topic = current_topic  # Stay with current topic if no clear match
            confidence = 0.3
        else:
            primary_topic = max(topic_scores, key=topic_scores.get)
            max_score = topic_scores[primary_topic]
            total_score = sum(topic_scores.values())

            # Improved confidence calculation
            if total_score == max_score:
                # Only one topic matched
                confidence = min(0.8, max_score / 3.0)  # Cap at 0.8, scale by keyword count
            else:
                # Multiple topics matched
                confidence = max_score / total_score
                # Boost confidence if there's a clear winner
                if max_score >= total_score * 0.6:
                    confidence = min(confidence * 1.2, 1.0)
                # Additional boost for topic transitions with strong indicators
                elif max_score >= 3 and confidence > 0.5:
                    confidence = min(confidence * 1.1, 0.9)

        # Find secondary topics
        secondary_topics = [
            topic for topic, score in topic_scores.items()
            if topic != primary_topic and score >= max(topic_scores.get(primary_topic, 0) * 0.5, 1)
        ]

        # Check for topic transition (lower threshold for better detection)
        suggested_transition = None
        if primary_topic != current_topic and confidence > 0.4:
            suggested_transition = TopicTransition(
                from_topic=current_topic,
                to_topic=primary_topic,
                trigger_message=message,
                confidence=confidence,
                suggested_questions=self._get_topic_questions(primary_topic)
            )

        return TopicClassificationResult(
            primary_topic=primary_topic,
            confidence=confidence,
            secondary_topics=secondary_topics,
            keywords_found=list(set(keywords_found)),
            suggested_transition=suggested_transition
        )

    def _get_topic_questions(self, topic: WorldbuildingTopic) -> List[str]:
        """Get suggested follow-up questions for a topic."""
        topic_questions = {
            'geography': [
                "What are the major geographical features of this region?",
                "How does the climate affect daily life here?",
                "What are the important cities or settlements?",
                "How do people travel between different locations?"
            ],
            'culture': [
                "What are the most important cultural traditions?",
                "How do people typically dress and behave?",
                "What are the social hierarchies and customs?",
                "What art forms and entertainment are popular?"
            ],
            'magic_system': [
                "How does magic work in this world?",
                "Who can use magic and how do they learn it?",
                "What are the limitations and costs of magic?",
                "How does society view and regulate magic use?"
            ],
            'politics': [
                "What type of government system exists?",
                "Who holds power and how is it maintained?",
                "What are the major political conflicts or tensions?",
                "How are laws made and enforced?"
            ],
            'history': [
                "What are the most significant historical events?",
                "How was this world or civilization founded?",
                "What major conflicts or changes shaped the current era?",
                "What legends or myths are important to understand?"
            ],
            'technology': [
                "What is the general level of technological advancement?",
                "What are the most important inventions or tools?",
                "How do people communicate and travel?",
                "What materials and techniques are commonly used?"
            ],
            'economy': [
                "What are the main sources of wealth and trade?",
                "How do people make a living?",
                "What goods and services are most valuable?",
                "How is commerce organized and regulated?"
            ],
            'religion': [
                "What gods, deities, or spiritual beliefs exist?",
                "How do people practice their faith?",
                "What role does religion play in daily life and politics?",
                "Are there religious conflicts or different belief systems?"
            ],
            'characters': [
                "Who are the most important or influential people?",
                "What kinds of personalities and motivations drive key figures?",
                "How do different social classes or groups interact?",
                "What notable heroes, villains, or leaders exist?"
            ],
            'languages': [
                "What languages are spoken and by whom?",
                "How do different groups communicate with each other?",
                "Are there written scripts or special forms of communication?",
                "Do certain languages have cultural or magical significance?"
            ],
            'conflicts': [
                "What are the major sources of tension or conflict?",
                "Are there ongoing wars, disputes, or rivalries?",
                "How do different factions or groups oppose each other?",
                "What threatens the stability or peace of this world?"
            ],
            'organizations': [
                "What important groups, guilds, or organizations exist?",
                "How are these organizations structured and led?",
                "What are their goals, methods, and areas of influence?",
                "How do different organizations interact or compete?"
            ],
            'general': [
                "What makes this world unique or interesting?",
                "What aspects of the world would you like to explore further?",
                "How do all these elements work together to create the setting?",
                "What mood or atmosphere are you trying to create?"
            ]
        }

        return topic_questions.get(topic, topic_questions['general'])

    def _apply_contextual_bonuses(self, message_lower: str, topic: WorldbuildingTopic, base_score: int) -> int:
        """Apply contextual bonuses to improve classification accuracy."""
        score = base_score

        # Magic system bonuses
        if topic == 'magic_system':
            magic_indicators = ['arcane', 'mystical', 'supernatural', 'enchant', 'spell', 'magic', 'wizard', 'mage']
            if any(indicator in message_lower for indicator in magic_indicators):
                score += 2  # Strong magic indicator

            # Boost for magic-specific phrases
            if any(phrase in message_lower for phrase in ['forbidden magic', 'arcane arts', 'magical power', 'cast spell']):
                score += 3

        # Culture bonuses
        elif topic == 'culture':
            culture_indicators = ['tradition', 'custom', 'value', 'belief', 'practice', 'honor', 'society']
            if any(indicator in message_lower for indicator in culture_indicators):
                score += 1

            # Boost for culture-specific phrases
            if any(
                phrase in message_lower for phrase in [
                    'people value',
                    'cultural tradition',
                    'social custom',
                    'developed unique traditions',
                    'people have developed']):
                score += 2

        # Geography bonuses
        elif topic == 'geography':
            geo_indicators = ['mountain', 'river', 'valley', 'hill', 'forest', 'desert', 'ocean', 'lake']
            geo_count = sum(1 for indicator in geo_indicators if indicator in message_lower)
            if geo_count >= 2:  # Multiple geographical features mentioned
                score += 2

        # Technology bonuses
        elif topic == 'technology':
            tech_indicators = ['ship', 'ships', 'flying', 'powered', 'engine', 'machine', 'device', 'vehicle']
            if any(indicator in message_lower for indicator in tech_indicators):
                score += 1

            # Boost for technology-specific phrases
            if any(phrase in message_lower for phrase in ['flying ships', 'powered by', 'use ships', 'transportation']):
                score += 2

        # Politics bonuses
        elif topic == 'politics':
            politics_indicators = ['ruled', 'rule', 'ruler', 'government',
                                   'king', 'queen', 'emperor', 'control', 'power', 'authority']
            if any(indicator in message_lower for indicator in politics_indicators):
                score += 1

            # Boost for politics-specific phrases
            if any(
                phrase in message_lower for phrase in [
                    'is ruled by',
                    'ruled by',
                    'controls the',
                    'who controls',
                    'government of']):
                score += 3

        # Politics penalty for magic-related content (but not for political control of magic)
        if topic == 'politics' and any(magic_word in message_lower for magic_word in ['arcane', 'spell', 'mystical']):
            # Don't penalize if it's about political control of magic
            if not any(control_phrase in message_lower for control_phrase in ['controls the magic', 'ruled by', 'keeper']):
                score = max(0, score - 2)  # Reduce politics score for magical content

        # Magic system penalty for technology-related content
        if topic == 'magic_system' and any(
            tech_word in message_lower for tech_word in [
                'ship',
                'ships',
                'flying ships',
                'vehicle',
                'transportation']):
            score = max(0, score - 1)  # Reduce magic score for technological content

        return score

    def suggest_topic_exploration(self, current_topics: List[WorldbuildingTopic]) -> List[WorldbuildingTopic]:
        """Suggest unexplored topics based on current conversation."""
        all_topics = list(self.topic_keywords.keys())
        unexplored = [topic for topic in all_topics if topic not in current_topics]

        # Prioritize core worldbuilding topics
        priority_topics = ['geography', 'culture', 'politics', 'history', 'magic_system']
        priority_unexplored = [topic for topic in priority_topics if topic in unexplored]

        return priority_unexplored + [topic for topic in unexplored if topic not in priority_unexplored]
