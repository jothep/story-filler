/**
 * Public API contracts shared by requests, playback and word interactions.
 * Nullable media matches the backend serializers; these types do not replace
 * validation of data received from an external API.
 *
 * @typedef {object} Word
 * @property {number} id
 * @property {string} maori_word
 * @property {string} english_translation
 * @property {string|null} image
 * @property {string|null} maori_audio
 * @property {string|null} english_audio
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
