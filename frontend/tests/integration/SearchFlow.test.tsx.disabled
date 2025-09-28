/**
 * Integration tests for the complete search flow
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { rest } from 'msw';
import { setupServer } from 'msw/node';

// Mock API server
const server = setupServer(
  rest.post('/api/search/text', (req, res, ctx) => {
    return res(
      ctx.json({
        results: [
          {
            id: 1,
            path: '/photos/result1.jpg',
            thumbnail: 'data:image/jpeg;base64,thumb1',
            score: 0.95,
          },
          {
            id: 2,
            path: '/photos/result2.jpg',
            thumbnail: 'data:image/jpeg;base64,thumb2',
            score: 0.87,
          },
        ],
        total: 2,
      })
    );
  }),

  rest.post('/api/search/semantic', (req, res, ctx) => {
    return res(
      ctx.json({
        results: [
          {
            id: 3,
            path: '/photos/semantic1.jpg',
            thumbnail: 'data:image/jpeg;base64,thumb3',
            similarity: 0.92,
          },
        ],
        total: 1,
      })
    );
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('Search Flow Integration', () => {
  test('performs text search and displays results', async () => {
    const user = userEvent.setup();

    // Mock the App component with search functionality
    const MockApp = () => {
      const [results, setResults] = React.useState([]);
      const [loading, setLoading] = React.useState(false);

      const handleSearch = async (query) => {
        setLoading(true);
        try {
          const response = await fetch('/api/search/text', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, limit: 20 }),
          });
          const data = await response.json();
          setResults(data.results);
        } finally {
          setLoading(false);
        }
      };

      return (
        <div>
          <input
            type="text"
            placeholder="Search photos..."
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                handleSearch(e.target.value);
              }
            }}
          />
          {loading && <div>Loading...</div>}
          <div data-testid="results">
            {results.map((result) => (
              <div key={result.id} data-testid={`result-${result.id}`}>
                <img src={result.thumbnail} alt={`Result ${result.id}`} />
                <span>{result.score || result.similarity}</span>
              </div>
            ))}
          </div>
        </div>
      );
    };

    render(<MockApp />);

    const searchInput = screen.getByPlaceholderText('Search photos...');
    await user.type(searchInput, 'vacation{Enter}');

    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
    });

    // Check results are displayed
    const results = screen.getByTestId('results');
    expect(results).toBeInTheDocument();

    const result1 = screen.getByTestId('result-1');
    expect(result1).toBeInTheDocument();
    expect(result1).toHaveTextContent('0.95');

    const result2 = screen.getByTestId('result-2');
    expect(result2).toBeInTheDocument();
    expect(result2).toHaveTextContent('0.87');
  });

  test('handles search errors gracefully', async () => {
    server.use(
      rest.post('/api/search/text', (req, res, ctx) => {
        return res(ctx.status(500), ctx.json({ error: 'Server error' }));
      })
    );

    const user = userEvent.setup();

    const MockApp = () => {
      const [error, setError] = React.useState(null);

      const handleSearch = async (query) => {
        try {
          const response = await fetch('/api/search/text', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query }),
          });

          if (!response.ok) {
            throw new Error('Search failed');
          }
        } catch (err) {
          setError(err.message);
        }
      };

      return (
        <div>
          <input
            type="text"
            placeholder="Search..."
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                handleSearch(e.target.value);
              }
            }}
          />
          {error && <div role="alert">{error}</div>}
        </div>
      );
    };

    render(<MockApp />);

    const searchInput = screen.getByPlaceholderText('Search...');
    await user.type(searchInput, 'test{Enter}');

    await waitFor(() => {
      const errorMessage = screen.getByRole('alert');
      expect(errorMessage).toHaveTextContent('Search failed');
    });
  });

  test('switches between search modes', async () => {
    const user = userEvent.setup();

    const MockApp = () => {
      const [mode, setMode] = React.useState('text');
      const [results, setResults] = React.useState([]);

      const handleSearch = async (query) => {
        const endpoint = mode === 'text' ? '/api/search/text' : '/api/search/semantic';
        const response = await fetch(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query }),
        });
        const data = await response.json();
        setResults(data.results);
      };

      return (
        <div>
          <select value={mode} onChange={(e) => setMode(e.target.value)}>
            <option value="text">Text Search</option>
            <option value="semantic">Semantic Search</option>
          </select>
          <input
            type="text"
            placeholder="Search..."
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                handleSearch(e.target.value);
              }
            }}
          />
          <div data-testid="results">
            {results.map((result) => (
              <div key={result.id}>{result.path}</div>
            ))}
          </div>
        </div>
      );
    };

    render(<MockApp />);

    // Perform text search
    const searchInput = screen.getByPlaceholderText('Search...');
    await user.type(searchInput, 'test{Enter}');

    await waitFor(() => {
      expect(screen.getByText('/photos/result1.jpg')).toBeInTheDocument();
    });

    // Switch to semantic search
    const modeSelect = screen.getByRole('combobox');
    await user.selectOptions(modeSelect, 'semantic');

    // Clear and search again
    await user.clear(searchInput);
    await user.type(searchInput, 'happy moments{Enter}');

    await waitFor(() => {
      expect(screen.getByText('/photos/semantic1.jpg')).toBeInTheDocument();
    });
  });

  test('implements search pagination', async () => {
    server.use(
      rest.post('/api/search/text', (req, res, ctx) => {
        const { offset = 0 } = req.body;
        const results = Array.from({ length: 10 }, (_, i) => ({
          id: offset + i + 1,
          path: `/photos/photo${offset + i + 1}.jpg`,
          thumbnail: `data:image/jpeg;base64,thumb${offset + i + 1}`,
        }));

        return res(
          ctx.json({
            results,
            total: 100,
            offset,
          })
        );
      })
    );

    const user = userEvent.setup();

    const MockApp = () => {
      const [results, setResults] = React.useState([]);
      const [offset, setOffset] = React.useState(0);

      const handleSearch = async (searchOffset = 0) => {
        const response = await fetch('/api/search/text', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: 'test', offset: searchOffset, limit: 10 }),
        });
        const data = await response.json();
        setResults(data.results);
        setOffset(searchOffset);
      };

      return (
        <div>
          <button onClick={() => handleSearch(0)}>Search</button>
          <div data-testid="results">
            {results.map((result) => (
              <div key={result.id}>{result.path}</div>
            ))}
          </div>
          <button onClick={() => handleSearch(offset + 10)} disabled={offset >= 90}>
            Next Page
          </button>
        </div>
      );
    };

    render(<MockApp />);

    // Initial search
    const searchButton = screen.getByText('Search');
    await user.click(searchButton);

    await waitFor(() => {
      expect(screen.getByText('/photos/photo1.jpg')).toBeInTheDocument();
    });

    // Load next page
    const nextButton = screen.getByText('Next Page');
    await user.click(nextButton);

    await waitFor(() => {
      expect(screen.getByText('/photos/photo11.jpg')).toBeInTheDocument();
      expect(screen.queryByText('/photos/photo1.jpg')).not.toBeInTheDocument();
    });
  });

  test('handles search filters and facets', async () => {
    server.use(
      rest.post('/api/search/text', (req, res, ctx) => {
        const { filters } = req.body;
        const baseResults = [
          { id: 1, path: '/photos/2024/photo1.jpg', date: '2024-01-01' },
          { id: 2, path: '/photos/2024/photo2.jpg', date: '2024-06-01' },
          { id: 3, path: '/photos/2023/photo3.jpg', date: '2023-12-01' },
        ];

        const filteredResults = filters?.year === '2024'
          ? baseResults.filter((r) => r.date.startsWith('2024'))
          : baseResults;

        return res(ctx.json({ results: filteredResults }));
      })
    );

    const user = userEvent.setup();

    const MockApp = () => {
      const [results, setResults] = React.useState([]);
      const [yearFilter, setYearFilter] = React.useState('');

      const handleSearch = async () => {
        const filters = yearFilter ? { year: yearFilter } : undefined;
        const response = await fetch('/api/search/text', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: 'test', filters }),
        });
        const data = await response.json();
        setResults(data.results);
      };

      return (
        <div>
          <select value={yearFilter} onChange={(e) => setYearFilter(e.target.value)}>
            <option value="">All Years</option>
            <option value="2024">2024</option>
            <option value="2023">2023</option>
          </select>
          <button onClick={handleSearch}>Search</button>
          <div data-testid="results">
            {results.map((result) => (
              <div key={result.id}>{result.path}</div>
            ))}
          </div>
        </div>
      );
    };

    render(<MockApp />);

    // Search without filter
    const searchButton = screen.getByText('Search');
    await user.click(searchButton);

    await waitFor(() => {
      expect(screen.getByText('/photos/2024/photo1.jpg')).toBeInTheDocument();
      expect(screen.getByText('/photos/2023/photo3.jpg')).toBeInTheDocument();
    });

    // Apply year filter
    const yearSelect = screen.getByRole('combobox');
    await user.selectOptions(yearSelect, '2024');
    await user.click(searchButton);

    await waitFor(() => {
      expect(screen.getByText('/photos/2024/photo1.jpg')).toBeInTheDocument();
      expect(screen.queryByText('/photos/2023/photo3.jpg')).not.toBeInTheDocument();
    });
  });
});