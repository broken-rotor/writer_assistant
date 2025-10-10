# Agent System Requirements

## Overview

The Writer Assistant uses specialized agents that provide stateless services for story creation. Each agent type serves a specific purpose in the chapter-by-chapter writing workflow, responding to requests with no persistent state between invocations. All agent behavior is configured through user-defined system prompts and character configurations stored client-side.

## Agent Types and Responsibilities

### 1. Writer Assistant Agent

**Primary Role**: Generate chapter content from plot points and incorporated feedback

**Operations**:

#### Chapter Generation
- **Input**: Plot point, incorporated feedback, story context, characters, previous chapters, worldbuilding
- **System Prompt**: Composed from: `mainPrefix + assistantSystemPrompt + mainSuffix`
- **Output**: Full chapter text
- **Stateless**: No memory between requests

#### Chapter Modification
- **Input**: Current chapter text, user modification request, story context
- **System Prompt**: Composed from: `mainPrefix + assistantSystemPrompt + mainSuffix`
- **Output**: Modified chapter text
- **Stateless**: No memory of previous modifications

#### AI Flesh-Out
- **Input**: Content to expand (worldbuilding, plot point), story context
- **System Prompt**: Composed from: `mainPrefix + assistantSystemPrompt + mainSuffix`
- **Output**: Expanded content
- **Stateless**: Each expansion independent

#### Character Detail Generation
- **Input**: Basic bio, story context
- **System Prompt**: Composed from: `mainPrefix + assistantSystemPrompt + mainSuffix`
- **Output**: Generated character fields (name, demographics, personality, etc.)
- **Stateless**: No memory of previous generations

**Key Principle**: All context provided in each request, no persistent state

### 2. Character Feedback Agents

**Primary Role**: Provide character-specific feedback on plot points

**Operation**:

#### Feedback Generation
- **Input**:
  - Character configuration (name, personality, motivations, fears, relationships, etc.)
  - Plot point
  - Incorporated feedback (from previous iterations)
  - Story context (title, worldbuilding, other characters, previous chapters)
- **System Prompt**: Generated from character personality and traits
- **Output Structure**:
```json
{
  "actions": ["What character would do"],
  "dialog": ["What character would say"],
  "physicalSensations": ["What character would physically experience"],
  "emotions": ["What character would feel"],
  "internalMonologue": ["What character would think"]
}
```
- **Stateless**: Each request independent, character personality from configuration

**Character Configuration Structure**:
```json
{
  "basicBio": "User-provided foundation",
  "name": "Generated or user-provided",
  "sex": "...",
  "gender": "...",
  "sexualPreference": "...",
  "age": 0,
  "physicalAppearance": "...",
  "usualClothing": "...",
  "personality": "...",
  "motivations": "...",
  "fears": "...",
  "relationships": "...",
  "isHidden": false,
  "metadata": {
    "creationSource": "user | ai_generated | imported",
    "lastModified": "..."
  }
}
```

**Visibility Rules**:
- Only characters with `isHidden: false` appear in Chapter Creation tab
- Hidden characters excluded from all feedback opportunities
- Character configuration stored client-side, loaded for each request

### 3. Rater Feedback Agents

**Primary Role**: Provide evaluation feedback on plot points

**Operation**:

#### Feedback Generation
- **Input**:
  - Rater configuration (name, system prompt)
  - Plot point
  - Incorporated feedback (from previous iterations)
  - Story context (title, worldbuilding, characters, previous chapters)
- **System Prompt**: Composed from: `mainPrefix + raterSystemPrompt + mainSuffix`
- **Output Structure**:
```json
{
  "opinion": "Overall assessment of plot point + incorporated feedback",
  "suggestions": [
    "Specific recommendation 1",
    "Specific recommendation 2",
    "..."
  ]
}
```
- **Stateless**: Each request independent, no memory of previous evaluations

**Rater Configuration Structure**:
```json
{
  "name": "User-provided name",
  "systemPrompt": "User-provided prompt defining role and criteria",
  "enabled": true,
  "metadata": {
    "created": "...",
    "lastModified": "..."
  }
}
```

