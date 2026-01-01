from fastapi import FastAPI, HTTPException, status

import httpx

async def fetch_breeds() -> list:
    valid_breeds = []
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("https://api.thecatapi.com/v1/breeds")
            breeds_data = response.json()
            valid_breeds = [breed["name"] for breed in breeds_data]
    except Exception as e:
        print(f"Failed to fetch breeds: {e}")
        valid_breeds = []

    return valid_breeds


# Helper function to validate breed
async def validate_breed(breed: str, valid_breeds: list):
    if breed not in valid_breeds:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid breed. Must be one of the valid cat breeds from TheCatAPI"
        )