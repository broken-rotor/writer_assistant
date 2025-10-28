import type { Meta, StoryObj } from '@storybook/angular';
import { TokenCounterComponent } from './token-counter.component';
import {
  TokenCounterData,
  TokenCounterDisplayMode
} from '../../models/token-counter.model';

const meta: Meta<TokenCounterComponent> = {
  title: 'Components/TokenCounter',
  component: TokenCounterComponent,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: `
# TokenCounter Component

A reusable Angular component for displaying token counts with visual indicators, progress bars, and status colors. 
Supports multiple display modes and accessibility features.

## Features

- **Multiple Display Modes**: Detailed, Compact, and Mobile-responsive layouts
- **Visual Status Indicators**: Color-coded progress bars and status icons
- **Accessibility**: Full ARIA support and keyboard navigation
- **Loading & Error States**: Graceful handling of different states
- **Customizable**: Configurable display options and styling

## Usage

\`\`\`typescript
// Basic usage
<app-token-counter
  [data]="{ current: 1247, limit: 2000 }"
  [config]="{ displayMode: 'detailed', showProgressBar: true }"
  (interaction)="onTokenCounterInteraction($event)">
</app-token-counter>
\`\`\`
        `
      }
    }
  },
  argTypes: {
    data: {
      description: 'Token count data including current count and limit',
      control: { type: 'object' }
    },
    config: {
      description: 'Configuration options for display and behavior',
      control: { type: 'object' }
    },
    loading: {
      description: 'Whether the component is in loading state',
      control: { type: 'boolean' }
    },
    error: {
      description: 'Error message to display',
      control: { type: 'text' }
    },
    interaction: {
      description: 'Event emitted on user interactions',
      action: 'interaction'
    },
    statusChange: {
      description: 'Event emitted when status changes',
      action: 'statusChange'
    }
  },
  tags: ['autodocs']
};

export default meta;
type Story = StoryObj<TokenCounterComponent>;

// Sample data for stories
const goodTokenData: TokenCounterData = {
  current: 500,
  limit: 1000,
  text: 'Sample text content for token counting'
};

const warningTokenData: TokenCounterData = {
  current: 850,
  limit: 1000,
  text: 'This is a longer text that approaches the token limit and should show warning status'
};

const overLimitTokenData: TokenCounterData = {
  current: 1200,
  limit: 1000,
  text: 'This is an even longer text that exceeds the token limit and should show over limit status with appropriate warnings'
};

const largeNumberTokenData: TokenCounterData = {
  current: 12500,
  limit: 15000,
  text: 'Sample text with large token counts to test formatting'
};

// Default story - Detailed mode with good status
export const Default: Story = {
  args: {
    data: goodTokenData,
    config: {
      displayMode: TokenCounterDisplayMode.DETAILED,
      showProgressBar: true,
      showCount: true,
      showStatus: true
    }
  }
};

// Display Mode Stories
export const DetailedMode: Story = {
  args: {
    data: goodTokenData,
    config: {
      displayMode: TokenCounterDisplayMode.DETAILED,
      showProgressBar: true,
      showCount: true,
      showStatus: true,
      showPercentage: true
    }
  },
  parameters: {
    docs: {
      description: {
        story: 'Detailed display mode with full information including progress bar, count, status, and percentage.'
      }
    }
  }
};

export const CompactMode: Story = {
  args: {
    data: goodTokenData,
    config: {
      displayMode: TokenCounterDisplayMode.COMPACT,
      showCount: true,
      showStatus: true
    }
  },
  parameters: {
    docs: {
      description: {
        story: 'Compact inline display mode suitable for integration within forms or tight spaces.'
      }
    }
  }
};

export const MobileMode: Story = {
  args: {
    data: goodTokenData,
    config: {
      displayMode: TokenCounterDisplayMode.MOBILE,
      showProgressBar: true,
      showCount: true,
      showStatus: true,
      showPercentage: true
    }
  },
  parameters: {
    docs: {
      description: {
        story: 'Mobile-optimized display mode with responsive layout and touch-friendly design.'
      }
    }
  }
};

// Status Stories
export const GoodStatus: Story = {
  args: {
    data: goodTokenData,
    config: {
      displayMode: TokenCounterDisplayMode.DETAILED,
      showProgressBar: true,
      showCount: true,
      showStatus: true
    }
  },
  parameters: {
    docs: {
      description: {
        story: 'Token count within safe limits (green status).'
      }
    }
  }
};

export const WarningStatus: Story = {
  args: {
    data: warningTokenData,
    config: {
      displayMode: TokenCounterDisplayMode.DETAILED,
      showProgressBar: true,
      showCount: true,
      showStatus: true
    }
  },
  parameters: {
    docs: {
      description: {
        story: 'Token count approaching limits (yellow/orange status).'
      }
    }
  }
};

export const OverLimitStatus: Story = {
  args: {
    data: overLimitTokenData,
    config: {
      displayMode: TokenCounterDisplayMode.DETAILED,
      showProgressBar: true,
      showCount: true,
      showStatus: true
    }
  },
  parameters: {
    docs: {
      description: {
        story: 'Token count exceeding limits (red status) with warning message.'
      }
    }
  }
};

// State Stories
export const LoadingState: Story = {
  args: {
    data: null,
    loading: true,
    config: {
      displayMode: TokenCounterDisplayMode.DETAILED
    }
  },
  parameters: {
    docs: {
      description: {
        story: 'Loading state with spinner animation while token counting is in progress.'
      }
    }
  }
};

