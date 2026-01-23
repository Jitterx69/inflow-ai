from typing import Dict, Any, List

class ContentGenerator:
    """
    Handles generation of scripts, captions, and hashtags.
    Mocks LLM calls for now.
    """
    
    def __init__(self):
        pass

    def generate_script(self, idea_context: Dict[str, Any], constraints: List[str]) -> str:
        """
        Generates a video script based on the idea and constraints.
        """
        topic = idea_context.get("topic", "General")
        format_type = idea_context.get("format", "Short")
        
        # Mock LLM generation
        script = f"Title: Why {topic} is the future\n\n"
        script += f"[Scene: Host talking to camera] ({format_type} format)\n"
        script += "Host: Have you ever wondered about this?\n"
        script += f"Host: Here is what you need to know about {topic}...\n"
        
        if constraints:
            script += f"\n[Notes: Constraints applied: {', '.join(constraints)}]"
            
        return script

    def generate_caption(self, script: str, tone: str) -> str:
        """
        Generates a caption for the video.
        """
        # Mock LLM generation
        return f"Check this out! 🚀 #{tone} #Viral"

    def generate_hashtags(self, content: str, topic: str) -> List[str]:
        """
        Generates relevant hashtags.
        """
        return [f"#{topic}", "#Trending", "#FYP", "#LearnOnTikTok"]
