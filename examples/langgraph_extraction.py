"""
Complete example using LangGraph workflow for document extraction.

This example demonstrates:
1. Creating an extraction workflow with LangGraph
2. Content analysis with strategy recommendation
3. Adaptive processing (text-only for now)
4. Cost and time tracking
5. Generating a processing report
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extractors import PDFExtractor
from src.graph import create_extraction_workflow


def print_separator(title=""):
    """Print a formatted separator."""
    if title:
        print(f"\n{'=' * 80}")
        print(f"  {title}")
        print('=' * 80)
    else:
        print('=' * 80)


def main(pdf_path: str):
    """Main example function."""

    print_separator("DocMind-AI - LangGraph Extraction Workflow")

    print(f"\n📄 Loading PDF: {pdf_path}\n")

    # Initialize extractor
    extractor = PDFExtractor(pdf_path)

    try:
        print("🔧 Creating extraction workflow...")
        workflow = create_extraction_workflow()

        print("🚀 Starting extraction with LangGraph...\n")
        print_separator("Extraction Process")

        # Run the extraction workflow
        result = workflow.extract(
            file_path=pdf_path,
            extractor=extractor,
        )

        print_separator("Extraction Complete!")

        # Display results
        print("\n📊 Processing Report")
        print_separator()

        report = result.get_processing_report()

        # Document info
        print("\n📄 Document:")
        print(f"   File: {report['document']['file_name']}")
        print(f"   Format: {report['document']['format']}")
        print(f"   Pages: {report['document']['total_pages']}")

        # Content summary
        print("\n📝 Content Summary:")
        print(f"   Total Words: {report['content_summary']['total_words']:,}")
        print(f"   Total Images: {report['content_summary']['total_images']}")
        print(f"   Total Tables: {report['content_summary']['total_tables']}")
        print(f"   Total Charts: {report['content_summary']['total_charts']}")

        # Processing metrics
        print("\n⚡ Processing:")
        print(f"   Total Time: {report['processing']['total_time']}")
        print(f"   Total Cost: {report['processing']['total_cost']}")
        print(f"   Avg Time/Page: {report['processing']['average_time_per_page']}")
        print(f"   Avg Cost/Page: {report['processing']['average_cost_per_page']}")

        # Quality
        print("\n✨ Quality:")
        print(f"   Average Score: {report['quality']['average_quality_score']}")
        print(f"   Fallbacks: {report['quality']['fallbacks_triggered']}")

        # Strategy breakdown
        print("\n🎯 Strategies Used:")
        for strategy, count in report['strategies'].items():
            print(f"   {strategy}: {count} pages")

        # Status
        print("\n✅ Status:")
        print(f"   Success: {report['status']['success']}")
        print(f"   Errors: {report['status']['errors']}")
        print(f"   Warnings: {report['status']['warnings']}")

        # Show sample text from first page
        if result.pages:
            print("\n📖 Sample Text (Page 1):")
            print_separator()
            sample_text = result.pages[0].text[:500]
            print(sample_text)
            if len(result.pages[0].text) > 500:
                print("\n   ... (truncated)")

        # Export options
        print("\n💾 Export Options:")
        print_separator()
        print("\n   The extracted content can be exported to:")
        print("   - Plain text: result.to_text()")
        print("   - Markdown: result.to_markdown()")
        print("   - JSON: result.model_dump_json()")

        # Show cost savings
        print("\n💰 Cost Analysis:")
        print_separator()
        naive_cost = len(result.pages) * 0.03  # Assuming all vision
        actual_cost = result.total_processing_cost
        savings = naive_cost - actual_cost
        savings_pct = (savings / naive_cost * 100) if naive_cost > 0 else 0

        print(f"\n   Naive approach (all vision): ${naive_cost:.4f}")
        print(f"   DocMind-AI (adaptive): ${actual_cost:.4f}")
        print(f"   💚 Savings: ${savings:.4f} ({savings_pct:.1f}%)")

        print_separator()
        print("\n✨ Extraction complete! ✨\n")

    except Exception as e:
        print(f"\n❌ Error during extraction: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Clean up
        extractor.close()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]

        if not Path(pdf_path).exists():
            print(f"❌ File not found: {pdf_path}")
            sys.exit(1)

        main(pdf_path)
    else:
        print("DocMind-AI - LangGraph Extraction Workflow")
        print("\nUsage:")
        print(f"   python {sys.argv[0]} <path_to_pdf>")
        print("\nExample:")
        print(f"   python {sys.argv[0]} sample.pdf")
