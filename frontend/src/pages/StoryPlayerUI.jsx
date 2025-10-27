// src/pages/StoryPlayerUI.jsx
import { useState } from 'react'; // 1. 重新导入 useState
import { DndContext, DragOverlay } from '@dnd-kit/core'; // 2. 重新导入 DragOverlay
import { Link } from 'react-router-dom';

// ... 导入你的所有组件 (StoryPicture, WordList, etc.) ...
import StoryPicture from '../components/StoryPicture';
import WordList from '../components/WordList';
import StoryContent from '../components/StoryContent';
import WordPic from '../components/WordPic';
import WordAudio from '../components/WordAudio';
import TriggerTips from '../components/TriggerTips';

import { useWordInteraction } from '../context/WordInteractionContext';
import { useStoryPlayback } from '../context/StoryPlaybackContext';

// 3. (新) 拖拽副本的组件
// 它被渲染在 DragOverlay 内部，样式为 'auto' 宽度
function WordOverlay({ word }) {
  return (
    <button type="button" className="nes-btn" style={{ width: 'auto' }}>
      {word.maori_word}
    </button>
  );
}

function StoryPlayerUI() {
  const {
    story,
    isMusicPlaying,
    handleToggleMusic,
    currentParagraph,
    currentParagraphIndex,
    handleNextParagraph,
    handlePrevParagraph,
    handlePlayParagraphAudio,
  } = useStoryPlayback();
  
  // 4. 从 hook 获取原始的 handlers
  const { handleDragStart: originalDragStart, handleDragEnd: originalDragEnd } =
    useWordInteraction();

  // 5. (新) 创建 state 来保存当前被拖拽的单词
  const [activeWord, setActiveWord] = useState(null);

  // 6. (新) 创建我们自己的 drag start handler
  const handleDragStart = (event) => {
    originalDragStart(event); // 调用 hook 里的原始逻辑
    // 找到被拖拽的单词对象
    const word = story.words_in_bank.find((w) => w.id === event.active.id);
    if (word) {
      setActiveWord(word); // 保存到 state 中
    }
  };

  // 7. (新) 创建我们自己的 drag end handler
  const handleDragEnd = (event) => {
    originalDragEnd(event); // 调用 hook 里的原始逻辑
    setActiveWord(null); // 清空 state
  };

  const paragraphsExist = story.paragraphs && story.paragraphs.length > 0;

  return (
    // 8. (修改) 把新的 handlers 传递给 DndContext
    <DndContext onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
      <div className="game-screen">
        {/* ... 这里是你所有的 layout-X div，保持不变 ... */}

        <div className="layout-nav"> {/* */}
          <div
            className="nes-container is-dark"
            style={{
              display: 'flex',
              alignItems: 'center',
              paddingTop: '0.5rem',
              paddingBottom: '0.5rem',
            }}
          >
            <Link
              to="/"
              style={{
                color: 'inherit',
                textDecoration: 'none',
                fontSize: '1rem',
                flexShrink: 0,
                padding: '0 0.5rem',
              }}
            >
              &lt;-- Menu
            </Link>
            <h1
              style={{
                flexGrow: 1,
                textAlign: 'center',
                fontSize: '2rem',
                margin: '0 1rem',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}
            >
              {story.title}
            </h1>
            {story.background_music_url && (
              <div style={{ flexShrink: 0 }}>
                <label>
                  <input
                    type="checkbox"
                    className="nes-checkbox is-dark"
                    checked={isMusicPlaying}
                    onChange={handleToggleMusic}
                  />
                  <span>BGM</span>
                </label>
              </div>
            )}
          </div>
        </div>

        <div className="layout-pic"> {/* */}
          <StoryPicture />
        </div>

        <div className="layout-list"> {/* */}
          <WordList words={story.words_in_bank} />
        </div>

        <div className="layout-text"> {/* */}
          {paragraphsExist ? (
            <StoryContent
              paragraph={currentParagraph}
              paragraphNumber={currentParagraphIndex + 1}
              totalParagraphs={story.paragraphs.length}
              onNext={handleNextParagraph}
              onPrev={handlePrevParagraph}
              onPlayAudio={handlePlayParagraphAudio}
            />
          ) : (
            <div className="nes-container is-dark" style={{ height: '100%', padding: '1rem' }}>
              <p>This story has no paragraphs yet.</p>
            </div>
          )}
        </div>

        <div className="layout-w-pic"> {/* */}
          <WordPic /> 
        </div>
        
        <div className="layout-w-audio"> {/* */}
          <WordAudio />
        </div>
        
        <div className="layout-tips"> {/* */}
          <TriggerTips /> 
        </div>

      </div>

      {/* 9. (新) 在这里添加 DragOverlay
          当 activeWord 存在时，它会渲染我们的“拖拽副本”
      */}
      {activeWord && (
        <DragOverlay>
          <WordOverlay word={activeWord} />
        </DragOverlay>
      )}
    </DndContext>
  );
}

export default StoryPlayerUI;