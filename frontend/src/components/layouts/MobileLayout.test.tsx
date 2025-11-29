import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MobileLayout } from './MobileLayout';

// Mock MobileNav component
vi.mock('../mobile/MobileNav', () => ({
  MobileNav: () => <nav data-testid="mobile-nav">Mobile Navigation</nav>,
}));

describe('MobileLayout', () => {
  it('should render children', () => {
    render(
      <MobileLayout>
        <div>Test Content</div>
      </MobileLayout>
    );

    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });

  it('should render mobile header', () => {
    render(<MobileLayout><div>Content</div></MobileLayout>);

    expect(screen.getByText('Lesson Planner')).toBeInTheDocument();
    expect(screen.getByText('Bilingual weekly plans')).toBeInTheDocument();
  });

  it('should render mobile navigation', () => {
    render(<MobileLayout><div>Content</div></MobileLayout>);

    expect(screen.getByTestId('mobile-nav')).toBeInTheDocument();
  });

  it('should have proper mobile structure', () => {
    const { container } = render(<MobileLayout><div>Content</div></MobileLayout>);

    const header = container.querySelector('header');
    const main = container.querySelector('main');
    const nav = container.querySelector('nav[data-testid="mobile-nav"]');

    expect(header).toBeInTheDocument();
    expect(main).toBeInTheDocument();
    expect(nav).toBeInTheDocument();
  });

  it('should have flex column layout', () => {
    const { container } = render(<MobileLayout><div>Content</div></MobileLayout>);

    const root = container.firstChild as HTMLElement;
    expect(root).toHaveClass('flex', 'flex-col');
  });
});

