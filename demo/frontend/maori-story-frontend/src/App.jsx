import React, { useState, useEffect } from 'react';

// 导入 MUI 组件
import {
    CssBaseline,
    AppBar,
    Toolbar,
    Typography,
    Container,
    CircularProgress,
    Box,
    Grid,
    Card,
    CardContent,
    Alert,
    Button
} from '@mui/material';

// Django API 的地址
const API_URL = 'http://127.0.0.1:8000/api/stories/';

function App() {
    const [stories, setStories] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const [selectedStory, setSelectedStory] = useState(null);

    useEffect(() => {
        const fetchStories = async () => {
            try {
                const response = await fetch(API_URL);
                if (!response.ok) {
                    throw new Error(`HTTP 错误！状态: ${response.status}`);
                }
                const data = await response.json();
                setStories(data);
            } catch (e) {
                console.error("获取数据失败:", e);
                setError("无法从后端加载故事数据。请确认您的Django服务器正在运行，并且CORS设置正确。");
            } finally {
                setLoading(false);
            }
        };
        fetchStories();
    }, []);

    // 用于渲染被选中的故事详情
    const renderStoryDetail = () => {
        // 假设 story 对象有 'title' 和 'content' 字段
        // 如果你的字段名不同 (比如 'text' 或 'body'), 请在这里修改
        
        return (
            <Box>
                <Button 
                    variant="outlined" 
                    onClick={() => setSelectedStory(null)} // 点击后清除选中的故事
                    sx={{ mb: 2 }}
                >
                    &larr; 返回列表
                </Button>
                <Typography variant="h3" component="h1" gutterBottom>
                    {selectedStory.title}
                </Typography>
                <Typography variant="body1" sx={{ whiteSpace: 'pre-line', lineHeight: 1.8 }}>
                    {selectedStory.full_text || "这个故事还没有内容。"}
                </Typography>
            </Box>
        );
    };

    const renderContent = () => {
        // 1. 优先检查是否正在加载
        if (loading) {
            return (
                <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
                    <CircularProgress />
                    <Typography variant="h6" sx={{ ml: 2 }}>正在加载故事...</Typography>
                </Box>
            );
        }

        // 2. 检查是否有错误
        if (error) {
            return <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>;
        }

        // 3. (新) 检查是否已选择一个故事
        // 如果 selectedStory 不是 null, 则显示详情
        if (selectedStory) {
            return renderStoryDetail();
        }
        
        // 4. 检查故事列表是否为空
        if (stories.length === 0) {
           return <Alert severity="info" sx={{ mt: 2 }}>没有找到故事。请尝试在Django后台添加一些内容。</Alert>;
        }

        // 5. (修改) 显示故事列表
        return (
            <Grid container spacing={3} sx={{ mt: 2 }}>
                {stories.map(story => (
                    <Grid size={{ xs: 12, sm: 6, md: 4 }} key={story.id}>
                        <Card 
                            sx={{ 
                                height: '100%', 
                                display: 'flex', 
                                flexDirection: 'column',
                                cursor: 'pointer', // 鼠标悬停时显示为指针
                                '&:hover': {
                                    boxShadow: 6, // 悬停时添加阴影
                                }
                            }}
                            onClick={() => setSelectedStory(story)} // <-- 添加点击事件
                        >
                            <CardContent>
                                <Typography gutterBottom variant="h5" component="div">
                                    {story.title}
                                </Typography>
                                <Typography variant="body2" color="text.secondary">
                                    点击开始学习这个故事！
                                </Typography>
                            </CardContent>
                        </Card>
                    </Grid>
                ))}
            </Grid>
        );
    };
    
    return (
        <React.Fragment>
            <CssBaseline />
            <AppBar position="static">
                <Toolbar>
                    <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                        Māori Story-Fill
                    </Typography>
                </Toolbar>
            </AppBar>
            <Container maxWidth="lg" component="main" sx={{ py: 4 }}>
                {/* renderContent 现在会处理所有逻辑 */}
                {renderContent()}
            </Container>
        </React.Fragment>
    );
}

export default App;