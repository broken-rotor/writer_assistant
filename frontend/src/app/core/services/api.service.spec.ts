import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { ApiService, ApiResponse } from './api.service';
import { StoryInput, StoryDraft, Character, FeedbackData } from '../../shared/models';
import { environment } from '../../../environments/environment';

describe('ApiService', () => {
  let service: ApiService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [ApiService]
    });
    service = TestBed.inject(ApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('generateDraft', () => {
    it('should send POST request with correct payload', () => {
      const mockInput: StoryInput = {
        theme: 'A detective story',
        genre: 'Mystery',
        length: 'short_story',
        style: 'Noir',
        focusAreas: ['plot', 'atmosphere']
      };

      const mockResponse: ApiResponse<StoryDraft> = {
        success: true,
        data: {
          title: 'The Dark Case',
          outline: [],
          characters: [],
          themes: ['mystery', 'noir'],
          metadata: {
            timestamp: new Date(),
            requestId: 'req-123',
            processingTime: 1500,
            model: 'test-model'
          }
        }
      };

      service.generateDraft(mockInput).subscribe(response => {
        expect(response.success).toBe(true);
        expect(response.data.title).toBe('The Dark Case');
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/generate/draft`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body.user_input.content).toBe('A detective story');
      req.flush(mockResponse);
    });
  });

  describe('reviseDraft', () => {
    it('should send revision request with feedback', () => {
      const mockDraft: StoryDraft = {
        title: 'Original Title',
        outline: [],
        characters: [],
        themes: ['mystery'],
        metadata: {
          timestamp: new Date(),
          requestId: 'req-456',
          processingTime: 2000,
          model: 'test-model'
        }
      };

      const mockResponse: ApiResponse<StoryDraft> = {
        success: true,
        data: {
          ...mockDraft,
          title: 'Revised Title'
        }
      };

      service.reviseDraft(mockDraft, 'Make it darker', ['Change title']).subscribe(response => {
        expect(response.data.title).toBe('Revised Title');
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/generate/revise-draft`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body.user_feedback).toBe('Make it darker');
      req.flush(mockResponse);
    });
  });

  describe('generateCharacterDialog', () => {
    it('should generate character dialog with context', () => {
      const mockCharacter: Character = {
        id: 'char-1',
        name: 'Detective Jones',
        role: 'protagonist',
        personality: {
          coreTraits: ['analytical', 'determined'],
          emotionalPatterns: ['stoic'],
          speechPatterns: ['direct'],
          motivations: ['justice']
        },
        background: 'Veteran detective',
        currentState: {
          emotionalState: 'focused',
          activeGoals: ['solve case'],
          currentKnowledge: ['crime scene details'],
          relationships: {}
        },
        memorySize: 1024,
        isHidden: false,
        creationSource: 'user_defined',
        aiExpansionHistory: []
      };

      const mockResponse: ApiResponse<any> = {
        success: true,
        data: {
          dialog: 'I need to find the truth',
          emotionalResponse: 'determined'
        }
      };

      service.generateCharacterDialog(mockCharacter, 'What do you think?', {}).subscribe(response => {
        expect(response.success).toBe(true);
        expect(response.data.dialog).toBeTruthy();
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/character/dialog`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body.character_definition.name).toBe('Detective Jones');
      req.flush(mockResponse);
    });
  });

  describe('generateCharacterReactions', () => {
    it('should generate reactions for selected characters', () => {
      const mockDraft: StoryDraft = {
        title: 'Test Story',
        outline: [],
        characters: [],
        themes: [],
        metadata: {
          timestamp: new Date(),
          requestId: 'req-789',
          processingTime: 1800,
          model: 'test-model'
        }
      };

      const mockResponse: ApiResponse<any> = {
        success: true,
        data: {
          reactions: [
            { characterId: 'char-1', reaction: 'surprised' }
          ]
        }
      };

      service.generateCharacterReactions(mockDraft, ['char-1'], 'React to plot twist').subscribe(response => {
        expect(response.data.reactions.length).toBe(1);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/character/generate-reactions`);
      expect(req.request.method).toBe('POST');
      req.flush(mockResponse);
    });
  });

  describe('generateDetailedContent', () => {
    it('should generate detailed content with user guidance', () => {
      const mockDraft: StoryDraft = {
        title: 'Test Story',
        outline: [],
        characters: [],
        themes: [],
        metadata: {
          timestamp: new Date(),
          requestId: 'req-101',
          processingTime: 3000,
          model: 'test-model'
        }
      };

      const mockResponse: ApiResponse<any> = {
        success: true,
        data: {
          content: 'Detailed chapter content...',
          wordCount: 2500
        }
      };

      service.generateDetailedContent(mockDraft, [], 'Focus on atmosphere').subscribe(response => {
        expect(response.data.content).toBeTruthy();
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/generate/detailed-content`);
      expect(req.request.method).toBe('POST');
      req.flush(mockResponse);
    });
  });

  describe('generateFeedback', () => {
    it('should request feedback from multiple agents', () => {
      const mockResponse: ApiResponse<FeedbackData[]> = {
        success: true,
        data: [
          {
            agentId: 'rater-1',
            agentName: 'Character Consistency',
            score: 8.5,
            feedback: 'Good character development',
            suggestions: ['Add more backstory'],
            timestamp: new Date()
          }
        ]
      };

      service.generateFeedback({}, {}, []).subscribe(response => {
        expect(response.data.length).toBeGreaterThan(0);
        expect(response.data[0].agentName).toBe('Character Consistency');
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/feedback/generate`);
      expect(req.request.method).toBe('POST');
      req.flush(mockResponse);
    });
  });

  describe('applySelectedFeedback', () => {
    it('should apply selected feedback to content', () => {
      const mockResponse: ApiResponse<any> = {
        success: true,
        data: {
          revisedContent: 'Updated content with feedback applied'
        }
      };

      service.applySelectedFeedback({}, {}, [], []).subscribe(response => {
        expect(response.data.revisedContent).toBeTruthy();
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/generate/apply-feedback`);
      expect(req.request.method).toBe('POST');
      req.flush(mockResponse);
    });
  });

  describe('Utility APIs', () => {
    it('should validate story structure', () => {
      const mockResponse: ApiResponse<any> = {
        success: true,
        data: {
          isValid: true,
          issues: []
        }
      };

      service.validateStoryStructure({}, {}).subscribe(response => {
        expect(response.data.isValid).toBe(true);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/validate/story-structure`);
      expect(req.request.method).toBe('POST');
      req.flush(mockResponse);
    });

    it('should get agent types', () => {
      const mockResponse: ApiResponse<any> = {
        success: true,
        data: {
          agents: ['writer', 'character', 'rater', 'editor']
        }
      };

      service.getAgentTypes().subscribe(response => {
        expect(response.data.agents.length).toBe(4);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/agents/types`);
      expect(req.request.method).toBe('GET');
      req.flush(mockResponse);
    });

    it('should get character templates', () => {
      const mockResponse: ApiResponse<any> = {
        success: true,
        data: {
          templates: ['detective', 'sidekick', 'villain']
        }
      };

      service.getCharacterTemplates().subscribe(response => {
        expect(response.data.templates.length).toBe(3);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/templates/characters`);
      expect(req.request.method).toBe('GET');
      req.flush(mockResponse);
    });

    it('should check API health', () => {
      const mockResponse: ApiResponse<any> = {
        success: true,
        data: {
          status: 'healthy',
          uptime: 12345
        }
      };

      service.checkApiHealth().subscribe(response => {
        expect(response.data.status).toBe('healthy');
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/health`);
      expect(req.request.method).toBe('GET');
      req.flush(mockResponse);
    });
  });

  describe('Error Handling', () => {
    it('should handle HTTP errors', () => {
      const mockInput: StoryInput = {
        theme: 'Test',
        genre: 'Test',
        length: 'short_story',
        style: 'Test',
        focusAreas: []
      };

      service.generateDraft(mockInput).subscribe(
        () => fail('Should have failed'),
        error => {
          expect(error.status).toBe(500);
        }
      );

      const req = httpMock.expectOne(`${environment.apiUrl}/generate/draft`);
      req.flush('Server Error', { status: 500, statusText: 'Internal Server Error' });
    });
  });
});
