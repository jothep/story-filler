// src/StoryPlayer.jsx
import { useParams } from 'react-router-dom';
import '../assets/StoryPlayer.css';
import StoryPlayerUI from './StoryPlayerUI';
import { useStory } from '../hooks/useStory';

import { WordInteractionProvider } from '../context/WordInteractionContext'; 
import { StoryPlaybackProvider } from '../context/StoryPlaybackContext';

/** 
 * function StoryPlayerUI() {
  
  // (已修改) 3. 从新的 Hook 获取所有 播放/导航 状态
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
  // 从 Context 中获取拖拽逻辑
  const { handleDragStart, handleDragEnd } = useWordInteraction();

  const paragraphsExist = story.paragraphs && story.paragraphs.length > 0; //

  return (
    // DndContext 使用 Context 提供的函数
    <DndContext onDragStart={handleDragStart} onDragEnd={handleDragEnd}>

      <div className="game-screen">
        
        <div className="layout-nav">
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
        color: 'inherit', // <-- 修复问题 1: 链接将变为白色
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
        flexGrow: 1, // <-- 修复问题 2: 标题将占据空间
        textAlign: 'center', // <-- 并居中
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


        <div className="layout-pic">
          <StoryPicture />
        </div>

       
        <div className="layout-list">
          
          <WordList words={story.words_in_bank} />
        </div>

       
        <div className="layout-text">
          {paragraphsExist ? (
            <StoryContent
              paragraph={currentParagraph}
              paragraphNumber={currentParagraphIndex + 1}
              totalParagraphs={story.paragraphs.length}
              onNext={handleNextParagraph}
              onPrev={handlePrevParagraph}
              onPlayAudio={handlePlayParagraphAudio}
              // filledBlanks 和 wrongAttempt 将从 Context 中自动获取
            />
          ) : (
            <div className="nes-container is-dark">
              <p>This story has no paragraphs yet.</p>
            </div>
          )}
        </div>

      
        <div className="layout-w-pic">
         
          <WordPic /> 
        </div>
        
      
        <div className="layout-w-audio">
        
          <WordAudio />
        </div>
        
      
        <div className="layout-tips">
       
          <TriggerTips /> 
        </div>

      </div>
    </DndContext>
  );
} */

