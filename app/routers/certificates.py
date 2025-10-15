"""
數位憑證相關 API 路由
整合政府數位憑證沙盒 API
"""
from fastapi import APIRouter, HTTPException, status
from app.models.models import (
    CertificateCreate, 
    CertificateResponse, 
    CertificateVerifyRequest,
    CertificateDisburseRequest,
    APIResponse
)
from app.models.database import db_service
from app.services.storage import storage_service
from app.services.gov_wallet import gov_wallet_service
from datetime import datetime, timedelta
import json

router = APIRouter(prefix="/certificates", tags=["數位憑證（政府沙盒整合）"])

@router.post("/", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_certificate(
    application_id: str,
    issued_by: str,
    expires_days: int = 365,
    use_gov_api: bool = True
):
    """
    為核准的申請案件建立數位憑證（整合政府沙盒 API）
    
    - **application_id**: 申請案件 ID
    - **issued_by**: 核發人 ID
    - **expires_days**: 憑證有效天數，預設 365 天
    - **use_gov_api**: 是否使用政府數位憑證 API，預設 True
    """
    try:
        # 檢查申請案件是否存在且已核准
        application = db_service.get_application_by_id(application_id)
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="申請案件不存在"
            )
        
        if application['status'] != 'approved':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只有已核准的案件才能建立憑證"
            )
        
        # 檢查是否已存在憑證
        try:
            existing_cert = db_service.get_certificate_by_application(application_id)
            if existing_cert:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="此案件已有憑證"
                )
        except:
            pass  # 憑證不存在，可以繼續
        
        # 生成憑證編號
        cert_no = f"CERT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{application_id[:8]}"
        
        gov_credential = None
        qr_result = None
        
        if use_gov_api:
            # 使用政府數位憑證 API 發行憑證
            try:
                gov_credential = await gov_wallet_service.create_disaster_relief_credential(
                    application_data=application,
                    approved_amount=float(application['approved_amount']),
                    case_no=application['case_no']
                )
                
                # 取得政府 API 回傳的憑證 ID 和 QR Code
                gov_cert_id = gov_credential.get('credentialId') or gov_credential.get('id')
                
                # 如果政府 API 有提供 QR Code，使用它；否則自己生成
                if gov_credential.get('qrCode'):
                    qr_data_str = json.dumps(gov_credential, ensure_ascii=False)
                    qr_result = storage_service.generate_qr_code(cert_no, gov_credential)
                else:
                    # 政府 API 沒有提供 QR Code，自己生成
                    qr_data = {
                        "certificate_no": cert_no,
                        "gov_credential_id": gov_cert_id,
                        "application_id": application_id,
                        "case_no": application['case_no'],
                        "applicant_name": application['applicant_name'],
                        "id_number": application['id_number'],
                        "approved_amount": float(application['approved_amount']),
                        "disaster_type": application.get('disaster_type'),
                        "issued_at": datetime.now().isoformat(),
                        "expires_at": (datetime.now() + timedelta(days=expires_days)).isoformat(),
                        "gov_api": True
                    }
                    qr_result = storage_service.generate_qr_code(cert_no, qr_data)
                
            except Exception as e:
                print(f"政府 API 發行憑證失敗，使用本地方式: {e}")
                use_gov_api = False
        
        if not use_gov_api or not gov_credential:
            # 使用本地方式生成 QR Code
            qr_data = {
                "certificate_no": cert_no,
                "application_id": application_id,
                "case_no": application['case_no'],
                "applicant_name": application['applicant_name'],
                "id_number": application['id_number'],
                "approved_amount": float(application['approved_amount']),
                "disaster_type": application.get('disaster_type'),
                "issued_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(days=expires_days)).isoformat(),
                "gov_api": False
            }
            qr_result = storage_service.generate_qr_code(cert_no, qr_data)
        
        # 建立憑證記錄
        certificate_data = {
            "application_id": application_id,
            "certificate_no": cert_no,
            "qr_code_data": qr_result['qr_data'],
            "qr_code_image_path": qr_result['storage_path'],
            "issued_amount": application['approved_amount'],
            "issued_by": issued_by,
            "expires_at": (datetime.now() + timedelta(days=expires_days)).isoformat()
        }
        
        result = db_service.create_certificate(certificate_data)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="建立憑證失敗"
            )
        
        # 將額外資訊加到結果中
        result['qr_code_url'] = qr_result['public_url']
        result['gov_credential'] = gov_credential if use_gov_api else None
        result['using_gov_api'] = use_gov_api
        
        return APIResponse(
            success=True,
            message=f"數位憑證建立成功{'（已整合政府沙盒 API）' if use_gov_api else '（本地模式）'}",
            data=result
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"發生錯誤: {str(e)}"
        )

