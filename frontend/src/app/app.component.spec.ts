import { TestBed } from '@angular/core/testing';
import { Router, NavigationEnd } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { AppComponent } from './app.component';
import { LocalStorageService } from './core/services/local-storage.service';
import { Subject } from 'rxjs';

describe('AppComponent', () => {
  let component: AppComponent;
  let mockRouter: any;
  let mockLocalStorageService: jasmine.SpyObj<LocalStorageService>;
  let routerEventsSubject: Subject<any>;

  beforeEach(async () => {
    routerEventsSubject = new Subject();

    mockRouter = {
      navigate: jasmine.createSpy('navigate'),
      events: routerEventsSubject.asObservable()
    };

    mockLocalStorageService = jasmine.createSpyObj('LocalStorageService', [
      'getStorageInfo',
      'getAllStories'
    ]);

    await TestBed.configureTestingModule({
      declarations: [AppComponent],
      imports: [
        RouterTestingModule,
        MatToolbarModule,
        MatIconModule,
        MatButtonModule
      ],
      providers: [
        { provide: Router, useValue: mockRouter },
        { provide: LocalStorageService, useValue: mockLocalStorageService }
      ]
    }).compileComponents();

    const fixture = TestBed.createComponent(AppComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create the app', () => {
    expect(component).toBeTruthy();
  });

  it('should have title "Writer Assistant"', () => {
    expect(component.title).toBe('Writer Assistant');
  });

  describe('Route Tracking', () => {
    it('should track current route on navigation', () => {
      const navigationEvent = new NavigationEnd(1, '/stories', '/stories');

      routerEventsSubject.next(navigationEvent);

      expect(component.currentRoute).toBe('/stories');
    });

    it('should update current route on multiple navigations', () => {
      routerEventsSubject.next(new NavigationEnd(1, '/stories', '/stories'));
      expect(component.currentRoute).toBe('/stories');

      routerEventsSubject.next(new NavigationEnd(2, '/story-input', '/story-input'));
      expect(component.currentRoute).toBe('/story-input');
    });

    it('should check if current route matches', () => {
      component.currentRoute = '/stories';

      expect(component.isCurrentRoute('/stories')).toBeTruthy();
      expect(component.isCurrentRoute('/story-input')).toBeFalsy();
    });

    it('should check route with path parameters', () => {
      component.currentRoute = '/draft-review/story-123';

      expect(component.isCurrentRoute('/draft-review')).toBeTruthy();
      expect(component.isCurrentRoute('/stories')).toBeFalsy();
    });
  });

  describe('Navigation Methods', () => {
    it('should navigate to stories list', () => {
      component.onNavigateToStories();

      expect(mockRouter.navigate).toHaveBeenCalledWith(['/stories']);
    });

    it('should navigate to create new story', () => {
      component.onCreateNewStory();

      expect(mockRouter.navigate).toHaveBeenCalledWith(['/story-input']);
    });
  });

  describe('Initialization', () => {
    it('should initialize currentRoute as empty string', () => {
      const newComponent = new AppComponent(mockRouter, mockLocalStorageService);
      expect(newComponent.currentRoute).toBe('');
    });

    it('should set up router event subscription on init', () => {
      component.ngOnInit();

      const navigationEvent = new NavigationEnd(1, '/test-route', '/test-route');
      routerEventsSubject.next(navigationEvent);

      expect(component.currentRoute).toBe('/test-route');
    });
  });
});
