import asyncio
import hashlib
import json
import logging
from pathlib import Path
from typing import Literal, Optional, overload

import aiohttp
from aiocache import cached
import requests


from fastapi import Depends, FastAPI, HTTPException, Request, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from starlette.background import BackgroundTask

from open_webui.models.models import Models
from open_webui.config import (
    CACHE_DIR,
)
from open_webui.env import (
    AIOHTTP_CLIENT_SESSION_SSL,
    AIOHTTP_CLIENT_TIMEOUT,
    AIOHTTP_CLIENT_TIMEOUT_MODEL_LIST,
    ENABLE_FORWARD_USER_INFO_HEADERS,
    BYPASS_MODEL_ACCESS_CONTROL,
)
from open_webui.models.users import UserModel

from open_webui.constants import ERROR_MESSAGES
from open_webui.env import ENV, SRC_LOG_LEVELS


from open_webui.utils.payload import (
    apply_model_params_to_body_openai,
    apply_model_system_prompt_to_body,
)
from open_webui.utils.misc import (
    convert_logit_bias_input_to_json,
)

from open_webui.utils.auth import get_admin_user, get_verified_user
from open_webui.utils.access_control import has_access
from open_webui.utils.schema_validation import validate_json_schema, convert_to_openai_schema
from open_webui.models.prompts import Prompts


log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["OPENAI"])


##########################################
#
# Utility functions
#
##########################################


async def send_get_request(url, key=None, user: UserModel = None):
    timeout = aiohttp.ClientTimeout(total=AIOHTTP_CLIENT_TIMEOUT_MODEL_LIST)
    try:
        async with aiohttp.ClientSession(timeout=timeout, trust_env=True) as session:
            async with session.get(
                url,
                headers={
                    **({"Authorization": f"Bearer {key}"} if key else {}),
                    **(
                        {
                            "X-OpenWebUI-User-Name": user.name,
                            "X-OpenWebUI-User-Id": user.id,
                            "X-OpenWebUI-User-Email": user.email,
                            "X-OpenWebUI-User-Role": user.role,
                        }
                        if ENABLE_FORWARD_USER_INFO_HEADERS and user
                        else {}
                    ),
                },
                ssl=AIOHTTP_CLIENT_SESSION_SSL,
            ) as response:
                return await response.json()
    except Exception as e:
        # Handle connection error here
        log.error(f"Connection error: {e}")
        return None


async def cleanup_response(
    response: Optional[aiohttp.ClientResponse],
    session: Optional[aiohttp.ClientSession],
):
    if response:
        response.close()
    if session:
        await session.close()


def openai_o_series_handler(payload):
    """
    Handle "o" series specific parameters
    """
    if "max_tokens" in payload:
        # Convert "max_tokens" to "max_completion_tokens" for all o-series models
        payload["max_completion_tokens"] = payload["max_tokens"]
        del payload["max_tokens"]

    # Handle system role conversion based on model type
    if payload["messages"][0]["role"] == "system":
        model_lower = payload["model"].lower()
        # Legacy models use "user" role instead of "system"
        if model_lower.startswith("o1-mini") or model_lower.startswith("o1-preview"):
            payload["messages"][0]["role"] = "user"
        else:
            payload["messages"][0]["role"] = "developer"

    return payload


##########################################
#
# API routes
#
##########################################

router = APIRouter()


@router.get("/config")
async def get_config(request: Request, user=Depends(get_admin_user)):
    return {
        "ENABLE_OPENAI_API": request.app.state.config.ENABLE_OPENAI_API,
        "OPENAI_API_BASE_URLS": request.app.state.config.OPENAI_API_BASE_URLS,
        "OPENAI_API_KEYS": request.app.state.config.OPENAI_API_KEYS,
        "OPENAI_API_CONFIGS": request.app.state.config.OPENAI_API_CONFIGS,
    }


class OpenAIConfigForm(BaseModel):
    ENABLE_OPENAI_API: Optional[bool] = None
    OPENAI_API_BASE_URLS: list[str]
    OPENAI_API_KEYS: list[str]
    OPENAI_API_CONFIGS: dict


