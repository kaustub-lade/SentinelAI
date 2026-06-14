from fastapi import APIRouter, Depends
from pymongo.database import Database

from app.core.database import get_db
from app.services.event_correlation import generate_attack_chains

router = APIRouter()


@router.get("/attack-chains")
async def get_attack_chains(
    db: Database = Depends(get_db),
):
    chains = generate_attack_chains(db)

    return {
        "attack_chains": chains,
        "count": len(chains),
    }