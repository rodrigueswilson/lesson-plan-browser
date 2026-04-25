import { describe, expect, it } from 'vitest';
import { classifyProgressPollPayload } from '@lesson-api';

describe('classifyProgressPollPayload', () => {
  it('treats completed status as terminal success', () => {
    const payload = classifyProgressPollPayload({ status: 'completed' });
    expect(payload.terminal).toBe(true);
    expect(payload.kind).toBe('success');
    expect(payload.normalizedStatus).toBe('completed');
  });

  it('treats failed status as terminal failure', () => {
    const payload = classifyProgressPollPayload({ stage: 'failed' });
    expect(payload.terminal).toBe(true);
    expect(payload.kind).toBe('failure');
    expect(payload.normalizedStatus).toBe('failed');
  });

  it('keeps processing status as ongoing', () => {
    const payload = classifyProgressPollPayload({ status: 'transforming' });
    expect(payload.terminal).toBe(false);
    expect(payload.kind).toBe('ongoing');
    expect(payload.normalizedStatus).toBe('transforming');
  });
});
