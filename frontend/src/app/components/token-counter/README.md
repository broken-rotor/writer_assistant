# TokenCounter Component

A reusable Angular component for displaying token counts with visual indicators, progress bars, and status colors. This component is designed to help users understand how their text inputs consume token budgets in AI applications.

## Features

- **Multiple Display Modes**: Detailed, Compact, and Mobile-responsive layouts
- **Visual Status Indicators**: Color-coded progress bars and status icons (🟢 Good, 🟡 Warning, 🔴 Over Limit)
- **Accessibility**: Full ARIA support, keyboard navigation, and screen reader compatibility
- **Loading & Error States**: Graceful handling of different states with appropriate UI feedback
- **Customizable**: Configurable display options, styling, and behavior
- **Responsive Design**: Mobile-first approach with responsive breakpoints
- **TypeScript**: Full type safety with comprehensive interfaces

## Installation

The component is part of the Writer Assistant Angular application. It's a standalone component that can be imported directly:

```typescript
import { TokenCounterComponent } from './components/token-counter/token-counter.component';
```

## Basic Usage

### Simple Example

```html
<app-token-counter
  [data]="{ current: 1247, limit: 2000 }"
  [config]="{ displayMode: 'detailed', showProgressBar: true }">
</app-token-counter>
```

### With Event Handling

```typescript
// Component
export class MyComponent {
  tokenData: TokenCounterData = {
    current: 1247,
    limit: 2000,
    text: 'Your text content here'
  };

  tokenConfig: TokenCounterConfig = {
    displayMode: TokenCounterDisplayMode.DETAILED,
    showProgressBar: true,
    showCount: true,
    showStatus: true
  };

  onTokenCounterInteraction(event: TokenCounterEvent) {
    console.log('Token counter interaction:', event);
  }

  onStatusChange(status: TokenCounterStatus) {
    console.log('Status changed to:', status);
  }
}
```

```html
<!-- Template -->
<app-token-counter
  [data]="tokenData"
  [config]="tokenConfig"
  (interaction)="onTokenCounterInteraction($event)"
  (statusChange)="onStatusChange($event)">
</app-token-counter>
```

## Display Modes

### Detailed Mode
The default mode showing full information with progress bars, counts, and status indicators.

```typescript
config: TokenCounterConfig = {
  displayMode: TokenCounterDisplayMode.DETAILED,
  showProgressBar: true,
  showCount: true,
  showStatus: true,
  showPercentage: true
};
```

### Compact Mode
Inline display suitable for forms and tight spaces.

```typescript
config: TokenCounterConfig = {
  displayMode: TokenCounterDisplayMode.COMPACT,
  showCount: true,
  showStatus: true
};
```

### Mobile Mode
Mobile-optimized responsive layout.

```typescript
config: TokenCounterConfig = {
  displayMode: TokenCounterDisplayMode.MOBILE,
  showProgressBar: true,
  showCount: true,
  showStatus: true
};
```

## API Reference

### Inputs

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `data` | `TokenCounterData \| null` | `null` | Token count data including current count and limit |
| `config` | `Partial<TokenCounterConfig>` | `{}` | Configuration options for display and behavior |
| `loading` | `boolean` | `false` | Whether the component is in loading state |
| `error` | `string \| null` | `null` | Error message to display |

### Outputs

| Event | Type | Description |
|-------|------|-------------|
| `interaction` | `EventEmitter<TokenCounterEvent>` | Emitted on user interactions (click, hover, focus) |
| `statusChange` | `EventEmitter<TokenCounterStatus>` | Emitted when the token status changes |

### Interfaces

#### TokenCounterData
```typescript
interface TokenCounterData {
  current: number;                    // Current token count
  limit: number;                      // Maximum allowed tokens
  warningThreshold?: number;          // Custom warning threshold (default: 80% of limit)
  text?: string;                      // Text content being counted
  metadata?: Record<string, any>;     // Additional metadata
}
```

#### TokenCounterConfig
```typescript
interface TokenCounterConfig {
  displayMode: TokenCounterDisplayMode;  // Display mode to use
  showProgressBar?: boolean;             // Whether to show progress bar
  showCount?: boolean;                   // Whether to show token count numbers
  showStatus?: boolean;                  // Whether to show status text
  showPercentage?: boolean;              // Whether to show percentage
  customClasses?: string[];              // Custom CSS classes
  disabled?: boolean;                    // Whether component is disabled
  ariaLabel?: string;                    // Custom ARIA label
}
```

#### TokenCounterEvent
```typescript
interface TokenCounterEvent {
  type: 'click' | 'hover' | 'focus' | 'status_change';
  data: TokenCounterData;
  status: TokenCounterStatus;
  metadata?: Record<string, any>;
}
```

### Enums

#### TokenCounterDisplayMode
```typescript
enum TokenCounterDisplayMode {
  DETAILED = 'detailed',
  COMPACT = 'compact',
  MOBILE = 'mobile'
}
```

#### TokenCounterStatus
```typescript
enum TokenCounterStatus {
  GOOD = 'good',           // Within safe limits (green)
  WARNING = 'warning',     // Approaching limits (yellow)
  OVER_LIMIT = 'over_limit', // Exceeds limits (red)
  LOADING = 'loading',     // Loading state
  ERROR = 'error'          // Error state
}
```

