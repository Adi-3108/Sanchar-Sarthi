import asyncio
import logging
from typing import Any

from sqlalchemy import select
from app.db.session import SessionLocal
from app.orm.incident import Incident
from app.services.map_route_service import RouteRequest, get_route, _ROUTE_CACHE, route_cache_key
from app.core.config import get_settings

logger = logging.getLogger(__name__)

async def _fetch_routes_loop():
    logger.info("Starting background route fetcher loop")
    while True:
        try:
            await asyncio.sleep(10)  # Check every 10 seconds
            
            # Use a new DB session
            with SessionLocal() as db:
                # Fetch active/confirmed incidents
                incidents = db.scalars(
                    select(Incident).where(
                        Incident.status.in_(["active", "confirmed"])
                    )
                ).all()

                for incident in incidents:
                    if not incident.latitude or not incident.longitude:
                        continue
                        
                    # Standard dummy destination for all routes just as a generic bypass route
                    # In a real app, destination might be specific to the incident's patrol area
                    # For now, we'll route from the incident to a fixed nearby offset
                    lng, lat = float(incident.longitude), float(incident.latitude)
                    # Match frontend exactly so cache keys align
                    origin = (lng - 0.015, lat + 0.015)
                    destination = (lng + 0.015, lat - 0.015)
                    
                    req = RouteRequest(
                        origin=origin,
                        destination=destination,
                        incident_id=incident.id
                    )
                    
                    c_key = route_cache_key(req)
                    
                    if c_key not in _ROUTE_CACHE:
                        logger.info(f"Background fetching route for incident {incident.id}")
                        try:
                            # Run synchronous HTTP request in threadpool
                            await asyncio.to_thread(get_route, db, req)
                            # Sleep 2 seconds after a successful API call to avoid overloading MapmyIndia
                            await asyncio.sleep(2)
                        except Exception as e:
                            logger.error(f"Failed to fetch route for {incident.id}: {e}")

        except asyncio.CancelledError:
            logger.info("Background route fetcher cancelled")
            break
        except Exception as e:
            logger.error(f"Error in background route fetcher: {e}")
            await asyncio.sleep(10)
