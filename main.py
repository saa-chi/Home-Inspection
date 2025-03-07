import os
from typing import List, Optional
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import json
from pydantic import BaseModel
from prompt_templates import BLOG_IDEA_PROMPT

app = FastAPI(title="Property Inspection Report")

# Set up templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# CORS Middleware (for frontend API calls)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this to specific frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration for open-webui API
WEBUI_ENABLED = True
WEBUI_BASE_URL = "https://chat.ivislabs.in/api"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6ImVjNDdjZTIzLTQ4MjMtNDU5MS04ZWUzLTYwZDJjNzU4ZjYyZCJ9.ICZu_2n4nH1mrZr4KnHhNK2xUqPT0bFNZpZiPcy2HVA"  # 🔴 Manually set your API key here

# Default model
DEFAULT_MODEL = "gemma2:2b"

# Ollama API Configuration (Fallback)
OLLAMA_ENABLED = True
OLLAMA_HOST = "localhost"
OLLAMA_PORT = "11434"
OLLAMA_API_URL = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}/api"

class GenerationRequest(BaseModel):
    niche: str
    property_age: Optional[str] = "Unknown"
    past_renovations: Optional[str] = "None"
    known_issues: Optional[str] = "None"
    num_ideas: int = 3
    include_outline: bool = True
    tone: Optional[str] = "professional"

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate")
async def generate_ideas(
    niche: str = Form(...),
    property_age: str = Form("Unknown"),
    past_renovations: str = Form("None"),
    known_issues: str = Form("None"),
    num_ideas: str = Form("3"),  # Receive as string
    include_outline: bool = Form(True),
    tone: str = Form("professional"),
    model: str = Form(DEFAULT_MODEL)
):
    try:
        num_ideas = int(num_ideas)  # Ensure num_ideas is an integer
        # valid_niche = {"residential", "commercial", "industrial", "real estate", "rental", "building inspection"}
        valid_niche = {"residential", "commercial", "industrial", "real estate", "rental", "building inspection","vacant land","mixed-use","hospitality","agricultural"}

        if niche.lower() not in valid_niche:
            raise HTTPException(status_code=400, detail=f"Invalid niche '{niche}'. Please choose from {', '.join(valid_niche)}.")

        # Build the prompt with additional details
        prompt = BLOG_IDEA_PROMPT.format(
            niche=niche,
            property_age=property_age,
            past_renovations=past_renovations,
            known_issues=known_issues,
            num_ideas=num_ideas,
            include_outline="with detailed outlines" if include_outline else "without outlines",
            tone=tone
        )

        # Try Open-WebUI API first
        if WEBUI_ENABLED and API_KEY:
            try:
                messages = [{"role": "user", "content": prompt}]
                request_payload = {"model": model, "messages": messages}

                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{WEBUI_BASE_URL}/chat/completions",
                        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
                        json=request_payload,
                        timeout=60.0
                    )

                if response.status_code == 200:
                    result = response.json()
                    generated_text = (
                        result.get("choices", [{}])[0].get("message", {}).get("content", "") or
                        result.get("choices", [{}])[0].get("text", "") or
                        result.get("response", "")
                    )

                    if generated_text:
                        return {"generated_ideas": generated_text}
            except Exception as e:
                print(f"Open-WebUI API error: {str(e)}")

        # Fallback to Ollama API
        if OLLAMA_ENABLED:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{OLLAMA_API_URL}/generate",
                        json={"model": model, "prompt": prompt, "stream": False},
                        timeout=60.0
                    )

                if response.status_code == 200:
                    result = response.json()
                    generated_text = result.get("response", "")

                    if generated_text:
                        return {"generated_ideas": generated_text}
            except Exception as e:
                print(f"Ollama API error: {str(e)}")

        raise HTTPException(status_code=500, detail="Failed to generate content from any available LLM API")

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid number format for num_ideas")
    except Exception as e:
        import traceback
        print(f"Error generating ideas: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error generating ideas: {str(e)}")

@app.get("/models")
async def get_models():
    try:
        if WEBUI_ENABLED and API_KEY:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{WEBUI_BASE_URL}/models",
                        headers={"Authorization": f"Bearer {API_KEY}"}
                    )

                if response.status_code == 200:
                    models_data = response.json()
                    model_names = [model["id"] for model in models_data.get("data", []) if "id" in model]

                    if model_names:
                        return {"models": model_names}
            except Exception as e:
                print(f"Error fetching models from Open-WebUI API: {str(e)}")

        return {"models": [DEFAULT_MODEL, "gemma2:2b", "qwen2.5:0.5b", "deepseek-r1:1.5b", "deepseek-coder:latest"]}
    except Exception as e:
        print(f"Unexpected error in get_models: {str(e)}")
        return {"models": [DEFAULT_MODEL]}
