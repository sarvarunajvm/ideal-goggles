/**
 * Basic test to ensure Jest is working
 */

describe('Basic tests', () => {
  test('should pass basic assertion', () => {
    expect(1 + 1).toBe(2);
  });

  test('should handle string operations', () => {
    const message = 'Hello World';
    expect(message).toContain('World');
  });

  test('should handle array operations', () => {
    const items = ['apple', 'banana', 'cherry'];
    expect(items).toHaveLength(3);
    expect(items).toContain('banana');
  });
});