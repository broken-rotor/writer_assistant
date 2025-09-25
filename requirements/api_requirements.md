# API Specifications

## Overview

The Writer Assistant backend provides RESTful APIs for story management, agent coordination, and real-time collaboration. The API design supports the two-phase development workflow, multi-agent interactions, and comprehensive story persistence.

## API Architecture

### Base URL Structure
```
Production: https://api.writer-assistant.com/v1
Development: http://localhost:8000/api/v1
```

### Authentication
- **Method**: JWT-based authentication
- **Headers**: `Authorization: Bearer <token>`
- **Token Refresh**: Automatic refresh with refresh tokens
- **Session Management**: Persistent sessions across devices

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

## Story Management APIs

### Story CRUD Operations

#### Create New Story
```http
POST /stories
Content-Type: application/json
Authorization: Bearer <token>

{
  "title": "My New Story",
  "genre": "mystery",
  "description": "A detective story set in Victorian London",
  "initial_guidance": "Create a story about a detective solving a murder mystery in a locked room",
  "configuration": {
    "style_profile": "literary_mystery",
    "character_templates": ["detective_archetype", "victim", "suspects"],
    "rater_preferences": ["mystery_expert", "character_consistency", "literary_quality"]
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "story_id": "story_123",
    "title": "My New Story",
    "genre": "mystery",
    "status": "outline_development",
    "created_at": "2025-09-24T10:30:00Z",
    "workflow_state": {
      "current_phase": "outline_development",
      "current_step": "initial_creation"
    }
  }
}
```

#### Get Story Details
```http
GET /stories/{story_id}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "story_id": "story_123",
    "title": "My New Story",
    "genre": "mystery",
    "status": "chapter_development",
    "progress": {
      "outline_approved": true,
      "chapters_completed": 3,
      "total_chapters_planned": 12,
      "overall_progress": 0.25
    },
    "content": {
      "outline": { ... },
      "chapters": [ ... ],
      "characters": [ ... ]
    },
    "workflow_state": { ... },
    "metadata": {
      "created_at": "2025-09-24T10:30:00Z",
      "last_modified": "2025-09-24T15:45:00Z",
      "word_count": 12500,
      "revision_count": 7
    }
  }
}
```

#### Update Story
```http
PUT /stories/{story_id}
Content-Type: application/json

{
  "title": "Updated Story Title",
  "description": "Updated description",
  "configuration_updates": {
    "style_profile": "commercial_mystery"
  }
}
```

#### Delete Story
```http
DELETE /stories/{story_id}
```

#### List User Stories
```http
GET /stories?limit=20&offset=0&status=active&sort=last_modified
```

**Response:**
```json
{
  "success": true,
  "data": {
    "stories": [
      {
        "story_id": "story_123",
        "title": "My New Story",
        "genre": "mystery",
        "status": "chapter_development",
        "progress": 0.25,
        "last_modified": "2025-09-24T15:45:00Z"
      }
    ],
    "pagination": {
      "total": 45,
      "limit": 20,
      "offset": 0,
      "has_more": true
    }
  }
}
```

## Workflow Management APIs

### Phase Management

#### Start Outline Development
```http
POST /stories/{story_id}/workflow/outline/start
Content-Type: application/json

{
  "user_guidance": "Create a mystery story with a detective solving a locked room murder",
  "parameters": {
    "target_length": "novel",
    "complexity_level": "moderate",
    "character_count": 5
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "workflow_id": "wf_456",
    "status": "in_progress",
    "estimated_completion": "2025-09-24T11:00:00Z",
    "active_agents": ["writer_agent"],
    "steps": [
      {
        "step": "context_assembly",
        "status": "completed",
        "duration": 1.2
      },
      {
        "step": "outline_generation",
        "status": "in_progress",
        "estimated_duration": 15.0
      }
    ]
  }
}
```

#### Get Workflow Status
```http
GET /stories/{story_id}/workflow/status
```

**Response:**
```json
{
  "success": true,
  "data": {
    "workflow_id": "wf_456",
    "current_phase": "outline_development",
    "current_step": "rater_review",
    "status": "awaiting_feedback",
    "progress": 0.65,
    "active_agents": ["consistency_rater", "flow_rater", "quality_rater"],
    "completed_steps": [ ... ],
    "pending_steps": [ ... ],
    "estimated_completion": "2025-09-24T16:30:00Z"
  }
}
```

#### Submit User Feedback
```http
POST /stories/{story_id}/workflow/feedback
Content-Type: application/json

{
  "phase": "outline_development",
  "feedback_type": "user_review",
  "feedback": {
    "overall_approval": false,
    "specific_feedback": "The detective character needs more depth and personal stakes in the case",
    "requested_changes": [
      "Add personal connection between detective and victim",
      "Increase emotional stakes for detective",
      "Clarify detective's unique investigative approach"
    ],
    "approval_status": "needs_revision"
  }
}
```

