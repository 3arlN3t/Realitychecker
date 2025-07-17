"""
Multi-Factor Authentication API endpoints.

This module provides REST API endpoints for managing MFA:
- MFA enrollment and setup
- TOTP verification
- Backup code management
- MFA status and statistics
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.models.data_models import User
from app.services.mfa_service import MFAService, MFAEnrollmentData, MFAVerificationResult, MFAStatus
from app.dependencies import get_current_active_user, require_admin_user
from app.utils.logging import get_logger, get_correlation_id, log_with_context


logger = get_logger(__name__)
router = APIRouter(prefix="/mfa", tags=["Multi-Factor Authentication"])


# Request/Response Models

class MFAEnrollmentResponse(BaseModel):
    """Response model for MFA enrollment."""
    qr_code_data: str = Field(..., description="Base64-encoded QR code image")
    backup_codes: List[str] = Field(..., description="List of backup codes")
    enrollment_token: str = Field(..., description="Token for completing enrollment")
    message: str = Field(..., description="Success message")


class MFAVerificationRequest(BaseModel):
    """Request model for MFA verification."""
    token: str = Field(..., min_length=6, max_length=8, description="TOTP code or backup code")


class MFAEnrollmentCompletionRequest(BaseModel):
    """Request model for completing MFA enrollment."""
    enrollment_token: str = Field(..., description="Enrollment token from setup")
    totp_code: str = Field(..., min_length=6, max_length=6, description="TOTP code from authenticator app")


class MFAVerificationResponse(BaseModel):
    """Response model for MFA verification."""
    valid: bool = Field(..., description="Whether the token is valid")
    backup_code_used: bool = Field(False, description="Whether a backup code was used")
    remaining_backup_codes: int = Field(0, description="Number of remaining backup codes")
    message: str = Field(..., description="Response message")


class MFAStatusResponse(BaseModel):
    """Response model for MFA status."""
    enabled: bool = Field(..., description="Whether MFA is enabled")
    enrolled: bool = Field(..., description="Whether MFA is enrolled")
    backup_codes_remaining: int = Field(..., description="Number of remaining backup codes")
    last_used: str | None = Field(None, description="Last MFA usage timestamp")
    recovery_codes_generated: int = Field(..., description="Number of times recovery codes were generated")


class BackupCodesResponse(BaseModel):
    """Response model for backup codes."""
    backup_codes: List[str] = Field(..., description="List of new backup codes")
    message: str = Field(..., description="Success message")


class MFAStatisticsResponse(BaseModel):
    """Response model for MFA statistics."""
    total_users_with_mfa: int = Field(..., description="Total users with MFA configured")
    enabled_users: int = Field(..., description="Users with MFA enabled")
    enrollment_rate: float = Field(..., description="MFA enrollment rate")
    active_enrollment_tokens: int = Field(..., description="Active enrollment tokens")


# Dependency to get MFA service
async def get_mfa_service() -> MFAService:
    """Get MFA service instance."""
    from app.dependencies import get_service_container
    # For now, we'll create a service instance
    # In production, this should be properly integrated with the service container
    from app.config import get_config
    config = get_config()
    return MFAService(config)


# MFA Enrollment Endpoints

@router.post("/setup", response_model=MFAEnrollmentResponse)
async def setup_mfa(
    current_user: User = Depends(get_current_active_user),
    mfa_service: MFAService = Depends(get_mfa_service)
):
    """
    Start MFA enrollment process.
    
    Generates a new TOTP secret, QR code, and backup codes for the user.
    """
    correlation_id = get_correlation_id()
    
    try:
        log_with_context(
            logger,
            logging.INFO,
            "Starting MFA setup",
            username=current_user.username,
            correlation_id=correlation_id
        )
        
        # Check if MFA is already enabled
        mfa_status = await mfa_service.get_mfa_status(current_user)
        if mfa_status.enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MFA is already enabled for this user"
            )
        
        # Start enrollment
        enrollment_data = await mfa_service.start_mfa_enrollment(current_user)
        
        log_with_context(
            logger,
            logging.INFO,
            "MFA setup completed",
            username=current_user.username,
            backup_codes_count=len(enrollment_data.backup_codes),
            correlation_id=correlation_id
        )
        
        return MFAEnrollmentResponse(
            qr_code_data=enrollment_data.qr_code_data,
            backup_codes=enrollment_data.backup_codes,
            enrollment_token=enrollment_data.enrollment_token,
            message="MFA setup initiated. Scan the QR code with your authenticator app and save the backup codes."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_with_context(
            logger,
            logging.ERROR,
            "MFA setup failed",
            username=current_user.username,
            error=str(e),
            correlation_id=correlation_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set up MFA"
        )


@router.post("/complete-setup")
async def complete_mfa_setup(
    request: MFAEnrollmentCompletionRequest,
    current_user: User = Depends(get_current_active_user),
    mfa_service: MFAService = Depends(get_mfa_service)
):
    """
    Complete MFA enrollment by verifying TOTP code.
    
    Validates the TOTP code from the user's authenticator app and enables MFA.
    """
    correlation_id = get_correlation_id()
    
    try:
        log_with_context(
            logger,
            logging.INFO,
            "Completing MFA setup",
            username=current_user.username,
            correlation_id=correlation_id
        )
        
        # Complete enrollment
        success = await mfa_service.complete_mfa_enrollment(
            request.enrollment_token,
            request.totp_code
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid enrollment token or TOTP code"
            )
        
        log_with_context(
            logger,
            logging.INFO,
            "MFA setup completed successfully",
            username=current_user.username,
            correlation_id=correlation_id
        )
        
        return {"message": "MFA has been successfully enabled for your account"}
        
    except HTTPException:
        raise
    except Exception as e:
        log_with_context(
            logger,
            logging.ERROR,
            "MFA setup completion failed",
            username=current_user.username,
            error=str(e),
            correlation_id=correlation_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete MFA setup"
        )


# MFA Verification Endpoints

@router.post("/verify", response_model=MFAVerificationResponse)
async def verify_mfa_token(
    request: MFAVerificationRequest,
    current_user: User = Depends(get_current_active_user),
    mfa_service: MFAService = Depends(get_mfa_service)
):
    """
    Verify MFA token (TOTP code or backup code).
    
    Validates the provided token and returns verification result.
    """
    correlation_id = get_correlation_id()
    
    try:
        log_with_context(
            logger,
            logging.INFO,
            "Verifying MFA token",
            username=current_user.username,
            correlation_id=correlation_id
        )
        
        # Verify token
        result = await mfa_service.verify_mfa_token(current_user, request.token)
        
        if result.valid:
            message = "MFA token verified successfully"
            if result.backup_code_used:
                message += f" (backup code used, {result.remaining_backup_codes} remaining)"
        else:
            message = result.error_message or "Invalid MFA token"
        
        log_with_context(
            logger,
            logging.INFO,
            "MFA verification completed",
            username=current_user.username,
            valid=result.valid,
            backup_code_used=result.backup_code_used,
            correlation_id=correlation_id
        )
        
        return MFAVerificationResponse(
            valid=result.valid,
            backup_code_used=result.backup_code_used,
            remaining_backup_codes=result.remaining_backup_codes,
            message=message
        )
        
    except Exception as e:
        log_with_context(
            logger,
            logging.ERROR,
            "MFA verification failed",
            username=current_user.username,
            error=str(e),
            correlation_id=correlation_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify MFA token"
        )


# MFA Management Endpoints

@router.get("/status", response_model=MFAStatusResponse)
async def get_mfa_status(
    current_user: User = Depends(get_current_active_user),
    mfa_service: MFAService = Depends(get_mfa_service)
):
    """
    Get MFA status for the current user.
    
    Returns current MFA enrollment and usage status.
    """
    try:
        status_data = await mfa_service.get_mfa_status(current_user)
        
        return MFAStatusResponse(
            enabled=status_data.enabled,
            enrolled=status_data.enrolled,
            backup_codes_remaining=status_data.backup_codes_remaining,
            last_used=status_data.last_used.isoformat() if status_data.last_used else None,
            recovery_codes_generated=status_data.recovery_codes_generated
        )
        
    except Exception as e:
        logger.error(f"Failed to get MFA status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get MFA status"
        )


@router.post("/disable")
async def disable_mfa(
    current_user: User = Depends(get_current_active_user),
    mfa_service: MFAService = Depends(get_mfa_service)
):
    """
    Disable MFA for the current user.
    
    Disables two-factor authentication for the user's account.
    """
    correlation_id = get_correlation_id()
    
    try:
        log_with_context(
            logger,
            logging.INFO,
            "Disabling MFA",
            username=current_user.username,
            correlation_id=correlation_id
        )
        
        success = await mfa_service.disable_mfa(current_user)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MFA is not enabled for this user"
            )
        
        log_with_context(
            logger,
            logging.INFO,
            "MFA disabled successfully",
            username=current_user.username,
            correlation_id=correlation_id
        )
        
        return {"message": "MFA has been disabled for your account"}
        
    except HTTPException:
        raise
    except Exception as e:
        log_with_context(
            logger,
            logging.ERROR,
            "Failed to disable MFA",
            username=current_user.username,
            error=str(e),
            correlation_id=correlation_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disable MFA"
        )


@router.post("/regenerate-backup-codes", response_model=BackupCodesResponse)
async def regenerate_backup_codes(
    current_user: User = Depends(get_current_active_user),
    mfa_service: MFAService = Depends(get_mfa_service)
):
    """
    Regenerate backup codes for the current user.
    
    Generates new backup codes and invalidates old ones.
    """
    correlation_id = get_correlation_id()
    
    try:
        log_with_context(
            logger,
            logging.INFO,
            "Regenerating backup codes",
            username=current_user.username,
            correlation_id=correlation_id
        )
        
        new_codes = await mfa_service.regenerate_backup_codes(current_user)
        
        log_with_context(
            logger,
            logging.INFO,
            "Backup codes regenerated successfully",
            username=current_user.username,
            codes_count=len(new_codes),
            correlation_id=correlation_id
        )
        
        return BackupCodesResponse(
            backup_codes=new_codes,
            message="New backup codes generated. Please save them securely."
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        log_with_context(
            logger,
            logging.ERROR,
            "Failed to regenerate backup codes",
            username=current_user.username,
            error=str(e),
            correlation_id=correlation_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to regenerate backup codes"
        )


# Admin Endpoints

@router.get("/statistics", response_model=MFAStatisticsResponse)
async def get_mfa_statistics(
    current_user: User = Depends(require_admin_user),
    mfa_service: MFAService = Depends(get_mfa_service)
):
    """
    Get MFA usage statistics.
    
    Returns statistics about MFA adoption and usage across all users.
    Admin only endpoint.
    """
    try:
        stats = await mfa_service.get_mfa_statistics()
        
        return MFAStatisticsResponse(
            total_users_with_mfa=stats['total_users_with_mfa'],
            enabled_users=stats['enabled_users'],
            enrollment_rate=stats['enrollment_rate'],
            active_enrollment_tokens=stats['active_enrollment_tokens']
        )
        
    except Exception as e:
        logger.error(f"Failed to get MFA statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get MFA statistics"
        )


@router.post("/cleanup")
async def cleanup_expired_tokens(
    current_user: User = Depends(require_admin_user),
    mfa_service: MFAService = Depends(get_mfa_service)
):
    """
    Clean up expired enrollment tokens.
    
    Removes expired enrollment tokens from memory.
    Admin only endpoint.
    """
    try:
        await mfa_service.cleanup_expired_tokens()
        return {"message": "Expired enrollment tokens cleaned up successfully"}
        
    except Exception as e:
        logger.error(f"Failed to cleanup expired tokens: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cleanup expired tokens"
        )