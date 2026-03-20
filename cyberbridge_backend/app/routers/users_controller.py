# routers/users_controller.py
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import base64
import os

from ..repositories import user_repository
from ..dtos import schemas
from ..database.database import get_db
from ..services.auth_service import get_current_active_user, get_current_user as get_current_user_dep, check_user_role
from ..services.security_service import verify_password, get_password_hash

router = APIRouter(prefix="/users", tags=["users"], responses={404: {"description": "Not found"}})

@router.post("/change-password", status_code=status.HTTP_200_OK)
def change_password(
    request: schemas.ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Change user's password - requires current password verification"""
    try:
        # Get the user from database to verify current password
        db_user = user_repository.get_user(db, user_id=uuid.UUID(str(current_user.id)))
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")

        # Verify current password
        if not verify_password(request.current_password, db_user.hashed_password):
            raise HTTPException(status_code=400, detail="Current password is incorrect")

        # Validate new password
        if len(request.new_password) < 8:
            raise HTTPException(status_code=400, detail="New password must be at least 8 characters long")

        if request.current_password == request.new_password:
            raise HTTPException(status_code=400, detail="New password must be different from current password")

        # Hash new password and update
        hashed_new_password = get_password_hash(request.new_password)
        updated_user = user_repository.update_user_password_hash(
            db,
            user_id=uuid.UUID(str(current_user.id)),
            hashed_password=hashed_new_password
        )

        if not updated_user:
            raise HTTPException(status_code=500, detail="Failed to update password")

        return {"message": "Password changed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while changing password: {str(e)}"
        )


@router.post("/force-change-password", status_code=status.HTTP_200_OK)
def force_change_password(
    request: schemas.ForceChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_dep)
):
    """Force change password on first login - no current password required, only works when must_change_password is True"""
    try:
        db_user = user_repository.get_user(db, user_id=uuid.UUID(str(current_user.id)))
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")

        if not db_user.must_change_password:
            raise HTTPException(status_code=400, detail="Password change is not required")

        if len(request.new_password) < 8:
            raise HTTPException(status_code=400, detail="New password must be at least 8 characters long")

        # Hash new password and update
        hashed_new_password = get_password_hash(request.new_password)
        db_user.hashed_password = hashed_new_password
        db_user.must_change_password = False
        db.commit()
        db.refresh(db_user)

        return {"message": "Password changed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while changing password: {str(e)}"
        )


@router.get("/profile", response_model=schemas.FullUserResponse)
def get_profile(
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get current user's full profile"""
    try:
        user = user_repository.get_user_full_profile(db, user_id=uuid.UUID(str(current_user.id)))
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching profile: {str(e)}"
        )


@router.put("/profile", response_model=schemas.FullUserResponse)
def update_profile(
    request: schemas.ProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Update current user's profile"""
    try:
        updated_user = user_repository.update_user_profile(
            db,
            user_id=uuid.UUID(str(current_user.id)),
            first_name=request.first_name,
            last_name=request.last_name,
            phone=request.phone,
            job_title=request.job_title,
            department=request.department,
            timezone=request.timezone,
            notification_preferences=request.notification_preferences
        )
        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")
        return updated_user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating profile: {str(e)}"
        )


