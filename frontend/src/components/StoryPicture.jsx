// src/components/StoryPicture.jsx
import myStoryImage from '../assets/sunny.jpg'; // <--- 你需要修改这里

// 2. (新) 为图片定义样式
const imageStyle = {
  width: '100%',  // 宽度 100%
  height: '100%', // 高度 100%
  
  // 关键: 'cover' 会缩放图片以填满整个框, 保持比例, 并裁剪多余部分
  // 这完全符合你的要求
  objectFit: 'cover', 
};

function StoryPicture() {
  return (
    <div
      className="nes-container is-dark"
      style={{
        height: '100%',
        boxSizing: 'border-box',
        
        // (新) 移除 nes-container 默认的内边距, 让图片填满
        padding: 0,
      }}
    >
      {/* 3. (修改) 用 <img> 替换 <p> */}
      <img
        src={myStoryImage} // <--- 使用你导入的图片
        alt="Story picture"
        style={imageStyle}
      />
    </div>
  );
}

export default StoryPicture;