from fastapi import APIRouter, Depends, Query
from supabase import Client

from app.core.deps import supabase_dep, current_user_dep
from app.schemas.support_enquiry import (
    SupportEnquiryCreate,
    SupportEnquiryOut,
    SupportEnquiryListResponse,
)
from app.services.support_enquiries_service import (
    create_support_enquiry_service,
    list_my_support_enquiries_service,
)

router = APIRouter(prefix="/support-enquiries", tags=["support-enquiries"])


@router.post("", response_model=SupportEnquiryOut)
def create_support_enquiry(
    payload: SupportEnquiryCreate,
    current_user=Depends(current_user_dep),
    sb: Client = Depends(supabase_dep),
):
    return create_support_enquiry_service(
        sb=sb,
        external_auth_id=current_user.id,
        payload=payload,
    )


@router.get("", response_model=SupportEnquiryListResponse)
def list_my_support_enquiries(
    current_user=Depends(current_user_dep),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    sb: Client = Depends(supabase_dep),
):
    return list_my_support_enquiries_service(
        sb=sb,
        external_auth_id=current_user.id,
        limit=limit,
        offset=offset,
    )