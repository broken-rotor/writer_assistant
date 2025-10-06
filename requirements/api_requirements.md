# API Specifications

## Overview

The Writer Assistant backend provides stateless RESTful APIs that support user-driven story development through selective agent engagement. The server maintains no session state or story data - all state management and persistence is handled entirely client-side using browser local storage. Each API request is self-contained and includes all necessary context for processing.

## API Architecture

### Base URL Structure
```
Production: https://api.writer-assistant.com/v1
Development: http://localhost:8000/api/v1
```

### Authentication
- **Method**: None required - completely stateless API
- **Access**: Open endpoints for story generation services
- **Session Management**: None - all context provided in each request

### Response Format
```json
{
  "success": true,
  "data": { ... },
  "metadata": {
    "timestamp": "2025-09-24T10:30:00Z",
    "request_id": "req_123456",
    "version": "1.0"
  },
  "errors": null
}
```

## User-Driven Story Generation APIs

#### Generate Draft from User Input
```http
POST /generate/draft
Content-Type: application/json

{
  "user_input": {
    "type": "theme_topic_outline",
    "content": "Create a mystery about a missing person in a small town where everyone has secrets",
    "expansion_request": "develop this into a detailed story outline"
  },
  "user_preferences": {
    "style_profile": "literary_mystery",
    "length_preference": "novella",
    "focus_areas": ["character_development", "atmospheric_setting"]
  },
  "story_context": {
    "existing_content": null,
    "characters": [],
    "previous_drafts": [],
    "user_feedback_history": []
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "draft_content": {
      "title": "Secrets of Millbrook",
      "outline": {
        "acts": [...],
        "chapters": [...],
        "characters": [...],
        "themes": [...]
      }
    },
    "generation_metadata": {
      "timestamp": "2025-09-24T10:30:00Z",
      "request_id": "req_123456",
      "processing_time": 2.3
    }
  }
}
```

#### Revise Draft Based on User Feedback
```http
POST /generate/revise-draft
Content-Type: application/json

{
  "original_draft": {
    "title": "Secrets of Millbrook",
    "outline": {...},
    "characters": [...],
    "themes": [...]
  },
  "user_feedback": "I like the overall concept but want the main character to be a journalist instead of a detective",
  "specific_changes": [
    "Change protagonist from detective to investigative journalist",
    "Add newspaper/media angle to the investigation",
    "Maintain the small town setting and secrets theme"
  ],
  "revision_context": {
    "previous_revisions": [],
    "user_preferences": {...}
  }
}
```

#### Generate Character Reactions
```http
POST /character/generate-reactions
Content-Type: application/json

{
  "story_draft": {
    "title": "Secrets of Millbrook",
    "outline": {...},
    "characters": [
      {
        "character_id": "sarah_journalist",
        "name": "Sarah Chen",
        "personality": {...},
        "background": {...}
      },
      {
        "character_id": "mayor_davidson",
        "name": "Robert Davidson",
        "personality": {...},
        "background": {...}
      }
    ]
  },
  "selected_characters": ["sarah_journalist", "mayor_davidson"],
  "reaction_prompt": "How do you each feel about the missing person case and the town's reaction?",
  "story_context": "The investigation has just begun and tensions are rising in the small town"
}
```

## Character Dialog APIs

#### Generate Character Dialog Response
```http
POST /character/dialog
Content-Type: application/json

{
  "character_definition": {
    "character_id": "sarah_journalist",
    "name": "Sarah Chen",
    "personality": {
      "core_traits": ["curious", "persistent", "empathetic"],
      "emotional_patterns": ["analytical_under_pressure"],
      "speech_patterns": ["direct", "questioning"]
    },
    "background": {...},
    "current_knowledge": [...],
    "emotional_state": "cautiously_determined"
  },
  "conversation_context": {
    "story_situation": "Sarah has just arrived in the small town to investigate the disappearance",
    "previous_dialog": [],
    "scene_setting": "Initial investigation phase"
  },
  "user_message": "How do you feel about investigating this missing person case?"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "character_response": {
      "character_id": "sarah_journalist",
      "message": "I feel a mix of excitement and unease. This town feels like it's holding its breath, and everyone I've spoken to seems to be hiding something. There's definitely more to this disappearance than meets the eye.",
      "emotional_state": "cautiously_determined",
      "internal_thoughts": "Something about the way the sheriff avoided eye contact when I asked about the timeline bothers me.",
      "personality_consistency_score": 0.95
    },
    "generation_metadata": {
      "timestamp": "2025-09-24T10:30:00Z",
      "processing_time": 1.2
    }
  }
}
```

