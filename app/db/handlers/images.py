import json
from uuid import UUID
from datetime import timezone
from app.db.handlers.base import BaseHandler
from app.models.image import ImageCreate, ImageRead

class ImageHandler(BaseHandler):
    async def create(self, image: ImageCreate) -> ImageRead:
        captured_at = image.captured_at
        if captured_at and captured_at.tzinfo:
            # Convert to UTC and strip tzinfo for TIMESTAMP (naive) column
            captured_at = captured_at.astimezone(timezone.utc).replace(tzinfo=None)

        if image.id:
            query = """
                INSERT INTO images (id, device_id, status, captured_at, image_path, context, route_key)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id, device_id, status, captured_at, image_path, context, route_key
            """
            args = (
                image.id,
                image.device_id,
                image.status,
                captured_at,
                image.image_path,
                json.dumps(image.context),
                image.route_key
            )
        else:
            query = """
                INSERT INTO images (device_id, status, captured_at, image_path, context, route_key)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id, device_id, status, captured_at, image_path, context, route_key
            """
            args = (
                image.device_id,
                image.status,
                captured_at,
                image.image_path,
                json.dumps(image.context),
                image.route_key
            )

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, *args)
            return ImageRead(
                id=row['id'],
                device_id=row['device_id'],
                status=row['status'],
                captured_at=row['captured_at'],
                image_path=row['image_path'],
                context=json.loads(row['context']) if isinstance(row['context'], str) else row['context'],
                route_key=row['route_key']
            )
