"""
End-to-end multimodal document extraction example.

This example demonstrates the complete DocMind-AI workflow with vision processing:
1. Content analysis for each page
2. Adaptive routing based on content type
3. Text extraction for simple pages
4. Vision API processing for complex visual content
5. Cost tracking and optimization

Expected document structure for best demonstration:
- Pages with pure text (reports, articles)
- Pages with charts/graphs
- Pages with images/diagrams
- Pages with tables
- Scanned document pages
"""

import os
from pathlib import Path

from src.extractors import PDFExtractor
from src.graph import create_extraction_workflow
from src.models import ProcessingStrategy
from src.utils import get_logger, setup_logger


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def print_page_analysis(page_num: int, analysis, result):
    """Print detailed analysis for a single page."""
    print(f"\n📄 Page {page_num + 1}:")
    print(f"   Content Type: {analysis.content_type.value}")
    print(f"   Strategy: {analysis.recommended_strategy.value}")
    print(f"   Text Quality: {analysis.text_quality.value}")
    print(f"   Images: {analysis.image_count}, Tables: {analysis.table_count}, Charts: {analysis.chart_count}")
    print(f"   Processing Time: {result.processing_time:.2f}s")
    print(f"   Processing Cost: ${result.processing_cost:.4f}")

    if result.extracted_images:
        print(f"   → Extracted {len(result.extracted_images)} images")
    if result.extracted_tables:
        print(f"   → Extracted {len(result.extracted_tables)} tables")
    if result.extracted_charts:
        print(f"   → Extracted {len(result.extracted_charts)} charts")


def calculate_naive_cost(result):
    """Calculate what the cost would be if we used vision API for all pages."""
    # Naive approach: process every page with vision API
    # Average vision cost per page: ~$0.02
    VISION_COST_PER_PAGE = 0.02
    return len(result.pages) * VISION_COST_PER_PAGE


def print_cost_analysis(result):
    """Print detailed cost analysis and savings."""
    print_section("Cost Analysis")

    # Actual costs
    actual_cost = result.total_processing_cost
    naive_cost = calculate_naive_cost(result)
    savings = naive_cost - actual_cost
    savings_pct = (savings / naive_cost * 100) if naive_cost > 0 else 0

    print(f"Adaptive Approach (DocMind-AI):")
    print(f"  Total Cost: ${actual_cost:.4f}")
    print(f"  Processing Time: {result.total_processing_time:.2f}s")
    print(f"  Average Quality Score: {result.average_quality_score:.2f}")

    print(f"\nNaive Approach (Vision API for all pages):")
    print(f"  Estimated Cost: ${naive_cost:.4f}")
    print(f"  Estimated Time: {len(result.pages) * 3.0:.2f}s (assuming 3s per vision call)")

    print(f"\n💰 Cost Savings: ${savings:.4f} ({savings_pct:.1f}% reduction)")
    print(f"⚡ Time Savings: {(len(result.pages) * 3.0 - result.total_processing_time):.2f}s")

    # Strategy breakdown
    print(f"\nStrategy Breakdown:")
    for strategy, count in result.strategies_used.items():
        print(f"  {strategy}: {count} pages")


def print_extraction_summary(result):
    """Print high-level extraction summary."""
    print_section("Extraction Summary")

    print(f"Document: {result.metadata.filename}")
    print(f"Total Pages: {result.metadata.total_pages}")
    print(f"File Size: {result.metadata.file_size / 1024:.1f} KB")
    print(f"Success: {'✅ Yes' if result.success else '❌ No'}")

    if result.errors:
        print(f"\n⚠️  Errors ({len(result.errors)}):")
        for error in result.errors:
            print(f"  - {error}")

    if result.warnings:
        print(f"\n⚠️  Warnings ({len(result.warnings)}):")
        for warning in result.warnings:
            print(f"  - {warning}")


def export_results(result, output_dir: Path):
    """Export extraction results to files."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Export full text
    text_file = output_dir / f"{result.metadata.filename}_extracted.txt"
    with open(text_file, "w", encoding="utf-8") as f:
        f.write(result.to_text())

    # Export markdown
    md_file = output_dir / f"{result.metadata.filename}_extracted.md"
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(result.to_markdown())

    # Export processing report
    report_file = output_dir / f"{result.metadata.filename}_report.txt"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(result.get_processing_report())

    print(f"\n📁 Results exported to: {output_dir}")
    print(f"  - {text_file.name}")
    print(f"  - {md_file.name}")
    print(f"  - {report_file.name}")


def main():
    """Run the multimodal extraction example."""
    # Setup logging
    setup_logger(level="INFO", log_file="logs/multimodal_example.log")
    logger = get_logger()

    print_section("DocMind-AI: Multimodal Document Extraction")

    # Get PDF file path from command line or use default
    import sys
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        # Use a sample PDF if available
        pdf_path = "data/samples/sample_document.pdf"
        if not os.path.exists(pdf_path):
            print(f"❌ No PDF file provided and sample not found at: {pdf_path}")
            print(f"\nUsage: python examples/multimodal_extraction.py <path_to_pdf>")
            print(f"\nFor best results, use a document with:")
            print(f"  - Pure text pages (articles, reports)")
            print(f"  - Charts and graphs")
            print(f"  - Images and diagrams")
            print(f"  - Tables with data")
            return

    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        return

    print(f"📄 Processing: {pdf_path}")

    # Step 1: Create PDF extractor
    print("\n🔧 Initializing PDF extractor...")
    extractor = PDFExtractor(pdf_path)
    print(f"   ✅ Loaded {extractor.page_count} pages")

    # Step 2: Create workflow with vision enabled
    print("\n🤖 Creating extraction workflow...")
    workflow = create_extraction_workflow()

    if workflow.enable_vision:
        print("   ✅ Vision processing enabled")
    else:
        print("   ⚠️  Vision processing disabled (no API key)")
        print("   💡 Set OPENAI_API_KEY in .env to enable vision features")

    # Step 3: Run extraction
    print("\n🚀 Starting extraction workflow...\n")
    print("This may take a few moments depending on document complexity...")

    try:
        result = workflow.extract(
            file_path=pdf_path,
            extractor=extractor,
            config=None  # Use default config
        )

        # Step 4: Display results
        print_extraction_summary(result)

        # Step 5: Page-by-page analysis
        print_section("Page-by-Page Analysis")

        # Get page analyses from extractor
        analyses = []
        for i in range(extractor.page_count):
            analysis = extractor.analyze_page_content(i)
            analyses.append(analysis)

        for i, (analysis, page_result) in enumerate(zip(analyses, result.pages)):
            print_page_analysis(i, analysis, page_result)

        # Step 6: Cost analysis
        print_cost_analysis(result)

        # Step 7: Export results
        print_section("Exporting Results")
        output_dir = Path("output/multimodal_example")
        export_results(result, output_dir)

        # Step 8: Content preview
        print_section("Content Preview")
        preview_length = 500
        if len(result.full_text) > preview_length:
            print(result.full_text[:preview_length] + "...")
            print(f"\n(Showing first {preview_length} characters of {len(result.full_text)} total)")
        else:
            print(result.full_text)

        print_section("Extraction Complete! ✅")

    except Exception as e:
        logger.error(f"Extraction failed: {e}", exc_info=True)
        print(f"\n❌ Extraction failed: {e}")
        return

    finally:
        extractor.close()


if __name__ == "__main__":
    main()