#### Generate Follow-up Character Dialog
```http
POST /character/dialog
Content-Type: application/json

{
  "character_definition": {
    "character_id": "sarah_journalist",
    "name": "Sarah Chen",
    "personality": {...},
    "background": {...},
    "current_knowledge": [...],
    "emotional_state": "cautiously_determined"
  },
  "conversation_context": {
    "story_situation": "Sarah investigating in small town",
    "previous_dialog": [
      {
        "user": "How do you feel about investigating this missing person case?",
        "character": "I feel a mix of excitement and unease. This town feels like it's holding its breath..."
      }
    ],
    "scene_setting": "Continuing investigation discussion"
  },
  "user_message": "What specifically makes you think people are hiding something?"
}
```

#### Generate Detailed Content
```http
POST /generate/detailed-content
Content-Type: application/json

{
  "story_draft": {
    "title": "Secrets of Millbrook",
    "outline": {...},
    "characters": [...],
    "themes": [...]
  },
  "selected_character_responses": [
    {
      "character_id": "sarah_journalist",
      "responses": [
        "I feel a mix of excitement and unease...",
        "The way people avoid eye contact when I mention the missing person..."
      ]
    }
  ],
  "user_guidance": "Focus on Sarah's arrival in town and her first interviews with locals",
  "generation_preferences": {
    "target_length": 2500,
    "pov_character": "sarah_journalist",
    "mood": "investigative_tension",
    "style": "literary_mystery"
  }
}
```

## User Feedback Selection APIs

#### Generate Agent Feedback
```http
POST /feedback/generate
Content-Type: application/json

{
  "content_to_review": {
    "type": "detailed_content",
    "title": "Secrets of Millbrook - Chapter 1",
    "text": "Sarah Chen's car crunched over the gravel...",
    "word_count": 2347,
    "metadata": {...}
  },
  "story_context": {
    "outline": {...},
    "characters": [...],
    "themes": [...],
    "previous_content": []
  },
  "feedback_agents": [
    {
      "agent_type": "character_consistency_rater",
      "focus_areas": ["character_voice", "personality_consistency"],
      "configuration": {...}
    },
    {
      "agent_type": "narrative_flow_rater",
      "focus_areas": ["pacing", "engagement"],
      "configuration": {...}
    }
  ]
}
```

#### Apply Selected Feedback
```http
POST /generate/apply-feedback
Content-Type: application/json

{
  "original_content": {
    "title": "Secrets of Millbrook - Chapter 1",
    "text": "Sarah Chen's car crunched over the gravel...",
    "metadata": {...}
  },
  "story_context": {
    "outline": {...},
    "characters": [...],
    "themes": [...]
  },
  "selected_feedback": [
    {
      "feedback_source": "narrative_flow_rater",
      "feedback_item": "Add more physical action to the interview scene",
      "user_modification": "Add the action but keep it subtle and character-appropriate",
      "priority": "high"
    }
  ],
  "ignored_feedback": [
    {
      "feedback_source": "character_consistency_rater",
      "feedback_item": "Clarify character motivation in scene",
      "reason": "Character ambiguity is intentional for plot development"
    }
  ]
}
```

## Health and Status APIs

### Service Health

#### Check API Health
```http
GET /health
```

