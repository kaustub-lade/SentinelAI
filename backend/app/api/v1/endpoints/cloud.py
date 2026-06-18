from fastapi import APIRouter


router = APIRouter()

@router.get("/findings")
async def get_cloud_findings():

    findings = [

        {
            "id": 1,
            "severity": "Critical",
            "title": "Public Storage Bucket",
            "description":
                "Cloud storage bucket is publicly accessible.",
            "resource":
                "sentinel-backups",
            "status": "Open"
        },

        {
            "id": 2,
            "severity": "High",
            "title": "MFA Disabled",
            "description":
                "Administrator account does not have MFA enabled.",
            "resource":
                "admin@sentinel.local",
            "status": "Open"
        },

        {
            "id": 3,
            "severity": "Medium",
            "title": "Overly Permissive IAM Role",
            "description":
                "Role has wildcard permissions.",
            "resource":
                "CloudAdminRole",
            "status": "Open"
        }
    ]

    return {
        "findings": findings
    }