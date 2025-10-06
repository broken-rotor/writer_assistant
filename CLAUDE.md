# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Writer Assistant is a multi-agent AI system for collaborative storytelling that uses specialized AI agents to create cohesive, well-crafted stories through a two-phase development process (outline → chapters).

## Technology Stack

- **Backend**: Python + LangChain + LangGraph for multi-agent workflow orchestration
- **Frontend**: Angular web application with client-side storage
- **LLM**: Local LLM using llama.cpp
- **Storage**: Browser local storage for all story data, memory, and configuration
- **Architecture**: Multi-agent system with hierarchical memory management and client-side persistence

## Development Commands

Since this is a requirements-only repository (no implementation yet), there are no build, test, or lint commands available. The project consists entirely of specification documents.

## Project Architecture

### Multi-Agent System Structure

The system employs five types of specialized agents:

1. **Writer Agent**: Main orchestrator that synthesizes inputs from all other agents and generates story content
2. **Character Sub-Agents**: Maintain individual character perspectives, memories, and authentic subjective experiences
3. **Rater Agents**: Multiple critics providing specialized feedback (Character Consistency, Narrative Flow, Literary Quality, Genre-Specific)
4. **Editor Agent**: Final quality gate ensuring consistency, tone coherence, and narrative flow

### Two-Phase Development Process

**Phase 1: Outline Development**
- User provides story concept → Writer creates outline → Rater feedback → User review → Iterative refinement until approval

**Phase 2: Chapter Development**
- Writer generates chapters → Character agents contribute perspectives → Rater review → User review → Editor final check → Iterative refinement

### Memory Architecture

- **Hierarchical Memory Structure**: Working memory, episodic memory, semantic memory
- **Agent-Specific Memory**: Individual perspectives and subjective experiences (feature: memory subjectivity allows conflicting character interpretations)
- **Memory Synchronization**: Coordination protocols for shared story elements
- **Omniscient Writer Access**: Writer agent has complete access to all character memories and internal states

### LangGraph Workflow Coordination

- **State Persistence**: Maintain workflow state across user sessions
- **Dynamic Routing**: Workflow paths determined by story needs and agent feedback
- **Parallel Processing**: Character agents and rater agents can execute simultaneously
- **Sequential Review Stages**: Raters → User → Editor in defined sequence
- **Error Recovery**: Graceful handling of agent failures and system interruptions

## Key Requirements Files

- `requirements/README.md`: Complete project overview and success criteria
- `requirements/architecture_requirements.md`: System architecture and technical design
- `requirements/agents_requirements.md`: Detailed specifications for each agent type including memory structures
- `requirements/workflow_requirements.md`: LangGraph workflow coordination and state management
- `requirements/memory_requirements.md`: Memory management and persistence systems
- `requirements/configuration_requirements.md`: JSON configuration schemas for all agents
- `requirements/ui_requirements.md`: Frontend requirements and user experience
- `requirements/api_requirements.md`: Backend API design and endpoints
- `requirements/export_import_requirements.md`: Story and memory export/import specifications

## Important Implementation Considerations

### Agent Configuration
- All agents use JSON-based personality and behavior configuration
- Character agents maintain subjective memory filtering based on personality traits
- Rater agents have configurable evaluation criteria and feedback styles
- Genre-specific raters adapt based on story type (Mystery, Romance, Thriller, Literary Fiction)

### Memory Management
- Characters only know what they realistically could know (knowledge limitations)
- Memory colored by emotional state and personality lens during events
- Memory subjectivity is intentional - conflicting character memories are a feature
- Writer agent synthesizes all perspectives while maintaining individual character authenticity

### Workflow States
- Clear phase separation between outline and chapter development
- State validation and recovery procedures for system resilience
- Progress tracking and resumption capabilities for long-running story development

### Performance Requirements
- Response time: < 30 seconds for chapter generation
- Memory efficiency: < 4KB context per agent per chapter
- Consistency scores: > 85% character consistency across story
- User satisfaction: > 4.0/5.0 rating on generated content