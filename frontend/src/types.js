/**
 * Public API contracts shared by requests, playback and word interactions.
 * Nullable media matches the backend serializers; these types do not replace
 * validation of data received from an external API.
 *
 * @typedef {object} Language
 * @property {string} code
 * @property {string} name
 *
 * A word as a story uses it. `text` and `audio` are in the story's learning
 * language; `translation` and `translation_audio` are in the story language
 * and null when the two languages are the same. A missing form is null.
 *
 * @typedef {object} Word
 * @property {number} id
 * @property {string|null} key
 * @property {string|null} image
 * @property {string|null} text
 * @property {string|null} audio
 * @property {string|null} translation
 * @property {string|null} translation_audio
 *
 * @typedef {object} BlankLink
 * @property {number} [id]
 * @property {string} [placeholder]
 * @property {Word|null} word
 *
 * @typedef {object} Paragraph
 * @property {number} id
 * @property {number} order
 * @property {string} text
 * @property {string|null} audio
 * @property {BlankLink[]} blank_links
 *
 * @typedef {object} StorySummary
 * @property {number} id
 * @property {string} title
 *
 * @typedef {StorySummary & {
 *   language: Language|null,
 *   learning_language: Language|null,
 *   paragraphs: Paragraph[],
 *   words_in_bank: Word[],
 *   background_music_url: string|null,
 *   picture_url: string|null
 * }} Story
 *
 * @typedef {object} PlaybackState
 * @property {Story} story
 * @property {boolean} isMusicPlaying
 * @property {Paragraph|null} currentParagraph
 * @property {number} currentParagraphIndex
 * @property {() => void} handleToggleMusic
 * @property {() => void} handleNextParagraph
 * @property {() => void} handlePrevParagraph
 * @property {(url: string|null) => Promise<void>} handlePlayParagraphAudio
 *
 * @typedef {object} WordInteractionState
 * @property {Word|null} selectedWord
 * @property {import('react').Dispatch<import('react').SetStateAction<Word|null>>} setSelectedWord
 * @property {Record<string, Word>} filledBlanks
 * @property {import('@dnd-kit/core').UniqueIdentifier|null} wrongAttempt
 * @property {(event: import('@dnd-kit/core').DragStartEvent) => void} handleDragStart
 * @property {(event: import('@dnd-kit/core').DragEndEvent) => void} handleDragEnd
 */

export {};
