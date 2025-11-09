import { Injectable } from '@angular/core';
import { 
  Story, 
  OutlineItem,
  PlotElement,
  UserRequest
} from '../models/story.model';

interface DraftOutlineItem {
  id: string;
  title: string;
  description: string;
  order: number;
  type?: string;
  sourceMessageId?: string;
}

@Injectable({
  providedIn: 'root'
})
export class PlotOutlineContextService {

  constructor() { 
    // Service initialization - no dependencies required
  }

  /**
   * Extract plot outline context relevant to a specific chapter
   */
  extractChapterPlotContext(
    story: Story, 
    chapterNumber: number
  ): { plotElements: PlotElement[], userRequests: UserRequest[] } {
    const plotElements: PlotElement[] = [];
    const userRequests: UserRequest[] = [];

    try {
      // Extract from structured plot outline if available
      if (story.plotOutline?.content) {
        const contentElements = this.extractFromPlotOutlineContent(
          story.plotOutline.content, 
          chapterNumber
        );
        plotElements.push(...contentElements);
      }

      // Extract from draft outline items if available in plot outline phase
      const draftItems = this.extractDraftOutlineItems(story);
      if (draftItems.length > 0) {
        const draftElements = this.extractFromDraftItems(draftItems, chapterNumber);
        plotElements.push(...draftElements);
      }

      // Create user requests from plot outline context
      if (plotElements.length > 0) {
        const contextRequest = this.createPlotOutlineUserRequest(plotElements, chapterNumber);
        userRequests.push(contextRequest);
      }

      console.log(`Extracted ${plotElements.length} plot elements and ${userRequests.length} user requests for chapter ${chapterNumber}`);

    } catch (error) {
      console.error('Error extracting plot outline context:', error);
    }

    return { plotElements, userRequests };
  }

  /**
   * Extract draft outline items from story's chapter compose state
   */
  private extractDraftOutlineItems(story: Story): DraftOutlineItem[] {
    // Chapter compose has been removed, return empty array
    return [];
  }

  /**
   * Extract plot elements from plot outline content string
   */
  private extractFromPlotOutlineContent(content: string, chapterNumber: number): PlotElement[] {
    const elements: PlotElement[] = [];

    try {
      // Split content into sections
      const sections = this.splitContentIntoSections(content);

      sections.forEach((section, index) => {
        if (this.isSectionRelevantToChapter(section, chapterNumber)) {
          const element: PlotElement = {
            id: `content_section_${index}`,
            type: 'chapter_outline',
            content: section.trim(),
            priority: this.determineContentPriority(section, chapterNumber),
            tags: this.extractContentTags(section),
            metadata: {
              chapter_number: chapterNumber,
              source: 'plot_outline_content',
              section_index: index,
              outline_summary: section.length > 200 ? section.substring(0, 200) + '...' : section
            }
          };
          elements.push(element);
        }
      });

    } catch (error) {
      console.warn('Error extracting from plot outline content:', error);
    }

    return elements;
  }

  /**
   * Extract plot elements from structured draft outline items
   */
  private extractFromDraftItems(draftItems: DraftOutlineItem[], chapterNumber: number): PlotElement[] {
    const elements: PlotElement[] = [];

    try {
      draftItems.forEach(item => {
        if (this.isItemRelevantToChapter(item, chapterNumber)) {
          const element: PlotElement = {
            id: `outline_item_${item.id}`,
            type: 'chapter_outline',
            content: this.formatOutlineItemContent(item),
            priority: this.determineItemPriority(item, chapterNumber),
            tags: this.extractItemTags(item),
            metadata: {
              chapter_number: chapterNumber,
              source: 'draft_outline_item',
              item_id: item.id,
              item_type: item.type || 'unknown',
              order: item.order,
              outline_summary: item.description.length > 200 ? item.description.substring(0, 200) + '...' : item.description
            }
          };
          elements.push(element);
        }
      });

    } catch (error) {
      console.warn('Error extracting from draft items:', error);
    }

    return elements;
  }

  /**
   * Split plot outline content into logical sections
   */
  private splitContentIntoSections(content: string): string[] {
    // Split by common section delimiters
    const delimiters = [
      /\n\s*Chapter\s+\d+/gi,
      /\n\s*Ch\s+\d+/gi,
      /\n\s*#\d+/g,
      /\n\s*\d+\./g,
      /\n\s*-\s*/g,
      /\n\n+/g
    ];

    let sections = [content];

    delimiters.forEach(delimiter => {
      const newSections: string[] = [];
      sections.forEach(section => {
        const parts = section.split(delimiter);
        newSections.push(...parts.filter(part => part.trim().length > 0));
      });
      sections = newSections;
    });

    // Filter out very short sections
    return sections.filter(section => section.trim().length > 20);
  }

  /**
   * Check if a draft outline item is relevant to the specified chapter
   */
  private isItemRelevantToChapter(item: DraftOutlineItem, chapterNumber: number): boolean {
    const itemText = `${item.title} ${item.description}`.toLowerCase();

    // Look for chapter references
    const chapterPatterns = [
      new RegExp(`chapter\\s*${chapterNumber}\\b`, 'i'),
      new RegExp(`ch\\s*${chapterNumber}\\b`, 'i'),
      new RegExp(`#${chapterNumber}\\b`, 'i')
    ];

    for (const pattern of chapterPatterns) {
      if (pattern.test(itemText)) {
        return true;
      }
    }

    // Check item order for sequential relevance
    if (item.order > 0) {
      // Include items around the chapter number for context
      return Math.abs(item.order - chapterNumber) <= 2;
    }

    // Check item type for general relevance
    const itemType = (item.type || '').toLowerCase();
    if (['chapter', 'scene', 'plot-point'].includes(itemType)) {
      return true;
    }

    return false;
  }

