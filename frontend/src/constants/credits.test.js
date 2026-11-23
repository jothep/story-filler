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
    expect(credits['Menu music']).toBe(
      'Schumann — Träumerei, Kinderszenen, Op. 15, No. 7'
    );
    expect(credits['Story music']).toBe('Dvořák — Humoresque, Op. 101, No. 7');
  });
});
