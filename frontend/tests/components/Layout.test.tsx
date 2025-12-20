import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Layout from '@/components/Layout';

// Mock child components to isolate Layout testing
jest.mock('@/components/Navigation', () => {
  const React = require('react');
  return {
    __esModule: true,
    default: function Navigation() {
      return React.createElement('div', { 'data-testid': 'navigation' }, 'Navigation Component');
    },
  };
});

jest.mock('@/components/StatusBar', () => {
  const React = require('react');
  return {
    __esModule: true,
    default: function StatusBar() {
      return React.createElement('div', { 'data-testid': 'status-bar' }, 'StatusBar Component');
    },
  };
});

jest.mock('@/components/ConfigurationBanner', () => {
  const React = require('react');
  return {
    __esModule: true,
    default: function ConfigurationBanner() {
      return React.createElement('div', { 'data-testid': 'config-banner' }, 'ConfigurationBanner Component');
    },
  };
});

describe('Layout', () => {
  describe('Rendering', () => {
    test('renders all layout components', () => {
      render(
        <BrowserRouter>
          <Layout>
            <div>Test Content</div>
          </Layout>
        </BrowserRouter>
      );

      // Check that all layout components are rendered
      expect(screen.getByTestId('navigation')).toBeInTheDocument();
      expect(screen.getByTestId('config-banner')).toBeInTheDocument();
      expect(screen.getByTestId('status-bar')).toBeInTheDocument();
    });

    test('renders children content', () => {
      render(
        <BrowserRouter>
          <Layout>
            <div>Child Content</div>
          </Layout>
        </BrowserRouter>
      );

      expect(screen.getByText('Child Content')).toBeInTheDocument();
    });

    test('renders multiple children', () => {
      render(
        <BrowserRouter>
          <Layout>
            <div>First Child</div>
            <div>Second Child</div>
            <div>Third Child</div>
          </Layout>
        </BrowserRouter>
      );

      expect(screen.getByText('First Child')).toBeInTheDocument();
      expect(screen.getByText('Second Child')).toBeInTheDocument();
      expect(screen.getByText('Third Child')).toBeInTheDocument();
    });

    test('renders with complex children components', () => {
      const ComplexChild = () => (
        <div>
          <h1>Complex Component</h1>
          <p>With nested elements</p>
          <button>Click me</button>
        </div>
      );

      render(
        <BrowserRouter>
          <Layout>
            <ComplexChild />
          </Layout>
        </BrowserRouter>
      );

      expect(screen.getByText('Complex Component')).toBeInTheDocument();
      expect(screen.getByText('With nested elements')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /click me/i })).toBeInTheDocument();
    });
  });

  describe('Layout Structure', () => {
    test('has correct CSS classes for layout structure', () => {
      const { container } = render(
        <BrowserRouter>
          <Layout>
            <div>Content</div>
          </Layout>
        </BrowserRouter>
      );

      // Check for flex container
      const layoutContainer = container.firstChild as HTMLElement;
      expect(layoutContainer).toHaveClass('flex', 'flex-col', 'h-screen');
      expect(layoutContainer).toHaveClass('bg-background', 'text-foreground');
    });

    test('main content area has correct CSS classes', () => {
      const { container } = render(
        <BrowserRouter>
          <Layout>
            <div data-testid="test-content">Content</div>
          </Layout>
        </BrowserRouter>
      );

      const mainElement = container.querySelector('main');
      expect(mainElement).toBeInTheDocument();
      expect(mainElement).toHaveClass('flex-1', 'overflow-auto');
      expect(mainElement).toHaveClass('bg-gradient-to-br', 'from-background', 'to-background/95');
    });

    test('maintains correct component order', () => {
      const { container } = render(
        <BrowserRouter>
          <Layout>
            <div>Content</div>
          </Layout>
        </BrowserRouter>
      );

      const layoutContainer = container.firstChild as HTMLElement;
      const children = Array.from(layoutContainer.children);

      // Navigation should be first
      expect(children[0]).toHaveAttribute('data-testid', 'navigation');

      // ConfigurationBanner should be second
      expect(children[1]).toHaveAttribute('data-testid', 'config-banner');

      // Main content should be third
      expect(children[2].tagName.toLowerCase()).toBe('main');

      // StatusBar should be last
      expect(children[3]).toHaveAttribute('data-testid', 'status-bar');
    });
  });

  describe('Content Overflow', () => {
    test('main content area allows scrolling', () => {
      const { container } = render(
        <BrowserRouter>
          <Layout>
            <div style={{ height: '2000px' }}>Very tall content</div>
          </Layout>
        </BrowserRouter>
      );

      const mainElement = container.querySelector('main');
      expect(mainElement).toHaveClass('overflow-auto');
    });

    test('layout container takes full screen height', () => {
      const { container } = render(
        <BrowserRouter>
          <Layout>
            <div>Content</div>
          </Layout>
        </BrowserRouter>
      );

      const layoutContainer = container.firstChild as HTMLElement;
      expect(layoutContainer).toHaveClass('h-screen');
    });
  });

  describe('Edge Cases', () => {
    test('renders without children', () => {
      const { container } = render(
        <BrowserRouter>
          <Layout>{null}</Layout>
        </BrowserRouter>
      );

      const mainElement = container.querySelector('main');
      expect(mainElement).toBeInTheDocument();
      expect(mainElement).toBeEmptyDOMElement();
    });

    test('renders with empty fragment as children', () => {
      render(
        <BrowserRouter>
          <Layout>
            <></>
          </Layout>
        </BrowserRouter>
      );

      // Layout components should still be present
      expect(screen.getByTestId('navigation')).toBeInTheDocument();
      expect(screen.getByTestId('config-banner')).toBeInTheDocument();
      expect(screen.getByTestId('status-bar')).toBeInTheDocument();
    });

    test('renders with conditional children', () => {
      const ConditionalContent = ({ show }: { show: boolean }) => (
        <>{show && <div>Conditional Content</div>}</>
      );

      const { rerender } = render(
        <BrowserRouter>
          <Layout>
            <ConditionalContent show={false} />
          </Layout>
        </BrowserRouter>
      );

      expect(screen.queryByText('Conditional Content')).not.toBeInTheDocument();

      rerender(
        <BrowserRouter>
          <Layout>
            <ConditionalContent show={true} />
          </Layout>
        </BrowserRouter>
      );

      expect(screen.getByText('Conditional Content')).toBeInTheDocument();
    });
  });

  describe('Integration', () => {
    test('layout persists when children change', () => {
      const { rerender } = render(
        <BrowserRouter>
          <Layout>
            <div>Initial Content</div>
          </Layout>
        </BrowserRouter>
      );

      expect(screen.getByText('Initial Content')).toBeInTheDocument();
      expect(screen.getByTestId('navigation')).toBeInTheDocument();

      rerender(
        <BrowserRouter>
          <Layout>
            <div>Updated Content</div>
          </Layout>
        </BrowserRouter>
      );

      expect(screen.getByText('Updated Content')).toBeInTheDocument();
      expect(screen.getByTestId('navigation')).toBeInTheDocument();
      expect(screen.getByTestId('config-banner')).toBeInTheDocument();
      expect(screen.getByTestId('status-bar')).toBeInTheDocument();
    });

    test('handles dynamic content updates', () => {
      const DynamicContent = ({ count }: { count: number }) => (
        <div>
          <h1>Count: {count}</h1>
          {Array.from({ length: count }, (_, i) => (
            <p key={i}>Item {i + 1}</p>
          ))}
        </div>
      );

      const { rerender } = render(
        <BrowserRouter>
          <Layout>
            <DynamicContent count={1} />
          </Layout>
        </BrowserRouter>
      );

      expect(screen.getByText('Count: 1')).toBeInTheDocument();
      expect(screen.getByText('Item 1')).toBeInTheDocument();

      rerender(
        <BrowserRouter>
          <Layout>
            <DynamicContent count={3} />
          </Layout>
        </BrowserRouter>
      );

      expect(screen.getByText('Count: 3')).toBeInTheDocument();
      expect(screen.getByText('Item 1')).toBeInTheDocument();
      expect(screen.getByText('Item 2')).toBeInTheDocument();
      expect(screen.getByText('Item 3')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    test('main element has proper semantic role', () => {
      const { container } = render(
        <BrowserRouter>
          <Layout>
            <div>Content</div>
          </Layout>
        </BrowserRouter>
      );

      const mainElement = container.querySelector('main');
      expect(mainElement).toBeInTheDocument();
      expect(mainElement?.tagName.toLowerCase()).toBe('main');
    });

    test('layout structure supports keyboard navigation', () => {
      render(
        <BrowserRouter>
          <Layout>
            <div>
              <button>Button 1</button>
              <button>Button 2</button>
              <a href="#">Link</a>
            </div>
          </Layout>
        </BrowserRouter>
      );

      // Content should be accessible
      expect(screen.getByRole('button', { name: /button 1/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /button 2/i })).toBeInTheDocument();
      expect(screen.getByRole('link')).toBeInTheDocument();
    });
  });
});