import { render, screen } from '@testing-library/react'
import { LogsPage } from '../../src/pages/LogsPage'

// Mock the LogViewer component to isolate LogsPage testing
jest.mock('../../src/components/LogViewer', () => ({
  LogViewer: function MockLogViewer() {
    return <div data-testid="log-viewer">LogViewer Component</div>
  },
}))

describe('LogsPage', () => {
  it('renders the LogViewer component', () => {
    render(<LogsPage />)
    
    expect(screen.getByTestId('log-viewer')).toBeInTheDocument()
    expect(screen.getByText('LogViewer Component')).toBeInTheDocument()
  })

  it('has correct layout structure', () => {
    const { container } = render(<LogsPage />)
    
    const layoutContainer = container.firstChild as HTMLElement
    expect(layoutContainer).toHaveClass('flex-1', 'overflow-auto', 'bg-background')
  })

  it('LogViewer is contained within the page', () => {
    const { container } = render(<LogsPage />)
    
    const logViewer = screen.getByTestId('log-viewer')
    expect(container.firstChild).toContainElement(logViewer)
  })
})
