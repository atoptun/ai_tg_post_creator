from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import Page, Params

from app.api.schemas import SourceCreate, SourceUpdate, SourceOut
from app.repositories.source import SourceRepoDep


router = APIRouter(prefix="/sources", tags=["Sources"])


@router.get("/", response_model=Page[SourceOut])
async def list_sources(source_repo: SourceRepoDep, params: Params = Depends()):
    """Get a paginated list of all active/inactive sources."""
    return await source_repo.get_paginated_list(params=params)


@router.post("/", response_model=SourceOut, status_code=201)
async def create_source(body: SourceCreate, source_repo: SourceRepoDep):
    """Create a new tracking source (Website or Telegram channel)."""
    return await source_repo.create(body)


@router.get("/{source_id}", response_model=SourceOut)
async def get_source(source_id: int, source_repo: SourceRepoDep):
    """Get detailed information about a specific source by ID."""
    source = await source_repo.get_by_id(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return source


@router.patch("/{source_id}", response_model=SourceOut)
async def update_source(source_id: int, body: SourceUpdate, source_repo: SourceRepoDep):
    """Partially update source configuration fields."""
    source = await source_repo.get_by_id(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return await source_repo.update(source, body)


@router.delete("/{source_id}", status_code=204)
async def delete_source(source_id: int, source_repo: SourceRepoDep):
    """Delete a source from the tracking registry."""
    source = await source_repo.get_by_id(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    await source_repo.delete(source)


