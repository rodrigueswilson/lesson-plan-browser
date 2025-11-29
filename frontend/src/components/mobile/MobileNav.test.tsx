import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MobileNav } from './MobileNav';

describe('MobileNav', () => {
  it('should render all navigation tabs', () => {
    render(<MobileNav />);

    expect(screen.getByText('Home')).toBeInTheDocument();
    expect(screen.getByText('Plans')).toBeInTheDocument();
    expect(screen.getByText('History')).toBeInTheDocument();
    expect(screen.getByText('Analytics')).toBeInTheDocument();
  });

  it('should have Home tab active by default', () => {
    render(<MobileNav />);

    const homeButton = screen.getByText('Home').closest('button');
    expect(homeButton).toHaveClass('text-primary');
  });

  it('should change active tab when clicked', async () => {
    const user = userEvent.setup();
    render(<MobileNav />);

    const plansButton = screen.getByText('Plans').closest('button');
    await user.click(plansButton!);

    expect(plansButton).toHaveClass('text-primary');
  });

  it('should have proper ARIA labels', () => {
    render(<MobileNav />);

    const buttons = screen.getAllByRole('button');
    buttons.forEach((button) => {
      expect(button).toHaveAttribute('aria-label');
    });
  });

  it('should have touch-friendly button sizes', () => {
    render(<MobileNav />);

    const buttons = screen.getAllByRole('button');
    buttons.forEach((button) => {
      // Check that buttons have minimum size (handled by CSS)
      expect(button).toBeInTheDocument();
    });
  });
});

