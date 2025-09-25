# Writer Assistant - Requirements Documentation

## Overview

The Writer Assistant is a multi-agent AI system designed to help users create cohesive, well-crafted stories through collaborative writing with specialized AI agents. The system uses a two-phase development approach with comprehensive feedback loops to ensure high-quality narrative output.

## Core Concept

A writer assistant that creates chapters based on user guidance, utilizing multiple specialized agents:
- **Writer Agent**: Main orchestrator that synthesizes inputs and generates content
- **Character Sub-Agents**: Specialized agents maintaining individual character perspectives and memories
- **Rater Agents**: Multiple critics providing feedback from different perspectives
- **Editor Agent**: Final reviewer ensuring consistency, tone, and coherence

## Two-Phase Development Process

### Phase 1: Outline Development
1. User provides initial story concept and guidance
2. Writer Agent creates basic story outline
3. Rater Agents provide feedback on structure, pacing, and viability
4. User reviews and provides feedback
5. Iterative refinement until approval from all parties
6. Outline locked as story foundation

### Phase 2: Chapter Development
1. Writer Agent fleshes out chapters with detailed content
2. Character Agents contribute individual perspectives and memories
3. Rater Agents review for authenticity, flow, and quality
4. User reviews content alignment with vision
5. Editor Agent performs final consistency and coherence check
6. Iterative refinement until all parties satisfied

## Key Features

- **Individual Agent Memory**: Each agent maintains subjective experiences and perspectives
- **Memory Subjectivity**: Different characters can have conflicting memories/interpretations (feature, not bug)
- **Configurable Personalities**: JSON configuration for characters, raters, and style preferences
- **Story Persistence**: Save/export stories and memory states in JSON format
- **Multi-Perspective Feedback**: Each rater brings unique evaluation criteria and standards

## Technology Stack

- **Backend**: Python + LangChain + LangGraph for workflow coordination
- **Frontend**: Angular web application
- **LLM**: Local LLM using llama.cpp
- **Storage**: JSON configuration files and story persistence
- **Architecture**: Multi-agent system with workflow orchestration

## User Workflow

1. **Story Initialization**: Set genre, tone, introduce characters
2. **Outline Creation**: Collaborate with AI to develop story structure
3. **Chapter Development**: Work with agents to flesh out detailed content
4. **Iterative Refinement**: Incorporate feedback from multiple perspectives
5. **Story Management**: Save, export, and continue stories across sessions

## Documentation Structure

This requirements documentation is organized into the following sections:

- [Architecture](architecture_requirements.md) - System architecture and technical design
- [Agents](agents_requirements.md) - Detailed specifications for each agent type
- [Memory System](memory_requirements.md) - Memory management and persistence
- [Workflow](workflow_requirements.md) - LangGraph workflow coordination and state management
- [Configuration](configuration_requirements.md) - JSON configuration schemas and examples
- [User Interface](ui_requirements.md) - Frontend requirements and user experience
- [API specifications](api_requirements.md) - Backend API design and endpoints
- [Export/Import](export_import_requirements.md) - Story and memory export/import specifications

## Success Criteria

- Generate coherent, engaging stories that maintain character consistency
- Provide meaningful, actionable feedback from multiple perspectives
- Support complex narrative techniques like unreliable narrators and subjective memory
- Maintain story coherence across multiple chapters and revision cycles
- Enable seamless story continuation across sessions
- Deliver intuitive user experience for both novice and experienced writers