### Chapter Development

#### Start Chapter Creation
```http
POST /stories/{story_id}/chapters/{chapter_number}/generate
Content-Type: application/json

{
  "user_guidance": "In this chapter, the detective interviews the first suspect and discovers a crucial clue",
  "parameters": {
    "target_length": 2500,
    "pov_character": "detective_main",
    "mood": "tense_investigative",
    "key_plot_points": [
      "interview_suspect_1",
      "discover_hidden_letter",
      "character_development_detective"
    ]
  },
  "scene_context": {
    "setting": "suspect's office",
    "time_of_day": "afternoon",
    "present_characters": ["detective_main", "suspect_1"],
    "emotional_context": "professional_but_underlying_tension"
  }
}
```

#### Get Chapter Content
```http
GET /stories/{story_id}/chapters/{chapter_number}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "chapter_number": 3,
    "title": "The First Interview",
    "content": {
      "text": "The office felt smaller than Detective Morrison had expected...",
      "word_count": 2347,
      "character_perspectives": {
        "detective_main": {
          "internal_monologue": [ ... ],
          "observations": [ ... ],
          "emotional_state": "cautiously_optimistic"
        }
      }
    },
    "metadata": {
      "generated_at": "2025-09-24T14:20:00Z",
      "revision_count": 2,
      "status": "awaiting_user_review",
      "quality_scores": {
        "consistency_rater": 8.2,
        "flow_rater": 7.5,
        "quality_rater": 8.0
      }
    },
    "feedback": [ ... ]
  }
}
```

## Agent Management APIs

### Agent Status and Control

#### Get Agent Status
```http
GET /stories/{story_id}/agents/status
```

**Response:**
```json
{
  "success": true,
  "data": {
    "writer_agent": {
      "status": "active",
      "current_task": "chapter_3_revision",
      "progress": 0.7,
      "estimated_completion": "2025-09-24T15:10:00Z",
      "memory_state": "loaded_and_current"
    },
    "character_agents": {
      "detective_main": {
        "status": "active",
        "last_update": "2025-09-24T14:45:00Z",
        "memory_updates": 3,
        "perspective_ready": true
      },
      "suspect_1": {
        "status": "standby",
        "reason": "not_in_current_scene"
      }
    },
    "rater_agents": {
      "consistency_rater": {
        "status": "completed",
        "feedback_submitted": true,
        "score": 8.2
      },
      "flow_rater": {
        "status": "in_progress",
        "progress": 0.4,
        "estimated_completion": "2025-09-24T15:05:00Z"
      }
    }
  }
}
```

#### Cancel Agent Task
```http
POST /stories/{story_id}/agents/{agent_id}/cancel
```

#### Restart Failed Agent
```http
POST /stories/{story_id}/agents/{agent_id}/restart
```

## Feedback and Review APIs

### Feedback Management

#### Get Feedback Summary
```http
GET /stories/{story_id}/feedback?phase=chapter_development&chapter=3
```

**Response:**
```json
{
  "success": true,
  "data": {
    "overall_summary": {
      "average_score": 7.9,
      "status": "needs_minor_revision",
      "consensus": "strong_character_work_pacing_needs_adjustment"
    },
    "rater_feedback": [
      {
        "rater_id": "consistency_rater",
        "score": 8.2,
        "feedback": {
          "strengths": ["character_voice_authentic", "internal_consistency_maintained"],
          "concerns": ["minor_dialogue_inconsistency"],
          "suggestions": ["clarify_detective_motivation_in_scene_2"],
          "priority": "low"
        }
      },
      {
        "rater_id": "flow_rater",
        "score": 7.5,
        "feedback": {
          "strengths": ["engaging_opening", "good_tension_building"],
          "concerns": ["pacing_slows_in_middle_section"],
          "suggestions": ["tighten_interview_sequence", "add_physical_action"],
          "priority": "medium"
        }
      }
    ],
    "user_feedback": null,
    "editor_feedback": {
      "status": "pending",
      "estimated_completion": "2025-09-24T15:30:00Z"
    }
  }
}
```

#### Submit Feedback Response
```http
POST /stories/{story_id}/feedback/respond
Content-Type: application/json

{
  "feedback_id": "fb_789",
  "response_type": "implementation",
  "response": {
    "changes_made": [
      "Added physical gesture during interview to improve pacing",
      "Clarified detective's emotional investment in case"
    ],
    "explanation": "Addressed pacing concerns by adding more dynamic elements to the interview scene",
    "request_review": true
  }
}
```

