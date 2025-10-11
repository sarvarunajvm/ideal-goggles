"""Face detection and recognition worker (optional feature)."""

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import numpy as np

from ..models.person import Face, Person
from ..models.photo import Photo

logger = logging.getLogger(__name__)


class FaceDetectionWorker:
    """Worker for face detection and recognition using InsightFace."""

    def __init__(
        self,
        max_workers: int = 2,
        model_name: str = "buffalo_l",
        detection_threshold: float = 0.5,
    ):
        self.max_workers = max_workers
        self.model_name = model_name
        self.detection_threshold = detection_threshold
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

        # Face detection and recognition models
        self.face_app = None
        self.device = "cpu"  # InsightFace typically uses CPU by default

        # Statistics
        self.stats = {
            "photos_processed": 0,
            "faces_detected": 0,
            "faces_recognized": 0,
            "processing_time": 0.0,
            "failed_detections": 0,
        }

        # Initialize face models
        self._initialize_face_models()

    def _initialize_face_models(self):
        """Initialize InsightFace models for detection and recognition."""
        try:
            import insightface
            from insightface.app import FaceAnalysis

            # Initialize face analysis app
            self.face_app = FaceAnalysis(
                name=self.model_name,
                providers=["CPUExecutionProvider"],  # Use CPU for stability
            )
            self.face_app.prepare(ctx_id=0, det_size=(640, 640))

            logger.info(f"InsightFace initialized with model: {self.model_name}")

        except ImportError as e:
            logger.warning(f"InsightFace not available: {e}")
            self.face_app = None
        except Exception as e:
            logger.exception(f"Failed to initialize InsightFace: {e}")
            self.face_app = None

    async def detect_faces(self, photo: Photo) -> list[Face]:
        """Detect faces in a photo."""
        if not self.face_app:
            logger.warning("Face detection not available (InsightFace not initialized)")
            return []

        start_time = time.time()

        try:
            # Run face detection in thread pool
            loop = asyncio.get_event_loop()
            detections = await loop.run_in_executor(
                self.executor, self._detect_faces_sync, photo.path
            )

            processing_time = time.time() - start_time
            self.stats["photos_processed"] += 1
            self.stats["processing_time"] += processing_time

            if detections:
                faces = []
                for detection in detections:
                    face = Face.from_detection_result(photo.id, detection)
                    faces.append(face)

                self.stats["faces_detected"] += len(faces)
                logger.debug(f"Detected {len(faces)} faces in {photo.path}")
                return faces
            return []

        except Exception as e:
            logger.warning(f"Face detection failed for {photo.path}: {e}")
            self.stats["failed_detections"] += 1
            return []

    def _detect_faces_sync(self, file_path: str) -> list[dict[str, Any]]:
        """Synchronously detect faces using InsightFace."""
        try:
            import cv2

            # Load image
            img = cv2.imread(file_path)
            if img is None:
                logger.debug(f"Could not load image: {file_path}")
                return []

            # Convert BGR to RGB
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            # Detect faces
            faces = self.face_app.get(img_rgb)

            detections = []
            for face in faces:
                # Extract bounding box (x1, y1, x2, y2)
                bbox = face.bbox.astype(int).tolist()

                # Extract face embedding
                embedding = face.normed_embedding.astype(np.float32)

                # Get detection confidence
                confidence = float(face.det_score)

                # Filter by confidence threshold
                if confidence >= self.detection_threshold:
                    detections.append(
                        {
                            "bbox": bbox,
                            "embedding": embedding,
                            "confidence": confidence,
                            "landmarks": (
                                face.kps.tolist() if hasattr(face, "kps") else None
                            ),
                        }
                    )

            return detections

        except Exception as e:
            logger.debug(f"InsightFace detection failed for {file_path}: {e}")
            return []

    async def recognize_faces(
        self, faces: list[Face], people: list[Person], similarity_threshold: float = 0.6
    ) -> list[dict[str, Any]]:
        """Recognize faces against enrolled people."""
        if not faces or not people:
            return []

        recognition_results = []

        for face in faces:
            if face.face_vector is None:
                continue

            best_match = None
            best_similarity = 0.0

            # Compare against all enrolled people
            for person in people:
                if not person.active or person.face_vector is None:
                    continue

                similarity = face.similarity_to_person(person)

                if similarity > best_similarity and similarity >= similarity_threshold:
                    best_similarity = similarity
                    best_match = person

            result = {
                "face": face,
                "matched_person": best_match,
                "similarity": best_similarity,
                "above_threshold": best_similarity >= similarity_threshold,
            }

            recognition_results.append(result)

            if best_match:
                self.stats["faces_recognized"] += 1

        return recognition_results

    async def process_batch(self, photos: list[Photo]) -> list[list[Face]]:
        """Process multiple photos for face detection."""
        if not photos:
            return []

        logger.info(f"Processing {len(photos)} photos for face detection")

        # Create tasks for concurrent processing
        tasks = [self.detect_faces(photo) for photo in photos]

        # Process with progress logging
        results = []
        for i, task in enumerate(asyncio.as_completed(tasks)):
            result = await task
            results.append(result)

            # Log progress periodically
            if (i + 1) % 50 == 0:
                logger.info(f"Face detection progress: {i + 1}/{len(photos)}")

        total_faces = sum(len(face_list) for face_list in results)
        logger.info(
            f"Face detection completed: {total_faces} faces detected across {len(photos)} photos"
        )

        return results

    async def enroll_person(
        self, name: str, sample_photos: list[Photo]
    ) -> Person | None:
        """Enroll a new person using sample photos."""
        if not sample_photos:
            msg = "At least one sample photo is required"
            raise ValueError(msg)

        logger.info(
            f"Enrolling person '{name}' with {len(sample_photos)} sample photos"
        )

        # Detect faces in all sample photos
        all_face_vectors = []

        for photo in sample_photos:
            faces = await self.detect_faces(photo)

            # For enrollment, we typically want high-confidence single faces
            high_conf_faces = [f for f in faces if f.confidence >= 0.8]

            if len(high_conf_faces) == 1:
                # Single high-confidence face is ideal
                all_face_vectors.append(high_conf_faces[0].face_vector)
            elif len(high_conf_faces) > 1:
                # Multiple faces - would need user to select which one
                logger.warning(f"Multiple faces detected in sample photo {photo.path}")
                # For now, take the highest confidence face
                best_face = max(high_conf_faces, key=lambda f: f.confidence)
                all_face_vectors.append(best_face.face_vector)
            else:
                logger.warning(f"No high-confidence faces in sample photo {photo.path}")

        if len(all_face_vectors) < 1:
            msg = "No suitable faces found in sample photos"
            raise ValueError(msg)

        # Create person with averaged face vector
        person = Person.create_from_face_vectors(name, all_face_vectors)

        logger.info(
            f"Successfully enrolled person '{name}' with {len(all_face_vectors)} face samples"
        )
        return person

    async def update_person_enrollment(
        self, person: Person, additional_photos: list[Photo]
    ) -> Person:
        """Update person enrollment with additional sample photos."""
        logger.info(
            f"Updating enrollment for '{person.name}' with {len(additional_photos)} additional photos"
        )

        # Detect faces in additional photos
        new_face_vectors = []

        for photo in additional_photos:
            faces = await self.detect_faces(photo)
            high_conf_faces = [f for f in faces if f.confidence >= 0.8]

            if high_conf_faces:
                best_face = max(high_conf_faces, key=lambda f: f.confidence)
                new_face_vectors.append(best_face.face_vector)

        if new_face_vectors:
            person.update_face_vector(new_face_vectors)
            logger.info(
                f"Updated '{person.name}' with {len(new_face_vectors)} new face samples"
            )

        return person

    def get_statistics(self) -> dict[str, Any]:
        """Get face processing statistics."""
        avg_time_per_photo = (
            self.stats["processing_time"] / self.stats["photos_processed"]
            if self.stats["photos_processed"] > 0
            else 0
        )

        return {
            "photos_processed": self.stats["photos_processed"],
            "faces_detected": self.stats["faces_detected"],
            "faces_recognized": self.stats["faces_recognized"],
            "failed_detections": self.stats["failed_detections"],
            "average_faces_per_photo": (
                self.stats["faces_detected"] / self.stats["photos_processed"]
                if self.stats["photos_processed"] > 0
                else 0
            ),
            "recognition_rate": (
                self.stats["faces_recognized"] / self.stats["faces_detected"]
                if self.stats["faces_detected"] > 0
                else 0
            ),
            "average_processing_time": avg_time_per_photo,
            "total_processing_time": self.stats["processing_time"],
            "model_name": self.model_name,
            "detection_threshold": self.detection_threshold,
            "model_available": self.face_app is not None,
        }

    def reset_statistics(self):
        """Reset face processing statistics."""
        self.stats = {
            "photos_processed": 0,
            "faces_detected": 0,
            "faces_recognized": 0,
            "processing_time": 0.0,
            "failed_detections": 0,
        }

    def is_available(self) -> bool:
        """Check if face detection is available."""
        return self.face_app is not None

    def shutdown(self):
        """Shutdown the executor and clean up resources."""
        self.executor.shutdown(wait=True)


