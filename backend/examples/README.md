# Writer Assistant API Examples

This directory contains comprehensive JSON examples for all Writer Assistant API endpoints. These examples demonstrate the request payload structures and provide realistic sample data to help developers understand and integrate with the API.

## Directory Structure

```
backend/examples/
├── README.md                    # This documentation file
├── common/                      # Shared components and templates
│   ├── request-context-complete.json
│   └── context-processing-config.json
├── health/                      # Health and status endpoints
│   ├── health-check.json
│   └── root-endpoint.json
├── tokens/                      # Token counting endpoints
│   ├── token-count-request.json
│   └── token-validation-request.json
├── archive/                     # Archive search and RAG endpoints
│   ├── search-request.json
│   ├── rag-query-request.json
│   └── rag-chat-request.json
└── ai-generation/              # AI generation endpoints
    ├── generate-chapter-request.json
    ├── modify-chapter-request.json
    ├── character-feedback-request.json
    ├── rater-feedback-request.json
    ├── editor-review-request.json
    ├── flesh-out-request.json
    ├── generate-character-details-request.json
    ├── regenerate-bio-request.json
    ├── generate-chapter-outlines-request.json
    └── llm-chat-request.json
```

## API Base URL

All endpoints are prefixed with `/api/v1/` when the server is running. For example:
- Health check: `GET /api/v1/health`
- Generate chapter: `POST /api/v1/generate-chapter`

## Fictional Story Universe

To provide realistic and coherent examples, all AI generation endpoints use a consistent fictional fantasy story called **"The Crystal Prophecy"**:

### Story Summary
A young mage named Aria discovers an ancient prophecy about crystal shards that could either save or destroy the realm of Eldoria. She must gather allies and navigate political intrigue while being pursued by the Shadow Council.

### Main Characters
- **Aria Moonwhisper**: 19-year-old protagonist, novice mage with untapped potential
- **Theron Blackstone**: 45-year-old mentor, former court wizard with a mysterious past
- **Kira Swiftblade**: 23-year-old rogue, Aria's loyal friend and scout
- **Lord Vex**: Primary antagonist, leader of the Shadow Council

### World Setting
- **Eldoria**: A magical realm with floating cities and crystal-powered technology
- **The Academy**: Where young mages learn their craft
- **Shadow Realm**: Dark dimension from which the Shadow Council operates

## Common Patterns

### RequestContext Structure
Most AI generation endpoints use a `RequestContext` object that contains:
- **configuration**: System prompts and agent settings
- **worldbuilding**: World details and development history
- **characters**: Complete character information and current states
- **story_outline**: Plot structure and story beats
- **chapters**: Written content with feedback and metadata
- **context_metadata**: Processing hints and story information

### Context Processing Config
Optional configuration for how context is processed:
- **summarization_enabled**: Whether to summarize long content
- **max_context_length**: Token limit for context
- **priority_filtering**: Whether to filter by priority levels
- **character_focus**: Specific characters to emphasize

## Endpoint Categories

### Health Endpoints
Simple status and health check endpoints with minimal payloads.

### Token Endpoints
Support batch token counting with different strategies:
- **exact**: Precise token count
- **estimated**: Fast estimation with small overhead
- **conservative**: Higher overhead for safety
- **optimistic**: Lower overhead for efficiency

### Archive Endpoints
Handle story archival and retrieval:
- **Search**: Semantic search through archived stories
- **RAG Query**: Question-answering using archived content
- **RAG Chat**: Conversational interface with story archive

### AI Generation Endpoints
Complex endpoints for story creation and editing:
- **generate-chapter**: Create new chapter content
- **modify-chapter**: Edit existing chapters
- **character-feedback**: Get character-specific suggestions
- **rater-feedback**: Get quality ratings and suggestions
- **editor-review**: Get editorial feedback
- **flesh-out**: Expand brief content into detailed text
- **generate-character-details**: Create detailed character profiles
- **regenerate-bio**: Create character bio summaries
- **generate-chapter-outlines**: Create chapter structure
- **llm-chat**: Direct conversation with AI agents

## Usage Instructions

1. **Copy the JSON**: Use these examples as templates for your API requests
2. **Modify as needed**: Adjust the content to match your specific story and requirements
3. **Validate structure**: Ensure your modifications maintain the required field structure
4. **Test with API**: Send requests to the running Writer Assistant server

## Testing with the API Script

A Python test script is provided to easily test any endpoint using the example files:

### Setup
```bash
# Install dependencies
pip install -r requirements.txt
```

### Usage
```bash
# Test a health endpoint
python test_api.py health/health-check.json

# Test token counting
python test_api.py tokens/token-count-request.json

# Test streaming AI generation (with custom timeout)
python test_api.py ai-generation/generate-chapter-request.json --timeout 60

# Test with custom server URL
python test_api.py archive/search-request.json --base-url http://localhost:8000
```

### Features
- **Automatic endpoint detection**: Recognizes streaming vs regular endpoints
- **SSE streaming support**: Handles Server-Sent Events for AI generation endpoints
- **Pretty output**: Formats responses with emojis and structured display
- **Error handling**: Provides clear error messages and connection diagnostics
- **Flexible configuration**: Supports custom base URLs and timeouts

### Example Output
```
🧪 Testing API endpoint with: tokens/token-count-request.json
================================================================================
📍 Endpoint: POST /api/v1/tokens/count
📝 Description: Count tokens for batch text inputs using different strategies
🌊 Streaming: No

🌐 Sending POST request to: http://localhost:8000/api/v1/tokens/count
📨 Response received in 0.45s:
🔢 Status Code: 200
📄 Response Body: {
  "success": true,
  "total_tokens": 250,
  ...
}
```

## Content Types for Token Counting

When using token endpoints, specify appropriate content types:
- `system_prompt`: System instructions and prompts
- `narrative`: Story narrative content
- `dialogue`: Character dialogue
- `character_description`: Character descriptions
- `scene_description`: Scene and setting descriptions
- `internal_monologue`: Character thoughts
- `metadata`: Structured metadata
- `unknown`: Auto-detected content type

## Notes

- All timestamps in examples use ISO 8601 format
- Character IDs and other identifiers use UUID format for realism
- Word counts and token estimates are realistic for the content length
- Feedback examples show various priority levels and incorporation states
- Context processing configurations demonstrate different optimization strategies

## Contributing

When adding new examples:
1. Follow the existing naming conventions
2. Use the established fictional universe for consistency
3. Include realistic sample data, not just structural placeholders
4. Validate JSON syntax before committing
5. Update this README if adding new categories or patterns