**Response:**
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "timestamp": "2025-09-24T16:30:00Z",
    "version": "1.0.0",
    "services": {
      "llm_backend": "available",
      "generation_engine": "operational",
      "feedback_agents": "ready"
    }
  }
}
```

## Agent Configuration APIs

#### Get Available Agent Types
```http
GET /agents/types
```

**Response:**
```json
{
  "success": true,
  "data": {
    "agent_types": [
      {
        "type": "character_consistency_rater",
        "description": "Evaluates character voice and personality consistency",
        "configurable_options": ["focus_areas", "strictness_level"],
        "default_config": {...}
      },
      {
        "type": "narrative_flow_rater",
        "description": "Analyzes pacing and reader engagement",
        "configurable_options": ["genre_focus", "target_audience"],
        "default_config": {...}
      }
    ]
  }
}
```

## Configuration and Templates APIs

#### Get Character Templates
```http
GET /templates/characters
```

**Response:**
```json
{
  "success": true,
  "data": {
    "character_templates": [
      {
        "template_id": "investigative_journalist",
        "name": "Investigative Journalist",
        "personality_traits": ["curious", "persistent", "analytical"],
        "background_elements": ["journalism_experience", "ethical_dilemmas"],
        "speech_patterns": ["direct_questioning", "fact_focused"]
      },
      {
        "template_id": "small_town_mayor",
        "name": "Small Town Mayor",
        "personality_traits": ["diplomatic", "secretive", "protective"],
        "background_elements": ["political_pressure", "community_ties"],
        "speech_patterns": ["measured", "political_speak"]
      }
    ]
  }
}
```

### Utility APIs

#### Validate Story Structure
```http
POST /validate/story-structure
Content-Type: application/json

{
  "story_content": {
    "title": "Secrets of Millbrook",
    "outline": {...},
    "characters": [...],
    "chapters": [...]
  },
  "validation_rules": {
    "check_character_consistency": true,
    "check_timeline_consistency": true,
    "check_plot_coherence": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "validation_results": {
      "overall_status": "valid_with_warnings",
      "character_consistency": {
        "status": "valid",
        "issues": []
      },
      "timeline_consistency": {
        "status": "warning",
        "issues": [
          {
            "type": "minor_timeline_gap",
            "description": "Two week gap between chapters 3 and 4",
            "severity": "low",
            "suggestions": ["add_transition_text", "bridge_timeline"]
          }
        ]
      }
    }
  }
}
```

## Data Privacy and Security APIs

#### Data Processing Information
```http
GET /privacy/data-processing
```

**Response:**
```json
{
  "success": true,
  "data": {
    "data_handling": {
      "server_storage": "none",
      "session_persistence": "none",
      "data_retention": "no_retention",
      "processing_location": "request_only"
    },
    "privacy_features": {
      "client_side_storage": "complete",
      "user_data_control": "full",
      "export_import": "supported",
      "data_portability": "json_format"
    }
  }
}
```

## Rate Limiting and Performance




## WebSocket APIs

### Real-Time Communication

#### Connection Endpoint
```
WSS /session/{session_id}/ws
```

#### Message Formats

**Agent Status Update:**
```json
{
  "type": "agent_status_update",
  "timestamp": "2025-09-24T15:30:00Z",
  "data": {
    "agent_id": "writer_agent",
    "status": "in_progress",
    "progress": 0.65,
    "current_task": "chapter_revision"
  }
}
```

**Feedback Available:**
```json
{
  "type": "feedback_available",
  "timestamp": "2025-09-24T15:35:00Z",
  "data": {
    "feedback_id": "fb_789",
    "source": "consistency_rater",
    "score": 8.2,
    "priority": "medium"
  }
}
```

**Error Notification:**
```json
{
  "type": "error",
  "timestamp": "2025-09-24T15:40:00Z",
  "data": {
    "error_code": "AGENT_TIMEOUT",
    "message": "Writer agent timed out during chapter generation",
    "recovery_options": ["restart_agent", "continue_without"],
    "severity": "medium"
  }
}
```

## Rate Limiting and Performance

### Rate Limits
- **Generation Requests**: 10 concurrent generations per session
- **WebSocket Connections**: 5 concurrent connections per session

### Performance Targets
- **API Response Time**: < 200ms for data retrieval
- **Story Generation**: Progress updates every 5 seconds
- **WebSocket Latency**: < 100ms for real-time updates
- **File Upload**: Support up to 50MB story imports
- **Concurrent Users**: Support 1000+ concurrent story sessions

### Caching Strategy
- **Agent Configurations**: In-memory cache with TTL
- **Session States**: Temporary cache for active generation sessions
- **Generated Content**: Temporary cache for revision cycles

## Error Handling

### HTTP Status Codes

#### Success Codes
- **200 OK**: Successful request
- **201 Created**: Resource created successfully
- **202 Accepted**: Request accepted for processing
- **204 No Content**: Successful deletion

#### Client Error Codes
- **400 Bad Request**: Invalid request parameters
- **401 Unauthorized**: Authentication required
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **409 Conflict**: Resource conflict (e.g., story being edited)
- **422 Unprocessable Entity**: Validation errors
- **429 Too Many Requests**: Rate limit exceeded

#### Server Error Codes
- **500 Internal Server Error**: Unexpected server error
- **502 Bad Gateway**: Upstream service error
- **503 Service Unavailable**: Service temporarily unavailable
- **504 Gateway Timeout**: Request timeout

### Error Response Format
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The provided story configuration is invalid",
    "details": {
      "field": "character_configuration.personality_profile",
      "issue": "missing_required_traits",
      "suggestion": "Please provide at least 3 core personality traits"
    },
    "request_id": "req_123456",
    "timestamp": "2025-09-24T15:45:00Z"
  },
  "data": null
}
```

