/**
 * Unit tests for AISentinel component.
 * 
 * Tests the forensic simulation chat interface including:
 * - Rendering states (with/without analysis results)
 * - Step-up authentication trigger logic
 * - User interaction with chat input
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import AISentinel from '../AISentinel';

// Mock analysis result for testing
const createMockResult = (overrides = {}) => ({
    forensic_summary: 'Synthetic audio markers detected in signal.',
    verdict: {
        risk_level: 'CRITICAL',
        ...overrides.verdict,
    },
    physics_engine: {
        latency_jitter: { value_ms: 250 },
        vocal_crypt: { value: 1 },
        geo_location: { value: 1 },
        ...overrides.physics_engine,
    },
    ...overrides,
});

describe('AISentinel', () => {
    describe('Rendering', () => {
        it('renders without crashing when no result provided', () => {
            render(<AISentinel result={null} />);
            expect(screen.getByText('AI Sentinel')).toBeInTheDocument();
        });

        it('renders header with AI Sentinel title', () => {
            render(<AISentinel result={createMockResult()} />);
            expect(screen.getByText('AI Sentinel')).toBeInTheDocument();
        });

        it('displays forensic summary in initial message', async () => {
            render(<AISentinel result={createMockResult()} />);
            await waitFor(() => {
                expect(screen.getByText(/Synthetic audio markers detected/)).toBeInTheDocument();
            });
        });

        it('renders input field for user queries', () => {
            render(<AISentinel result={createMockResult()} />);
            expect(screen.getByPlaceholderText('Type your query...')).toBeInTheDocument();
        });
    });

    describe('Step-Up Authentication Logic', () => {
        it('shows step-up alert when jitter > 200ms', async () => {
            const result = createMockResult({
                physics_engine: {
                    latency_jitter: { value_ms: 250 },
                    vocal_crypt: { value: 1 },
                    geo_location: { value: 1 },
                },
            });
            render(<AISentinel result={result} />);

            expect(screen.getByText('Step-Up Authentication Required')).toBeInTheDocument();
            expect(screen.getByText(/250ms/)).toBeInTheDocument();
            expect(screen.getByText(/\[FAIL\]/)).toBeInTheDocument();
        });

        it('shows step-up alert when VocalCrypt is 0', async () => {
            const result = createMockResult({
                physics_engine: {
                    latency_jitter: { value_ms: 50 },
                    vocal_crypt: { value: 0 },
                    geo_location: { value: 1 },
                },
            });
            render(<AISentinel result={result} />);

            expect(screen.getByText('Step-Up Authentication Required')).toBeInTheDocument();
            expect(screen.getByText(/VocalCrypt:.*FAILED/)).toBeInTheDocument();
        });

        it('shows step-up alert when geo-location is 0', async () => {
            const result = createMockResult({
                physics_engine: {
                    latency_jitter: { value_ms: 50 },
                    vocal_crypt: { value: 1 },
                    geo_location: { value: 0 },
                },
            });
            render(<AISentinel result={result} />);

            expect(screen.getByText('Step-Up Authentication Required')).toBeInTheDocument();
            expect(screen.getByText('MISMATCH', { exact: false })).toBeInTheDocument();
        });

        it('does NOT show step-up alert when all checks pass', () => {
            const result = createMockResult({
                physics_engine: {
                    latency_jitter: { value_ms: 50 },  // < 200
                    vocal_crypt: { value: 1 },         // != 0
                    geo_location: { value: 1 },        // != 0
                },
            });
            render(<AISentinel result={result} />);

            expect(screen.queryByText('Step-Up Authentication Required')).not.toBeInTheDocument();
        });

        // FIDO2 button removed per Dieter Rams "honest design" audit
    });

    describe('User Interaction', () => {
        it('allows user to type in input field', () => {
            render(<AISentinel result={createMockResult()} />);
            const input = screen.getByPlaceholderText('Type your query...');

            fireEvent.change(input, { target: { value: 'test query' } });
            expect(input.value).toBe('test query');
        });

        it('sends message on Enter key press', async () => {
            render(<AISentinel result={createMockResult()} />);
            const input = screen.getByPlaceholderText('Type your query...');

            fireEvent.change(input, { target: { value: 'What is jitter?' } });
            fireEvent.keyPress(input, { key: 'Enter', charCode: 13 });

            await waitFor(() => {
                expect(screen.getByText('What is jitter?')).toBeInTheDocument();
            });
        });

        it('clears input after sending message', async () => {
            render(<AISentinel result={createMockResult()} />);
            const input = screen.getByPlaceholderText('Type your query...');

            fireEvent.change(input, { target: { value: 'test message' } });
            fireEvent.keyPress(input, { key: 'Enter', charCode: 13 });

            await waitFor(() => {
                expect(input.value).toBe('');
            });
        });

        it('does not send empty messages', () => {
            render(<AISentinel result={createMockResult()} />);
            const input = screen.getByPlaceholderText('Type your query...');

            fireEvent.change(input, { target: { value: '   ' } });
            fireEvent.keyPress(input, { key: 'Enter', charCode: 13 });

            // Should only have the initial system message
            const messages = screen.getAllByText(/System|You/);
            expect(messages.length).toBe(1); // Only system label
        });
    });

    describe('Simulated AI Responses', () => {
        it('responds to jitter-related queries with jitter explanation', async () => {
            const result = createMockResult({
                physics_engine: {
                    latency_jitter: { value_ms: 150 },
                    vocal_crypt: { value: 1 },
                    geo_location: { value: 1 },
                },
            });
            render(<AISentinel result={result} />);
            const input = screen.getByPlaceholderText('Type your query...');

            fireEvent.change(input, { target: { value: 'explain the jitter value' } });
            fireEvent.keyPress(input, { key: 'Enter', charCode: 13 });

            await waitFor(() => {
                expect(screen.getByText(/150ms/)).toBeInTheDocument();
                expect(screen.getByText(/voice conversion artifacts/i)).toBeInTheDocument();
            }, { timeout: 1500 });
        });

        it('responds to CRITICAL risk with high probability message', async () => {
            const result = createMockResult({
                verdict: { risk_level: 'CRITICAL' },
                physics_engine: {
                    latency_jitter: { value_ms: 50 },
                    vocal_crypt: { value: 1 },
                    geo_location: { value: 1 },
                },
            });
            render(<AISentinel result={result} />);
            const input = screen.getByPlaceholderText('Type your query...');

            fireEvent.change(input, { target: { value: 'analyze this' } });
            fireEvent.keyPress(input, { key: 'Enter', charCode: 13 });

            await waitFor(() => {
                expect(screen.getByText(/94%/)).toBeInTheDocument();
            }, { timeout: 1500 });
        });

        it('responds with organic signal message for non-critical queries', async () => {
            const result = createMockResult({
                verdict: { risk_level: 'LOW' },
                physics_engine: {
                    latency_jitter: { value_ms: 50 },
                    vocal_crypt: { value: 1 },
                    geo_location: { value: 1 },
                },
            });
            render(<AISentinel result={result} />);
            const input = screen.getByPlaceholderText('Type your query...');

            fireEvent.change(input, { target: { value: 'what do you see?' } });
            fireEvent.keyPress(input, { key: 'Enter', charCode: 13 });

            await waitFor(() => {
                expect(screen.getByText(/organic glottal excitation/i)).toBeInTheDocument();
            }, { timeout: 1500 });
        });
    });

    describe('Edge Cases', () => {
        it('handles missing physics_engine gracefully', () => {
            const result = {
                forensic_summary: 'Test summary',
                verdict: { risk_level: 'UNKNOWN' },
            };
            render(<AISentinel result={result} />);

            // Should show step-up because all values default to 0
            expect(screen.getByText('Step-Up Authentication Required')).toBeInTheDocument();
        });

        it('handles undefined result properties', () => {
            render(<AISentinel result={{}} />);
            expect(screen.getByText('AI Sentinel')).toBeInTheDocument();
        });
    });
});
