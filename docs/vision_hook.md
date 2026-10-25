# NEXUS Vision Ingestion Hook — Architecture Design (Step 5.C.1)

This document specifies the architectural hook and interface for integrating a local small Vision-Language Model (VLM) into the NEXUS RAG and document ingestion pipeline without exceeding the laptop hardware budget.

---

## 1. Target Hardware & VRAM Allocation

- **Host Machine:** Laptop with NVIDIA RTX 4060 (8 GB VRAM).
- **Core LLM Allocation:** Qwen3 4B takes ~2.6 GB VRAM; Qwen3 8B takes ~5.5 GB VRAM.
- **VLM Strategy:** A vision model **must not run concurrently in GPU memory** with Qwen3 8B.
  - **Selected Model:** `Qwen2-VL-2B-Instruct` or `MiniCPM-V 2.6` (quantized 4-bit).
  - **VRAM Footprint:** ~1.8 GB to 2.2 GB.
  - **Execution Constraint:** Sequential time-slicing. When processing complex images or PDF architectural diagrams, the ingestion worker acquires the single GPU worker lock (`gpu_semaphore`), loads or calls the vision endpoint, and releases the lock before text reasoning resumes.

---

## 2. Ingestion Vision Hook Interface

```python
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class VisionDescription(BaseModel):
    caption: str
    extracted_text: str
    diagram_elements: List[str]
    confidence: float

class VisionIngestionHook:
    """Plugs into app.rag.ocr and app.rag.loaders for image/scanned PDF processing."""
    
    async def is_available(self) -> bool:
        """Returns True if local VLM endpoint is reachable."""
        ...

    async def describe_image(
        self,
        image_bytes: bytes,
        mime_type: str,
        prompt: Optional[str] = "Describe this technical diagram, including architecture, nodes, data flows, and code snippets.",
    ) -> VisionDescription:
        """Invokes local VLM to generate markdown description for chunk indexing."""
        ...
```

---

## 3. When to Trigger the Vision Hook

1. **Pure Images (`.png`, `.jpg`, `.jpeg`):**
   - Fallback if Tesseract/OCR produces $< 30$ words on an image $> 300\times300$ px (indicating a flowchart, UML diagram, or schematic).
2. **Embedded PDF Figures:**
   - Vector graphics or raster figures extracted during PyMuPDF parsing.
3. **Chunk Enrichment:**
   - The generated `VisionDescription.caption` is formatted as a synthetic knowledge chunk:
     `[Diagram Description: {caption}]` and embedded into ChromaDB alongside regular text chunks.