@router.get("/{certificate_no}", response_model=APIResponse)
async def get_certificate(certificate_no: str):
    """
    根據憑證編號取得憑證資料
    """
    try:
        certificate = db_service.get_certificate_by_no(certificate_no)
        
        if not certificate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="憑證不存在"
            )
        
        # 取得 QR Code URL
        qr_url = storage_service.get_qr_code_url(certificate['qr_code_image_path'])
        certificate['qr_code_url'] = qr_url
        
        return APIResponse(
            success=True,
            message="取得憑證資料成功",
            data=certificate
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"發生錯誤: {str(e)}"
        )

@router.get("/application/{application_id}", response_model=APIResponse)
async def get_certificate_by_application(application_id: str):
    """
    根據申請案件 ID 取得憑證
    """
    try:
        certificate = db_service.get_certificate_by_application(application_id)
        
        if not certificate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="此案件尚未建立憑證"
            )
        
        # 取得 QR Code URL
        qr_url = storage_service.get_qr_code_url(certificate['qr_code_image_path'])
        certificate['qr_code_url'] = qr_url
        
        return APIResponse(
            success=True,
            message="取得憑證資料成功",
            data=certificate
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"發生錯誤: {str(e)}"
        )

@router.post("/verify", response_model=APIResponse)
async def verify_certificate(verify_request: CertificateVerifyRequest):
    """
    驗證憑證
    
    - **certificate_no**: 憑證編號
    - **verified_by**: 驗證人 ID
    """
    try:
        # 取得憑證
        certificate = db_service.get_certificate_by_no(verify_request.certificate_no)
        
        if not certificate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="憑證不存在"
            )
        
        # 檢查憑證是否已驗證
        if certificate['is_verified']:
            return APIResponse(
                success=True,
                message="此憑證已經驗證過",
                data=certificate
            )
        
        # 檢查憑證是否過期
        if certificate.get('expires_at'):
            from datetime import timezone
            expires_at = datetime.fromisoformat(certificate['expires_at'].replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            if now > expires_at:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="憑證已過期"
                )
        
        # 驗證憑證
        result = db_service.verify_certificate(
            certificate['id'], 
            verify_request.verified_by
        )
        
        return APIResponse(
            success=True,
            message="憑證驗證成功",
            data=result
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"發生錯誤: {str(e)}"
        )

@router.post("/disburse", response_model=APIResponse)
async def disburse_certificate(disburse_request: CertificateDisburseRequest):
    """
    發放補助
    
    - **certificate_id**: 憑證 ID
    - **disbursement_method**: 發放方式 (bank_transfer, check, cash)
    """
    try:
        # 取得憑證（使用 ID）
        certificate = db_service.get_certificate_by_no(disburse_request.certificate_id)
        
        if not certificate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="憑證不存在"
            )
        
        # 檢查憑證是否已驗證
        if not certificate['is_verified']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="憑證尚未驗證，無法發放補助"
            )
        
        # 檢查是否已發放
        if certificate['is_disbursed']:
            return APIResponse(
                success=True,
                message="此憑證已經發放過補助",
                data=certificate
            )
        
        # 發放補助
        result = db_service.disburse_certificate(
            certificate['id'],
            disburse_request.disbursement_method
        )
        
        # 更新申請案件狀態為已完成
        db_service.update_application_status(
            certificate['application_id'],
            status='completed',
            completed_at=datetime.now().isoformat()
        )
        
        return APIResponse(
            success=True,
            message="補助發放成功",
            data=result
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"發生錯誤: {str(e)}"
        )

