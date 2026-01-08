"""
Quickstart example for DocMind-AI.

The simplest way to extract content from a document with multimodal support.
"""

from src.extractors import PDFExtractor
from src.graph import create_extraction_workflow


def main():
    # 1. Create extractor for your document
    pdf_path = "data/samples/sample_document.pdf"
    extractor = PDFExtractor(pdf_path)

    # 2. Create extraction workflow (vision enabled by default)
    workflow = create_extraction_workflow()

    # 3. Extract content
    result = workflow.extract(
        file_path=pdf_path,
        extractor=extractor
    )

    # 4. Access results
    print(f"Extracted {len(result.pages)} pages")
    print(f"Total cost: ${result.total_processing_cost:.4f}")
    print(f"Processing time: {result.total_processing_time:.2f}s")
    print(f"\nFull text:\n{result.full_text}")

    # Save to file
    with open("output/extracted.txt", "w") as f:
        f.write(result.to_text())

    # Clean up
    extractor.close()


if __name__ == "__main__":
    main()
