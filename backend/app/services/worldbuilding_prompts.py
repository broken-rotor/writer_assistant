"""
Worldbuilding prompt templates for different topics and conversation contexts.
Provides specialized prompts for various aspects of world creation.
"""
from typing import Dict, List
from app.models.worldbuilding_models import WorldbuildingTopic, WorldbuildingPromptTemplate


class WorldbuildingPromptService:
    """Service for managing worldbuilding-specific prompts and templates."""
    
    def __init__(self):
        self.prompt_templates = self._initialize_prompt_templates()
        self.conversation_starters = self._initialize_conversation_starters()
        self.follow_up_generators = self._initialize_follow_up_generators()
    
    def _initialize_prompt_templates(self) -> Dict[WorldbuildingTopic, WorldbuildingPromptTemplate]:
        """Initialize comprehensive prompt templates for each worldbuilding topic."""
        return {
            'geography': WorldbuildingPromptTemplate(
                topic='geography',
                system_prompt="""You are a worldbuilding specialist focused on geography and physical settings. Help users create detailed, immersive physical worlds including landscapes, climates, locations, and how geography affects civilization. Ask thoughtful questions about terrain, weather patterns, natural resources, and how the physical world shapes the societies that inhabit it.""",
                context_prompt="""Focus on geographical and physical aspects of the world. Consider:
- Major landforms (mountains, rivers, forests, deserts, etc.)
- Climate patterns and weather systems
- Natural resources and their distribution
- How geography influences settlements and travel
- Unique or fantastical geographical features
- The relationship between environment and civilization""",
                followup_prompts=[
                    "What major geographical features define this region?",
                    "How does the climate affect daily life and culture?",
                    "What natural resources are available and how are they used?",
                    "How do people travel and trade across different terrains?",
                    "Are there any unique or magical geographical phenomena?"
                ],
                key_questions=[
                    "What does the overall landscape look like?",
                    "What are the major cities, towns, or settlements?",
                    "How do seasons and weather patterns work?",
                    "What natural barriers or connections exist between regions?",
                    "How has geography shaped the development of civilizations?"
                ],
                completion_criteria=[
                    "Major landforms and terrain types described",
                    "Climate and weather patterns established",
                    "Key locations and settlements identified",
                    "Natural resources and their uses explained",
                    "Geographic influences on society addressed"
                ]
            ),
            
            'culture': WorldbuildingPromptTemplate(
                topic='culture',
                system_prompt="""You are a worldbuilding specialist focused on cultures and societies. Help users develop rich, authentic cultural systems including traditions, customs, social structures, arts, and daily life. Ask insightful questions about values, beliefs, social norms, and how culture shapes behavior and identity.""",
                context_prompt="""Focus on cultural and social aspects of the world. Consider:
- Core values, beliefs, and worldviews
- Social structures and hierarchies
- Traditions, customs, and rituals
- Arts, entertainment, and cultural expression
- Daily life, work, and social interactions
- How culture varies between different groups or regions""",
                followup_prompts=[
                    "What are the core values and beliefs of this culture?",
                    "How is society organized and structured?",
                    "What important traditions or rituals exist?",
                    "How do people express themselves through art and culture?",
                    "What does daily life look like for different social groups?"
                ],
                key_questions=[
                    "What do people in this culture value most?",
                    "How are families and communities organized?",
                    "What are the most important cultural celebrations or events?",
                    "How do different social classes or groups interact?",
                    "What forms of art, music, or entertainment are popular?"
                ],
                completion_criteria=[
                    "Core cultural values and beliefs defined",
                    "Social structure and hierarchies established",
                    "Important traditions and customs described",
                    "Cultural expressions and arts outlined",
                    "Daily life patterns for different groups explained"
                ]
            ),
            
            'magic_system': WorldbuildingPromptTemplate(
                topic='magic_system',
                system_prompt="""You are a worldbuilding specialist focused on magic systems and supernatural elements. Help users create consistent, logical magic systems with clear rules, limitations, and consequences. Ask detailed questions about how magic works, who can use it, what it costs, and how it affects society.""",
                context_prompt="""Focus on magical and supernatural aspects of the world. Consider:
- How magic works and its fundamental rules
- Who can use magic and how they learn it
- Limitations, costs, and consequences of magic use
- Different types or schools of magic
- How society views and regulates magic
- The impact of magic on technology, politics, and daily life""",
                followup_prompts=[
                    "What are the fundamental rules of how magic works?",
                    "Who can use magic and how do they develop their abilities?",
                    "What are the costs, limitations, or dangers of magic?",
                    "How does society view and control magical practices?",
                    "What different types or schools of magic exist?"
                ],
                key_questions=[
                    "What is the source or origin of magical power?",
                    "How do people learn and practice magic?",
                    "What can and cannot be accomplished with magic?",
                    "How does magic affect the balance of power in society?",
                    "Are there magical creatures, artifacts, or locations?"
                ],
                completion_criteria=[
                    "Magic system rules and mechanics defined",
                    "Magic users and learning methods established",
                    "Limitations and costs clearly outlined",
                    "Social impact and regulation addressed",
                    "Different magical disciplines or types described"
                ]
            ),
            
            'politics': WorldbuildingPromptTemplate(
                topic='politics',
                system_prompt="""You are a worldbuilding specialist focused on political systems and governance. Help users create complex, realistic political structures including governments, power dynamics, laws, and conflicts. Ask probing questions about leadership, authority, justice, and how political systems affect people's lives.""",
                context_prompt="""Focus on political and governmental aspects of the world. Consider:
- Types of government and leadership structures
- How power is gained, maintained, and transferred
- Legal systems and law enforcement
- Political conflicts, alliances, and tensions
- How politics affects different social groups
- International or inter-regional relations""",
                followup_prompts=[
                    "What type of government or leadership system exists?",
                    "How do leaders gain and maintain their power?",
                    "What are the major political conflicts or tensions?",
                    "How are laws made, enforced, and adjudicated?",
                    "What political alliances or rivalries exist?"
                ],
                key_questions=[
                    "Who holds political power and how did they get it?",
                    "What are the major political institutions or bodies?",
                    "How are disputes and crimes handled?",
                    "What are the biggest political challenges or threats?",
                    "How do different regions or groups relate politically?"
                ],
                completion_criteria=[
                    "Government structure and leadership defined",
                    "Power dynamics and succession explained",
                    "Legal system and enforcement established",
                    "Major political conflicts identified",
                    "Inter-group political relationships described"
                ]
            ),
            
            'history': WorldbuildingPromptTemplate(
                topic='history',
                system_prompt="""You are a worldbuilding specialist focused on history and historical events. Help users create rich historical backgrounds including major events, timelines, legends, and how the past shapes the present. Ask thoughtful questions about origins, conflicts, changes, and the legacy of historical events.""",
                context_prompt="""Focus on historical and temporal aspects of the world. Consider:
- Major historical events and their consequences
- Timeline of important developments and changes
- Legends, myths, and cultural memories
- How the past influences current politics and society
- Historical figures and their lasting impact
- Cycles of rise and fall, conflict and peace""",
                followup_prompts=[
                    "What are the most significant events in this world's history?",
                    "How was this civilization or world founded?",
                    "What major conflicts or changes shaped the current era?",
                    "What legends or myths are important to understand?",
                    "How do historical events still influence the present?"
                ],
                key_questions=[
                    "What are the origins of the current civilizations?",
                    "What major wars, disasters, or changes occurred?",
                    "Who were the most important historical figures?",
                    "What historical events are celebrated or mourned?",
                    "How accurate are the historical records and legends?"
                ],
                completion_criteria=[
                    "Major historical events and timeline established",
                    "Origins and founding stories described",
                    "Important historical figures identified",
                    "Cultural legends and myths outlined",
                    "Historical influence on present explained"
                ]
            ),
            
            'technology': WorldbuildingPromptTemplate(
                topic='technology',
                system_prompt="""You are a worldbuilding specialist focused on technology and innovation. Help users develop consistent technological levels including tools, weapons, transportation, communication, and how technology affects society. Ask detailed questions about materials, methods, and the social impact of technological development.""",
                context_prompt="""Focus on technological and material aspects of the world. Consider:
- General level of technological advancement
- Important tools, weapons, and devices
- Materials, crafting techniques, and manufacturing
- Transportation and communication methods
- How technology affects social structures and daily life
- The relationship between technology and magic (if applicable)""",
                followup_prompts=[
                    "What is the general level of technological development?",
                    "What are the most important tools, weapons, or inventions?",
                    "How do people travel and communicate over distances?",
                    "What materials and techniques are used in crafting?",
                    "How does technology affect social classes and power?"
                ],
                key_questions=[
                    "What technological capabilities do people have?",
                    "How are goods manufactured and distributed?",
                    "What are the most advanced or impressive technologies?",
                    "How do technological differences affect different groups?",
                    "What technological challenges or limitations exist?"
                ],
                completion_criteria=[
                    "General technological level established",
                    "Key technologies and inventions described",
                    "Manufacturing and crafting methods explained",
                    "Transportation and communication systems outlined",
                    "Social impact of technology addressed"
                ]
            ),
            
            'economy': WorldbuildingPromptTemplate(
                topic='economy',
                system_prompt="""You are a worldbuilding specialist focused on economic systems and trade. Help users create realistic economic structures including resources, trade, currency, and how people make their living. Ask insightful questions about wealth, commerce, labor, and economic relationships.""",
                context_prompt="""Focus on economic and commercial aspects of the world. Consider:
- Primary sources of wealth and resources
- Trade routes, markets, and commercial centers
- Currency systems and methods of exchange
- Different occupations and how people earn their living
- Economic classes and wealth distribution
- How economics affects politics and social structures""",
                followup_prompts=[
                    "What are the main sources of wealth and prosperity?",
                    "How do people make their living and what jobs exist?",
                    "What goods are traded and how is commerce organized?",
                    "What currency or exchange systems are used?",
                    "How is wealth distributed among different social groups?"
                ],
                key_questions=[
                    "What are the most valuable resources or commodities?",
                    "How are goods produced, distributed, and sold?",
                    "What are the major trade relationships or routes?",
                    "How do economic differences affect social status?",
                    "What economic challenges or opportunities exist?"
                ],
                completion_criteria=[
                    "Primary economic activities identified",
                    "Trade systems and commerce described",
                    "Currency and exchange methods established",
                    "Wealth distribution and classes explained",
                    "Economic challenges and opportunities outlined"
                ]
            ),
            
            'religion': WorldbuildingPromptTemplate(
                topic='religion',
                system_prompt="""You are a worldbuilding specialist focused on religions and belief systems. Help users create meaningful spiritual systems including deities, practices, institutions, and how faith affects society. Ask thoughtful questions about beliefs, worship, religious authority, and the role of spirituality in daily life.""",
                context_prompt="""Focus on religious and spiritual aspects of the world. Consider:
- Deities, spirits, or supernatural forces that are worshipped
- Religious practices, rituals, and ceremonies
- Religious institutions, clergy, and authority structures
- How faith affects daily life, morality, and decision-making
- Religious conflicts, schisms, or different belief systems
- The relationship between religion and politics or magic""",
                followup_prompts=[
                    "What gods, deities, or spiritual forces are worshipped?",
                    "How do people practice their faith in daily life?",
                    "What religious institutions or clergy exist?",
                    "Are there religious conflicts or competing belief systems?",
                    "How does religion influence politics and social norms?"
                ],
                key_questions=[
                    "What are the core religious beliefs and teachings?",
                    "How is religious authority organized and maintained?",
                    "What are the most important religious ceremonies or holidays?",
                    "How do different religions or sects interact?",
                    "What role does religion play in governance and law?"
                ],
                completion_criteria=[
                    "Major deities or spiritual forces described",
                    "Religious practices and rituals established",
                    "Religious institutions and hierarchy outlined",
                    "Faith's role in daily life explained",
                    "Religious conflicts or diversity addressed"
                ]
            ),
            
            'characters': WorldbuildingPromptTemplate(
                topic='characters',
                system_prompt="""You are a worldbuilding specialist focused on characters and notable figures. Help users create memorable, influential people who shape their world including leaders, heroes, villains, and important personalities. Ask detailed questions about motivations, relationships, and how these figures affect the broader world.""",
                context_prompt="""Focus on important characters and personalities in the world. Consider:
- Leaders, rulers, and figures of authority
- Heroes, villains, and morally complex characters
- Influential thinkers, artists, or innovators
- How these characters' actions affect the broader world
- Relationships and conflicts between important figures
- The legacy and reputation of notable personalities""",
                followup_prompts=[
                    "Who are the most powerful or influential people?",
                    "What notable heroes, villains, or complex figures exist?",
                    "How do these characters' actions affect the world?",
                    "What are the key relationships and conflicts between important figures?",
                    "What legacies or reputations do these characters have?"
                ],
                key_questions=[
                    "Who holds the most power and influence?",
                    "What are the motivations and goals of key figures?",
                    "How do different characters relate to and conflict with each other?",
                    "What impact have these characters had on history and society?",
                    "Are there legendary or mythical figures that still influence the present?"
                ],
                completion_criteria=[
                    "Key political and social leaders identified",
                    "Important heroes, villains, or complex figures described",
                    "Character motivations and goals established",
                    "Relationships and conflicts between figures outlined",
                    "Characters' impact on the world explained"
                ]
            ),
            
            'languages': WorldbuildingPromptTemplate(
                topic='languages',
                system_prompt="""You are a worldbuilding specialist focused on languages and communication. Help users create linguistic diversity including different languages, dialects, writing systems, and how language affects culture and society. Ask detailed questions about communication, literacy, and the cultural significance of different languages.""",
                context_prompt="""Focus on linguistic and communication aspects of the world. Consider:
- Different languages spoken by various groups
- Writing systems, scripts, and literacy levels
- How language barriers affect communication and trade
- Cultural or magical significance of certain languages
- Evolution and history of languages
- How language reflects and shapes cultural identity""",
                followup_prompts=[
                    "What languages are spoken and by which groups?",
                    "How do different peoples communicate with each other?",
                    "What writing systems or scripts are used?",
                    "Do certain languages have special cultural or magical significance?",
                    "How do language barriers affect trade and diplomacy?"
                ],
                key_questions=[
                    "What is the linguistic diversity of the world?",
                    "How widespread is literacy and education?",
                    "Are there common languages used for trade or diplomacy?",
                    "What role do languages play in cultural identity?",
                    "Are there ancient or sacred languages with special meaning?"
                ],
                completion_criteria=[
                    "Major languages and their speakers identified",
                    "Writing systems and literacy levels described",
                    "Language barriers and solutions addressed",
                    "Cultural significance of languages explained",
                    "Communication methods and challenges outlined"
                ]
            ),
            
            'conflicts': WorldbuildingPromptTemplate(
                topic='conflicts',
                system_prompt="""You are a worldbuilding specialist focused on conflicts and tensions. Help users create compelling sources of drama including wars, rivalries, disputes, and threats that drive stories and shape the world. Ask probing questions about the causes, stakes, and consequences of various conflicts.""",
                context_prompt="""Focus on conflicts, tensions, and sources of drama in the world. Consider:
- Major wars, battles, or military conflicts
- Political disputes and power struggles
- Social tensions and cultural clashes
- Economic competition and resource conflicts
- Personal rivalries and vendettas
- External threats and existential dangers""",
                followup_prompts=[
                    "What are the major sources of conflict and tension?",
                    "Are there ongoing wars, disputes, or rivalries?",
                    "What threatens the stability or peace of this world?",
                    "How do different factions or groups oppose each other?",
                    "What are the stakes and potential consequences of these conflicts?"
                ],
                key_questions=[
                    "What are the most significant conflicts affecting the world?",
                    "Who are the main opposing sides or factions?",
                    "What are the root causes of these conflicts?",
                    "How do these conflicts affect ordinary people?",
                    "What would happen if these conflicts escalated or were resolved?"
                ],
                completion_criteria=[
                    "Major conflicts and their causes identified",
                    "Opposing factions and their motivations described",
                    "Stakes and potential consequences outlined",
                    "Impact on society and individuals explained",
                    "Potential resolutions or escalations considered"
                ]
            ),
            
            'organizations': WorldbuildingPromptTemplate(
                topic='organizations',
                system_prompt="""You are a worldbuilding specialist focused on organizations and institutions. Help users create influential groups including guilds, orders, societies, and institutions that shape the world. Ask detailed questions about structure, purpose, influence, and how these organizations interact with each other and society.""",
                context_prompt="""Focus on organizations, institutions, and influential groups in the world. Consider:
- Guilds, orders, and professional organizations
- Religious institutions and spiritual orders
- Military organizations and fighting forces
- Political parties and advocacy groups
- Secret societies and underground organizations
- How these groups compete, cooperate, or conflict""",
                followup_prompts=[
                    "What important organizations, guilds, or institutions exist?",
                    "How are these groups structured and led?",
                    "What are their goals, methods, and areas of influence?",
                    "How do different organizations interact or compete?",
                    "What role do these groups play in society and politics?"
                ],
                key_questions=[
                    "What are the most powerful or influential organizations?",
                    "How do people join or advance within these groups?",
                    "What services or functions do these organizations provide?",
                    "Are there rivalries or alliances between different groups?",
                    "How do these organizations affect the balance of power?"
                ],
                completion_criteria=[
                    "Major organizations and their purposes identified",
                    "Organizational structures and leadership described",
                    "Areas of influence and activities outlined",
                    "Inter-organizational relationships explained",
                    "Impact on society and politics addressed"
                ]
            ),
            
            'general': WorldbuildingPromptTemplate(
                topic='general',
                system_prompt="""You are a worldbuilding specialist helping create rich, immersive fictional worlds. Guide users through developing comprehensive world details across all aspects of worldbuilding. Ask thoughtful questions to help them explore and expand their creative vision, and suggest areas that might need more development.""",
                context_prompt="""Focus on the overall worldbuilding vision and how different elements work together. Consider:
- The unique aspects that make this world interesting
- How different worldbuilding elements connect and influence each other
- The overall mood, atmosphere, and themes
- Areas that might need more development or detail
- The coherence and consistency of the world as a whole""",
                followup_prompts=[
                    "What makes this world unique or interesting?",
                    "How do the different aspects of your world work together?",
                    "What mood or atmosphere are you trying to create?",
                    "What areas of your world would you like to develop further?",
                    "How does this world serve the stories you want to tell?"
                ],
                key_questions=[
                    "What is the central concept or theme of your world?",
                    "What aspects of worldbuilding are most important to your vision?",
                    "How do you want people to feel when they experience this world?",
                    "What makes your world different from others in its genre?",
                    "What worldbuilding elements still need more development?"
                ],
                completion_criteria=[
                    "Core worldbuilding vision articulated",
                    "Unique elements and themes identified",
                    "Overall coherence and consistency addressed",
                    "Areas for further development recognized",
                    "Connection to storytelling goals established"
                ]
            )
        }
    
    def _initialize_conversation_starters(self) -> Dict[WorldbuildingTopic, List[str]]:
        """Initialize conversation starter prompts for each topic."""
        return {
            'geography': [
                "Let's start with the physical world. What does the landscape look like where your story takes place?",
                "Tell me about the geography of your world. Are there mountains, oceans, forests, or other major features?",
                "What's the climate like in your world? How does the weather affect daily life?",
                "Where are the major cities or settlements located, and why did people choose to build there?"
            ],
            'culture': [
                "What are the people like in your world? What do they value and believe in?",
                "Tell me about the culture and society. What are their traditions and customs?",
                "How do people live their daily lives? What's considered normal or important?",
                "What makes this culture unique? What would a visitor find surprising or interesting?"
            ],
            'magic_system': [
                "Does magic exist in your world? If so, how does it work?",
                "Tell me about the supernatural elements. What's possible and what isn't?",
                "Who can use magic or special abilities, and how do they learn?",
                "What are the rules and limitations of magic in your world?"
            ],
            'politics': [
                "Who's in charge in your world? What kind of government or leadership exists?",
                "Tell me about the political situation. Who has power and how do they use it?",
                "Are there any major political conflicts or tensions?",
                "How are laws made and enforced? What happens to those who break them?"
            ],
            'history': [
                "What's the history of your world? How did it come to be the way it is?",
                "Tell me about important events from the past that still matter today.",
                "Are there any legends, myths, or historical figures that people remember?",
                "What major changes or conflicts have shaped the current era?"
            ]
        }
    
    def _initialize_follow_up_generators(self) -> Dict[str, List[str]]:
        """Initialize follow-up question generators based on conversation context."""
        return {
            'expansion': [
                "That's interesting! Can you tell me more about {topic}?",
                "How does {element} affect other aspects of your world?",
                "What are the implications of {concept} for daily life?",
                "Are there any exceptions or variations to {rule}?"
            ],
            'connection': [
                "How does {topic1} relate to {topic2}?",
                "What happens when {element1} conflicts with {element2}?",
                "How do {group1} and {group2} interact?",
                "What's the relationship between {concept1} and {concept2}?"
            ],
            'consequence': [
                "What are the consequences of {action} in your world?",
                "How do people react to {situation}?",
                "What problems does {system} create or solve?",
                "What would happen if {condition} changed?"
            ],
            'detail': [
                "Can you give me a specific example of {concept}?",
                "What would a typical {person} experience?",
                "How would someone from outside react to {custom}?",
                "What does {place} look, sound, and feel like?"
            ]
        }
    
    def get_prompt_template(self, topic: WorldbuildingTopic) -> WorldbuildingPromptTemplate:
        """Get the prompt template for a specific worldbuilding topic."""
        return self.prompt_templates.get(topic, self.prompt_templates['general'])
    
    def get_conversation_starter(self, topic: WorldbuildingTopic) -> str:
        """Get a conversation starter for a specific topic."""
        starters = self.conversation_starters.get(topic, self.conversation_starters.get('general', []))
        if starters:
            import random
            return random.choice(starters)
        return "Tell me about your world. What would you like to explore?"
    
    def build_contextual_prompt(self, topic: WorldbuildingTopic, conversation_context: str = "", 
                              story_context: str = "") -> str:
        """Build a contextual prompt combining template, conversation, and story context."""
        template = self.get_prompt_template(topic)
        
        prompt_parts = [template.system_prompt]
        
        if story_context:
            prompt_parts.append(f"\nStory Context:\n{story_context}")
        
        if conversation_context:
            prompt_parts.append(f"\nConversation Context:\n{conversation_context}")
        
        prompt_parts.append(f"\n{template.context_prompt}")
        
        return "\n".join(prompt_parts)
    
    def generate_follow_up_questions(self, topic: WorldbuildingTopic, context: str = "") -> List[str]:
        """Generate contextual follow-up questions for a topic."""
        template = self.get_prompt_template(topic)
        questions = template.followup_prompts.copy()
        
        # Add context-specific questions if available
        if context:
            # This could be enhanced with more sophisticated context analysis
            questions.extend(template.key_questions[:2])  # Add some key questions
        
        return questions[:5]  # Return top 5 questions
