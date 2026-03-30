from fastapi import APIRouter, Request

from app.templating import templates

router = APIRouter()


@router.get("/ueber-das-oel")
def ueber_das_oel(request: Request):
    return templates.TemplateResponse(
        request, "ueber-das-oel.html", {"active_page": "ueber-das-oel"}
    )
