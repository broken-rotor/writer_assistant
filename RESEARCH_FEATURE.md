# Archive Research Feature - Plot Point Assistant

## Overview

The Archive Research feature adds an AI-powered research assistant to the chapter creation workflow. When working on a plot point, writers can now click a button to query their story archive and receive contextual insights, suggestions, and relevant excerpts from previous work.

## Feature Description

### What It Does

When a writer enters a plot point in the Chapter Creation tab, they can click the "📚 Research Archive" button to:

1. **Query the Archive**: Sends the plot point to the RAG system with a detailed research prompt
2. **Retrieve Relevant Content**: Finds 8 relevant sections from archived stories
3. **Generate AI Insights**: Uses LLM to provide:
   - Similar plot developments from previous stories
   - Character interactions and dynamics
   - Relevant thematic elements
   - Writing style suggestions
   - Creative enhancements
4. **Display in Sidebar**: Shows results in a sliding sidebar with source transparency

### User Experience

1. User enters a plot point (e.g., "Sarah discovers a hidden letter that reveals her father's secret past")
2. User clicks "📚 Research Archive" button
3. Sidebar slides in from the right side
4. Loading indicator appears while querying archive
5. Results display in sidebar:
   - **Insights Section**: AI-generated suggestions and ideas
   - **Sources Section**: Relevant story excerpts with similarity scores
   - **Help Text**: Tips for using the insights
6. User can read insights while working on their plot point
7. User closes sidebar when done

## Technical Implementation

### Frontend Changes

#### New Files

1. **`frontend/src/app/pipes/newline-to-br.pipe.ts`**
   - Pipe to convert newlines to HTML `<br>` tags
   - Sanitizes HTML for safe rendering
   - Used for displaying multi-paragraph AI responses

#### Modified Files

2. **`frontend/src/app/components/story-workspace/story-workspace.component.ts`**
   - Added `ArchiveService` import
   - Added research state properties:
     - `showResearchSidebar`: Controls sidebar visibility
     - `researchLoading`: Loading state
     - `researchError`: Error message
     - `researchData`: RAG response data
   - Added research methods:
     - `researchPlotPoint()`: Main research function
     - `closeResearchSidebar()`: Close sidebar
     - Helper methods for displaying results

3. **`frontend/src/app/components/story-workspace/story-workspace.component.html`**
   - Added "📚 Research Archive" button in plot point section (line 302)
   - Added research sidebar markup (lines 527-583):
     - Sidebar header with close button
     - Loading state
     - Error state
     - Research results display
     - AI insights section
     - Sources list with similarity badges
     - Help text

4. **`frontend/src/app/components/story-workspace/story-workspace.component.scss`**
   - Added complete sidebar styling (lines 691-922):
     - Fixed positioning with slide-in animation
     - Header styling
     - Loading spinner animation
     - Error message styling
     - Insights content styling
     - Sources list styling
     - Similarity badge colors (high/medium/low)

### Research Query Design

The research query is carefully crafted to provide maximum value:

```typescript
const researchQuery = `Based on my story archive, provide relevant ideas, themes, plot elements, character archetypes, or writing patterns related to this plot point: "${this.story.chapterCreation.plotPoint}".

Help me understand:
1. Similar plot developments or scenes from my previous stories
2. Character interactions or dynamics that could inform this scene
3. Thematic elements that might be relevant
4. Writing style or techniques I've used in similar situations

Provide actionable insights and creative suggestions to enhance this plot point.`;
```

### RAG Parameters

- **Context Chunks**: 8 (more than default for better coverage)
- **Max Tokens**: 1500 (longer response for detailed insights)
- **Temperature**: 0.4 (slightly creative but still grounded)

## UI Design

### Sidebar Layout

```
┌─────────────────────────────────────┐
│ 📚 Archive Research            [✕]  │ ← Header (blue)
├─────────────────────────────────────┤
│                                     │
│ 💡 Insights & Suggestions           │
│ ┌─────────────────────────────────┐ │
│ │ AI-generated insights appear    │ │
│ │ here with suggestions based on  │ │
│ │ retrieved content...            │ │
│ └─────────────────────────────────┘ │
│                                     │
│ 📖 Sources (8)                      │
│ ┌─────────────────────────────────┐ │
│ │ story1.txt      [High] (0.87)   │ │
│ │ "Relevant excerpt from story..."│ │
│ └─────────────────────────────────┘ │
│ ┌─────────────────────────────────┐ │
│ │ story2.txt    [Medium] (0.72)   │ │
│ │ "Another relevant excerpt..."   │ │
│ └─────────────────────────────────┘ │
│ ...                                 │
│                                     │
│ ℹ️ Tip: Use these insights to      │
│ enhance your plot point...         │
│                                     │
└─────────────────────────────────────┘
```

### Visual Features

1. **Slide-in Animation**: Smooth transition from right side
2. **Color Coding**: Similarity badges use traffic light colors
   - Green (High): ≥ 0.8
   - Orange (Medium): 0.6 - 0.8
   - Gray (Low): < 0.6
3. **Scrollable Content**: Sidebar scrolls if content exceeds viewport
4. **Professional Styling**: Matches existing workspace aesthetic
5. **Loading States**: Spinner with descriptive text

## Requirements

### To Use This Feature

1. **Archive Configured**: Story archive must be set up and populated
2. **LLM Configured**: Local LLM must be available for RAG queries
3. **Plot Point Entered**: User must have text in the plot point field

If requirements aren't met, appropriate error messages guide the user.

## Error Handling

### Error States

