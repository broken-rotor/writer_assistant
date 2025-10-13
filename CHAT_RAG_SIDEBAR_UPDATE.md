# Chat RAG Sidebar Update

## Overview
Updated the Chat RAG feature in the archive section to improve usability with a sidebar layout for sources and markdown formatting support for responses.

## Changes Made

### 1. Data Model Updates (`archive.service.ts`)
- **Modified `RAGChatMessage` interface** to include optional `sources` property
  - This allows each assistant message to store its associated sources
  - User messages don't have sources

### 2. Component Logic Updates (`archive.component.ts`)
- **Added `selectedMessageIndex` property** to track which message is currently selected
- **Updated `sendChatMessage()` method** to:
  - Store sources with each assistant message
  - Auto-select the latest assistant message
- **Added `selectMessage()` method** to handle clicking on messages
  - Updates sidebar to show sources for the selected message
  - Only works for assistant messages with sources
- **Added `isMessageSelected()` method** to determine visual selection state
- **Added `parseMarkdown()` method** to convert markdown to HTML
  - Supports **bold** (`**text**`)
  - Supports *italic* (`*text*`)
  - Supports lists (lines starting with `-` or `*`)
  - Preserves line breaks
- **Updated `clearChat()` and `switchMode()` methods** to reset `selectedMessageIndex`

### 3. Template Updates (`archive.component.html`)
- **Restructured chat container** to use flexbox with sidebar layout:
  - `.chat-main` - contains messages and input (flexible width)
  - `.chat-sidebar` - contains sources (fixed 320px width)
- **Updated message rendering**:
  - Added click handler `(click)="selectMessage(i)"` for assistant messages
  - Added `message-selected` class for visual feedback
  - Changed cursor to pointer for clickable messages
  - Changed `{{ message.content }}` to `[innerHTML]="parseMarkdown(message.content)"` for markdown rendering
- **Moved sources to sidebar**:
  - Shows "Click on a response to view its sources" hint when no message is selected
  - Displays sources for the selected message
  - Sidebar only appears when there are messages in the chat
- **Updated source score display** to show percentage: `{{ (source.similarity_score * 100).toFixed(0) }}%`

### 4. Style Updates (`archive.component.scss`)
- **Modified `.chat-container`** to use `flex-direction: row` for horizontal layout
- **Added `.chat-main`** styles for the main chat area
- **Updated `.message` styles**:
  - Added transition for smooth visual feedback
  - Added hover effect for assistant messages (lighter background)
  - Added `.message-selected` state with blue highlight and border
  - Added markdown formatting styles (bold, italic, lists)
- **Replaced `.chat-sources`** with new `.chat-sidebar`** styles:
  - Fixed width sidebar (320px)
  - Separate header with title and hint
  - Scrollable source list
  - Improved source item styling with hover effects

## User Experience Improvements

1. **Sidebar Layout**
   - Sources are always visible in a dedicated sidebar
   - Main chat area has more space for conversations
   - Cleaner separation of concerns

2. **Source Selection**
   - Click any assistant response to view its specific sources
   - Visual feedback shows which message is selected (blue highlight)
   - Cursor changes to pointer on hoverable messages

3. **Markdown Support**
   - LLM responses can use formatting for better readability
   - Bold text for emphasis
   - Lists for structured information
   - Line breaks preserved

4. **Visual Feedback**
   - Selected messages have blue highlight and border
   - Hover effects on assistant messages
   - Smooth transitions for professional feel

## Technical Notes

- Changes are backward compatible with existing chat history
- Markdown parsing is client-side (no server changes needed)
- Simple regex-based markdown parser (sufficient for basic formatting)
- Sources are stored per message (no additional API calls needed)
- Sidebar has fixed width for consistent layout across screens
