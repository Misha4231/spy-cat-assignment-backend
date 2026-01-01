from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

import uuid

from database import cats_db, missions_db, valid_breeds
from models import *
from helper import fetch_breeds, validate_breed

async def lifespan(app: FastAPI):
    global valid_breeds
    valid_breeds = await fetch_breeds()

    yield

    valid_breeds.clear()


app = FastAPI(title="Spy Cat Agency API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Spy Cats Endpoints
@app.post("/cats", response_model=SpyCatResponse, status_code=status.HTTP_201_CREATED)
async def create_cat(cat: SpyCat):
    await validate_breed(cat.breed, valid_breeds)
    cat_id = str(uuid.uuid4())
    cats_db[cat_id] = {**cat.model_dump(), "id": cat_id, "mission_id": None}
    return cats_db[cat_id]

@app.get("/cats", response_model=List[SpyCatResponse])
async def list_cats():
    return list(cats_db.values())

@app.get("/cats/{cat_id}", response_model=SpyCatResponse)
async def get_cat(cat_id: str):
    if cat_id not in cats_db:
        raise HTTPException(status_code=404, detail="Cat not found")
    return cats_db[cat_id]

@app.patch("/cats/{cat_id}", response_model=SpyCatResponse)
async def update_cat(cat_id: str, update: SpyCatUpdate):
    if cat_id not in cats_db:
        raise HTTPException(status_code=404, detail="Cat not found")
    cats_db[cat_id]["salary"] = update.salary
    return cats_db[cat_id]

@app.delete("/cats/{cat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cat(cat_id: str):
    if cat_id not in cats_db:
        raise HTTPException(status_code=404, detail="Cat not found")
    del cats_db[cat_id]
    return None

# Missions Endpoints
@app.post("/missions", response_model=MissionResponse, status_code=status.HTTP_201_CREATED)
async def create_mission(mission: Mission):
    mission_id = str(uuid.uuid4())
    targets_with_ids = [
        {**target.dict(), "id": str(uuid.uuid4())}
        for target in mission.targets
    ]
    missions_db[mission_id] = {
        "id": mission_id,
        "cat_id": None,
        "targets": targets_with_ids,
        "complete": False
    }
    return missions_db[mission_id]

@app.get("/missions", response_model=List[MissionResponse])
async def list_missions():
    return list(missions_db.values())

@app.get("/missions/{mission_id}", response_model=MissionResponse)
async def get_mission(mission_id: str):
    if mission_id not in missions_db:
        raise HTTPException(status_code=404, detail="Mission not found")
    return missions_db[mission_id]

@app.delete("/missions/{mission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mission(mission_id: str):
    if mission_id not in missions_db:
        raise HTTPException(status_code=404, detail="Mission not found")
    
    mission = missions_db[mission_id]
    if mission["cat_id"] is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete mission that is assigned to a cat"
        )
    
    del missions_db[mission_id]
    return None

@app.patch("/missions/{mission_id}/targets/{target_id}")
async def update_target(mission_id: str, target_id: str, update: MissionUpdate):
    if mission_id not in missions_db:
        raise HTTPException(status_code=404, detail="Mission not found")
    
    mission = missions_db[mission_id]
    target = next((t for t in mission["targets"] if t["id"] == target_id), None)
    
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    
    if update.notes is not None:
        if target["complete"] or mission["complete"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update notes for completed target or mission"
            )
        target["notes"] = update.notes
    
    if update.complete is not None:
        target["complete"] = update.complete
        
        # Check if all targets are complete
        if all(t["complete"] for t in mission["targets"]):
            mission["complete"] = True
    
    return mission

@app.post("/missions/{mission_id}/assign")
async def assign_cat_to_mission(mission_id: str, assign: AssignCat):
    if mission_id not in missions_db:
        raise HTTPException(status_code=404, detail="Mission not found")
    
    if assign.cat_id not in cats_db:
        raise HTTPException(status_code=404, detail="Cat not found")
    
    cat = cats_db[assign.cat_id]
    if cat["mission_id"] is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cat already has an active mission"
        )
    
    missions_db[mission_id]["cat_id"] = assign.cat_id
    cats_db[assign.cat_id]["mission_id"] = mission_id
    
    return missions_db[mission_id]

@app.get("/breeds")
async def get_breeds():
    global valid_breeds

    if not valid_breeds:
        valid_breeds = await fetch_breeds()

    return valid_breeds

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)