## Memory Management APIs

### Memory Operations

#### Get Story Memory State
```http
GET /stories/{story_id}/memory
```

**Response:**
```json
{
  "success": true,
  "data": {
    "memory_summary": {
      "total_size": "15.2KB",
      "last_sync": "2025-09-24T14:50:00Z",
      "consistency_score": 0.92
    },
    "agent_memories": {
      "writer_agent": {
        "working_memory_size": "3.2KB",
        "episodic_events": 47,
        "semantic_facts": 156,
        "last_update": "2025-09-24T14:48:00Z"
      },
      "character_agents": {
        "detective_main": {
          "personal_memory_size": "2.1KB",
          "internal_monologue_entries": 23,
          "relationship_tracking": 4,
          "memory_reliability": 0.87
        }
      }
    },
    "memory_conflicts": [],
    "sync_status": "current"
  }
}
```

#### Export Memory State
```http
GET /stories/{story_id}/memory/export?format=json&include_full_context=true
```

#### Import Memory State
```http
POST /stories/{story_id}/memory/import
Content-Type: application/json

{
  "memory_data": { ... },
  "validation_level": "strict",
  "conflict_resolution": "preserve_existing"
}
```

## Configuration APIs

### Configuration Management

#### Get Configuration
```http
GET /stories/{story_id}/configuration
```

#### Update Configuration
```http
PUT /stories/{story_id}/configuration
Content-Type: application/json

{
  "character_updates": {
    "detective_main": {
      "personality_profile.core_traits.primary": ["analytical", "determined", "empathetic"]
    }
  },
  "rater_updates": {
    "consistency_rater": {
      "standards_and_tolerances.quality_expectations.minimum_acceptable_score": 6.0
    }
  }
}
```

## Export/Import APIs

### Story Export

#### Export Complete Story
```http
GET /stories/{story_id}/export?format=json&include_memory=true&include_config=true
```

**Response:**
```json
{
  "success": true,
  "data": {
    "export_metadata": {
      "export_id": "exp_123",
      "exported_at": "2025-09-24T16:00:00Z",
      "format": "json",
      "size": "2.4MB"
    },
    "download_url": "https://api.writer-assistant.com/v1/exports/exp_123/download",
    "expires_at": "2025-09-25T16:00:00Z"
  }
}
```

#### Export Formats
- **JSON**: Complete story with memory and configuration
- **DOCX**: Formatted document for editing
- **PDF**: Print-ready format
- **EPUB**: E-book format
- **TXT**: Plain text version

### Story Import

#### Import Story
```http
POST /stories/import
Content-Type: multipart/form-data

{
  "file": <story_file>,
  "import_options": {
    "preserve_ids": false,
    "merge_conflicts": "prompt_user",
    "validation_level": "standard"
  }
}
```

## WebSocket APIs

### Real-Time Communication

#### Connection Endpoint
```
WSS /stories/{story_id}/ws?token=<jwt_token>
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
- **Story Operations**: 100 requests per hour per user
- **Generation Requests**: 10 concurrent generations per user
- **WebSocket Connections**: 5 concurrent connections per user
- **Export Operations**: 20 exports per day per user

### Performance Targets
- **API Response Time**: < 200ms for data retrieval
- **Story Generation**: Progress updates every 5 seconds
- **WebSocket Latency**: < 100ms for real-time updates
- **File Upload**: Support up to 50MB story imports
- **Concurrent Users**: Support 1000+ concurrent story sessions

### Caching Strategy
- **Story Data**: Redis cache for frequently accessed stories
- **Agent Configurations**: In-memory cache with TTL
- **Memory States**: Compressed cache for active sessions
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

#### JWT Token Structure
```json
{
  "header": {
    "alg": "RS256",
    "typ": "JWT"
  },
  "payload": {
    "user_id": "user_123",
    "username": "writer_user",
    "permissions": ["story.read", "story.write", "story.delete"],
    "subscription_tier": "premium",
    "exp": 1695657600,
    "iat": 1695654000
  }
}
```

#### Permission System
- **story.read**: View stories and content
- **story.write**: Create and modify stories
- **story.delete**: Delete stories
- **story.share**: Share stories with others
- **config.modify**: Modify system configurations
- **admin.access**: Administrative functions

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

#### Personal Data Handling
- **Data Minimization**: Collect only necessary information
- **Encryption**: AES-256 encryption for sensitive data
- **Access Logging**: Log all access to personal data
- **Data Retention**: Automatic deletion after specified periods
- **User Rights**: Support for data export and deletion requests

#### GDPR Compliance
```http
GET /users/{user_id}/data/export
DELETE /users/{user_id}/data
POST /users/{user_id}/data/anonymize
```

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