import React from 'react';
import { render } from '@testing-library/react';
import App from './App';

test('renders without crashing', () => {
  const { container } = render(<App />);
  // Just check that the app renders without throwing an error
  expect(container).toBeTruthy();
});

