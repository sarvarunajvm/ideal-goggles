import { render, screen } from '@testing-library/react'
import { RouteErrorBoundary } from '../../src/components/RouteErrorBoundary'

jest.mock('react-router-dom', () => {
  const actual = jest.requireActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => jest.fn(),
    useRouteError: jest.fn(),
    isRouteErrorResponse: jest.fn(),
  }
})

describe('RouteErrorBoundary', () => {
  test('shows 404 message for route error response', async () => {
    const { useRouteError, isRouteErrorResponse } = require('react-router-dom')
    isRouteErrorResponse.mockReturnValue(true)
    useRouteError.mockReturnValue({ status: 404, statusText: 'Not Found' })
    render(<RouteErrorBoundary />)
    expect(await screen.findByText(/Error 404/)).toBeInTheDocument()
    expect(
      await screen.findByText(/does not exist/)
    ).toBeInTheDocument()
  })

  test('shows generic error for thrown Error', async () => {
    const { useRouteError, isRouteErrorResponse } = require('react-router-dom')
    isRouteErrorResponse.mockReturnValue(false)
    useRouteError.mockReturnValue(new Error('Boom'))
    render(<RouteErrorBoundary />)
    expect(await screen.findByText(/Error/i)).toBeInTheDocument()
    expect(await screen.findByText('Boom')).toBeInTheDocument()
  })
})