@router.post("/config/update")
async def update_config(
    request: Request, form_data: OpenAIConfigForm, user=Depends(get_admin_user)
):
    request.app.state.config.ENABLE_OPENAI_API = form_data.ENABLE_OPENAI_API
    request.app.state.config.OPENAI_API_BASE_URLS = form_data.OPENAI_API_BASE_URLS
    request.app.state.config.OPENAI_API_KEYS = form_data.OPENAI_API_KEYS

    # Check if API KEYS length is same than API URLS length
    if len(request.app.state.config.OPENAI_API_KEYS) != len(
        request.app.state.config.OPENAI_API_BASE_URLS
    ):
        if len(request.app.state.config.OPENAI_API_KEYS) > len(
            request.app.state.config.OPENAI_API_BASE_URLS
        ):
            request.app.state.config.OPENAI_API_KEYS = (
                request.app.state.config.OPENAI_API_KEYS[
                    : len(request.app.state.config.OPENAI_API_BASE_URLS)
                ]
            )
        else:
            request.app.state.config.OPENAI_API_KEYS += [""] * (
                len(request.app.state.config.OPENAI_API_BASE_URLS)
                - len(request.app.state.config.OPENAI_API_KEYS)
            )

    request.app.state.config.OPENAI_API_CONFIGS = form_data.OPENAI_API_CONFIGS

    # Remove the API configs that are not in the API URLS
    keys = list(map(str, range(len(request.app.state.config.OPENAI_API_BASE_URLS))))
    request.app.state.config.OPENAI_API_CONFIGS = {
        key: value
        for key, value in request.app.state.config.OPENAI_API_CONFIGS.items()
        if key in keys
    }

    return {
        "ENABLE_OPENAI_API": request.app.state.config.ENABLE_OPENAI_API,
        "OPENAI_API_BASE_URLS": request.app.state.config.OPENAI_API_BASE_URLS,
        "OPENAI_API_KEYS": request.app.state.config.OPENAI_API_KEYS,
        "OPENAI_API_CONFIGS": request.app.state.config.OPENAI_API_CONFIGS,
    }