### Specific Error Types

#### Workflow Errors
```json
{
  "error": {
    "code": "AGENT_TIMEOUT",
    "message": "Agent failed to respond within timeout period",
    "details": {
      "agent_id": "writer_agent",
      "timeout_duration": "30s",
      "recovery_actions": [
        "restart_agent",
        "continue_with_fallback",
        "manual_intervention"
      ]
    }
  }
}
```

#### Memory Errors
```json
{
  "error": {
    "code": "MEMORY_CORRUPTION",
    "message": "Story memory state is inconsistent",
    "details": {
      "affected_agents": ["character_john", "character_mary"],
      "corruption_type": "conflicting_memories",
      "recovery_options": [
        "restore_from_backup",
        "manual_memory_repair",
        "reset_to_last_checkpoint"
      ]
    }
  }
}
```

#### Configuration Errors
```json
{
  "error": {
    "code": "INVALID_CONFIGURATION",
    "message": "Character configuration contains invalid values",
    "details": {
      "validation_errors": [
        {
          "field": "personality_profile.core_traits",
          "error": "must_contain_at_least_3_traits",
          "current_value": ["analytical", "introverted"]
        }
      ]
    }
  }
}
```

## Security Requirements

### Authentication and Authorization

#### No Authentication Required
- Local development environment
- Open access to generation APIs

### Input Validation

#### Request Validation Rules
- **SQL Injection Prevention**: Parameterized queries only
- **XSS Protection**: HTML sanitization for all text inputs
- **File Upload Security**: Type validation and virus scanning
- **Input Sanitization**: Remove potentially harmful content
- **Size Limits**: Enforce maximum payload sizes

#### Content Filtering
```json
{
  "validation_rules": {
    "story_content": {
      "max_length": 1000000,
      "allowed_html_tags": ["p", "em", "strong", "br"],
      "forbidden_patterns": ["script", "iframe", "object"],
      "character_whitelist": "unicode_letters_numbers_punctuation"
    },
    "configuration_data": {
      "schema_validation": "strict",
      "type_checking": "enforced",
      "range_validation": "numeric_within_bounds"
    }
  }
}
```

### Data Privacy

#### Stateless Data Handling
- **No Server-Side Storage**: Server maintains no state or user data whatsoever
- **Request-Only Processing**: Each request is processed independently with no persistence
- **No Session Management**: No session cookies, tokens, or server-side session storage
- **Complete Client Control**: All story data, memory, and state managed entirely by client
- **Zero Data Retention**: No data retained on server after request completion

