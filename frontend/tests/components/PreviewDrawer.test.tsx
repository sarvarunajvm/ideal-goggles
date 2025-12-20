import { render, screen, fireEvent } from '@testing-library/react'
import PreviewDrawer from '../../src/components/PreviewDrawer'

jest.mock('../../src/services/apiClient', () => ({
  getThumbnailBaseUrl: jest.fn(() => '/thumbnails'),
}))

const item = {
  file_id: 1,
  path: '/photos/1.jpg',
  folder: '/photos',
  filename: '1.jpg',
  thumb_path: 't/1.jpg',
  shot_dt: '2024-01-01T00:00:00Z',
  score: 0.9,
  badges: ['OCR', 'EXIF'],
  snippet: 'hello world',
}

describe('PreviewDrawer', () => {
  test('renders when open and displays file info and badges', () => {
    render(
      <PreviewDrawer item={item as any} isOpen onClose={() => {}} />
    )
    expect(screen.getByText('1.jpg')).toBeInTheDocument()
    expect(screen.getByText('/photos/1.jpg')).toBeInTheDocument()
    expect(screen.getByText('OCR')).toBeInTheDocument()
    expect(screen.getByText('EXIF')).toBeInTheDocument()
    expect(screen.getByText(/Text Match/)).toBeInTheDocument()
  })

  test('keyboard shortcuts trigger handlers', async () => {
    const onClose = jest.fn()
    const onNext = jest.fn()
    const onPrevious = jest.fn()
    render(
      <PreviewDrawer
        item={item as any}
        isOpen
        onClose={onClose}
        onNext={onNext}
        onPrevious={onPrevious}
      />
    )
    fireEvent.keyDown(document, { key: 'ArrowRight' })
    fireEvent.keyDown(document, { key: 'ArrowLeft' })
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(onNext).toHaveBeenCalled()
    expect(onPrevious).toHaveBeenCalled()
    expect(onClose).toHaveBeenCalled()
  })
})