class FaceSearchEngine:
    """Engine for searching photos by face similarity."""

    def __init__(self, similarity_threshold: float = 0.6):
        self.similarity_threshold = similarity_threshold

    async def search_by_person(
        self, target_person: Person, all_faces: list[Face], top_k: int = 50
    ) -> list[dict[str, Any]]:
        """Search for photos containing a specific person."""
        if target_person.face_vector is None or not all_faces:
            return []

        matches = []

        for face in all_faces:
            if face.face_vector is None:
                continue

            similarity = face.similarity_to_person(target_person)

            if similarity >= self.similarity_threshold:
                matches.append(
                    {
                        "face": face,
                        "file_id": face.file_id,
                        "similarity": similarity,
                        "confidence": face.confidence,
                        "person_id": target_person.id,
                    }
                )

        # Sort by similarity (highest first)
        matches.sort(key=lambda x: x["similarity"], reverse=True)

        return matches[:top_k]

    async def search_by_face_image(
        self, query_face_vector: np.ndarray, all_faces: list[Face], top_k: int = 50
    ) -> list[dict[str, Any]]:
        """Search for similar faces using a query face vector."""
        if query_face_vector is None or not all_faces:
            return []

        matches = []

        for face in all_faces:
            if face.face_vector is None:
                continue

            # Calculate cosine similarity
            similarity = float(np.dot(face.face_vector, query_face_vector))

            if similarity >= self.similarity_threshold:
                matches.append(
                    {
                        "face": face,
                        "file_id": face.file_id,
                        "similarity": similarity,
                        "confidence": face.confidence,
                        "person_id": face.person_id,
                    }
                )

        # Sort by similarity (highest first)
        matches.sort(key=lambda x: x["similarity"], reverse=True)

        return matches[:top_k]

    async def find_duplicate_faces(
        self, faces: list[Face], duplicate_threshold: float = 0.95
    ) -> list[list[Face]]:
        """Find groups of very similar faces (potential duplicates)."""
        if not faces:
            return []

        duplicate_groups = []
        processed = set()

        for i, face1 in enumerate(faces):
            if i in processed or face1.face_vector is None:
                continue

            group = [face1]
            processed.add(i)

            for j, face2 in enumerate(faces[i + 1 :], i + 1):
                if j in processed or face2.face_vector is None:
                    continue

                similarity = face1.similarity_to_face(face2)

                if similarity >= duplicate_threshold:
                    group.append(face2)
                    processed.add(j)

            if len(group) > 1:
                duplicate_groups.append(group)

        return duplicate_groups

    async def cluster_unknown_faces(
        self, unknown_faces: list[Face], cluster_threshold: float = 0.7
    ) -> list[list[Face]]:
        """Cluster unknown faces into potential person groups."""
        if not unknown_faces:
            return []

        # Simple clustering based on similarity
        clusters = []
        processed = set()

        for i, face1 in enumerate(unknown_faces):
            if i in processed or face1.face_vector is None:
                continue

            cluster = [face1]
            processed.add(i)

            for j, face2 in enumerate(unknown_faces[i + 1 :], i + 1):
                if j in processed or face2.face_vector is None:
                    continue

                # Check similarity to any face in current cluster
                max_similarity = 0.0
                for cluster_face in cluster:
                    similarity = face2.similarity_to_face(cluster_face)
                    max_similarity = max(max_similarity, similarity)

                if max_similarity >= cluster_threshold:
                    cluster.append(face2)
                    processed.add(j)

            clusters.append(cluster)

        # Sort clusters by size (largest first)
        clusters.sort(key=len, reverse=True)

        return clusters