function StoryPlayer() {
  const { storyId } = useParams();
  const { story, loading, error } = useStory(storyId);

  // 2. 交互状态 (已移至 Context，这里不再需要)
  // const [selectedWord, setSelectedWord] = useState(null); (已移除)
  // const [filledBlanks, setFilledBlanks] = useState({}); (已移除)
  // const [wrongAttempt, setWrongAttempt] = useState(null); (已移除)

  // 3. 音频和段落状态 (保留在 StoryPlayer)
  // const [isMusicPlaying, setIsMusicPlaying] = useState(true); //
  // const bgmAudioRef = useRef(null); //
  //const paragraphAudioRef = useRef(null); //
  //const [currentParagraphIndex, setCurrentParagraphIndex] = useState(0); //

  // BGM Effect (保留)
  /* useEffect(() => {
    if (!story || !story.background_music_url) {
      return;
    }
    const audio = new Audio(story.background_music_url);
    audio.loop = true;
    audio.volume = 0.3;
    bgmAudioRef.current = audio;

    if (isMusicPlaying) {
      audio.play().catch((e) => console.warn('BGM 自动播放被阻止:', e));
    }
    return () => {
      audio.pause();
      bgmAudioRef.current = null;
    };
  }, [story]); 

const handleToggleMusic = () => {
    const audio = bgmAudioRef.current;
    if (!audio) return;
    const newMusicState = !isMusicPlaying;
    setIsMusicPlaying(newMusicState);
    newMusicState ? audio.play() : audio.pause();
  }; //

  const handleNextParagraph = () => {
    if (paragraphAudioRef.current) paragraphAudioRef.current.pause(); // 切换时停止朗读
    setCurrentParagraphIndex((prev) =>
      Math.min(prev + 1, story.paragraphs.length - 1)
    );
  }; //

  const handlePrevParagraph = () => {
    if (paragraphAudioRef.current) paragraphAudioRef.current.pause(); // 切换时停止朗读
    setCurrentParagraphIndex((prev) => Math.max(prev - 1, 0));
  }; //

  const handlePlayParagraphAudio = (audioUrl) => {
    if (!audioUrl) return;

    // 如果当前有音频在播放，则暂停
    if (paragraphAudioRef.current) {
      paragraphAudioRef.current.pause();
      paragraphAudioRef.current = null;
    }

    const audio = new Audio(audioUrl);
    paragraphAudioRef.current = audio;
    audio.play().catch((e) => console.warn('段落音频播放失败:', e));
  }; //

  // 4. 拖拽逻辑 (已移至 Context)
  // function handleDragStart() { ... } (已移除)
  // function handleDragEnd(event) { ... } (已移除)
 */

  // 5. Loading / Error / No Data 处理 (保留)
  if (loading) {
    return <div style={{ color: 'white', padding: '2rem' }}>Loading story...</div>; //
  }
  if (error) {
    return <div style={{ color: 'red', padding: '2rem' }}>Error loading story: {error}</div>; //
  }
  if (!story) {
    return <div>No story found.</div>; //
  }

  // 6. 派生状态 (保留)
  //const currentParagraph = (story.paragraphs && story.paragraphs.length > 0)
  //  ? story.paragraphs[currentParagraphIndex]
  //  : null; //

  // 7. 渲染
  return (
    // 1. (修复) 添加 StoryPlaybackProvider 并传入 story
    <StoryPlaybackProvider story={story}>
      <WordInteractionProvider wordsInBank={story.words_in_bank}>

        <StoryPlayerUI />

      </WordInteractionProvider>
    </StoryPlaybackProvider>
  );
}