@router.post("/scan/{certificate_no}", response_model=APIResponse)
async def scan_qr_code(certificate_no: str):
    """
    掃描 QR Code 驗證憑證（模擬掃描功能）
    
    - **certificate_no**: 憑證編號（從 QR Code 掃描取得）
    """
    try:
        certificate = db_service.get_certificate_by_no(certificate_no)
        
        if not certificate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="無效的憑證"
            )
        
        # 取得申請案件資料
        application = db_service.get_application_by_id(certificate['application_id'])
        
        # 檢查憑證狀態
        status_info = {
            "certificate_valid": True,
            "is_verified": certificate['is_verified'],
            "is_disbursed": certificate['is_disbursed'],
            "expires_at": certificate.get('expires_at'),
            "is_expired": False
        }
        
        # 檢查是否過期
        if certificate.get('expires_at'):
            from datetime import timezone
            expires_at = datetime.fromisoformat(certificate['expires_at'].replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            if now > expires_at:
                status_info['is_expired'] = True
                status_info['certificate_valid'] = False
        
        # 解析 QR Code 資料
        qr_data = json.loads(certificate['qr_code_data'])
        
        result = {
            "certificate": certificate,
            "application": application,
            "qr_data": qr_data,
            "status": status_info
        }
        
        return APIResponse(
            success=True,
            message="QR Code 掃描成功",
            data=result
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"發生錯誤: {str(e)}"
        )

@router.post("/gov/verify-qr", response_model=APIResponse)
async def verify_qr_with_gov_api(qr_data: str):
    """
    使用政府驗證端 API 驗證 QR Code
    
    - **qr_data**: QR Code 掃描後的資料（JSON 字串）
    
    此端點會呼叫政府數位憑證驗證端 API 進行驗證
    """
    try:
        # 呼叫政府驗證 API
        verification_result = await gov_wallet_service.scan_qr_code_for_verification(qr_data)
        
        if verification_result.get('success') and verification_result.get('verified'):
            return APIResponse(
                success=True,
                message="憑證驗證成功（政府 API）",
                data={
                    "verified": True,
                    "verification_method": "gov_api",
                    "case_number": verification_result.get('case_number'),
                    "applicant_name": verification_result.get('applicant_name'),
                    "id_number": verification_result.get('id_number'),
                    "approved_amount": verification_result.get('approved_amount'),
                    "disaster_type": verification_result.get('disaster_type'),
                    "expiration_date": verification_result.get('expiration_date'),
                    "credential_data": verification_result.get('credential_data')
                }
            )
        else:
            return APIResponse(
                success=False,
                message=f"憑證驗證失敗: {verification_result.get('reason', '未知原因')}",
                data={
                    "verified": False,
                    "reason": verification_result.get('reason')
                }
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"驗證失敗: {str(e)}"
        )

@router.post("/gov/create-verification-request", response_model=APIResponse)
async def create_verification_request():
    """
    建立補助發放驗證請求（用於發放窗口）
    
    此端點會產生一個 QR Code，災民掃描後出示憑證，
    系統即可驗證並發放補助
    """
    try:
        # 建立驗證請求
        verification_request = await gov_wallet_service.create_verification_request(
            required_credentials=["DisasterReliefCredential"],
            purpose="颱風水災補助發放"
        )
        
        return APIResponse(
            success=True,
            message="驗證請求建立成功",
            data={
                "verification_request": verification_request,
                "qr_code": verification_request.get('qrCode'),
                "request_id": verification_request.get('requestId'),
                "usage": "請災民掃描此 QR Code 並出示憑證"
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"建立驗證請求失敗: {str(e)}"
        )