1. **RAG Not Available (503)**:
   - Message: "RAG feature is not available. Please ensure both archive and LLM are configured. See RAG_FEATURE.md for setup instructions."
   - Displays in sidebar with error styling

2. **Other Errors (500)**:
   - Message: "Failed to research plot point. Please try again."
   - Generic fallback for unexpected errors

3. **No Plot Point**:
   - Alert: "Please enter a plot point first"
   - Prevents empty queries

### Error Recovery

- Errors are displayed in sidebar (doesn't close)
- User can close sidebar and try again
- Previous successful results are cleared on new query
- Loading state properly managed in all cases

## Use Cases

### Example 1: Mystery Scene

**Plot Point**: "Detective finds a cryptic note at the crime scene"

**Research Results Might Include**:
- Similar investigation scenes from previous mysteries
- Character detective techniques used before
- Typical clue discovery patterns
- Red herring strategies
- Atmospheric descriptions from crime scenes

### Example 2: Romance Scene

**Plot Point**: "Emma confesses her feelings but gets rejected"

**Research Results Might Include**:
- Previous confession scenes
- How characters handled rejection
- Emotional aftermath descriptions
- Similar relationship dynamics
- Recovery/growth patterns

### Example 3: Fantasy Battle

**Plot Point**: "The heroes make their final stand against the dark army"

**Research Results Might Include**:
- Battle scene structures
- Team coordination in previous battles
- Magic system usage patterns
- Victory/defeat emotional beats
- Sacrifice themes

## Benefits

### For Writers

1. **Consistency**: Maintain consistent world-building and character behavior
2. **Inspiration**: Get ideas from your own successful patterns
3. **Efficiency**: Quick access to relevant past content
4. **Learning**: Understand your own writing patterns and strengths
5. **Context**: See how similar situations were handled before

### For the Writing Process

1. **Reduces Writer's Block**: Provides concrete starting points
2. **Enhances Continuity**: Helps maintain story coherence
3. **Supports Callbacks**: Easier to reference previous events
4. **Informs Character Growth**: See character arc patterns
5. **Style Consistency**: Maintain voice across chapters

## Performance

### Response Times

- **Query Processing**: 3-10 seconds (depending on model/hardware)
- **Sidebar Animation**: 300ms slide-in
- **UI Responsiveness**: Non-blocking (user can continue working)

### Resource Usage

- Uses existing RAG infrastructure
- No additional backend services needed
- Memory: Similar to archive chat feature
- GPU: Same as other LLM operations

## Future Enhancements

Potential improvements for future versions:

- [ ] Research specific characters or themes
- [ ] Filter by story/genre/time period
- [ ] Save research results for later reference
- [ ] Compare multiple plot points
- [ ] Export insights to document
- [ ] Inline incorporation (click to add to plot point)
- [ ] Research history/cache
- [ ] Customizable query templates
- [ ] Collaborative research (share insights)
- [ ] Visual similarity graph

## Accessibility

- Keyboard accessible (Esc to close sidebar)
- Proper ARIA labels on all interactive elements
- High contrast text and backgrounds
- Readable font sizes
- Clear error messages
- Loading states announced

## Browser Compatibility

- Chrome/Edge: Full support
- Firefox: Full support
- Safari: Full support
- Mobile: Sidebar adapts to smaller screens (responsive design)

## Integration Points

The feature integrates seamlessly with:

1. **Chapter Creation Workflow**: Button in plot point section
2. **Archive Service**: Uses existing `ragQuery()` method
3. **RAG System**: Leverages full RAG infrastructure
4. **Story Context**: Queries based on current story's plot point
5. **UI Theme**: Matches workspace styling

## Testing Recommendations

### Manual Testing

- [ ] Enter plot point and click Research Archive
- [ ] Verify sidebar slides in smoothly
- [ ] Check loading indicator appears
- [ ] Confirm insights display correctly
- [ ] Verify sources show with correct formatting
- [ ] Test similarity badges (high/medium/low)
- [ ] Close sidebar with X button
- [ ] Test with RAG disabled → error message
- [ ] Test with empty plot point → alert
- [ ] Test with no relevant content → appropriate response
- [ ] Long plot points → query works
- [ ] Special characters in plot point → handled correctly

### Edge Cases

- Very short plot points (2-3 words)
- Very long plot points (500+ words)
- No matching content in archive
- Archive empty
- LLM timeout
- Network issues
- Rapid clicks on research button

## Security Considerations

- All queries stay local (no external APIs)
- User's story content never leaves their machine
- No logging of plot points or research results
- Sanitized HTML output (XSS protection)
- Input validation on plot point content

## Documentation Updates

This feature is documented in:
- `RAG_FEATURE.md` - Full RAG documentation
- `RESEARCH_FEATURE.md` - This file
- `CHANGELOG_RAG.md` - Implementation changelog
- Component comments in code

## Deployment Notes

### Installation

No additional installation required beyond RAG setup:
1. Archive must be configured (ARCHIVE_DB_PATH)
2. LLM must be configured (MODEL_PATH)
3. Frontend automatically includes new feature

### Configuration

Uses default RAG configuration:
- Can adjust in `story-workspace.component.ts:914-917`
- Parameters: `n_context_chunks`, `max_tokens`, `temperature`

### Rollback

To disable feature without code changes:
- Remove/hide "Research Archive" button in HTML
- Or add feature flag in component

## Support

For issues or questions:
1. Check RAG_FEATURE.md for RAG setup
2. Verify archive is populated with stories
3. Test RAG in Archive tab first
4. Check browser console for errors
5. Review backend logs for API issues

## License

Part of Writer Assistant project, same license applies.
