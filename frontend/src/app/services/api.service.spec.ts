import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { ApiService } from './api.service';
import {
  CharacterFeedbackRequest,
  CharacterFeedbackResponse,
  RaterFeedbackRequest,
  RaterFeedbackResponse,
  GenerateChapterRequest,
  GenerateChapterResponse
} from '../models/story.model';

describe('ApiService', () => {
  let service: ApiService;
  let httpMock: HttpTestingController;
  const baseUrl = 'http://localhost:8000/api/v1';

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

  describe('requestCharacterFeedback', () => {
    it('should send POST request to character-feedback endpoint', () => {
      const request: CharacterFeedbackRequest = {
        systemPrompts: {
          mainPrefix: '',
          mainSuffix: ''
        },
        worldbuilding: 'A fantasy world',
        storySummary: 'A story',
        previousChapters: [],
        character: {
          name: 'Test Character',
          basicBio: 'A hero',
          sex: 'Male',
          gender: 'Male',
          sexualPreference: 'Heterosexual',
          age: 30,
          physicalAppearance: 'Tall',
          usualClothing: 'Armor',
          personality: 'Brave',
          motivations: 'Justice',
          fears: 'Failure',
          relationships: 'None'
        },
        plotPoint: 'The hero enters the dungeon'
      };

      const mockResponse: CharacterFeedbackResponse = {
        characterName: 'Test Character',
        feedback: {
          actions: ['Draw sword'],
          dialog: ['I must be brave'],
          sensations: ['Heart pounding'],
          emotions: ['Fear', 'Determination'],
          thoughts: ['What dangers await?']
        }
      };

      service.requestCharacterFeedback(request).subscribe(response => {
        expect(response).toEqual(mockResponse);
      });

      const req = httpMock.expectOne(`${baseUrl}/character-feedback`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual(request);
      req.flush(mockResponse);
    });
  });

  describe('requestRaterFeedback', () => {
    it('should send POST request to rater-feedback endpoint', () => {
      const request: RaterFeedbackRequest = {
        systemPrompts: {
          mainPrefix: '',
          mainSuffix: ''
        },
        raterPrompt: 'Evaluate pacing',
        worldbuilding: 'A fantasy world',
        storySummary: 'A story',
        previousChapters: [],
        plotPoint: 'The hero enters the dungeon'
      };

      const mockResponse: RaterFeedbackResponse = {
        raterName: 'Pacing Rater',
        feedback: {
          opinion: 'The pacing is good',
          suggestions: [
            {
              issue: 'Slow intro',
              suggestion: 'Start with action',
              priority: 'medium'
            }
          ]
        }
      };

      service.requestRaterFeedback(request).subscribe(response => {
        expect(response).toEqual(mockResponse);
      });

      const req = httpMock.expectOne(`${baseUrl}/rater-feedback`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual(request);
      req.flush(mockResponse);
    });
  });

  describe('generateChapter', () => {
    it('should send POST request to generate-chapter endpoint', () => {
      const request: GenerateChapterRequest = {
        systemPrompts: {
          mainPrefix: '',
          mainSuffix: '',
          assistantPrompt: 'You are a writer'
        },
        worldbuilding: 'A fantasy world',
        storySummary: 'A story',
        previousChapters: [],
        characters: [],
        plotPoint: 'The hero enters the dungeon',
        incorporatedFeedback: []
      };

      const mockResponse: GenerateChapterResponse = {
        chapterText: 'The hero stepped into the dark dungeon...'
      };

      service.generateChapter(request).subscribe(response => {
        expect(response).toEqual(mockResponse);
      });

      const req = httpMock.expectOne(`${baseUrl}/generate-chapter`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual(request);
      req.flush(mockResponse);
    });
  });

  describe('modifyChapter', () => {
    it('should send POST request to modify-chapter endpoint', () => {
      const request = {
        systemPrompts: {
          mainPrefix: '',
          mainSuffix: '',
          assistantPrompt: 'You are a writer'
        },
        worldbuilding: 'A fantasy world',
        storySummary: 'A story',
        previousChapters: [],
        currentChapter: 'Original chapter text',
        userRequest: 'Make it more exciting'
      };

      const mockResponse = {
        modifiedChapterText: 'The hero burst into the dark dungeon...'
      };

      service.modifyChapter(request).subscribe(response => {
        expect(response).toEqual(mockResponse);
      });

      const req = httpMock.expectOne(`${baseUrl}/modify-chapter`);
      expect(req.request.method).toBe('POST');
      req.flush(mockResponse);
    });
  });

  describe('requestEditorReview', () => {
    it('should send POST request to editor-review endpoint', () => {
      const request = {
        systemPrompts: {
          mainPrefix: '',
          mainSuffix: '',
          editorPrompt: 'You are an editor'
        },
        worldbuilding: 'A fantasy world',
        storySummary: 'A story',
        previousChapters: [],
        characters: [],
        chapterToReview: 'Chapter text to review'
      };

      const mockResponse = {
        overallAssessment: 'Good chapter',
        suggestions: [
          {
            issue: 'Pacing issue',
            suggestion: 'Add more action',
            priority: 'high' as const,
            selected: false
          }
        ]
      };

      service.requestEditorReview(request).subscribe(response => {
        expect(response).toEqual(mockResponse);
      });

      const req = httpMock.expectOne(`${baseUrl}/editor-review`);
      expect(req.request.method).toBe('POST');
      req.flush(mockResponse);
    });
  });

  describe('fleshOut', () => {
    it('should send POST request to flesh-out endpoint', () => {
      const request = {
        systemPrompts: {
          mainPrefix: '',
          mainSuffix: ''
        },
        worldbuilding: 'A fantasy world',
        storySummary: 'A story',
        textToFleshOut: 'The hero is brave',
        context: 'character description'
      };

      const mockResponse = {
        fleshedOutText: 'The hero is brave, standing tall in the face of danger...'
      };

      service.fleshOut(request).subscribe(response => {
        expect(response).toEqual(mockResponse);
      });

      const req = httpMock.expectOne(`${baseUrl}/flesh-out`);
      expect(req.request.method).toBe('POST');
      req.flush(mockResponse);
    });
  });

  describe('generateCharacterDetails', () => {
    it('should send POST request to generate-character-details endpoint', () => {
      const request = {
        systemPrompts: {
          mainPrefix: '',
          mainSuffix: ''
        },
        worldbuilding: 'A fantasy world',
        storySummary: 'A story',
        basicBio: 'A brave knight',
        existingCharacters: []
      };

      const mockResponse = {
        name: 'Sir Galahad',
        sex: 'Male',
        gender: 'Male',
        sexualPreference: 'Heterosexual',
        age: 35,
        physicalAppearance: 'Tall and muscular',
        usualClothing: 'Plate armor',
        personality: 'Brave and honorable',
        motivations: 'Protect the weak',
        fears: 'Dishonor',
        relationships: 'Loyal to the king'
      };

      service.generateCharacterDetails(request).subscribe(response => {
        expect(response).toEqual(mockResponse);
      });

      const req = httpMock.expectOne(`${baseUrl}/generate-character-details`);
      expect(req.request.method).toBe('POST');
      req.flush(mockResponse);
    });
  });
});