**Common Rater Types** (user-configured examples):
- **Character Consistency Rater**: Focus on character voice, personality consistency
- **Narrative Flow Rater**: Focus on pacing, tension, engagement
- **Genre Expert**: Focus on genre-specific conventions (mystery, romance, etc.)
- **Prose Quality Rater**: Focus on writing craft, style

**Key Points**:
- Raters are fully user-configurable through system prompts
- Only enabled raters appear in Chapter Creation tab
- Rater configuration stored client-side, loaded for each request

### 4. Editor Review Agent

**Primary Role**: Provide final review suggestions for generated chapters

**Operation**:

#### Review Generation
- **Input**:
  - Chapter draft text
  - Plot point used
  - Incorporated feedback
  - Story context (title, worldbuilding, characters, previous chapters)
- **System Prompt**: Composed from: `mainPrefix + editorSystemPrompt + mainSuffix`
- **Output Structure**:
```json
{
  "suggestions": [
    {
      "issue": "Description of issue",
      "suggestion": "Specific recommendation",
      "priority": "high | medium | low"
    },
    ...
  ]
}
```
- **Stateless**: Each review independent, no memory of previous reviews

**Editor Configuration**:
- System prompt defined in General tab
- Composed with mainPrefix and mainSuffix for consistency
- Focus typically on:
  - Continuity and consistency
  - Tone and voice
  - Professional polish
  - Readability and flow

**Key Principle**: Provides suggestions, user decides what to apply

## Agent Interaction Patterns

### Stateless Request-Response Model

All agents follow a simple stateless pattern:

**Request Flow**:
1. Client sends complete context in HTTP request
2. Server processes with appropriate agent
3. Server returns response (no state retained)
4. Client decides what to do with response

**No Direct Agent Communication**:
- Agents never communicate directly with each other
- All coordination through client-side state
- User explicitly incorporates feedback between agents

### User Control Points

**Character Feedback**:
- User clicks character name to request feedback
- User can iterate (suggest changes, regenerate)
- User selects which feedback elements to incorporate
- Incorporated feedback added to client state

**Rater Feedback**:
- User clicks rater name to request feedback
- User reviews opinion and suggestions
- User can iterate or incorporate selectively

**Chapter Generation**:
- User triggers when ready
- User reviews generated chapter
- User can edit directly or request AI modifications

**Editor Review**:
- User requests when chapter complete
- User selects which suggestions to apply
- User can iterate or accept chapter

## Agent Configuration

### System Prompt Composition

All agents use composed system prompts:

**Format**: `mainPrefix + agentSpecificPrompt + mainSuffix`

**Example**:
```
mainPrefix: "You are helping write a mystery novel."
assistantPrompt: "Generate chapter content based on plot points..."
mainSuffix: "Always maintain suspense and foreshadowing."

Final prompt: "You are helping write a mystery novel. Generate chapter content based on plot points... Always maintain suspense and foreshadowing."
```

### Configuration Storage

All configuration stored client-side in browser local storage:

**Story Configuration**:
```json
{
  "general": {
    "title": "...",
    "systemPrompts": {
      "mainPrefix": "...",
      "mainSuffix": "...",
      "assistantPrompt": "...",
      "editorPrompt": "..."
    },
    "worldbuilding": "..."
  },
  "characters": {...},
  "raters": {...}
}
```

No server-side configuration or state.

## Performance Requirements

### Response Times
- Character feedback: < 10 seconds
- Rater feedback: < 10 seconds
- Chapter generation: < 30 seconds
- Editor review: < 15 seconds
- AI flesh-out: < 10 seconds

### Quality Expectations
- Character consistency with configuration
- Actionable, specific feedback from raters
- Coherent chapter generation incorporating feedback
- Editor suggestions addressing real issues

### Error Handling
- Clear error messages on generation failures
- Retry capability for failed requests
- Timeouts for long-running operations
- User notification for system issues

This simplified agent architecture provides powerful AI assistance while maintaining complete user control and zero server-side state.