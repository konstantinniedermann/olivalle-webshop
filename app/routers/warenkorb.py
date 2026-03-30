from fastapi import APIRouter, Request

from app.templating import templates

router = APIRouter()


@router.get("/warenkorb")
def warenkorb(request: Request):
    return templates.TemplateResponse(
        request, "warenkorb.html", {"active_page": "warenkorb"}
    )
