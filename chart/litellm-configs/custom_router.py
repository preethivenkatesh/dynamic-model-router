from litellm.integrations.custom_logger import CustomLogger
import litellm
from litellm.proxy.proxy_server import UserAPIKeyAuth, DualCache
from typing import Optional, Literal
from semantic_router import Route
from semantic_router.layer import RouteLayer
from semantic_router.encoders import FastEmbedEncoder
import json
import re


# Define routes for complexity-based routing
simple_tasks = Route(
    name="simple-xeon",
    utterances=[
        "What is",
        "Define",
        "Explain briefly",
        "Simple question",
        "Quick answer",
        "Tell me about",
        "What does",
        "How do you spell",
        "What's the meaning of",
        "Give me a summary",
        "What time",
        "What date",
        "Basic information",
        "Simple definition",
        "Short explanation"
    ],
)

complex_tasks = Route(
    name="complex-gaudi",
    utterances=[
        "Analyze the complex relationship",
        "Write a detailed report",
        "Provide a comprehensive analysis",
        "Create a detailed plan",
        "Develop a strategy",
        "Write code for",
        "Debug this complex problem",
        "Solve this mathematical equation",
        "Generate a detailed explanation",
        "Compare and contrast multiple",
        "Perform deep analysis",
        "Research and provide insights",
        "Create a detailed algorithm",
        "Design a complex system",
        "Provide step-by-step solution"
    ],
)

class ComplexityBasedRouter(CustomLogger):
    def __init__(self):
        # Removed medical_tasks from routes - only simple and complex now
        self.routes = [simple_tasks, complex_tasks]
        self.encoder = FastEmbedEncoder(name="BAAI/bge-small-en-v1.5", score_threshold=0.5)
        self.routelayer = RouteLayer(encoder=self.encoder, routes=self.routes)
        
        # Complexity indicators - these patterns suggest complex tasks
        self.complexity_patterns = [
            r'\b(analyze|analysis|detailed|comprehensive|complex|algorithm|debug|strategy)\b',
            r'\b(compare.*contrast|step.*by.*step|in.*depth|thoroughly)\b',
            r'\b(code|programming|function|class|method|variable)\b',
            r'\b(mathematical|equation|formula|calculation|solve)\b',
            r'\b(research|investigate|examine|explore)\b',
            r'\b(design|architect|implement|develop)\b'
        ]
        
        # Simple task indicators
        self.simple_patterns = [
            r'^\s*(what\s+is|define|explain\s+briefly|tell\s+me\s+about)\b',
            r'^\s*(how\s+do\s+you\s+spell|what.*meaning|quick\s+answer)\b',
            r'^\s*(what\s+time|what\s+date|basic\s+information)\b'
        ]

    def assess_complexity(self, message: str) -> str:
        """
        Assess the complexity of a message using multiple factors:
        1. Length (longer messages often indicate complexity)
        2. Pattern matching for complex/simple keywords
        3. Semantic routing results
        4. Question structure
        """
        message_lower = message.lower()
        
        # Factor 1: Length-based assessment
        word_count = len(message.split())
        length_score = min(word_count / 20.0, 1.0)  # Normalize to 0-1, cap at 20 words
        
        # Factor 2: Pattern matching
        complexity_score = 0.0
        simple_score = 0.0
        
        for pattern in self.complexity_patterns:
            if re.search(pattern, message_lower, re.IGNORECASE):
                complexity_score += 0.3
                
        for pattern in self.simple_patterns:
            if re.search(pattern, message_lower, re.IGNORECASE):
                simple_score += 0.4
        
        # Factor 3: Semantic routing
        route = self.routelayer(message)
        route_metrics = self.routelayer.retrieve_multiple_routes(message)
        
        semantic_score = 0.0
        if route_metrics:
            for route_choice in route_metrics:
                if "complex" in route_choice.name:
                    semantic_score += route_choice.similarity_score * 0.5
                elif "simple" in route_choice.name:
                    semantic_score -= route_choice.similarity_score * 0.3
        
        # Combine all factors
        total_complexity = length_score + complexity_score + semantic_score - simple_score
        
        print(f"Complexity Assessment: length={length_score:.2f}, patterns={complexity_score:.2f}, "
              f"simple_patterns={simple_score:.2f}, semantic={semantic_score:.2f}, "
              f"total={total_complexity:.2f}")
        
        # Decision threshold
        if total_complexity > 0.6:
            return "complex-gaudi"
        else:
            return "simple-xeon"

    async def async_pre_call_hook(self, user_api_key_dict: UserAPIKeyAuth, cache: DualCache, data: dict, call_type: Literal[
            "completion",
            "text_completion", 
            "embeddings",
            "image_generation",
            "moderation",
            "audio_transcription",
        ]): 
        msg = data['messages'][-1]['content']
        
        # Assess complexity and route accordingly
        selected_model = self.assess_complexity(msg)
        
        # Try semantic routing first
        route = self.routelayer(msg)
        route_metrics = self.routelayer.retrieve_multiple_routes(msg)
        
        print(f"Semantic route metrics: {route_metrics}")
        
        if route_metrics and route_metrics[0].similarity_score > 0.7:
            # High confidence semantic match
            selected_model = route.name
            print(f"High confidence semantic routing to: {selected_model}")
        else:
            # Use complexity-based routing
            print(f"Complexity-based routing to: {selected_model}")
        
        data["model"] = selected_model
        #data["selected_model"] = selected_model  # <-- Add this line
        data.setdefault("_router_meta", {})["final_model"] = selected_model
        print(f"Final model selection: {selected_model}")           
        return data 

    async def async_post_call_failure_hook(
        self, 
        request_data: dict,
        original_exception: Exception, 
        user_api_key_dict: UserAPIKeyAuth
    ):
        print(f"Request failed: {original_exception}")

    async def async_post_call_success_hook(
        self,
        data: dict,
        user_api_key_dict: UserAPIKeyAuth,
        response,
    ):
        pass

    async def async_moderation_hook(
        self,
        data: dict,
        user_api_key_dict: UserAPIKeyAuth,
        call_type: Literal["completion", "embeddings", "image_generation", "moderation", "audio_transcription"],
    ):
        pass

    async def async_post_call_streaming_hook(
        self,
        user_api_key_dict: UserAPIKeyAuth,
        response: str,
    ):
        try:
            text = response.decode("utf-8", "ignore") if isinstance(response, (bytes, bytearray)) else str(response)
            # (Optional) LOG ONLY – do not modify stream
            # for line in text.splitlines():
            #     if line.startswith("data:"):
            #         payload = line[5:].strip()
            #         if payload and payload != "[DONE]":
            #             try:
            #                 obj = json.loads(payload)
            #                 if "model" in obj: print(f"[stream] model={obj['model']}")
            #             except Exception:
            #                 pass
        except Exception:
        # swallow errors to avoid breaking post_success
            pass
    # IMPORTANT: don't return anything; hook is side-effect only
        return

proxy_handler_instance = ComplexityBasedRouter()