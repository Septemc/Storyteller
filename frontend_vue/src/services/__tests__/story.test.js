import { beforeEach, describe, expect, it, vi } from 'vitest';

import { STORAGE_KEYS } from '../../constants/storage';
import { generateStream } from '../modules/story';

describe('story service', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
  });

  it('attaches bearer token for stream generation requests', async () => {
    localStorage.setItem(STORAGE_KEYS.token, 'token-123');

    const reader = {
      read: vi
        .fn()
        .mockResolvedValueOnce({
          done: false,
          value: new TextEncoder().encode('event: done\ndata: {}\n\n'),
        })
        .mockResolvedValueOnce({ done: true, value: undefined }),
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      body: { getReader: () => reader },
    });

    await generateStream({ session_id: 'S1', user_input: 'hello' });

    expect(global.fetch).toHaveBeenCalledWith(
      '/api/story/generate_stream',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          Authorization: 'Bearer token-123',
          'Content-Type': 'application/json',
        }),
      }),
    );
  });
});