## API Documentation

### OpenAPI Specification

#### Specification Structure
```yaml
openapi: 3.0.3
info:
  title: Writer Assistant API
  version: 1.0.0
  description: Multi-agent collaborative story writing system
  contact:
    name: API Support
    email: api-support@writer-assistant.com
  license:
    name: MIT
    url: https://opensource.org/licenses/MIT

servers:
  - url: https://api.writer-assistant.com/v1
    description: Production server
  - url: https://staging-api.writer-assistant.com/v1
    description: Staging server

paths:
  /stories:
    get:
      summary: List user stories
      parameters:
        - name: limit
          in: query
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 20
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/StoryList'
```

### SDK Support

#### Python SDK Example
```python
# Conceptual Python SDK usage
from writer_assistant_sdk import WriterAssistantClient

client = WriterAssistantClient(api_key="your_api_key")

# Create new story
story = client.stories.create(
    title="My Mystery Novel",
    genre="mystery",
    initial_guidance="Create a locked room mystery"
)

# Start outline development
workflow = story.start_outline_development(
    user_guidance="Focus on character-driven mystery with psychological depth"
)

# Monitor progress
for update in workflow.watch_progress():
    print(f"Status: {update.status}, Progress: {update.progress}")

# Get feedback
feedback = story.get_feedback(phase="outline")
for rater_feedback in feedback.rater_feedback:
    print(f"{rater_feedback.rater_id}: {rater_feedback.score}/10")
```

#### JavaScript/TypeScript SDK Example
```typescript
// Conceptual TypeScript SDK usage
import { WriterAssistantClient } from '@writer-assistant/sdk';

const client = new WriterAssistantClient({
  apiKey: 'your_api_key',
  baseUrl: 'https://api.writer-assistant.com/v1'
});

// Create story with async/await
const story = await client.stories.create({
  title: 'My Romance Novel',
  genre: 'romance',
  initialGuidance: 'Create a contemporary romance with strong character development'
});

// Start chapter development
const chapter = await story.chapters.generate(1, {
  userGuidance: 'Introduce the main characters in a meet-cute scenario',
  targetLength: 2500,
  mood: 'light_and_playful'
});

// Real-time updates via WebSocket
const ws = story.connectWebSocket();
ws.on('agentStatusUpdate', (update) => {
  console.log(`Agent ${update.agentId}: ${update.status}`);
});
```

## Testing and Validation

### API Testing Requirements

#### Test Coverage Areas
- **Endpoint Functionality**: All endpoints tested with valid inputs
- **Error Handling**: All error conditions properly tested
- **Authentication**: Security and permission validation
- **Performance**: Load testing for concurrent users
- **Integration**: End-to-end workflow testing

#### Test Data Management
```json
{
  "test_scenarios": {
    "story_creation": {
      "valid_inputs": [
        {
          "title": "Test Story",
          "genre": "mystery",
          "description": "Test description"
        }
      ],
      "invalid_inputs": [
        {
          "title": "",
          "expected_error": "VALIDATION_ERROR"
        }
      ]
    },
    "workflow_execution": {
      "outline_development": {
        "happy_path": "complete_workflow_with_approval",
        "error_scenarios": ["agent_timeout", "user_rejection", "memory_conflict"]
      }
    }
  }
}
```

### Performance Testing

#### Load Testing Scenarios
- **Concurrent Story Creation**: 100 simultaneous new stories
- **Workflow Execution**: 50 concurrent chapter generations
- **WebSocket Connections**: 500 concurrent real-time connections
- **Memory Operations**: High-frequency memory updates and retrievals

#### Performance Benchmarks
- **API Latency**: 95th percentile < 500ms
- **Throughput**: 1000 requests/second sustained
- **Memory Usage**: < 512MB per story session
- **Storage I/O**: < 100ms for story operations

This comprehensive API specification ensures robust, secure, and performant communication between the frontend interface and the multi-agent backend system, supporting all aspects of the collaborative story writing workflow.