# Writer Assistant - Requirements Documentation

## Overview

The Writer Assistant is a simplified multi-agent AI system for chapter-by-chapter story creation. Users work through a tabbed web interface, with all story data stored in browser local storage. The system provides stateless AI services for content generation, character feedback, and editorial review.

## Core Concept

A web-based story creation tool with AI assistance at every step:
- **Tabbed Interface**: General, Characters, Raters, Story, Chapter Creation
- **Writer Assistant**: Generates chapters from plot points and feedback
- **Character Feedback**: Characters provide perspective-specific input
- **Rater Feedback**: User-configured critics provide evaluations
- **Editor Review**: Final polish suggestions before chapter acceptance

## Story Creation Workflow

### Setup Phase
1. User configures story settings (title, system prompts, worldbuilding)
2. User creates characters (basic bio, AI can generate details)
3. User configures rater agents (name, system prompt)

### Chapter Creation Phase
1. User enters plot point for chapter
2. User requests feedback from selected characters/raters
3. User iterates with agents until satisfied
4. User selects feedback to incorporate
5. User generates chapter from plot point + feedback
6. User edits chapter (direct edit or AI-assisted)
7. User requests editor review
8. User applies selected suggestions
9. User accepts chapter (added to story)

## Key Features

- **Browser Local Storage**: All story data stored client-side, complete privacy
- **Stateless Backend**: Server maintains no user data or session state
- **User-Configurable Agents**: Custom system prompts for all agents
- **AI-Assisted Character Creation**: Generate character details from basic bio
- **Iterative Feedback**: Request feedback from agents multiple times
- **Flexible Chapter Editing**: Direct editing or AI-assisted modifications
- **Story Export/Import**: JSON export for portability

## Technology Stack

- **Backend**: Python + LangChain for stateless AI services
- **Frontend**: Angular web application with local storage
- **LLM**: Local LLM using llama.cpp
- **Storage**: Browser local storage only (no database)
- **Architecture**: Stateless multi-agent services

## UI Structure

**General Tab**: Story title, system prompts, worldbuilding
**Characters Tab**: Create and manage characters (hide/unhide, AI generation)
**Raters Tab**: Configure feedback agents
**Story Tab**: View chapters and story summary
**Chapter Creation Tab**: Create chapters with AI assistance

## Documentation Structure

This requirements documentation is organized into the following sections:

- [UI Basic Flow](ui_basic_flow.md) - Simple visual flow of the UI
- [User Interface](ui_requirements.md) - Detailed frontend requirements and components
- [Workflow](workflow_requirements.md) - Chapter creation workflow and state management
- [Architecture](architecture_requirements.md) - System architecture and technical design
- [Agents](agents_requirements.md) - Agent specifications and interaction patterns
- [Configuration](configuration_requirements.md) - JSON configuration schemas
- [API Specifications](api_requirements.md) - Backend API endpoints
- [Memory Requirements](memory_requirements.md) - (May be simplified/deprecated)
- [Export/Import](export_import_requirements.md) - Story portability

## Success Criteria

- Generate coherent chapters from user plot points and agent feedback
- Provide actionable feedback from character and rater agents
- Maintain character consistency based on configurations
- Enable iterative refinement with agent collaboration
- Ensure complete user privacy with local-only storage
- Deliver intuitive tabbed interface for story creation
- Support story export/import for portability