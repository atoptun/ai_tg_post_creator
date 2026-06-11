from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import Page, Params

from app.api.schemas import KeywordCreate, KeywordOut
from app.repositories.keywords import KeywordRepoDep


router = APIRouter(prefix="/keywords", tags=["Keywords"])


@router.get("/", response_model=Page[KeywordOut])
async def list_keywords(keyword_repo: KeywordRepoDep, params: Params = Depends()):
    """Get a paginated list of all keywords."""
    return await keyword_repo.get_paginated_list(params=params)


@router.post("/", response_model=KeywordOut, status_code=201)
async def create_keyword(body: KeywordCreate, keyword_repo: KeywordRepoDep):
    """Create a new keyword."""
    return await keyword_repo.create(**body.model_dump())


@router.get("/{keyword_id}", response_model=KeywordOut)
async def get_keyword(keyword_id: int, keyword_repo: KeywordRepoDep):
    """Get detailed information about a specific keyword by ID."""
    keyword = await keyword_repo.get_by_id(keyword_id)
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")
    return keyword


@router.delete("/{keyword_id}", status_code=204)
async def delete_keyword(keyword_id: int, keyword_repo: KeywordRepoDep):
    """Delete a keyword from the database."""
    keyword = await keyword_repo.get_by_id(keyword_id)
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")
    await keyword_repo.delete(keyword)