class FaceQualityAnalyzer:
    """Analyzer for face detection and recognition quality."""

    @staticmethod
    def analyze_face_quality(face: Face) -> dict[str, Any]:
        """Analyze quality of a detected face."""
        quality_score = 0.0
        issues = []

        # Check detection confidence
        if face.confidence >= 0.9:
            quality_score += 0.3
        elif face.confidence >= 0.7:
            quality_score += 0.2
        elif face.confidence >= 0.5:
            quality_score += 0.1
        else:
            issues.append("Low detection confidence")

        # Check bounding box size
        box_area = face.get_box_area()
        if box_area >= 10000:  # Large face
            quality_score += 0.3
        elif box_area >= 5000:  # Medium face
            quality_score += 0.2
        elif box_area >= 2000:  # Small face
            quality_score += 0.1
        else:
            issues.append("Very small face detection")

        # Check face vector quality
        if face.face_vector is not None:
            vector_norm = np.linalg.norm(face.face_vector)
            if 0.9 <= vector_norm <= 1.1:  # Well normalized
                quality_score += 0.2
            else:
                issues.append("Face vector normalization issue")

            # Check for reasonable value distribution
            vector_std = np.std(face.face_vector)
            if vector_std > 0.1:
                quality_score += 0.2
            else:
                issues.append("Low feature diversity in face vector")
        else:
            issues.append("No face vector available")

        return {
            "quality_score": min(1.0, quality_score),
            "quality_grade": FaceQualityAnalyzer._get_quality_grade(quality_score),
            "issues": issues,
            "suitable_for_enrollment": quality_score >= 0.7,
            "suitable_for_recognition": quality_score >= 0.5,
        }

    @staticmethod
    def _get_quality_grade(score: float) -> str:
        """Convert quality score to letter grade."""
        if score >= 0.9:
            return "A"
        if score >= 0.7:
            return "B"
        if score >= 0.5:
            return "C"
        if score >= 0.3:
            return "D"
        return "F"

    @staticmethod
    def analyze_enrollment_quality(
        person: Person, sample_faces: list[Face]
    ) -> dict[str, Any]:
        """Analyze quality of person enrollment."""
        if not sample_faces:
            return {
                "enrollment_quality": 0.0,
                "recommendations": ["No sample faces provided"],
            }

        # Analyze individual face qualities
        face_qualities = [
            FaceQualityAnalyzer.analyze_face_quality(face) for face in sample_faces
        ]

        avg_quality = sum(fq["quality_score"] for fq in face_qualities) / len(
            face_qualities
        )
        high_quality_faces = sum(
            1 for fq in face_qualities if fq["quality_score"] >= 0.7
        )

        recommendations = []

        # Check number of samples
        if len(sample_faces) < 3:
            recommendations.append("Add more sample photos (recommended: 3-5)")

        # Check quality distribution
        if high_quality_faces < len(sample_faces) * 0.6:
            recommendations.append(
                "Improve sample photo quality (better lighting, larger faces)"
            )

        # Check diversity (if we had pose/angle information)
        recommendations.append(
            "Ensure sample photos show different angles and expressions"
        )

        enrollment_quality = min(1.0, avg_quality * (1.0 + len(sample_faces) * 0.1))

        return {
            "enrollment_quality": enrollment_quality,
            "average_face_quality": avg_quality,
            "high_quality_samples": high_quality_faces,
            "total_samples": len(sample_faces),
            "recommendations": recommendations,
            "face_qualities": face_qualities,
        }
