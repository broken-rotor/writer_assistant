import { ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';

import { TokenCounterComponent } from './token-counter.component';
import {
  TokenCounterData,
  TokenCounterConfig,
  TokenCounterDisplayMode,
  TokenCounterStatus,
  TokenCounterUtils
} from '../../models/token-counter.model';

describe('TokenCounterComponent', () => {
  let component: TokenCounterComponent;
  let fixture: ComponentFixture<TokenCounterComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TokenCounterComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(TokenCounterComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  describe('Component Initialization', () => {
    it('should initialize with default configuration', () => {
      component.ngOnInit();
      
      expect(component.computedConfig.displayMode).toBe(TokenCounterDisplayMode.DETAILED);
      expect(component.computedConfig.showProgressBar).toBe(true);
      expect(component.computedConfig.showCount).toBe(true);
      expect(component.computedConfig.showStatus).toBe(true);
    });

    it('should merge custom configuration with defaults', () => {
      const customConfig: Partial<TokenCounterConfig> = {
        displayMode: TokenCounterDisplayMode.COMPACT,
        showProgressBar: false,
        customClasses: ['custom-class']
      };
      
      component.config = customConfig;
      component.ngOnInit();
      
      expect(component.computedConfig.displayMode).toBe(TokenCounterDisplayMode.COMPACT);
      expect(component.computedConfig.showProgressBar).toBe(false);
      expect(component.computedConfig.showCount).toBe(true); // Should keep default
      expect(component.computedConfig.customClasses).toEqual(['custom-class']);
    });
  });

  describe('State Management', () => {
    it('should handle loading state', () => {
      component.loading = true;
      component.ngOnInit();
      
      expect(component.state.status).toBe(TokenCounterStatus.LOADING);
      expect(component.state.isLoading).toBe(true);
    });

    it('should handle error state', () => {
      component.error = 'Test error message';
      component.ngOnInit();
      
      expect(component.state.status).toBe(TokenCounterStatus.ERROR);
      expect(component.state.errorMessage).toBe('Test error message');
      expect(component.state.isLoading).toBe(false);
    });

    it('should calculate status correctly for good token count', () => {
      const data: TokenCounterData = { current: 500, limit: 1000 };
      component.data = data;
      component.ngOnInit();
      
      expect(component.state.status).toBe(TokenCounterStatus.GOOD);
      expect(component.state.percentage).toBe(50);
    });

    it('should calculate status correctly for warning token count', () => {
      const data: TokenCounterData = { current: 850, limit: 1000 };
      component.data = data;
      component.ngOnInit();
      
      expect(component.state.status).toBe(TokenCounterStatus.WARNING);
      expect(component.state.percentage).toBe(85);
    });

    it('should calculate status correctly for over limit token count', () => {
      const data: TokenCounterData = { current: 1200, limit: 1000 };
      component.data = data;
      component.ngOnInit();
      
      expect(component.state.status).toBe(TokenCounterStatus.OVER_LIMIT);
      expect(component.state.percentage).toBe(100); // Capped at 100%
    });

    it('should use custom warning threshold', () => {
      const data: TokenCounterData = { 
        current: 700, 
        limit: 1000, 
        warningThreshold: 600 
      };
      component.data = data;
      component.ngOnInit();
      
      expect(component.state.status).toBe(TokenCounterStatus.WARNING);
      expect(component.state.warningThreshold).toBe(600);
    });

    it('should emit status change events', () => {
      spyOn(component.statusChange, 'emit');
      
      const data: TokenCounterData = { current: 500, limit: 1000 };
      component.data = data;
      component.ngOnInit();
      
      expect(component.statusChange.emit).toHaveBeenCalledWith(TokenCounterStatus.GOOD);
    });
  });

  describe('Display Mode Logic', () => {
    it('should show detailed mode correctly', () => {
      component.config = { displayMode: TokenCounterDisplayMode.DETAILED };
      component.ngOnInit();
      
      expect(component.shouldShowDetailed()).toBe(true);
      expect(component.shouldShowCompact()).toBe(false);
      expect(component.shouldShowMobile()).toBe(false);
    });

    it('should show compact mode correctly', () => {
      component.config = { displayMode: TokenCounterDisplayMode.COMPACT };
      component.ngOnInit();
      
      expect(component.shouldShowDetailed()).toBe(false);
      expect(component.shouldShowCompact()).toBe(true);
      expect(component.shouldShowMobile()).toBe(false);
    });

    it('should show mobile mode correctly', () => {
      component.config = { displayMode: TokenCounterDisplayMode.MOBILE };
      component.ngOnInit();
      
      expect(component.shouldShowDetailed()).toBe(false);
      expect(component.shouldShowCompact()).toBe(false);
      expect(component.shouldShowMobile()).toBe(true);
    });
  });

  describe('Event Handling', () => {
    beforeEach(() => {
      const data: TokenCounterData = { current: 500, limit: 1000 };
      component.data = data;
      component.ngOnInit();
    });

    it('should emit click events', () => {
      spyOn(component.interaction, 'emit');
      
      const mockEvent = new MouseEvent('click');
      component.onComponentClick(mockEvent);
      
      expect(component.interaction.emit).toHaveBeenCalledWith(
        jasmine.objectContaining({
          type: 'click',
          data: component.data,
          status: component.state.status
        })
      );
    });

    it('should emit hover events', () => {
      spyOn(component.interaction, 'emit');
      
      const mockEvent = new MouseEvent('mouseenter');
      component.onComponentHover(mockEvent);
      
      expect(component.interaction.emit).toHaveBeenCalledWith(
        jasmine.objectContaining({
          type: 'hover',
          data: component.data,
          status: component.state.status
        })
      );
    });

    it('should emit focus events', () => {
      spyOn(component.interaction, 'emit');
      
      const mockEvent = new FocusEvent('focus');
      component.onComponentFocus(mockEvent);
      
      expect(component.interaction.emit).toHaveBeenCalledWith(
        jasmine.objectContaining({
          type: 'focus',
          data: component.data,
          status: component.state.status
        })
      );
    });

    it('should not emit events when disabled', () => {
      spyOn(component.interaction, 'emit');
      component.config = { disabled: true };
      component.ngOnInit();
      
      const mockEvent = new MouseEvent('click');
      component.onComponentClick(mockEvent);
      
      expect(component.interaction.emit).not.toHaveBeenCalled();
    });

    it('should not emit events when no data', () => {
      spyOn(component.interaction, 'emit');
      component.data = null;
      component.ngOnInit();
      
      const mockEvent = new MouseEvent('click');
      component.onComponentClick(mockEvent);
      
      expect(component.interaction.emit).not.toHaveBeenCalled();
    });
  });

  describe('CSS Classes', () => {
    it('should generate correct CSS classes for good status', () => {
      const data: TokenCounterData = { current: 500, limit: 1000 };
      component.data = data;
      component.config = { displayMode: TokenCounterDisplayMode.DETAILED };
      component.ngOnInit();
      
      const classes = component.getComponentClasses();
      
      expect(classes).toContain('token-counter');
      expect(classes).toContain('token-counter--detailed');
      expect(classes).toContain('token-counter--good');
    });

    it('should generate correct CSS classes for warning status', () => {
      const data: TokenCounterData = { current: 850, limit: 1000 };
      component.data = data;
      component.config = { displayMode: TokenCounterDisplayMode.COMPACT };
      component.ngOnInit();
      
      const classes = component.getComponentClasses();
      
      expect(classes).toContain('token-counter');
      expect(classes).toContain('token-counter--compact');
      expect(classes).toContain('token-counter--warning');
    });

    it('should include custom classes', () => {
      const data: TokenCounterData = { current: 500, limit: 1000 };
      component.data = data;
      component.config = { 
        displayMode: TokenCounterDisplayMode.DETAILED,
        customClasses: ['custom-1', 'custom-2']
      };
      component.ngOnInit();
      
      const classes = component.getComponentClasses();
      
      expect(classes).toContain('custom-1');
      expect(classes).toContain('custom-2');
    });

    it('should include loading class when loading', () => {
      component.loading = true;
      component.ngOnInit();
      
      const classes = component.getComponentClasses();
      
      expect(classes).toContain('token-counter--loading');
    });

    it('should include disabled class when disabled', () => {
      component.config = { disabled: true };
      component.ngOnInit();
      
      const classes = component.getComponentClasses();
      
      expect(classes).toContain('token-counter--disabled');
    });
  });

  describe('Accessibility', () => {
    it('should generate correct ARIA label', () => {
      const data: TokenCounterData = { current: 500, limit: 1000 };
      component.data = data;
      component.ngOnInit();
      
      const ariaLabel = component.getAriaLabel();
      
      expect(ariaLabel).toContain('Token counter: 500 of 1000 tokens used (50%). Status: Good');
    });

    it('should use custom ARIA label when provided', () => {
      const data: TokenCounterData = { current: 500, limit: 1000 };
      component.data = data;
      component.config = { ariaLabel: 'Custom token counter label' };
      component.ngOnInit();
      
      const ariaLabel = component.getAriaLabel();
      
      expect(ariaLabel).toBe('Custom token counter label');
    });

    it('should handle no data in ARIA label', () => {
      component.data = null;
      component.ngOnInit();
      
      const ariaLabel = component.getAriaLabel();
      
      expect(ariaLabel).toBe('Token counter: No data');
    });
  });

  describe('Utility Methods', () => {
    beforeEach(() => {
      const data: TokenCounterData = { current: 1247, limit: 2000 };
      component.data = data;
      component.ngOnInit();
    });

    it('should format token count correctly', () => {
      const formatted = component.getFormattedCount();
      expect(formatted).toBe('1.2K/2.0K');
    });

    it('should calculate progress bar width correctly', () => {
      const width = component.getProgressBarWidth();
      expect(width).toBe(62); // 1247/2000 * 100, rounded
    });

    it('should calculate excess tokens when over limit', () => {
      const data: TokenCounterData = { current: 2500, limit: 2000 };
      component.data = data;
      component.ngOnInit();
      
      const excess = component.getExcessTokens();
      expect(excess).toBe(500);
    });

    it('should return zero excess tokens when under limit', () => {
      const excess = component.getExcessTokens();
      expect(excess).toBe(0);
    });
  });

  describe('Template Rendering', () => {
    it('should render detailed mode template', () => {
      const data: TokenCounterData = { current: 500, limit: 1000 };
      component.data = data;
      component.config = { displayMode: TokenCounterDisplayMode.DETAILED };
      fixture.detectChanges();
      
      const detailedElement = fixture.debugElement.query(By.css('.token-counter__detailed'));
      expect(detailedElement).toBeTruthy();
      
      const compactElement = fixture.debugElement.query(By.css('.token-counter__compact'));
      expect(compactElement).toBeFalsy();
    });

    it('should render compact mode template', () => {
      const data: TokenCounterData = { current: 500, limit: 1000 };
      component.data = data;
      component.config = { displayMode: TokenCounterDisplayMode.COMPACT };
      fixture.detectChanges();
      
      const compactElement = fixture.debugElement.query(By.css('.token-counter__compact'));
      expect(compactElement).toBeTruthy();
      
      const detailedElement = fixture.debugElement.query(By.css('.token-counter__detailed'));
      expect(detailedElement).toBeFalsy();
    });

    it('should render mobile mode template', () => {
      const data: TokenCounterData = { current: 500, limit: 1000 };
      component.data = data;
      component.config = { displayMode: TokenCounterDisplayMode.MOBILE };
      fixture.detectChanges();
      
      const mobileElement = fixture.debugElement.query(By.css('.token-counter__mobile'));
      expect(mobileElement).toBeTruthy();
      
      const detailedElement = fixture.debugElement.query(By.css('.token-counter__detailed'));
      expect(detailedElement).toBeFalsy();
    });

    it('should render loading state', () => {
      component.loading = true;
      fixture.detectChanges();
      
      const loadingElement = fixture.debugElement.query(By.css('.token-counter__loading'));
      expect(loadingElement).toBeTruthy();
      
      const spinnerElement = fixture.debugElement.query(By.css('.token-counter__spinner'));
      expect(spinnerElement).toBeTruthy();
    });

    it('should render error state', () => {
      component.error = 'Test error';
      fixture.detectChanges();
      
      const errorElement = fixture.debugElement.query(By.css('.token-counter__error'));
      expect(errorElement).toBeTruthy();
      
      const errorText = errorElement.nativeElement.textContent;
      expect(errorText).toContain('Test error');
    });

    it('should render progress bar when enabled', () => {
      const data: TokenCounterData = { current: 500, limit: 1000 };
      component.data = data;
      component.config = { 
        displayMode: TokenCounterDisplayMode.DETAILED,
        showProgressBar: true 
      };
      fixture.detectChanges();
      
      const progressBar = fixture.debugElement.query(By.css('.token-counter__progress-bar'));
      expect(progressBar).toBeTruthy();
      
      const progressFill = fixture.debugElement.query(By.css('.token-counter__progress-fill'));
      expect(progressFill).toBeTruthy();
    });

    it('should not render progress bar when disabled', () => {
      const data: TokenCounterData = { current: 500, limit: 1000 };
      component.data = data;
      component.config = { 
        displayMode: TokenCounterDisplayMode.DETAILED,
        showProgressBar: false 
      };
      fixture.detectChanges();
      
      const progressBar = fixture.debugElement.query(By.css('.token-counter__progress-bar'));
      expect(progressBar).toBeFalsy();
    });

    it('should render over limit warning', () => {
      const data: TokenCounterData = { current: 1200, limit: 1000 };
      component.data = data;
      component.config = { displayMode: TokenCounterDisplayMode.DETAILED };
      fixture.detectChanges();
      
      const warningElement = fixture.debugElement.query(By.css('.token-counter__over-limit-warning'));
      expect(warningElement).toBeTruthy();
      
      const warningText = warningElement.nativeElement.textContent;
      expect(warningText).toContain('Exceeds limit by');
      expect(warningText).toContain('200');
    });
  });

  describe('Change Detection', () => {
    it('should update state when data changes', () => {
      const initialData: TokenCounterData = { current: 500, limit: 1000 };
      component.data = initialData;
      component.ngOnInit();
      
      expect(component.state.status).toBe(TokenCounterStatus.GOOD);
      
      const newData: TokenCounterData = { current: 1200, limit: 1000 };
      component.data = newData;
      component.ngOnChanges({
        data: {
          currentValue: newData,
          previousValue: initialData,
          firstChange: false,
          isFirstChange: () => false
        }
      });
      
      expect(component.state.status).toBe(TokenCounterStatus.OVER_LIMIT);
    });

    it('should update configuration when config changes', () => {
      const initialConfig = { displayMode: TokenCounterDisplayMode.DETAILED };
      component.config = initialConfig;
      component.ngOnInit();
      
      expect(component.computedConfig.displayMode).toBe(TokenCounterDisplayMode.DETAILED);
      
      const newConfig = { displayMode: TokenCounterDisplayMode.COMPACT };
      component.config = newConfig;
      component.ngOnChanges({
        config: {
          currentValue: newConfig,
          previousValue: initialConfig,
          firstChange: false,
          isFirstChange: () => false
        }
      });
      
      expect(component.computedConfig.displayMode).toBe(TokenCounterDisplayMode.COMPACT);
    });
  });
});

describe('TokenCounterUtils', () => {
  describe('calculateStatus', () => {
    it('should return GOOD for low token counts', () => {
      const status = TokenCounterUtils.calculateStatus(500, 1000);
      expect(status).toBe(TokenCounterStatus.GOOD);
    });

    it('should return WARNING for high token counts', () => {
      const status = TokenCounterUtils.calculateStatus(850, 1000);
      expect(status).toBe(TokenCounterStatus.WARNING);
    });

    it('should return OVER_LIMIT for exceeded token counts', () => {
      const status = TokenCounterUtils.calculateStatus(1200, 1000);
      expect(status).toBe(TokenCounterStatus.OVER_LIMIT);
    });

    it('should use custom warning threshold', () => {
      const status = TokenCounterUtils.calculateStatus(700, 1000, 600);
      expect(status).toBe(TokenCounterStatus.WARNING);
    });

    it('should return ERROR for invalid inputs', () => {
      expect(TokenCounterUtils.calculateStatus(-1, 1000)).toBe(TokenCounterStatus.ERROR);
      expect(TokenCounterUtils.calculateStatus(500, 0)).toBe(TokenCounterStatus.ERROR);
      expect(TokenCounterUtils.calculateStatus(500, -1)).toBe(TokenCounterStatus.ERROR);
    });
  });

  describe('calculatePercentage', () => {
    it('should calculate percentage correctly', () => {
      expect(TokenCounterUtils.calculatePercentage(500, 1000)).toBe(50);
      expect(TokenCounterUtils.calculatePercentage(750, 1000)).toBe(75);
      expect(TokenCounterUtils.calculatePercentage(1200, 1000)).toBe(100); // Capped at 100
    });

    it('should handle edge cases', () => {
      expect(TokenCounterUtils.calculatePercentage(0, 1000)).toBe(0);
      expect(TokenCounterUtils.calculatePercentage(500, 0)).toBe(0);
    });
  });

  describe('formatTokenCount', () => {
    it('should format small numbers as-is', () => {
      expect(TokenCounterUtils.formatTokenCount(500)).toBe('500');
      expect(TokenCounterUtils.formatTokenCount(999)).toBe('999');
    });

    it('should format thousands with K suffix', () => {
      expect(TokenCounterUtils.formatTokenCount(1000)).toBe('1.0K');
      expect(TokenCounterUtils.formatTokenCount(1500)).toBe('1.5K');
      expect(TokenCounterUtils.formatTokenCount(12500)).toBe('12.5K');
    });

    it('should format millions with M suffix', () => {
      expect(TokenCounterUtils.formatTokenCount(1000000)).toBe('1.0M');
      expect(TokenCounterUtils.formatTokenCount(2500000)).toBe('2.5M');
    });
  });

  describe('getStatusText', () => {
    it('should return correct status text', () => {
      expect(TokenCounterUtils.getStatusText(TokenCounterStatus.GOOD)).toBe('Good');
      expect(TokenCounterUtils.getStatusText(TokenCounterStatus.WARNING)).toBe('High');
      expect(TokenCounterUtils.getStatusText(TokenCounterStatus.OVER_LIMIT)).toBe('Over!');
      expect(TokenCounterUtils.getStatusText(TokenCounterStatus.LOADING)).toBe('Loading...');
      expect(TokenCounterUtils.getStatusText(TokenCounterStatus.ERROR)).toBe('Error');
    });
  });

  describe('getStatusIcon', () => {
    it('should return correct status icons', () => {
      expect(TokenCounterUtils.getStatusIcon(TokenCounterStatus.GOOD)).toBe('🟢');
      expect(TokenCounterUtils.getStatusIcon(TokenCounterStatus.WARNING)).toBe('🟡');
      expect(TokenCounterUtils.getStatusIcon(TokenCounterStatus.OVER_LIMIT)).toBe('🔴');
      expect(TokenCounterUtils.getStatusIcon(TokenCounterStatus.LOADING)).toBe('⏳');
      expect(TokenCounterUtils.getStatusIcon(TokenCounterStatus.ERROR)).toBe('❌');
    });
  });
});
