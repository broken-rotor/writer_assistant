/**
 * Utility functions for transforming frontend feedback selection to backend API format
 */

import { 
  CharacterFeedbackItem, 
  RaterFeedbackItem, 
  EditorFeedbackItem,
  Story,
  CharacterFeedbackResponse,
  RaterFeedbackResponse
} from '../models/story.model';
import { FeedbackSelection } from '../components/feedback-selector/feedback-selector.component';

/**
 * Transform frontend FeedbackSelection to backend CharacterFeedbackItem array
 */
export function transformCharacterFeedback(
  feedbackSelection: FeedbackSelection,
  story: Story,
  characterFeedbackResponses: CharacterFeedbackResponse[]
): CharacterFeedbackItem[] {
  const characterFeedback: CharacterFeedbackItem[] = [];
  
  // Iterate through selected character feedback
  Object.entries(feedbackSelection.characterFeedback).forEach(([characterName, selectedFeedbackTexts]) => {
    // Find the character's feedback response by name
    const characterResponse = characterFeedbackResponses.find((cf: CharacterFeedbackResponse) => cf.characterName === characterName);
    if (!characterResponse) return;
    
    // Transform each selected feedback text
    selectedFeedbackTexts.forEach(feedbackText => {
      // Determine the feedback type by checking which array contains this text
      let feedbackType: CharacterFeedbackItem['type'] | null = null;
      
      if (characterResponse.feedback.actions.includes(feedbackText)) {
        feedbackType = 'action';
      } else if (characterResponse.feedback.dialog.includes(feedbackText)) {
        feedbackType = 'dialog';
      } else if (characterResponse.feedback.physicalSensations.includes(feedbackText)) {
        feedbackType = 'physicalSensation';
      } else if (characterResponse.feedback.emotions.includes(feedbackText)) {
        feedbackType = 'emotion';
      } else if (characterResponse.feedback.internalMonologue.includes(feedbackText)) {
        feedbackType = 'internalMonologue';
      } else if (characterResponse.feedback.goals.includes(feedbackText)) {
        feedbackType = 'goals';
      } else if (characterResponse.feedback.memories.includes(feedbackText)) {
        feedbackType = 'memories';
      } else if (characterResponse.feedback.subtext.includes(feedbackText)) {
        feedbackType = 'subtext';
      }
      
      if (feedbackType) {
        characterFeedback.push({
          character_name: characterName,
          type: feedbackType,
          content: feedbackText
        });
      }
    });
  });
  
  return characterFeedback;
}

/**
 * Transform frontend FeedbackSelection to backend RaterFeedbackItem array
 */
export function transformRaterFeedback(
  feedbackSelection: FeedbackSelection,
  story: Story,
  raterFeedbackResponses: RaterFeedbackResponse[]
): RaterFeedbackItem[] {
  const raterFeedback: RaterFeedbackItem[] = [];
  
  // Iterate through selected rater feedback
  Object.entries(feedbackSelection.raterFeedback).forEach(([raterName, selectedFeedbackTexts]) => {
    // Find the rater's feedback response by name
    const raterResponse = raterFeedbackResponses.find((rf: RaterFeedbackResponse) => rf.raterName === raterName);
    if (!raterResponse) return;
    
    // Transform each selected feedback text
    selectedFeedbackTexts.forEach(feedbackText => {
      // Check if this text is in the opinion or suggestions
      if (raterResponse.feedback.opinion === feedbackText) {
        raterFeedback.push({
          rater_name: raterName,
          content: feedbackText
        });
      } else {
        // Check if it's one of the suggestions
        const suggestion = raterResponse.feedback.suggestions.find(s => 
          s.issue === feedbackText || s.suggestion === feedbackText
        );
        if (suggestion) {
          raterFeedback.push({
            rater_name: raterName,
            content: feedbackText
          });
        }
      }
    });
  });
  
  return raterFeedback;
}

/**
 * Transform editor feedback (currently not implemented in frontend, returns empty array)
 */
export function transformEditorFeedback(
  _feedbackSelection: FeedbackSelection,
  _story: Story
): EditorFeedbackItem[] {
  // Editor feedback is not currently implemented in the frontend feedback selector
  // Return empty array for now
  return [];
}

/**
 * Transform complete feedback selection to backend format
 */
export function transformFeedbackSelection(
  feedbackSelection: FeedbackSelection,
  story: Story,
  characterFeedbackResponses: CharacterFeedbackResponse[] = [],
  raterFeedbackResponses: RaterFeedbackResponse[] = []
): {
  character_feedback: CharacterFeedbackItem[];
  rater_feedback: RaterFeedbackItem[];
  editor_feedback: EditorFeedbackItem[];
} {
  return {
    character_feedback: transformCharacterFeedback(feedbackSelection, story, characterFeedbackResponses),
    rater_feedback: transformRaterFeedback(feedbackSelection, story, raterFeedbackResponses),
    editor_feedback: transformEditorFeedback(feedbackSelection, story)
  };
}