@router.post("/audio/speech")
async def speech(request: Request, user=Depends(get_verified_user)):
    idx = None
    try:
        idx = request.app.state.config.OPENAI_API_BASE_URLS.index(
            "https://api.openai.com/v1"
        )

        body = await request.body()
        name = hashlib.sha256(body).hexdigest()

        SPEECH_CACHE_DIR = CACHE_DIR / "audio" / "speech"
        SPEECH_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        file_path = SPEECH_CACHE_DIR.joinpath(f"{name}.mp3")
        file_body_path = SPEECH_CACHE_DIR.joinpath(f"{name}.json")

        # Check if the file already exists in the cache
        if file_path.is_file():
            return FileResponse(file_path)

        url = request.app.state.config.OPENAI_API_BASE_URLS[idx]

        r = None
        try:
            r = requests.post(
                url=f"{url}/audio/speech",
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {request.app.state.config.OPENAI_API_KEYS[idx]}",
                    **(
                        {
                            "HTTP-Referer": "https://openwebui.com/",
                            "X-Title": "Open WebUI",
                        }
                        if "openrouter.ai" in url
                        else {}
                    ),
                    **(
                        {
                            "X-OpenWebUI-User-Name": user.name,
                            "X-OpenWebUI-User-Id": user.id,
                            "X-OpenWebUI-User-Email": user.email,
                            "X-OpenWebUI-User-Role": user.role,
                        }
                        if ENABLE_FORWARD_USER_INFO_HEADERS
                        else {}
                    ),
                },
                stream=True,
            )

            r.raise_for_status()

            # Save the streaming content to a file
            with open(file_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

            with open(file_body_path, "w") as f:
                json.dump(json.loads(body.decode("utf-8")), f)

            # Return the saved file
            return FileResponse(file_path)

        except Exception as e:
            log.exception(e)

            detail = None
            if r is not None:
                try:
                    res = r.json()
                    if "error" in res:
                        detail = f"External: {res['error']}"
                except Exception:
                    detail = f"External: {e}"

            raise HTTPException(
                status_code=r.status_code if r else 500,
                detail=detail if detail else "Open WebUI: Server Connection Error",
            )

    except ValueError:
        raise HTTPException(status_code=401, detail=ERROR_MESSAGES.OPENAI_NOT_FOUND)


async def get_all_models_responses(request: Request, user: UserModel) -> list:
    if not request.app.state.config.ENABLE_OPENAI_API:
        return []

    # Check if API KEYS length is same than API URLS length
    num_urls = len(request.app.state.config.OPENAI_API_BASE_URLS)
    num_keys = len(request.app.state.config.OPENAI_API_KEYS)

    if num_keys != num_urls:
        # if there are more keys than urls, remove the extra keys
        if num_keys > num_urls:
            new_keys = request.app.state.config.OPENAI_API_KEYS[:num_urls]
            request.app.state.config.OPENAI_API_KEYS = new_keys
        # if there are more urls than keys, add empty keys
        else:
            request.app.state.config.OPENAI_API_KEYS += [""] * (num_urls - num_keys)

    request_tasks = []
    for idx, url in enumerate(request.app.state.config.OPENAI_API_BASE_URLS):
        if (str(idx) not in request.app.state.config.OPENAI_API_CONFIGS) and (
            url not in request.app.state.config.OPENAI_API_CONFIGS  # Legacy support
        ):
            request_tasks.append(
                send_get_request(
                    f"{url}/models",
                    request.app.state.config.OPENAI_API_KEYS[idx],
                    user=user,
                )
            )
        else:
            api_config = request.app.state.config.OPENAI_API_CONFIGS.get(
                str(idx),
                request.app.state.config.OPENAI_API_CONFIGS.get(
                    url, {}
                ),  # Legacy support
            )

            enable = api_config.get("enable", True)
            model_ids = api_config.get("model_ids", [])

            if enable:
                if len(model_ids) == 0:
                    request_tasks.append(
                        send_get_request(
                            f"{url}/models",
                            request.app.state.config.OPENAI_API_KEYS[idx],
                            user=user,
                        )
                    )
                else:
                    model_list = {
                        "object": "list",
                        "data": [
                            {
                                "id": model_id,
                                "name": model_id,
                                "owned_by": "openai",
                                "openai": {"id": model_id},
                                "urlIdx": idx,
                            }
                            for model_id in model_ids
                        ],
                    }

                    request_tasks.append(
                        asyncio.ensure_future(asyncio.sleep(0, model_list))
                    )
            else:
                request_tasks.append(asyncio.ensure_future(asyncio.sleep(0, None)))

    responses = await asyncio.gather(*request_tasks)

    for idx, response in enumerate(responses):
        if response:
            url = request.app.state.config.OPENAI_API_BASE_URLS[idx]
            api_config = request.app.state.config.OPENAI_API_CONFIGS.get(
                str(idx),
                request.app.state.config.OPENAI_API_CONFIGS.get(
                    url, {}
                ),  # Legacy support
            )

            connection_type = api_config.get("connection_type", "external")
            prefix_id = api_config.get("prefix_id", None)
            tags = api_config.get("tags", [])

            for model in (
                response if isinstance(response, list) else response.get("data", [])
            ):
                if prefix_id:
                    model["id"] = f"{prefix_id}.{model['id']}"

                if tags:
                    model["tags"] = tags

                if connection_type:
                    model["connection_type"] = connection_type

    log.debug(f"get_all_models:responses() {responses}")
    return responses


async def get_filtered_models(models, user):
    # Filter models based on user access control
    filtered_models = []
    for model in models.get("data", []):
        model_info = Models.get_model_by_id(model["id"])
        if model_info:
            if user.id == model_info.user_id or has_access(
                user.id, type="read", access_control=model_info.access_control
            ):
                filtered_models.append(model)
    return filtered_models


@cached(ttl=1)
async def get_all_models(request: Request, user: UserModel) -> dict[str, list]:
    log.info("get_all_models()")

    if not request.app.state.config.ENABLE_OPENAI_API:
        return {"data": []}

    responses = await get_all_models_responses(request, user=user)

    def extract_data(response):
        if response and "data" in response:
            return response["data"]
        if isinstance(response, list):
            return response
        return None

    def merge_models_lists(model_lists):
        log.debug(f"merge_models_lists {model_lists}")
        merged_list = []

        for idx, models in enumerate(model_lists):
            if models is not None and "error" not in models:

                merged_list.extend(
                    [
                        {
                            **model,
                            "name": model.get("name", model["id"]),
                            "owned_by": "openai",
                            "openai": model,
                            "connection_type": model.get("connection_type", "external"),
                            "urlIdx": idx,
                        }
                        for model in models
                        if (model.get("id") or model.get("name"))
                        and (
                            "api.openai.com"
                            not in request.app.state.config.OPENAI_API_BASE_URLS[idx]
                            or not any(
                                name in model["id"]
                                for name in [
                                    "babbage",
                                    "dall-e",
                                    "davinci",
                                    "embedding",
                                    "tts",
                                    "whisper",
                                ]
                            )
                        )
                    ]
                )

        return merged_list

    models = {"data": merge_models_lists(map(extract_data, responses))}
    log.debug(f"models: {models}")

    request.app.state.OPENAI_MODELS = {model["id"]: model for model in models["data"]}
    return models


@router.get("/models")
@router.get("/models/{url_idx}")
async def get_models(
    request: Request, url_idx: Optional[int] = None, user=Depends(get_verified_user)
):
    models = {
        "data": [],
    }

    if url_idx is None:
        models = await get_all_models(request, user=user)
    else:
        url = request.app.state.config.OPENAI_API_BASE_URLS[url_idx]
        key = request.app.state.config.OPENAI_API_KEYS[url_idx]

        api_config = request.app.state.config.OPENAI_API_CONFIGS.get(
            str(url_idx),
            request.app.state.config.OPENAI_API_CONFIGS.get(url, {}),  # Legacy support
        )

        r = None
        async with aiohttp.ClientSession(
            trust_env=True,
            timeout=aiohttp.ClientTimeout(total=AIOHTTP_CLIENT_TIMEOUT_MODEL_LIST),
        ) as session:
            try:
                headers = {
                    "Content-Type": "application/json",
                    **(
                        {
                            "X-OpenWebUI-User-Name": user.name,
                            "X-OpenWebUI-User-Id": user.id,
                            "X-OpenWebUI-User-Email": user.email,
                            "X-OpenWebUI-User-Role": user.role,
                        }
                        if ENABLE_FORWARD_USER_INFO_HEADERS
                        else {}
                    ),
                }

                if api_config.get("azure", False):
                    models = {
                        "data": api_config.get("model_ids", []) or [],
                        "object": "list",
                    }
                else:
                    headers["Authorization"] = f"Bearer {key}"

                    async with session.get(
                        f"{url}/models",
                        headers=headers,
                        ssl=AIOHTTP_CLIENT_SESSION_SSL,
                    ) as r:
                        if r.status != 200:
                            # Extract response error details if available
                            error_detail = f"HTTP Error: {r.status}"
                            res = await r.json()
                            if "error" in res:
                                error_detail = f"External Error: {res['error']}"
                            raise Exception(error_detail)

                        response_data = await r.json()

                        # Check if we're calling OpenAI API based on the URL
                        if "api.openai.com" in url:
                            # Filter models according to the specified conditions
                            response_data["data"] = [
                                model
                                for model in response_data.get("data", [])
                                if not any(
                                    name in model["id"]
                                    for name in [
                                        "babbage",
                                        "dall-e",
                                        "davinci",
                                        "embedding",
                                        "tts",
                                        "whisper",
                                    ]
                                )
                            ]

                        models = response_data
            except aiohttp.ClientError as e:
                # ClientError covers all aiohttp requests issues
                log.exception(f"Client error: {str(e)}")
                raise HTTPException(
                    status_code=500, detail="Open WebUI: Server Connection Error"
                )
            except Exception as e:
                log.exception(f"Unexpected error: {e}")
                error_detail = f"Unexpected error: {str(e)}"
                raise HTTPException(status_code=500, detail=error_detail)

    if user.role == "user" and not BYPASS_MODEL_ACCESS_CONTROL:
        models["data"] = await get_filtered_models(models, user)

    return models


class ConnectionVerificationForm(BaseModel):
    url: str
    key: str

    config: Optional[dict] = None


@router.post("/verify")
async def verify_connection(
    form_data: ConnectionVerificationForm, user=Depends(get_admin_user)
):
    url = form_data.url
    key = form_data.key

    api_config = form_data.config or {}

    async with aiohttp.ClientSession(
        trust_env=True,
        timeout=aiohttp.ClientTimeout(total=AIOHTTP_CLIENT_TIMEOUT_MODEL_LIST),
    ) as session:
        try:
            headers = {
                "Content-Type": "application/json",
                **(
                    {
                        "X-OpenWebUI-User-Name": user.name,
                        "X-OpenWebUI-User-Id": user.id,
                        "X-OpenWebUI-User-Email": user.email,
                        "X-OpenWebUI-User-Role": user.role,
                    }
                    if ENABLE_FORWARD_USER_INFO_HEADERS
                    else {}
                ),
            }

            if api_config.get("azure", False):
                headers["api-key"] = key
                api_version = api_config.get("api_version", "") or "2023-03-15-preview"

                async with session.get(
                    url=f"{url}/openai/models?api-version={api_version}",
                    headers=headers,
                    ssl=AIOHTTP_CLIENT_SESSION_SSL,
                ) as r:
                    if r.status != 200:
                        # Extract response error details if available
                        error_detail = f"HTTP Error: {r.status}"
                        res = await r.json()
                        if "error" in res:
                            error_detail = f"External Error: {res['error']}"
                        raise Exception(error_detail)

                    response_data = await r.json()
                    return response_data
            else:
                headers["Authorization"] = f"Bearer {key}"

                async with session.get(
                    f"{url}/models",
                    headers=headers,
                    ssl=AIOHTTP_CLIENT_SESSION_SSL,
                ) as r:
                    if r.status != 200:
                        # Extract response error details if available
                        error_detail = f"HTTP Error: {r.status}"
                        res = await r.json()
                        if "error" in res:
                            error_detail = f"External Error: {res['error']}"
                        raise Exception(error_detail)

                    response_data = await r.json()
                    return response_data

        except aiohttp.ClientError as e:
            # ClientError covers all aiohttp requests issues
            log.exception(f"Client error: {str(e)}")
            raise HTTPException(
                status_code=500, detail="Open WebUI: Server Connection Error"
            )
        except Exception as e:
            log.exception(f"Unexpected error: {e}")
            error_detail = f"Unexpected error: {str(e)}"
            raise HTTPException(status_code=500, detail=error_detail)


def convert_to_azure_payload(
    url,
    payload: dict,
):
    model = payload.get("model", "")

    # Filter allowed parameters based on Azure OpenAI API
    allowed_params = {
        "messages",
        "temperature",
        "role",
        "content",
        "contentPart",
        "contentPartImage",
        "enhancements",
        "dataSources",
        "n",
        "stream",
        "stop",
        "max_tokens",
        "presence_penalty",
        "frequency_penalty",
        "logit_bias",
        "user",
        "function_call",
        "functions",
        "tools",
        "tool_choice",
        "top_p",
        "log_probs",
        "top_logprobs",
        "response_format",
        "seed",
        "max_completion_tokens",
    }

    # Special handling for o-series models
    if model.startswith("o") and model.endswith("-mini"):
        # Convert max_tokens to max_completion_tokens for o-series models
        if "max_tokens" in payload:
            payload["max_completion_tokens"] = payload["max_tokens"]
            del payload["max_tokens"]

        # Remove temperature if not 1 for o-series models
        if "temperature" in payload and payload["temperature"] != 1:
            log.debug(
                f"Removing temperature parameter for o-series model {model} as only default value (1) is supported"
            )
            del payload["temperature"]

    # Filter out unsupported parameters
    payload = {k: v for k, v in payload.items() if k in allowed_params}

    url = f"{url}/openai/deployments/{model}"
    return url, payload


@router.post("/chat/completions")
async def generate_chat_completion(
    request: Request,
    form_data: dict,
    user=Depends(get_verified_user),
    bypass_filter: Optional[bool] = False,
):
    if BYPASS_MODEL_ACCESS_CONTROL:
        bypass_filter = True

    idx = 0

    payload = {**form_data}
    metadata = payload.pop("metadata", None)

    model_id = form_data.get("model")
    model_info = Models.get_model_by_id(model_id)

    # Check model info and override the payload
    if model_info:
        if model_info.base_model_id:
            payload["model"] = model_info.base_model_id
            model_id = model_info.base_model_id

        params = model_info.params.model_dump()

        if params:
            system = params.pop("system", None)

            payload = apply_model_params_to_body_openai(params, payload)
            payload = apply_model_system_prompt_to_body(system, payload, metadata, user)

        # Check if user has access to the model
        if not bypass_filter and user.role == "user":
            if not (
                user.id == model_info.user_id
                or has_access(
                    user.id, type="read", access_control=model_info.access_control
                )
            ):
                raise HTTPException(
                    status_code=403,
                    detail="Model not found",
                )
    elif not bypass_filter:
        if user.role != "admin":
            raise HTTPException(
                status_code=403,
                detail="Model not found",
            )

    await get_all_models(request, user=user)
    model = request.app.state.OPENAI_MODELS.get(model_id)
    if model:
        idx = model["urlIdx"]
    else:
        raise HTTPException(
            status_code=404,
            detail="Model not found",
        )

    # Get the API config for the model
    api_config = request.app.state.config.OPENAI_API_CONFIGS.get(
        str(idx),
        request.app.state.config.OPENAI_API_CONFIGS.get(
            request.app.state.config.OPENAI_API_BASE_URLS[idx], {}
        ),  # Legacy support
    )

    prefix_id = api_config.get("prefix_id", None)
    if prefix_id:
        payload["model"] = payload["model"].replace(f"{prefix_id}.", "")

    # Add user info to the payload if the model is a pipeline
    if "pipeline" in model and model.get("pipeline"):
        payload["user"] = {
            "name": user.name,
            "id": user.id,
            "email": user.email,
            "role": user.role,
        }

    url = request.app.state.config.OPENAI_API_BASE_URLS[idx]
    key = request.app.state.config.OPENAI_API_KEYS[idx]

    # Check if model is from "o" series
    is_o_series = payload["model"].lower().startswith(("o1", "o3", "o4"))
    if is_o_series:
        payload = openai_o_series_handler(payload)
    elif "api.openai.com" not in url:
        # Remove "max_completion_tokens" from the payload for backward compatibility
        if "max_completion_tokens" in payload:
            payload["max_tokens"] = payload["max_completion_tokens"]
            del payload["max_completion_tokens"]

    if "max_tokens" in payload and "max_completion_tokens" in payload:
        del payload["max_tokens"]

    # Handle system message override from attached prompt
    if metadata and metadata.get("system_message_override"):
        system_message_override = metadata.get("system_message_override")
        messages = payload.get("messages", [])
        
        # Find existing system message and replace it, or add new one at the beginning
        system_message_found = False
        for message in messages:
            if message.get("role") == "system":
                message["content"] = system_message_override
                system_message_found = True
                log.info(f"🔄 Replaced existing system message with attached prompt")
                break
        
        if not system_message_found:
            messages.insert(0, {
                "role": "system",
                "content": system_message_override
            })
            log.info(f"➕ Added system message from attached prompt")
        
        payload["messages"] = messages
        log.info(f"📋 Applied system message override from attached prompt: {system_message_override[:100]}...")

    # Check for prompt usage and apply structured output configuration
    if metadata:
        prompt_command = metadata.get("prompt_command")
        if prompt_command:
            # Get prompt configuration
            prompt = Prompts.get_prompt_by_command(prompt_command)
            if prompt and prompt.structured_output:
                # Apply prompt's structured output configuration to metadata
                metadata["structured_output"] = True
                if prompt.structured_output_schema:
                    metadata["structured_output_schema"] = prompt.structured_output_schema
                log.info(f"Applied structured output from prompt '{prompt_command}': {prompt.structured_output}")

    # Handle structured output for OpenAI models
    structured_output_enabled = metadata and metadata.get("structured_output", False) is True
    structured_output_schema = metadata and metadata.get("structured_output_schema")
    
    log.info(f"🔍 Structured Output Debug: enabled={structured_output_enabled}, has_schema={bool(structured_output_schema)}, schema_length={len(structured_output_schema) if structured_output_schema else 0}")
    
    if structured_output_enabled:
        # Only apply structured output for OpenAI API endpoints (including compatible ones)
        is_openai_compatible = any([
            "api.openai.com" in url,
            "openai" in url.lower(),
        ])
        
        log.info(f"🔍 OpenAI Compatible: {is_openai_compatible} for URL: {url}")
        
        if is_openai_compatible:
            # Check if we have a valid schema to use
            if structured_output_schema:
                try:
                    log.info(f"🔍 Processing structured output schema: {structured_output_schema[:200]}...")
                    is_valid, error_msg, parsed_schema = validate_json_schema(structured_output_schema)
                    log.info(f"🔍 Schema validation result: valid={is_valid}, error={error_msg}")
                    
                    if is_valid and parsed_schema:
                        # Use structured output with schema
                        openai_schema = convert_to_openai_schema(parsed_schema, "response")
                        payload["response_format"] = openai_schema
                        log.info(f"✅ Applied structured output schema: {openai_schema}")
                        
                        # Add schema instruction to system message for better compliance
                        messages = payload.get("messages", [])
                        schema_instruction = f"\n\nIMPORTANT: Please respond with valid JSON that matches this schema:\n{json.dumps(parsed_schema, indent=2)}"
                        
                        # Find or create system message
                        system_message_found = False
                        for message in messages:
                            if message.get("role") == "system":
                                message["content"] += schema_instruction
                                system_message_found = True
                                break
                        
                        if not system_message_found:
                            messages.insert(0, {
                                "role": "system", 
                                "content": f"You are a helpful assistant.{schema_instruction}"
                            })
                        
                        payload["messages"] = messages
                    else:
                        log.warning(f"⚠️ Invalid schema for structured output: {error_msg}")
                        # Fallback to basic JSON object format
                        payload["response_format"] = {"type": "json_object"}
                        log.info(f"🔄 Using fallback JSON object format")
                except Exception as e:
                    log.error(f"❌ Error processing structured output schema: {e}", exc_info=True)
                    # Fallback to basic JSON object format
                    payload["response_format"] = {"type": "json_object"}
                    log.info(f"🔄 Using fallback JSON object format due to error")
            else:
                # No schema provided, use basic JSON object format
                payload["response_format"] = {"type": "json_object"}
                log.info(f"🔄 No schema provided, using basic JSON object format")
            
            # Ensure system message instructs JSON output (for compatibility)
            messages = payload.get("messages", [])
            system_message_updated = False
            
            for message in messages:
                if message.get("role") == "system":
                    content = message.get("content", "")
                    if "json" not in content.lower() and "JSON" not in content:
                        message["content"] = content + "\n\nPlease format your response as valid JSON."
                    system_message_updated = True
                    break
            
            # Add system message if none exists
            if not system_message_updated:
                messages.insert(0, {
                    "role": "system",
                    "content": "Please format your response as valid JSON."
                })
                payload["messages"] = messages
    else:
        # Explicitly ensure no response_format is passed when structured output is disabled
        payload.pop("response_format", None)

    # Convert the modified body back to JSON
    if "logit_bias" in payload:
        payload["logit_bias"] = json.loads(
            convert_logit_bias_input_to_json(payload["logit_bias"])
        )

    headers = {
        "Content-Type": "application/json",
        **(
            {
                "HTTP-Referer": "https://openwebui.com/",
                "X-Title": "Open WebUI",
            }
            if "openrouter.ai" in url
            else {}
        ),
        **(
            {
                "X-OpenWebUI-User-Name": user.name,
                "X-OpenWebUI-User-Id": user.id,
                "X-OpenWebUI-User-Email": user.email,
                "X-OpenWebUI-User-Role": user.role,
            }
            if ENABLE_FORWARD_USER_INFO_HEADERS
            else {}
        ),
    }

    if api_config.get("azure", False):
        request_url, payload = convert_to_azure_payload(url, payload)
        api_version = api_config.get("api_version", "") or "2023-03-15-preview"
        headers["api-key"] = key
        headers["api-version"] = api_version
        request_url = f"{request_url}/chat/completions?api-version={api_version}"
    else:
        request_url = f"{url}/chat/completions"
        headers["Authorization"] = f"Bearer {key}"

    # Log the final payload before sending to OpenAI (but mask sensitive data)
    payload_debug = payload.copy()
    if "messages" in payload_debug:
        payload_debug["messages"] = f"[{len(payload_debug['messages'])} messages]"
    log.info(f"🚀 Final OpenAI payload: {payload_debug}")
    
    payload = json.dumps(payload)

    r = None
    session = None
    streaming = False
    response = None

    try:
        session = aiohttp.ClientSession(
            trust_env=True, timeout=aiohttp.ClientTimeout(total=AIOHTTP_CLIENT_TIMEOUT)
        )

        r = await session.request(
            method="POST",
            url=request_url,
            data=payload,
            headers=headers,
            ssl=AIOHTTP_CLIENT_SESSION_SSL,
        )

        # Check if response is SSE
        if "text/event-stream" in r.headers.get("Content-Type", ""):
            streaming = True
            return StreamingResponse(
                r.content,
                status_code=r.status,
                headers=dict(r.headers),
                background=BackgroundTask(
                    cleanup_response, response=r, session=session
                ),
            )
        else:
            try:
                response = await r.json()
            except Exception as e:
                log.error(e)
                response = await r.text()

            r.raise_for_status()
            return response
    except Exception as e:
        log.exception(e)

        detail = None
        if isinstance(response, dict):
            if "error" in response:
                detail = f"{response['error']['message'] if 'message' in response['error'] else response['error']}"
        elif isinstance(response, str):
            detail = response

        # Check if this is a structured output related error
        if (r and r.status == 400 and 
            structured_output_enabled and 
            "response_format" in payload_debug and
            detail and "json_schema" in str(detail).lower()):
            
            log.warning(f"🔄 Structured output request failed, retrying with basic JSON format: {detail}")
            
            # Retry with basic JSON object format
            try:
                # Rebuild the payload without structured output schema
                retry_payload = json.loads(payload)
                retry_payload["response_format"] = {"type": "json_object"}
                
                log.info(f"🔄 Retrying with basic JSON object format")
                
                # Retry the request
                retry_session = aiohttp.ClientSession(
                    trust_env=True, timeout=aiohttp.ClientTimeout(total=AIOHTTP_CLIENT_TIMEOUT)
                )
                
                retry_r = await retry_session.request(
                    method="POST",
                    url=request_url,
                    data=json.dumps(retry_payload),
                    headers=headers,
                    ssl=AIOHTTP_CLIENT_SESSION_SSL,
                )
                
                # Check if retry succeeded
                if retry_r.status == 200 or "text/event-stream" in retry_r.headers.get("Content-Type", ""):
                    log.info(f"✅ Retry with basic JSON format succeeded")
                    if "text/event-stream" in retry_r.headers.get("Content-Type", ""):
                        return StreamingResponse(
                            retry_r.content,
                            status_code=retry_r.status,
                            headers=dict(retry_r.headers),
                            background=BackgroundTask(
                                cleanup_response, response=retry_r, session=retry_session
                            ),
                        )
                    else:
                        retry_response = await retry_r.json()
                        retry_r.raise_for_status()
                        await retry_session.close()
                        return retry_response
                else:
                    await retry_session.close()
                    
            except Exception as retry_e:
                log.error(f"❌ Retry with basic JSON format also failed: {retry_e}")

        raise HTTPException(
            status_code=r.status if r else 500,
            detail=detail if detail else "Open WebUI: Server Connection Error",
        )
    finally:
        if not streaming and session:
            if r:
                r.close()
            await session.close()


async def embeddings(request: Request, form_data: dict, user):
    """
    Calls the embeddings endpoint for OpenAI-compatible providers.

    Args:
        request (Request): The FastAPI request context.
        form_data (dict): OpenAI-compatible embeddings payload.
        user (UserModel): The authenticated user.

    Returns:
        dict: OpenAI-compatible embeddings response.
    """
    idx = 0
    # Prepare payload/body
    body = json.dumps(form_data)
    # Find correct backend url/key based on model
    await get_all_models(request, user=user)
    model_id = form_data.get("model")
    models = request.app.state.OPENAI_MODELS
    if model_id in models:
        idx = models[model_id]["urlIdx"]
    url = request.app.state.config.OPENAI_API_BASE_URLS[idx]
    key = request.app.state.config.OPENAI_API_KEYS[idx]
    r = None
    session = None
    streaming = False
    try:
        session = aiohttp.ClientSession(trust_env=True)
        r = await session.request(
            method="POST",
            url=f"{url}/embeddings",
            data=body,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                **(
                    {
                        "X-OpenWebUI-User-Name": user.name,
                        "X-OpenWebUI-User-Id": user.id,
                        "X-OpenWebUI-User-Email": user.email,
                        "X-OpenWebUI-User-Role": user.role,
                    }
                    if ENABLE_FORWARD_USER_INFO_HEADERS and user
                    else {}
                ),
            },
        )
        r.raise_for_status()
        if "text/event-stream" in r.headers.get("Content-Type", ""):
            streaming = True
            return StreamingResponse(
                r.content,
                status_code=r.status,
                headers=dict(r.headers),
                background=BackgroundTask(
                    cleanup_response, response=r, session=session
                ),
            )
        else:
            response_data = await r.json()
            return response_data
    except Exception as e:
        log.exception(e)
        detail = None
        if r is not None:
            try:
                res = await r.json()
                if "error" in res:
                    detail = f"External: {res['error']['message'] if 'message' in res['error'] else res['error']}"
            except Exception:
                detail = f"External: {e}"
        raise HTTPException(
            status_code=r.status if r else 500,
            detail=detail if detail else "Open WebUI: Server Connection Error",
        )
    finally:
        if not streaming and session:
            if r:
                r.close()
            await session.close()


