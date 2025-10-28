# ⚠️ .agent Directory - Internal Meta Documentation

**Status**: Archived meta-docs for AI agent configuration  
**Purpose**: Internal development reference only  
**Last Updated**: 2025-10-28  
**Note**: These files are meta-configuration for AI agent development, not user-facing documentation.

## Memory Management Features

- **Clear all agent memory**: Reset the entire memory state of the agent
- **Clear thread memory**: Clear memory specifically associated with a particular thread
- **Clear workflow memory**: Reset workflow-specific context and state
- **Clear AI model context**: Reset LLM conversation and reasoning context

> The `thread_id` parameter is used to specify the target thread for memory clearing.

## API Memory Management

```bash
curl --location '{base_url}/agents/clean-memory' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer {jwt_token}' \
--data '{
    "agent_id": "hyperagent",
    "thread_id": "contract_generation",
    "clean_agent_memory": true,
    "clean_skills_memory": true
}'
```

## HyperAgent Memory Management

### Contract Development Context
- **Generation Memory**: Clear previous contract generation context and templates
- **Audit Session Memory**: Reset security audit session data and findings
- **Deployment Memory**: Clear deployment history and transaction context
- **Verification Memory**: Reset contract verification status and results

### Workflow State Management
- **Workflow Progress**: Clear incomplete workflow states and checkpoints
- **Stage Memory**: Reset individual workflow stage context (Generate, Audit, Deploy, Verify, Test)
- **Error Context**: Clear error handling and retry context
- **User Preferences**: Reset user-specific workflow preferences and settings

### AI Model Context
- **LLM Conversations**: Reset AI model conversation history and context
- **Model Selection**: Clear AI model selection preferences and performance data
- **Response Caching**: Clear cached AI responses and generated content
- **Learning Context**: Reset AI learning and adaptation context

## CLI Memory Management

HyperAgent provides CLI commands for memory management:

```bash
# Clear all agent memory
hyperagent config reset --memory

# Clear specific workflow memory
hyperagent workflow reset --memory

# Clear contract generation context
hyperagent generate reset --context

# Clear audit session memory
hyperagent audit reset --session

# Clear deployment history
hyperagent deploy reset --history
```

## Memory Management Use Cases

### Development Workflow
- **Testing**: Clear memory between test runs for consistent results
- **Debugging**: Reset context to isolate specific issues
- **Iteration**: Clear previous attempts when iterating on contract design

### Production Operations
- **User Privacy**: Clear sensitive conversation data and user context
- **Performance**: Reset memory for optimal performance and resource usage
- **Security**: Clear potentially sensitive information from memory

### Maintenance
- **Session Cleanup**: Regular memory cleanup for long-running sessions
- **Resource Management**: Clear memory to free up system resources
- **Context Reset**: Reset context for fresh start on new projects