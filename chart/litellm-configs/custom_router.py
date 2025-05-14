from litellm.integrations.custom_logger import CustomLogger
import litellm
from litellm.proxy.proxy_server import UserAPIKeyAuth, DualCache
from typing import Optional, Literal
from semantic_router import Route
from semantic_router.layer import RouteLayer
from semantic_router.encoders import FastEmbedEncoder
import json



doctor = Route(
    name="doctor",
    utterances=[
        "I have a pain",
        "I'm not feeling well",
        "There's this thing on my",
        "I need some advice on",
        "Is there a tablet for",
    ],
)

solver = Route(
    name="dcot",
    utterances=[
        "provide a solution",
        "can you solve the following ",
        "I have this problem",
        "what's the best way",
        "how would you go about",
    ],
)

class CustomRouterHandler(CustomLogger):
    # Class variables or attributes
    def __init__(self):
        self.routes = [doctor, solver]
        self.encoder = FastEmbedEncoder(name="BAAI/bge-small-en-v1.5", score_threshold=0.6)
        self.routelayer = RouteLayer(encoder=self.encoder, routes=self.routes)
        pass

    #### CALL HOOKS - proxy only #### 

    async def async_pre_call_hook(self, user_api_key_dict: UserAPIKeyAuth, cache: DualCache, data: dict, call_type: Literal[
            "completion",
            "text_completion",
            "embeddings",
            "image_generation",
            "moderation",
            "audio_transcription",
        ]): 
        msg = data['messages'][-1]['content']
        route = self.routelayer(msg)
        route_metrics = self.routelayer.retrieve_multiple_routes((msg))
        print(route_metrics)
        if route_metrics:
            data["model"] = route.name            
        else:   
            print("No specific model found defaulting to Phi2")            
            data["model"] = "" 
        print(data["model"])
        return data 

    async def async_post_call_failure_hook(
        self, 
        request_data: dict,
        original_exception: Exception, 
        user_api_key_dict: UserAPIKeyAuth
    ):
        pass

    async def async_post_call_success_hook(
        self,
        data: dict,
        user_api_key_dict: UserAPIKeyAuth,
        response,
    ):
        pass

    async def async_moderation_hook( # call made in parallel to llm api call
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
        pass
proxy_handler_instance = CustomRouterHandler()