@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy(path: str, request: Request, user=Depends(get_verified_user)):
    """
    Deprecated: proxy all requests to OpenAI API
    """

    body = await request.body()

    idx = 0
    url = request.app.state.config.OPENAI_API_BASE_URLS[idx]
    key = request.app.state.config.OPENAI_API_KEYS[idx]
    api_config = request.app.state.config.OPENAI_API_CONFIGS.get(
        str(idx),
        request.app.state.config.OPENAI_API_CONFIGS.get(
            request.app.state.config.OPENAI_API_BASE_URLS[idx], {}
        ),  # Legacy support
    )

    r = None
    session = None
    streaming = False

    try:
        headers = {
            "Content-Type": "application/json",
            **(
                {
                    "X-OpenWebUI-User-Name": user.name,
                    "X-OpenWebUI-User-Id": user.id,
                    "X-OpenWebUI-User-Email": user.email,
                    "X-OpenWebUI-User-Role": user.role,
                }
                if ENABLE_FORWARD_USER_INFO_HEADERS
                else {}
            ),
        }

        if api_config.get("azure", False):
            headers["api-key"] = key
            headers["api-version"] = (
                api_config.get("api_version", "") or "2023-03-15-preview"
            )

            payload = json.loads(body)
            url, payload = convert_to_azure_payload(url, payload)
            body = json.dumps(payload).encode()

            request_url = f"{url}/{path}?api-version={api_config.get('api_version', '2023-03-15-preview')}"
        else:
            headers["Authorization"] = f"Bearer {key}"
            request_url = f"{url}/{path}"

        session = aiohttp.ClientSession(trust_env=True)
        r = await session.request(
            method=request.method,
            url=request_url,
            data=body,
            headers=headers,
            ssl=AIOHTTP_CLIENT_SESSION_SSL,
        )
        r.raise_for_status()

        # Check if response is SSE
        if "text/event-stream" in r.headers.get("Content-Type", ""):
            streaming = True
            return StreamingResponse(
                r.content,
                status_code=r.status,
                headers=dict(r.headers),
                background=BackgroundTask(
                    cleanup_response, response=r, session=session
                ),
            )
        else:
            response_data = await r.json()
            return response_data

    except Exception as e:
        log.exception(e)

        detail = None
        if r is not None:
            try:
                res = await r.json()
                log.error(res)
                if "error" in res:
                    detail = f"External: {res['error']['message'] if 'message' in res['error'] else res['error']}"
            except Exception:
                detail = f"External: {e}"
        raise HTTPException(
            status_code=r.status if r else 500,
            detail=detail if detail else "Open WebUI: Server Connection Error",
        )
    finally:
        if not streaming and session:
            if r:
                r.close()
            await session.close()