## Status Colors and Thresholds

The component uses a color-coded system to indicate token usage status:

- **🟢 Good (Green)**: Token count is within safe limits (< 80% of limit by default)
- **🟡 Warning (Yellow)**: Token count is approaching limits (≥ 80% of limit)
- **🔴 Over Limit (Red)**: Token count exceeds the limit

### Custom Warning Threshold

You can customize the warning threshold:

```typescript
const data: TokenCounterData = {
  current: 600,
  limit: 1000,
  warningThreshold: 500  // Warning at 50% instead of default 80%
};
```

## Accessibility Features

The component includes comprehensive accessibility support:

- **ARIA Labels**: Descriptive labels for screen readers
- **Progress Bars**: Proper `role="progressbar"` with value attributes
- **Keyboard Navigation**: Focusable with keyboard support
- **Screen Reader Announcements**: Live regions for status changes
- **High Contrast Support**: Enhanced visibility in high contrast mode
- **Reduced Motion**: Respects user's motion preferences

### ARIA Label Example

```typescript
config: TokenCounterConfig = {
  ariaLabel: 'System prompt token counter: 1247 of 2000 tokens used'
};
```

## Styling and Customization

### CSS Classes

The component generates CSS classes based on its state:

- `.token-counter` - Base component class
- `.token-counter--detailed` - Detailed display mode
- `.token-counter--compact` - Compact display mode
- `.token-counter--mobile` - Mobile display mode
- `.token-counter--good` - Good status (green)
- `.token-counter--warning` - Warning status (yellow)
- `.token-counter--over_limit` - Over limit status (red)
- `.token-counter--loading` - Loading state
- `.token-counter--error` - Error state
- `.token-counter--disabled` - Disabled state

### Custom Classes

Add custom CSS classes for additional styling:

```typescript
config: TokenCounterConfig = {
  customClasses: ['my-custom-class', 'another-class']
};
```

### SCSS Variables

The component uses SCSS variables for consistent theming:

```scss
$color-good: #4caf50;
$color-warning: #ff9800;
$color-over-limit: #f44336;
$color-loading: #2196f3;
$color-error: #9e9e9e;
```

## Integration Examples

### With Reactive Forms

```typescript
export class FormComponent {
  form = this.fb.group({
    systemPrompt: ['', Validators.required]
  });

  tokenData: TokenCounterData = {
    current: 0,
    limit: 2000
  };

  constructor(private fb: FormBuilder) {
    // Update token count when form value changes
    this.form.get('systemPrompt')?.valueChanges.subscribe(value => {
      this.updateTokenCount(value);
    });
  }

  private updateTokenCount(text: string) {
    // Integrate with TokenCountingService
    this.tokenCountingService.countTokens(text).subscribe(result => {
      this.tokenData = {
        current: result.token_count,
        limit: 2000,
        text: text
      };
    });
  }
}
```

### With TokenCountingService

```typescript
export class MyComponent implements OnInit {
  tokenData: TokenCounterData | null = null;
  loading = false;
  error: string | null = null;

  constructor(private tokenCountingService: TokenCountingService) {}

  ngOnInit() {
    this.countTokens('Your text here');
  }

  private countTokens(text: string) {
    this.loading = true;
    this.error = null;

    this.tokenCountingService.countTokens([{ text }])
      .subscribe({
        next: (response) => {
          this.tokenData = {
            current: response.results[0].token_count,
            limit: 2000,
            text: text
          };
          this.loading = false;
        },
        error: (error) => {
          this.error = 'Failed to count tokens';
          this.loading = false;
        }
      });
  }
}
```

## Testing

The component includes comprehensive unit tests covering:

- Component initialization and configuration
- State management (loading, error, success states)
- Display mode logic
- Event handling
- CSS class generation
- Accessibility features
- Template rendering
- Change detection
- Utility functions

### Running Tests

```bash
# Run unit tests
ng test

# Run tests with coverage
ng test --code-coverage

# Run specific component tests
ng test --include="**/token-counter.component.spec.ts"
```

## Storybook

The component includes Storybook stories for visual testing and documentation:

```bash
# Start Storybook
npm run storybook

# Build Storybook
npm run build-storybook
```

Stories include:
- All display modes
- All status states
- Loading and error states
- Configuration options
- Comparison views

## Performance Considerations

- Uses `OnPush` change detection strategy for optimal performance
- Minimal DOM updates through efficient state management
- CSS animations respect `prefers-reduced-motion`
- Lazy loading of heavy computations

## Browser Support

- Modern browsers (Chrome, Firefox, Safari, Edge)
- Mobile browsers (iOS Safari, Chrome Mobile)
- Accessibility tools and screen readers
- High contrast mode support

## Contributing

When contributing to this component:

1. Follow the existing code style and patterns
2. Add unit tests for new functionality
3. Update Storybook stories for visual changes
4. Ensure accessibility compliance
5. Test across different display modes
6. Update documentation as needed

## Changelog

### Version 1.0.0
- Initial implementation
- Three display modes (detailed, compact, mobile)
- Full accessibility support
- Comprehensive testing
- Storybook integration
- TypeScript interfaces and utilities
