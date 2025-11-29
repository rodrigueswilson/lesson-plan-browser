import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { DesktopLayout } from './DesktopLayout';

describe('DesktopLayout', () => {
  it('should render children', () => {
    render(
      <DesktopLayout>
        <div>Test Content</div>
      </DesktopLayout>
    );

    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });

  it('should render header with app title', () => {
    render(<DesktopLayout><div>Content</div></DesktopLayout>);

    expect(screen.getByText('Bilingual Lesson Planner')).toBeInTheDocument();
    expect(screen.getByText('Weekly lesson plan generator with WIDA support')).toBeInTheDocument();
  });

  it('should render footer', () => {
    render(<DesktopLayout><div>Content</div></DesktopLayout>);

    expect(screen.getByText(/Bilingual Lesson Planner v1.0.0/)).toBeInTheDocument();
  });

  it('should have proper structure', () => {
    const { container } = render(<DesktopLayout><div>Content</div></DesktopLayout>);

    const header = container.querySelector('header');
    const main = container.querySelector('main');
    const footer = container.querySelector('footer');

    expect(header).toBeInTheDocument();
    expect(main).toBeInTheDocument();
    expect(footer).toBeInTheDocument();
  });
});

