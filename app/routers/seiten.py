from fastapi import APIRouter, Request

from app.templating import templates

router = APIRouter()


@router.get("/ueber-das-oel")
def ueber_das_oel(request: Request):
    return templates.TemplateResponse(
        request, "ueber-das-oel.html", {"active_page": "ueber-das-oel"}
    )


@router.get("/impressum")
def impressum(request: Request):
    return templates.TemplateResponse(request, "impressum.html")


@router.get("/datenschutz")
def datenschutz(request: Request):
    return templates.TemplateResponse(request, "datenschutz.html")


@router.get("/agb")
def agb(request: Request):
    return templates.TemplateResponse(request, "agb.html")