export const ErrorState: Story = {
  args: {
    data: null,
    error: 'Failed to count tokens. Please try again.',
    config: {
      displayMode: TokenCounterDisplayMode.DETAILED
    }
  },
  parameters: {
    docs: {
      description: {
        story: 'Error state when token counting fails with appropriate error message.'
      }
    }
  }
};

// Configuration Stories
export const WithoutProgressBar: Story = {
  args: {
    data: goodTokenData,
    config: {
      displayMode: TokenCounterDisplayMode.DETAILED,
      showProgressBar: false,
      showCount: true,
      showStatus: true
    }
  },
  parameters: {
    docs: {
      description: {
        story: 'Component without progress bar, showing only count and status information.'
      }
    }
  }
};

export const WithPercentage: Story = {
  args: {
    data: goodTokenData,
    config: {
      displayMode: TokenCounterDisplayMode.DETAILED,
      showProgressBar: true,
      showCount: true,
      showStatus: true,
      showPercentage: true
    }
  },
  parameters: {
    docs: {
      description: {
        story: 'Component showing percentage alongside other information.'
      }
    }
  }
};

export const CustomClasses: Story = {
  args: {
    data: goodTokenData,
    config: {
      displayMode: TokenCounterDisplayMode.DETAILED,
      showProgressBar: true,
      showCount: true,
      showStatus: true,
      customClasses: ['custom-border', 'custom-shadow']
    }
  },
  parameters: {
    docs: {
      description: {
        story: 'Component with custom CSS classes applied for additional styling.'
      }
    }
  }
};

export const DisabledState: Story = {
  args: {
    data: goodTokenData,
    config: {
      displayMode: TokenCounterDisplayMode.DETAILED,
      showProgressBar: true,
      showCount: true,
      showStatus: true,
      disabled: true
    }
  },
  parameters: {
    docs: {
      description: {
        story: 'Disabled component state with reduced opacity and no interactions.'
      }
    }
  }
};

// Large Numbers Story
export const LargeNumbers: Story = {
  args: {
    data: largeNumberTokenData,
    config: {
      displayMode: TokenCounterDisplayMode.DETAILED,
      showProgressBar: true,
      showCount: true,
      showStatus: true,
      showPercentage: true
    }
  },
  parameters: {
    docs: {
      description: {
        story: 'Component handling large token counts with proper formatting (K, M suffixes).'
      }
    }
  }
};

// Custom Warning Threshold Story
export const CustomWarningThreshold: Story = {
  args: {
    data: {
      current: 600,
      limit: 1000,
      warningThreshold: 500,
      text: 'Text with custom warning threshold'
    },
    config: {
      displayMode: TokenCounterDisplayMode.DETAILED,
      showProgressBar: true,
      showCount: true,
      showStatus: true
    }
  },
  parameters: {
    docs: {
      description: {
        story: 'Component with custom warning threshold (50% instead of default 80%).'
      }
    }
  }
};

// All Display Modes Comparison
export const AllDisplayModes: Story = {
  render: (args) => ({
    props: args,
    template: `
      <div style="display: flex; flex-direction: column; gap: 20px; padding: 20px;">
        <div>
          <h3>Detailed Mode</h3>
          <app-token-counter 
            [data]="data" 
            [config]="{ displayMode: 'detailed', showProgressBar: true, showCount: true, showStatus: true }">
          </app-token-counter>
        </div>
        
        <div>
          <h3>Compact Mode</h3>
          <app-token-counter 
            [data]="data" 
            [config]="{ displayMode: 'compact', showCount: true, showStatus: true }">
          </app-token-counter>
        </div>
        
        <div>
          <h3>Mobile Mode</h3>
          <app-token-counter 
            [data]="data" 
            [config]="{ displayMode: 'mobile', showProgressBar: true, showCount: true, showStatus: true }">
          </app-token-counter>
        </div>
      </div>
    `
  }),
  args: {
    data: warningTokenData
  },
  parameters: {
    docs: {
      description: {
        story: 'Comparison of all three display modes side by side.'
      }
    }
  }
};

// All Status States Comparison
export const AllStatusStates: Story = {
  render: (args) => ({
    props: args,
    template: `
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; padding: 20px;">
        <div>
          <h3>Good Status (Green)</h3>
          <app-token-counter 
            [data]="goodData" 
            [config]="config">
          </app-token-counter>
        </div>
        
        <div>
          <h3>Warning Status (Yellow)</h3>
          <app-token-counter 
            [data]="warningData" 
            [config]="config">
          </app-token-counter>
        </div>
        
        <div>
          <h3>Over Limit Status (Red)</h3>
          <app-token-counter 
            [data]="overLimitData" 
            [config]="config">
          </app-token-counter>
        </div>
        
        <div>
          <h3>Loading State</h3>
          <app-token-counter 
            [loading]="true"
            [config]="config">
          </app-token-counter>
        </div>
        
        <div>
          <h3>Error State</h3>
          <app-token-counter 
            [error]="'Failed to count tokens'"
            [config]="config">
          </app-token-counter>
        </div>
      </div>
    `
  }),
  args: {
    goodData: goodTokenData,
    warningData: warningTokenData,
    overLimitData: overLimitTokenData,
    config: {
      displayMode: TokenCounterDisplayMode.DETAILED,
      showProgressBar: true,
      showCount: true,
      showStatus: true
    }
  },
  parameters: {
    docs: {
      description: {
        story: 'Comparison of all status states including loading and error states.'
      }
    }
  }
};