/** 
 function StoryPlayer() {
  const { storyId } = useParams();
  const { story, loading, error } = useStory(storyId);

  const [selectedWord, setSelectedWord] = useState(null);
  const [filledBlanks, setFilledBlanks] = useState({});
  const [wrongAttempt, setWrongAttempt] = useState(null);
  const [isMusicPlaying, setIsMusicPlaying] = useState(true);
  const bgmAudioRef = useRef(null); // BGM 音频
  const paragraphAudioRef = useRef(null); // (新增) 段落朗读音频
  const [currentParagraphIndex, setCurrentParagraphIndex] = useState(0);

  useEffect(() => {
    if (!story || !story.background_music_url) {
      return;
    }
    const audio = new Audio(story.background_music_url);
    audio.loop = true;
    audio.volume = 0.3;
    bgmAudioRef.current = audio;

    if (isMusicPlaying) {
      audio.play().catch((e) => console.warn('BGM 自动播放被阻止:', e));
    }
    return () => {
      audio.pause();
      bgmAudioRef.current = null;
    };
  }, [story]); // 依赖 story 对象

  const handleToggleMusic = () => {
    const audio = bgmAudioRef.current;
    if (!audio) return;
    const newMusicState = !isMusicPlaying;
    setIsMusicPlaying(newMusicState);
    newMusicState ? audio.play() : audio.pause();
  };

  const handleNextParagraph = () => {
    if (paragraphAudioRef.current) paragraphAudioRef.current.pause(); // 切换时停止朗读
    setCurrentParagraphIndex((prev) =>
      Math.min(prev + 1, story.paragraphs.length - 1)
    );
  };

  const handlePrevParagraph = () => {
    if (paragraphAudioRef.current) paragraphAudioRef.current.pause(); // 切换时停止朗读
    setCurrentParagraphIndex((prev) => Math.max(prev - 1, 0));
  };

  const handlePlayParagraphAudio = (audioUrl) => {
    if (!audioUrl) return;

    // 如果当前有音频在播放，则暂停
    if (paragraphAudioRef.current) {
      paragraphAudioRef.current.pause();
      paragraphAudioRef.current = null;
    }

    const audio = new Audio(audioUrl);
    paragraphAudioRef.current = audio;
    audio.play().catch((e) => console.warn('段落音频播放失败:', e));
  };

  function handleDragStart() {
    setWrongAttempt(null);
  }

  function handleDragEnd(event) {
    const { active, over } = event;

    if (!over || !active) return;

    const draggedWord = story.words_in_bank.find(
      (word) => word.id === active.id
    );

    if (!draggedWord) return;

    if (over.id === 'trigger-tips-droppable') {
      setSelectedWord(draggedWord);
      return;
    }

    const dropZoneType = over.data.current?.type;
    if (dropZoneType === 'blank') {
      const uniqueBlankId = over.id;
      const correctWordId = over.data.current.correctWordId;

      if (draggedWord.id === correctWordId) {
        setFilledBlanks((prevBlanks) => ({
          ...prevBlanks,
          [uniqueBlankId]: draggedWord,
        }));
        setWrongAttempt(null);
      } else {
        console.log('Wrong answer.');
        setWrongAttempt(uniqueBlankId);
      }
    }
  }

  if (loading) {
    return (
      <div style={{ color: 'white', padding: '2rem' }}>Loading story...</div>
    );
  }
  if (error) {
    return (
      <div style={{ color: 'red', padding: '2rem' }}>
        Error loading story: {error}
      </div>
    );
  }
  if (!story) {
    return <div>No story found.</div>;
  }

  const paragraphsExist = story.paragraphs && story.paragraphs.length > 0;
  const currentParagraph = paragraphsExist
    ? story.paragraphs[currentParagraphIndex]
    : null;

  return (
    <DndContext onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
      <div className="game-screen">
        <div className="layout-nav">
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
                color: 'inherit', // 继承 .is-dark 容器的白色
                textDecoration: 'none', // 去掉链接的下划线
                fontSize: '1rem', // 设置字体大小 (和标题一致)
                flexShrink: 0, // (来自 StoryPlayer.jsx) 防止被压缩
                padding: '0 0.5rem', // 给文字一点左右的内边距
              }}
            >
              &lt;-- Menu
            </Link>

    
            <h1
              style={{
                flexGrow: 1, // 占据所有剩余空间
                textAlign: 'center', // 文本居中
                fontSize: '2rem', // 调整字体大小 (nes.css 字体很大)
                margin: '0 1rem', // 左右留出间距
                whiteSpace: 'nowrap', // 防止标题换行
                overflow: 'hidden', // 隐藏溢出内容
                textOverflow: 'ellipsis', // 标题太长时显示...
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

        <div className="layout-pic">
          <StoryPicture />
        </div>

        <div className="layout-list">
          <WordList
            words={story.words_in_bank}
            onWordSelect={setSelectedWord}
          />
        </div>

        <div className="layout-text">
          {paragraphsExist ? (
            <StoryContent
              paragraph={currentParagraph}
              paragraphNumber={currentParagraphIndex + 1}
              totalParagraphs={story.paragraphs.length}
              onNext={handleNextParagraph}
              onPrev={handlePrevParagraph}
              onPlayAudio={handlePlayParagraphAudio}
              filledBlanks={filledBlanks}
              wrongAttempt={wrongAttempt}
            />
          ) : (
            <div
              className="nes-container is-dark"
              style={{ height: '100%', padding: '1rem' }}
            >
              <p>This story has no paragraphs yet.</p>
            </div>
          )}
        </div>

        <div className="layout-w-pic">
          <WordPic word={selectedWord} />
        </div>
        <div className="layout-w-audio">
          <WordAudio word={selectedWord} />
        </div>
        <div className="layout-tips">
          <TriggerTips selectedWord={selectedWord} />
        </div>
      </div>
    </DndContext>
  );
} */

export default StoryPlayer;