@router.post("/profile/picture", response_model=schemas.ProfilePictureResponse)
async def upload_profile_picture(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Upload profile picture - accepts image files up to 5MB"""
    try:
        # Validate file type
        allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Invalid file type. Allowed: JPEG, PNG, GIF, WebP")

        # Read file content
        content = await file.read()

        # Validate file size (5MB max)
        max_size = 5 * 1024 * 1024  # 5MB
        if len(content) > max_size:
            raise HTTPException(status_code=400, detail="File too large. Maximum size is 5MB")

        # Convert to base64 data URL
        base64_content = base64.b64encode(content).decode('utf-8')
        data_url = f"data:{file.content_type};base64,{base64_content}"

        # Update user's profile picture
        updated_user = user_repository.update_user_profile_picture(
            db,
            user_id=uuid.UUID(str(current_user.id)),
            profile_picture=data_url
        )

        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")

        return schemas.ProfilePictureResponse(
            profile_picture=data_url,
            message="Profile picture uploaded successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while uploading profile picture: {str(e)}"
        )


@router.delete("/profile/picture")
def delete_profile_picture(
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Delete current user's profile picture"""
    try:
        updated_user = user_repository.update_user_profile_picture(
            db,
            user_id=uuid.UUID(str(current_user.id)),
            profile_picture=None
        )
        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"message": "Profile picture deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while deleting profile picture: {str(e)}"
        )

@router.post("/", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: schemas.UserCreate,db: Session = Depends(get_db),current_user: schemas.UserBase = Depends(check_user_role(["super_admin", "org_admin"]))): # Super admin and org admin can create users
    try:
        db_user = user_repository.get_user_by_email(db, email=str(user.email))
        if db_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        return user_repository.create_user(db=db, user=user)
    except HTTPException:
        # Re-raise HTTP exceptions as they are already handled
        raise
    except Exception as e:
        # Log the exception here if you have logging configured
        # logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating the user: {str(e)}"
        )


@router.get("/", response_model=List[schemas.FullUserResponse])
def read_users(skip: int = 0,limit: int = 100,db: Session = Depends(get_db),current_user: schemas.UserBase = Depends(check_user_role(["super_admin"])) ): # Only admins can list all users
    users = user_repository.get_users(db, skip=skip, limit=limit)
    return users

@router.post("/fetch_organisation_users", response_model=List[schemas.FullUserResponse])
def fetch_organisation_users(request:schemas.OnlyIdInStringFormat ,db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        organisation_id = request.id
        users_data = user_repository.get_organisation_users(db, organisation_id=organisation_id)
        users = []
        for user in users_data:
            # Filter out superadmin users if current user is org_admin
            if current_user.role_name == "org_admin" and user.role_name == "super_admin":
                continue

            users.append(schemas.FullUserResponse(
                id=str(user.id),
                email=user.email,
                role_id=str(user.role_id),
                organisation_id=str(user.organisation_id),
                status=user.status,
                role_name=user.role_name,
                organisation_name=user.organisation_name,
                organisation_logo=user.organisation_logo,
                organisation_domain=user.organisation_domain,
                auth_provider=getattr(user, 'auth_provider', 'local')
            ))
        return users
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred: {str(e)}")

@router.post("/get_current_user_by_email", response_model=schemas.FullUserResponse)
def get_current_user(request: schemas.UserEmail , db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)): #check if token is valid! - route protection
    try:
        user = user_repository.get_user_by_email(db, email=str(request.email))
        response = schemas.FullUserResponse(id=str(user.id), email=user.email, role_id=str(user.role_id), organisation_id=str(user.organisation_id), status=user.status, role_name=user.role_name, organisation_name=user.organisation_name, organisation_logo=user.organisation_logo, organisation_domain=user.organisation_domain, auth_provider=getattr(user, 'auth_provider', 'local'))
        return response
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,)

