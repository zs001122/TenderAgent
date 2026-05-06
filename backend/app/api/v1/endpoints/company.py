from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

from app.db.repository import get_company_repository, CompanyRepository
from app.services.company_excel_importer import CompanyExcelImporter


router = APIRouter()
_IMPORT_PREVIEWS: Dict[str, Dict[str, Any]] = {}


class CompanyProfileInput(BaseModel):
    name: Optional[str] = None
    target_domains: Optional[List[str]] = None
    budget_range: Optional[List[float]] = None
    qualifications: Optional[List[str]] = None
    service_regions: Optional[List[str]] = None
    bid_history: Optional[List[Dict[str, Any]]] = None


class CompanyImportResponse(BaseModel):
    batch_id: str
    company_name: str
    summary: Dict[str, Any]
    warnings: List[str]


class CompanyImportConfirmInput(BaseModel):
    preview_id: Optional[str] = None


class CompanyAssetInput(BaseModel):
    company_name: Optional[str] = None
    asset_type: str
    source_sheet: Optional[str] = "手工维护"
    name: str
    category: Optional[str] = None
    certificate_no: Optional[str] = None
    issuer: Optional[str] = None
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None
    status: Optional[str] = "有效"
    amount_wanyuan: Optional[float] = None
    keywords: Optional[List[str]] = None
    data: Optional[Dict[str, Any]] = None
    source_type: Optional[str] = None


class CompanyAssetDeleteInput(BaseModel):
    reason: Optional[str] = None


@router.get("/", response_model=Dict[str, Any])
def get_company_profile(
    repo: CompanyRepository = Depends(get_company_repository)
):
    """获取公司画像配置"""
    return repo.get_profile_dict()


@router.put("/", response_model=Dict[str, Any])
def update_company_profile(
    profile_data: CompanyProfileInput,
    repo: CompanyRepository = Depends(get_company_repository)
):
    """更新公司画像配置"""
    update_dict = profile_data.dict(exclude_unset=True)
    profile = repo.save_profile(update_dict)
    return repo.get_profile_dict()


@router.post("/import-excel/preview", response_model=Dict[str, Any])
async def import_company_excel(
    file: UploadFile = File(...),
):
    """解析公司资料 Excel，返回预览结果，不写入资料库。"""
    filename = file.filename or ""
    if not filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="仅支持 .xlsx 公司资料文件")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="上传文件为空")

    try:
        parsed = CompanyExcelImporter().parse(content)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Excel 解析失败: {exc}") from exc

    preview_id = parsed["batch_id"]
    _IMPORT_PREVIEWS[preview_id] = {
        **parsed,
        "filename": filename,
        "created_at": datetime.utcnow().isoformat(),
    }
    return {
        "preview_id": preview_id,
        "batch_id": parsed["batch_id"],
        "company_name": parsed.get("company_name", ""),
        "filename": filename,
        "summary": parsed["summary"],
        "warnings": parsed["warnings"],
        "assets_sample": parsed["assets"][:20],
    }


@router.post("/import-excel", response_model=CompanyImportResponse)
async def confirm_company_excel_import(
    payload: CompanyImportConfirmInput,
    repo: CompanyRepository = Depends(get_company_repository),
):
    """确认导入预览结果，并替换当前结构化资料库。"""
    if not payload.preview_id:
        raise HTTPException(status_code=400, detail="preview_id 不能为空")
    parsed = _IMPORT_PREVIEWS.get(payload.preview_id)
    if not parsed:
        raise HTTPException(status_code=404, detail="导入预览不存在或已过期，请重新上传")

    repo.replace_assets(parsed["assets"])
    repo.sync_profile_from_assets(parsed.get("company_name", ""))
    _IMPORT_PREVIEWS.pop(payload.preview_id, None)
    return CompanyImportResponse(
        batch_id=parsed["batch_id"],
        company_name=parsed.get("company_name", ""),
        summary=repo.get_asset_summary(),
        warnings=parsed["warnings"],
    )


@router.get("/assets", response_model=Dict[str, Any])
def list_company_assets(
    asset_type: Optional[str] = None,
    status: Optional[str] = None,
    source_sheet: Optional[str] = None,
    keyword: Optional[str] = None,
    include_deleted: bool = False,
    skip: int = 0,
    limit: int = 200,
    repo: CompanyRepository = Depends(get_company_repository),
):
    safe_skip = max(skip, 0)
    safe_limit = min(max(limit, 1), 500)
    return {
        "total": repo.count_assets(
            asset_type=asset_type,
            status=status,
            source_sheet=source_sheet,
            keyword=keyword,
            include_deleted=include_deleted,
        ),
        "skip": safe_skip,
        "limit": safe_limit,
        "items": repo.get_assets(
            asset_type=asset_type,
            status=status,
            source_sheet=source_sheet,
            keyword=keyword,
            include_deleted=include_deleted,
            skip=safe_skip,
            limit=safe_limit,
        ),
    }


@router.post("/assets", response_model=Dict[str, Any])
def create_company_asset(
    asset_data: CompanyAssetInput,
    repo: CompanyRepository = Depends(get_company_repository),
):
    payload = asset_data.dict(exclude_unset=True)
    payload["source_type"] = payload.get("source_type") or "manual"
    return repo.create_asset(payload)


@router.put("/assets/{asset_id}", response_model=Dict[str, Any])
def update_company_asset(
    asset_id: int,
    asset_data: CompanyAssetInput,
    repo: CompanyRepository = Depends(get_company_repository),
):
    payload = asset_data.dict(exclude_unset=True)
    result = repo.update_asset(asset_id, payload)
    if not result:
        raise HTTPException(status_code=404, detail="资料不存在")
    return result


@router.delete("/assets/{asset_id}", response_model=Dict[str, Any])
def delete_company_asset(
    asset_id: int,
    payload: CompanyAssetDeleteInput = CompanyAssetDeleteInput(),
    repo: CompanyRepository = Depends(get_company_repository),
):
    result = repo.soft_delete_asset(asset_id, payload.reason or "")
    if not result:
        raise HTTPException(status_code=404, detail="资料不存在")
    return result


@router.post("/assets/{asset_id}/restore", response_model=Dict[str, Any])
def restore_company_asset(
    asset_id: int,
    repo: CompanyRepository = Depends(get_company_repository),
):
    result = repo.restore_asset(asset_id)
    if not result:
        raise HTTPException(status_code=404, detail="资料不存在")
    return result


@router.get("/assets/summary", response_model=Dict[str, Any])
def get_company_asset_summary(
    repo: CompanyRepository = Depends(get_company_repository),
):
    return repo.get_asset_summary()


@router.post("/reset")
def reset_company_profile(
    repo: CompanyRepository = Depends(get_company_repository)
):
    """重置为默认公司画像"""
    default_profile = {
        "name": "默认公司",
        "target_domains": ["软件开发", "大数据", "AI/人工智能"],
        "budget_range": [50, 1000],
        "qualifications": ["CMMI3", "ISO27001", "高新技术企业"],
        "service_regions": ["广东省", "北京市", "上海市"],
        "bid_history": [],
    }
    repo.save_profile(default_profile)
    return {"message": "已重置为默认配置", "profile": default_profile}
