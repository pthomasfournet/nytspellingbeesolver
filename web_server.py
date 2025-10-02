#!/usr/bin/env python3
"""
FastAPI Web Server for Spelling Bee Solver

Production-ready web API with:
- RESTful /api/solve endpoint
- Static file serving for PWA
- CORS support for development
- Comprehensive error handling
- Request validation with Pydantic
"""

import logging
import time
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from starlette.types import Scope

# Import our existing solver (zero code duplication!)
from src.spelling_bee_solver.unified_solver import UnifiedSpellingBeeSolver

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# === Lifespan Events ===

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    # Startup
    logger.info("=" * 60)
    logger.info("🐝 Spelling Bee Solver API Starting...")
    logger.info("=" * 60)
    logger.info("API Documentation: http://localhost:8000/api/docs")
    logger.info("Web Interface: http://localhost:8000/")
    logger.info("=" * 60)

    yield

    # Shutdown
    logger.info("🐝 Spelling Bee Solver API Shutting down...")

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Spelling Bee Solver API",
    description="RESTful API for solving NYT Spelling Bee puzzles",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# CORS configuration (allow all origins in development, restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Initialize solver once (singleton pattern for performance)
solver: Optional[UnifiedSpellingBeeSolver] = None


def get_solver() -> UnifiedSpellingBeeSolver:
    """Get or create solver instance (lazy initialization)."""
    global solver
    if solver is None:
        logger.info("Initializing UnifiedSpellingBeeSolver...")
        try:
            solver = UnifiedSpellingBeeSolver(verbose=False)
            logger.info("✓ Solver initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize solver: %s", e)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Solver initialization failed: {str(e)}"
            )
    return solver


# === Pydantic Models ===

class PuzzleRequest(BaseModel):
    """Request model for puzzle solving."""
    center_letter: str = Field(..., min_length=1, max_length=1,
                                description="Required center letter (1 character)")
    other_letters: str = Field(..., min_length=6, max_length=6,
                                description="The other 6 puzzle letters")
    exclude_words: Optional[List[str]] = Field(default=None, max_items=200,
                                                description="Words to exclude from results")

    @field_validator('center_letter', 'other_letters')
    @classmethod
    def validate_letters(cls, v):
        """Ensure only alphabetic characters."""
        if not v.isalpha():
            raise ValueError(f"Must contain only letters, got: {v}")
        return v.lower()

    @field_validator('exclude_words')
    @classmethod
    def validate_exclude_words(cls, v):
        """Normalize excluded words."""
        if v is None:
            return None
        return [word.lower().strip() for word in v if word and word.strip()]


class WordResult(BaseModel):
    """Individual word result."""
    word: str
    confidence: float = Field(..., ge=0, le=100)
    is_pangram: bool
    length: int = Field(..., ge=4)


class PuzzleStats(BaseModel):
    """Puzzle statistics."""
    total_found: int
    excluded_count: int
    remaining: int
    progress_percent: float = Field(..., ge=0, le=100)
    solve_time: float
    pangram_count: int


class PuzzleResponse(BaseModel):
    """Response model for successful solve."""
    success: bool = True
    puzzle: dict  # {letters, center}
    results: List[WordResult]
    stats: PuzzleStats
    excluded_words: List[str]


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = False
    error: str
    detail: Optional[str] = None


# === API Endpoints ===

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Test solver initialization
        get_solver()
        return {
            "status": "healthy",
            "service": "Spelling Bee Solver API",
            "version": "1.0.0",
            "solver_ready": True
        }
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": str(e),
                "solver_ready": False
            }
        )


@app.post("/api/solve", response_model=PuzzleResponse)
async def solve_puzzle(request: PuzzleRequest):
    """
    Solve a Spelling Bee puzzle.

    Args:
        request: Puzzle parameters (center letter, other letters, exclude words)

    Returns:
        PuzzleResponse with words, stats, and metadata

    Raises:
        HTTPException: 400 for invalid input, 500 for solver errors
    """
    start_time = time.time()

    try:
        # Get solver instance
        solver_instance = get_solver()

        # Convert exclude words list to set
        exclude_set = set(request.exclude_words) if request.exclude_words else None

        # Call solver (reuses existing implementation!)
        results = solver_instance.solve_puzzle(
            required_letter=request.center_letter,
            letters=request.other_letters,
            exclude_words=exclude_set
        )

        # Extract stats from solver (ensure defaults if not present)
        stats = solver_instance.stats
        excluded_count = stats.get("excluded_count", 0) if exclude_set else 0
        excluded_words = stats.get("excluded_words", []) if exclude_set else []
        solve_time = stats.get("solve_time", 0.0)

        # Calculate additional stats
        total_found = len(results) + excluded_count
        progress_percent = (excluded_count / total_found * 100) if total_found > 0 else 0

        # Count pangrams
        all_letters_set = set(request.center_letter + request.other_letters)
        pangram_count = sum(1 for word, _ in results if len(set(word)) == 7)

        # Format response
        word_results = [
            WordResult(
                word=word,
                confidence=round(confidence, 1),
                is_pangram=len(set(word)) == 7,
                length=len(word)
            )
            for word, confidence in results
        ]

        response = PuzzleResponse(
            puzzle={
                "letters": request.center_letter + request.other_letters,
                "center": request.center_letter
            },
            results=word_results,
            stats=PuzzleStats(
                total_found=total_found,
                excluded_count=excluded_count,
                remaining=len(results),
                progress_percent=round(progress_percent, 1),
                solve_time=round(solve_time, 3),
                pangram_count=pangram_count
            ),
            excluded_words=excluded_words
        )

        logger.info(
            "Solved puzzle %s (center: %s) in %.3fs - %d words, %d excluded",
            request.center_letter + request.other_letters,
            request.center_letter,
            time.time() - start_time,
            len(results),
            excluded_count
        )

        return response

    except ValueError as e:
        # Input validation errors from solver
        logger.warning("Invalid puzzle input: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:
        # Unexpected solver errors
        logger.error("Solver error: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Solver error: {str(e)}"
        )


# === Static File Serving ===

class NoCacheStaticFiles(StaticFiles):
    """StaticFiles with no-cache headers for development."""

    async def get_response(self, path: str, scope: Scope) -> Response:
        response = await super().get_response(path, scope)
        # Prevent browser caching during development
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

# Mount static directory (for PWA frontend)
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/", NoCacheStaticFiles(directory=str(static_dir), html=True), name="static")
    logger.info("✓ Serving static files from: %s (no-cache for dev)", static_dir)
else:
    logger.warning("Static directory not found: %s", static_dir)


# === Error Handlers ===

@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 handler."""
    return JSONResponse(
        status_code=404,
        content=ErrorResponse(
            error="Not Found",
            detail=f"Endpoint not found: {request.url.path}"
        ).dict()
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Custom 500 handler."""
    logger.error("Internal server error: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal Server Error",
            detail="An unexpected error occurred. Please try again."
        ).dict()
    )




# === Main (for development) ===

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "web_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Hot reload in development
        log_level="info"
    )
