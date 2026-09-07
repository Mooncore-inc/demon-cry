from fastapi import APIRouter, HTTPException

from demon_cry.api.dependencies import LLMRepo
from demon_cry.api.schemas.llm_models import LLMModelResponse, LLMModelCreate, LLMModelUpdate

llm_models_router = APIRouter(prefix="/llm-models")


@llm_models_router.get("/", response_model=list[LLMModelResponse])
async def get_all_models(llm_repo: LLMRepo):
    return await llm_repo.get_all()


@llm_models_router.get("/{model_name}", response_model=LLMModelResponse)
async def get_model(model_name: str, llm_repo: LLMRepo):
    model = await llm_repo.get(model_name=model_name)
    if not model:
        raise HTTPException(status_code=404, detail="LLM model not found")
    return model


@llm_models_router.post("/", response_model=LLMModelResponse, status_code=201)
async def create_model(body: LLMModelCreate, llm_repo: LLMRepo):
    existing = await llm_repo.get(model_name=body.model_name)
    if existing:
        raise HTTPException(status_code=409, detail="Model with this name already exists")
    return await llm_repo.create(**body.model_dump())


@llm_models_router.patch("/{model_name}", response_model=LLMModelResponse)
async def update_model(model_name: str, body: LLMModelUpdate, llm_repo: LLMRepo):
    model = await llm_repo.get(model_name=model_name)
    if not model:
        raise HTTPException(status_code=404, detail="LLM model not found")
    return await llm_repo.update(model, **body.model_dump(exclude_unset=True))


@llm_models_router.delete("/{model_name}", status_code=204)
async def delete_model(model_name: str, llm_repo: LLMRepo):
    model = await llm_repo.get(model_name=model_name)
    if not model:
        raise HTTPException(status_code=404, detail="LLM model not found")
    await llm_repo.delete(model)
