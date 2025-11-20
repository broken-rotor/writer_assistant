/**
 * Utility functions for transforming frontend feedback selection to backend API format
 */

import { 
  CharacterFeedbackItem, 
  RaterFeedbackItem, 
  EditorFeedbackItem
} from '../models/story.model';
import { FeedbackSelection } from '../components/feedback-selector/feedback-selector.component';

/**
 * Transform frontend FeedbackSelection to backend CharacterFeedbackItem array
 */
export function transformCharacterFeedback(
  feedbackSelection: FeedbackSelection
): CharacterFeedbackItem[] {
  return feedbackSelection.characterFeedback.map(item => ({
    character_name: item.characterName,
    type: item.type,
    content: item.content
  }));
}

/**
 * Transform frontend FeedbackSelection to backend RaterFeedbackItem array
 */
export function transformRaterFeedback(
  feedbackSelection: FeedbackSelection
): RaterFeedbackItem[] {
  return feedbackSelection.raterFeedback.map(item => ({
    rater_name: item.raterName,
    content: item.content
  }));
}

/**
 * Transform editor feedback (currently not implemented in frontend, returns empty array)
 */
export function transformEditorFeedback(
  _feedbackSelection: FeedbackSelection
): EditorFeedbackItem[] {
  // Editor feedback is not currently implemented in the frontend feedback selector
  // Return empty array for now
  return [];
}

/**
 * Transform complete feedback selection to backend format
 */
export function transformFeedbackSelection(
  feedbackSelection: FeedbackSelection
): {
  character_feedback: CharacterFeedbackItem[];
  rater_feedback: RaterFeedbackItem[];
  editor_feedback: EditorFeedbackItem[];
} {
  return {
    character_feedback: transformCharacterFeedback(feedbackSelection),
    rater_feedback: transformRaterFeedback(feedbackSelection),
    editor_feedback: transformEditorFeedback(feedbackSelection)
  };
}
