from app import db
from app.models import Image, Insights


class ImageService:
    @staticmethod
    def create_analysis_task(filepath, filename, file_size, format, width, height):
        try:
            image = Image(
                filename=filename,
                filepath=filepath,
                file_size=file_size,
                format=format,
                width=width,
                height=height,
                processed=False,
            )

            db.session.add(image)
            db.session.commit()

            return {"id": image.id, "status": "processing"}

        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Failed to create analysis task: {str(e)}")

    @staticmethod
    def get_analysis_results(image_id):
        try:
            if not isinstance(image_id, int):
                image_id = int(image_id)

            image = db.session.get(Image, image_id)

            if not image:
                return None

            if image.error_message:
                return {
                    "id": image.id,
                    "status": "failed",
                    "error": image.error_message,
                }

            if not image.processed:
                return {"id": image.id, "status": "processing"}

            insights = db.session.query(Insights).filter_by(image_id=image.id).first()

            if insights:
                return {
                    "id": image.id,
                    "status": "completed",
                    "insights": insights.to_dict(),
                }
            else:
                return {"id": image.id, "status": "completed", "insights": None}

        except Exception:
            return None
