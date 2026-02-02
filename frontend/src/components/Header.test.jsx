import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import Header from './header';

describe('Header Component', () => {
  it('renders the header text', () => {
    render(<Header />);

    const headerElement = screen.getByRole('heading', { level: 1 });
    expect(headerElement).toBeInTheDocument();
    expect(headerElement).toHaveTextContent("Prova dell'header");
  });

  it('renders as a header element', () => {
    const { container } = render(<Header />);

    const header = container.querySelector('header');
    expect(header).toBeInTheDocument();
  });
});