  /**
   * Check if a content section is relevant to the specified chapter
   */
  private isSectionRelevantToChapter(section: string, chapterNumber: number): boolean {
    const sectionLower = section.toLowerCase();

    // Look for chapter references
    const chapterPatterns = [
      new RegExp(`chapter\\s*${chapterNumber}\\b`, 'i'),
      new RegExp(`ch\\s*${chapterNumber}\\b`, 'i'),
      new RegExp(`#${chapterNumber}\\b`, 'i')
    ];

    for (const pattern of chapterPatterns) {
      if (pattern.test(sectionLower)) {
        return true;
      }
    }

    // Include substantial sections for general context
    return section.trim().length > 50;
  }

  /**
   * Format a draft outline item into content for PlotElement
   */
  private formatOutlineItemContent(item: DraftOutlineItem): string {
    if (item.title && item.description) {
      return `${item.title}: ${item.description}`;
    } else if (item.title) {
      return item.title;
    } else if (item.description) {
      return item.description;
    } else {
      return 'Plot outline item';
    }
  }

  /**
   * Determine priority level for a draft outline item
   */
  private determineItemPriority(item: DraftOutlineItem, chapterNumber: number): 'high' | 'medium' | 'low' {
    const itemText = `${item.title} ${item.description}`.toLowerCase();

    // High priority for items that directly reference the chapter
    const chapterPatterns = [
      new RegExp(`chapter\\s*${chapterNumber}\\b`, 'i'),
      new RegExp(`ch\\s*${chapterNumber}\\b`, 'i')
    ];

    for (const pattern of chapterPatterns) {
      if (pattern.test(itemText)) {
        return 'high';
      }
    }

    // Medium priority for items with relevant types
    const itemType = (item.type || '').toLowerCase();
    if (['chapter', 'scene', 'plot-point'].includes(itemType)) {
      return 'medium';
    }

    return 'low';
  }

  /**
   * Determine priority level for a content section
   */
  private determineContentPriority(section: string, chapterNumber: number): 'high' | 'medium' | 'low' {
    const sectionLower = section.toLowerCase();

    // High priority for sections that directly reference the chapter
    const chapterPatterns = [
      new RegExp(`chapter\\s*${chapterNumber}\\b`, 'i'),
      new RegExp(`ch\\s*${chapterNumber}\\b`, 'i')
    ];

    for (const pattern of chapterPatterns) {
      if (pattern.test(sectionLower)) {
        return 'high';
      }
    }

    // Medium priority for substantial sections
    if (section.trim().length > 100) {
      return 'medium';
    }

    return 'low';
  }

  /**
   * Extract tags from a draft outline item
   */
  private extractItemTags(item: DraftOutlineItem): string[] {
    const tags = ['plot_outline', 'chapter_context'];

    // Add type-based tags
    if (item.type) {
      tags.push(`type_${item.type}`);
    }

    // Add order-based tags
    if (item.order > 0) {
      tags.push(`order_${item.order}`);
    }

    return tags;
  }

  /**
   * Extract tags from a content section
   */
  private extractContentTags(section: string): string[] {
    const tags = ['plot_outline', 'chapter_context', 'content_section'];
    const sectionLower = section.toLowerCase();

    // Add content-based tags
    if (sectionLower.includes('conflict')) {
      tags.push('conflict');
    }
    if (sectionLower.includes('resolution')) {
      tags.push('resolution');
    }
    if (sectionLower.includes('character')) {
      tags.push('character_focus');
    }
    if (sectionLower.includes('scene')) {
      tags.push('scene');
    }

    return tags;
  }

  /**
   * Create a user request that incorporates plot outline context
   */
  private createPlotOutlineUserRequest(plotElements: PlotElement[], chapterNumber: number): UserRequest {
    const outlineContent = plotElements
      .filter(element => element.priority === 'high' || element.priority === 'medium')
      .map(element => element.content)
      .join('\n\n');

    const content = `Please use the following plot outline context when creating this chapter:\n\n${outlineContent}\n\nEnsure the chapter aligns with and advances the plot outline while maintaining narrative flow.`;

    return {
      id: `plot_outline_context_ch${chapterNumber}`,
      type: 'general',
      content: content,
      priority: 'high',
      target: `chapter_${chapterNumber}`,
      context: 'plot_outline_integration',
      timestamp: new Date()
    };
  }

  /**
   * Check if story has plot outline data available
   */
  hasPlotOutlineData(story: Story): boolean {
    return !!(story.plotOutline?.content);
  }

  /**
   * Get a summary of available plot outline data for display
   */
  getPlotOutlineSummary(story: Story): string {
    if (!this.hasPlotOutlineData(story)) {
      return 'No plot outline available';
    }

    const summaryParts: string[] = [];

    if (story.plotOutline?.content) {
      const wordCount = story.plotOutline.content.split(/\s+/).length;
      summaryParts.push(`Plot outline: ${wordCount} words`);
    }

    const draftItems = this.extractDraftOutlineItems(story);
    if (draftItems.length > 0) {
      summaryParts.push(`${draftItems.length} outline items`);
    }

    return summaryParts.join(', ');
  }
}
