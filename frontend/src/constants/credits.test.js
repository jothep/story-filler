import { describe, it, expect } from 'vitest';
import { CREDITS_CONTENT } from './credits';

describe('CREDITS_CONTENT.materials', () => {
  it('uses unique labels, which the credits list uses as React keys', () => {
    const labels = CREDITS_CONTENT.materials.map((item) => item.label);
    expect(new Set(labels).size).toBe(labels.length);
  });

  it('credits both pieces of music in use', () => {
    const credits = Object.fromEntries(
      CREDITS_CONTENT.materials.map((item) => [item.label, item.credit])
    );
    expect(credits['Menu music']).toMatch(/Träumerei/);
    expect(credits['Story music']).toMatch(/Humoresque/);
  });
});