@router.post("/create_user_in_organisation", response_model=schemas.FullUserResponse)
def create_user_in_organisation(request: schemas.UserCreateInOrganisation, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(check_user_role(["super_admin", "org_admin"]))):
    try:
        # Security check: org_admin can only create users in their own organization
        if current_user.role_name == "org_admin":
            if str(current_user.organisation_id) != str(request.organisation_id):
                raise HTTPException(status_code=403, detail="Organization admins can only create users within their own organization")

        user = user_repository.create_user_in_organisation(db, user=request)
        response = schemas.FullUserResponse(
            id=str(user.id),
            email=user.email,
            role_id=str(user.role_id),
            organisation_id=str(user.organisation_id),
            status=user.status,
            role_name=user.role_name,
            organisation_name=user.organisation_name,
            organisation_logo=user.organisation_logo,
            organisation_domain=user.organisation_domain,
            auth_provider=user.auth_provider
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while creating the user in the organisation: {str(e)}")

@router.post("/update_user_in_organisation", response_model=schemas.FullUserResponse)
def update_user_in_organisation(request: schemas.UserUpdateInOrganisation, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        # Get the user being updated
        target_user = user_repository.get_user(db, user_id=uuid.UUID(request.user_id))
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Permission checks
        if current_user.role_name == "super_admin":
            # Super admin can update any user
            pass
        elif current_user.role_name == "org_admin":
            # Org admin can update users in their organization
            if str(current_user.organisation_id) != str(target_user.organisation_id):
                raise HTTPException(status_code=403, detail="Not authorized to update users outside your organization")
        elif current_user.role_name == "org_user":
            # Org user can only update their own profile
            if str(current_user.id) != request.user_id:
                raise HTTPException(status_code=403, detail="Not authorized to update other users")
            # Org user cannot change their role
            if request.role_id and request.role_id != str(target_user.role_id):
                raise HTTPException(status_code=403, detail="Not authorized to change your role")
        else:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        user = user_repository.update_user_in_organisation(db, user=request)
        response = schemas.FullUserResponse(
            id=str(user.id),
            email=user.email,
            role_id=str(user.role_id),
            organisation_id=str(user.organisation_id),
            status=user.status,
            role_name=user.role_name,
            organisation_name=user.organisation_name,
            organisation_logo=user.organisation_logo,
            organisation_domain=user.organisation_domain,
            auth_provider=getattr(user, 'auth_provider', 'local')
        )
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while updating the user in the organisation: {str(e)}")

@router.post("/create_organisation", response_model=schemas.OrganisationResponse)
def create_organisation(request: schemas.OrganisationRequest, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        # Check if id is provided in the request (not None and not empty string)
        if hasattr(request, 'id') and request.id is not None and request.id.strip() != "":
            # Call update_organisation function if id exists
            organisation = user_repository.update_organisation(db, organisation_id=uuid.UUID(request.id), request=request)
        else:
            # Call create_organisation if no id is provided
            organisation = user_repository.create_organisation(db, request=request)

        # Convert UUID to string before returning
        response = schemas.OrganisationResponse(
            id=str(organisation.id),
            name=organisation.name,
            domain=organisation.domain,
            logo=organisation.logo
        )
        return response
    except ValueError as e:
        # Catch the specific ValueError and return it as a 400 Bad Request
        if "Organisation with this name already exists" in str(e):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        # Re-raise other ValueErrors as 500 errors
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while processing the organisation: {str(e)}")

@router.get("/get_all_organisations", response_model=List[schemas.OrganisationResponse])
def get_all_organisations(db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        organisations_data = user_repository.get_all_organisations(db, current_user=current_user)
        organisations = []
        for org in organisations_data:
            organisations.append(schemas.OrganisationResponse(
                id=str(org.id),
                name=org.name,
                domain=org.domain,
                logo=org.logo
            ))
        return organisations
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while fetching all organisations: {str(e)}")

@router.get("/get_all_roles", response_model=List[schemas.RoleResponse])
def get_all_roles(db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        roles_data = user_repository.get_all_roles(db)
        roles = []
        for role in roles_data:
            roles.append(schemas.RoleResponse(
                id=str(role.id),
                role_name=role.role_name
            ))
        return roles
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while fetching all roles: {str(e)}")

@router.get("/truncate_all_database_tables")
def truncate_all_database_tables(db: Session = Depends(get_db),current_user: schemas.UserBase = Depends(check_user_role(["super_admin"]))):
    try:
        user_repository.truncate_all_database_tables(db)
        return {"message": "All tables truncated successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while truncating all database tables: {str(e)}"
        )

@router.get("/drop_all_database_tables")
def truncate_all_database_tables(db: Session = Depends(get_db),current_user: schemas.UserBase = Depends(check_user_role(["super_admin"]))):
    try:
        user_repository.drop_all_database_tables(db)
        return {"message": "All tables truncated successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while truncating all database tables: {str(e)}"
        )

@router.get("/{user_id}", response_model=schemas.UserResponse)
def read_user(user_id: uuid.UUID, db: Session = Depends(get_db),current_user: schemas.UserBase = Depends(get_current_active_user)):
    # Allow users to access their own data or admins to access any user data
    if str(current_user.id) != str(user_id) and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to access this user data")

    db_user = user_repository.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.put("/{user_id}", response_model=schemas.UserResponse)
def update_user(user_id: uuid.UUID,user_update: schemas.UserCreate,db: Session = Depends(get_db),current_user: schemas.UserBase = Depends(get_current_active_user)):
    # Allow users to update their own data or admins to update any user data
    if str(current_user.id) != str(user_id) and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to update this user data")

    db_user = user_repository.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        # Updated to match the user_repository.update_user function signature from the first code block
        return user_repository.update_user(db=db, user_id=user_id, user=user_update)
    except Exception as e:
        # Log the exception here if you have logging configured
        # logger.error(f"Error updating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating the user: {str(e)}"
        )


@router.delete("/{user_id}") #status_code=status.HTTP_204_NO_CONTENT
def delete_user(user_id: uuid.UUID,db: Session = Depends(get_db),current_user: schemas.UserBase = Depends(check_user_role(["super_admin"]))): # Only admins can delete users
    try:
        # Check if user exists
        db_user = user_repository.get_user(db, user_id=user_id)
        if db_user is None:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Rule: Cannot delete yourself
        if str(user_id) == str(current_user.id):
            raise HTTPException(status_code=403, detail="Cannot delete your own user account")
        
        user_repository.delete_user(db, user_id=user_id)
        return {"message": "User deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while deleting the user: {str(e)}"
        )


@router.get("/{user_id}/notifications", response_model=List[schemas.NotificationResponse])
def read_user_notifications(user_id: uuid.UUID, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    db_user = user_repository.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    notifications = user_repository.get_user_notifications(db, user_id=user_id, skip=skip, limit=limit)
    return notifications


@router.delete("/organisation/{organisation_id}")
def delete_organisation(organisation_id: uuid.UUID, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(check_user_role(["super_admin"]))):
    """Delete organization with complete cascading deletes - only super_admin from Clone Systems can delete organizations"""
    try:
        # Check if organization exists
        db_organisation = user_repository.get_organisation_by_id(db, str(organisation_id))
        if db_organisation is None:
            raise HTTPException(status_code=404, detail="Organisation not found")
        
        # Get current user's organization details
        current_user_org = user_repository.get_organisation_by_id(db, str(current_user.organisation_id))
        if not current_user_org:
            raise HTTPException(status_code=403, detail="User organization not found")
        
        # Rule 1: Only users from "clone-systems.com" domain organization can delete organizations
        if current_user_org.domain != "clone-systems.com":
            raise HTTPException(status_code=403, detail="Only users from Clone Systems organization can delete organizations")
        
        # Rule 2: Cannot delete own organization
        if str(organisation_id) == str(current_user.organisation_id):
            raise HTTPException(status_code=403, detail="Cannot delete your own organization")
        
        # Rule 3: Cannot delete the last organization
        total_orgs = db.query(user_repository.models.Organisations).count()
        if total_orgs <= 1:
            raise HTTPException(status_code=403, detail="Cannot delete the last organization")
        
        success = user_repository.delete_organisation(db, organisation_id)
        if success:
            return {"message": "Organisation and all associated data deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete organisation")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while deleting the organisation: {str(e)}"
        )
