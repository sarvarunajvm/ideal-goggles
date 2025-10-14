import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import PhotoGrid from '../../src/components/PhotoGrid'

const samplePhotos = [
  { id: 1, path: '/p/1.jpg', name: 'one', size: 1024 },
  { id: 2, path: '/p/2.jpg', name: 'two', size: 2048 },
  { id: 3, path: '/p/3.jpg', name: 'three', size: 4096 },
]

describe('PhotoGrid', () => {
  test('shows loading state when loading with no photos', () => {
    render(<PhotoGrid photos={[]} loading />)
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  test('shows empty state when no photos and not loading', () => {
    render(<PhotoGrid photos={[]} />)
    expect(screen.getByText(/No photos found/)).toBeInTheDocument()
  })

  test('renders photos and handles click and double click zoom', async () => {
    const onClick = jest.fn()
    render(<PhotoGrid photos={samplePhotos} onPhotoClick={onClick} />)
    const img = screen.getAllByAltText('one')[0]
    await userEvent.click(img)
    expect(onClick).toHaveBeenCalledWith(expect.objectContaining({ id: 1 }))

    // Double click opens zoom overlay
    await userEvent.dblClick(img)
    expect(screen.getAllByAltText('one')[1]).toBeInTheDocument()
  })

  test('selection mode toggles checkbox and select all', async () => {
    const onSelect = jest.fn()
    render(
      <PhotoGrid
        photos={samplePhotos}
        selectable
        showSelectAll
        onPhotoSelect={onSelect}
      />
    )

    // Select first photo via checkbox
    const firstCheckbox = screen.getByLabelText('Select one')
    await userEvent.click(firstCheckbox)
    expect(onSelect).toHaveBeenCalledWith([expect.objectContaining({ id: 1 })])

    // Select all
    const selectAll = screen.getByLabelText('Select all photos')
    await userEvent.click(selectAll)
    expect(onSelect).toHaveBeenLastCalledWith(expect.arrayContaining(samplePhotos))
  })

  test('keyboard navigation changes focus and Enter toggles selection', () => {
    render(<PhotoGrid photos={samplePhotos} selectable />)
    const grid = screen.getByRole('grid')
    grid.focus()
    fireEvent.keyDown(grid, { key: 'ArrowRight' })
    fireEvent.keyDown(grid, { key: 'Enter' })
    const secondCell = screen.getAllByRole('gridcell')[1]
    expect(secondCell).toHaveAttribute('aria-selected', 'true')
  })
})
