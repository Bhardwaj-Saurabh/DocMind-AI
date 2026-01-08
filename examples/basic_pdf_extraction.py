"""
Basic example of using the PDF extractor with content analysis.

This example demonstrates:
1. Loading a PDF document
2. Analyzing each page's content
3. Viewing the recommended processing strategy
4. Extracting content from pages
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.extractors import PDFExtractor
from src.models import ProcessingStrategy


def main():
    """Main example function."""

    # Example PDF file path (you need to provide your own PDF)
    pdf_path = "sample.pdf"  # Replace with your PDF file

    if not Path(pdf_path).exists():
        print(f"Please provide a valid PDF file path.")
        print(f"Usage: python {__file__} <path_to_pdf>")
        return

    print("="* 80)
    print("DocMind-AI - PDF Extraction Example")
    print("=" * 80)

    # Initialize extractor
    print(f"\nLoading PDF: {pdf_path}")
    extractor = PDFExtractor(pdf_path)

    # Get metadata
    print("\n--- Document Metadata ---")
    metadata = extractor.get_metadata()
    print(f"Title: {metadata.title or 'N/A'}")
    print(f"Author: {metadata.author or 'N/A'}")
    print(f"Pages: {metadata.total_pages}")
    print(f"File size: {metadata.file_size / 1024:.1f} KB")
    print(f"Format: {metadata.format.value}")

    # Analyze all pages
    print("\n--- Page Analysis ---")
    print("Analyzing content on each page to determine optimal processing strategy...\n")

    total_cost = 0.0
    total_time = 0.0
    strategy_counts = {}

    for page_num in range(1, min(6, metadata.total_pages + 1)):  # Analyze first 5 pages
        print(f"Page {page_num}:")

        # Analyze content
        analysis = extractor.analyze_page_content(page_num)

        print(f"  Content Type: {analysis.content_type.value}")
        print(f"  Text Quality: {analysis.text_quality.value}")
        print(f"  Text Length: {analysis.text_length} characters")
        print(f"  Images: {analysis.embedded_images_count}")
        print(f"  Tables: {analysis.table_info.count} ({analysis.table_info.complexity})")
        print(f"  Charts: {analysis.charts_count}")
        print(f"  Is Scanned: {analysis.is_scanned}")
        print(f"  → Recommended Strategy: {analysis.recommended_strategy.value}")
        print(f"  → Estimated Cost: ${analysis.estimated_cost:.4f}")
        print(f"  → Estimated Time: {analysis.estimated_time:.2f}s")
        print()

        total_cost += analysis.estimated_cost
        total_time += analysis.estimated_time

        strategy = analysis.recommended_strategy.value
        strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1

    # Show totals
    print("--- Processing Summary ---")
    print(f"Total Estimated Cost: ${total_cost:.4f}")
    print(f"Total Estimated Time: {total_time:.2f}s")
    print(f"\nStrategy Breakdown:")
    for strategy, count in strategy_counts.items():
        print(f"  {strategy}: {count} pages")

    # Extract content from first page
    print("\n--- Sample Extraction ---")
    print("Extracting content from page 1...\n")

    page_content = extractor.extract_page(1)
    print(f"Text Preview (first 300 chars):")
    print(page_content.text[:300] if page_content.text else "No text found")
    print(f"\nWord Count: {page_content.word_count}")
    print(f"Processing Cost: ${page_content.processing_cost:.4f}")

    # Cleanup
    extractor.close()

    print("\n" + "=" * 80)
    print("Example complete!")
    print("=" * 80)


if __name__ == "__main__":
    # Accept PDF path from command line if provided
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        main()
    else:
        print("Please provide a PDF file path:")
        print(f"Usage: python {sys.argv[0]} <path_to_pdf>")
