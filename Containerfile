FROM ghcr.io/berriai/litellm:main-latest

RUN pip install semantic_router semantic-router[fastembed]
