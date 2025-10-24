import React, { useState, useEffect } from 'react';

// import MUI
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

// Django API
// const API_URL = 'http://127.0.0.1:8000/api/stories/';
const API_URL = '/api/stories/';

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
                    throw new Error(`HTTP Error! Status: ${response.status}`);
                }
                const data = await response.json();
                setStories(data);
            } catch (e) {
                console.error("Get data failed:", e);
                setError("无法从后端加载故事数据。请确认您的Django服务器正在运行,并且CORS设置正确。");
            } finally {
                setLoading(false);
            }
        };
        fetchStories();
    }, []);

    // Story details
    const renderStoryDetail = () => {
        
        return (
            <Box>
                <Button 
                    variant="outlined" 
                    onClick={() => setSelectedStory(null)} 
                    sx={{ mb: 2 }}
                >
                    &larr; Return to list
                </Button>
                <Typography variant="h3" component="h1" gutterBottom>
                    {selectedStory.title}
                </Typography>
                <Typography variant="body1" sx={{ whiteSpace: 'pre-line', lineHeight: 1.8 }}>
                    {selectedStory.full_text || "This story has no contents"}
                </Typography>
            </Box>
        );
    };

    const renderContent = () => {
        if (loading) {
            return (
                <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
                    <CircularProgress />
                    <Typography variant="h6" sx={{ ml: 2 }}>Loading story...</Typography>
                </Box>
            );
        }

        if (error) {
            return <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>;
        }

        if (selectedStory) {
            return renderStoryDetail();
        }
        
        if (stories.length === 0) {
           return <Alert severity="info" sx={{ mt: 2 }}>Didn&apos;t find story. Please add some story in Django firstly.</Alert>;
        }

        return (
            <Grid container spacing={3} sx={{ mt: 2 }}>
                {stories.map(story => (
                    <Grid size={{ xs: 12, sm: 6, md: 4 }} key={story.id}>
                        <Card 
                            sx={{ 
                                height: '100%', 
                                display: 'flex', 
                                flexDirection: 'column',
                                cursor: 'pointer', 
                                '&:hover': {
                                    boxShadow: 6, 
                                }
                            }}
                            onClick={() => setSelectedStory(story)} 
                        >
                            <CardContent>
                                <Typography gutterBottom variant="h5" component="div">
                                    {story.title}
                                </Typography>
                                <Typography variant="body2" color="text.secondary">
                                    Click to learn this story.
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
                {/* renderContent now to take all logics */}
                {renderContent()}
            </Container>
        </React.Fragment>
    );
}

export default App;