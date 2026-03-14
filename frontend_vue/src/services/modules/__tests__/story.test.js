import { describe, expect, it } from 'vitest';
import { generateStream } from '../story';

describe('story service error sanitization', () => {
  it('sanitizes cloudflare html error pages', async () => {
    global.fetch = async () => ({
      ok: false,
      text: async () => '<!DOCTYPE html><html><head><title>ggchan.dev | 520: Web server is returning an unknown error</title></head></html>',
    });

    await expect(generateStream({})).rejects.toThrow('???????????');
  });
});
