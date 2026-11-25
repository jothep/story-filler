/**
 * The text a player sees for a word: its form in the story's learning
 * language. A word without that form falls back to its key, so a button or
 * filled blank is never empty.
 *
 * @param {import('../types').Word|null|undefined} word
 * @returns {string}
 */
export function wordText(word) {
  return word?.text || word?.key || '';
}
