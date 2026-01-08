"""
Table extraction example with rule-based and vision fallback.

This example demonstrates:
1. Rule-based table extraction using PyMuPDF (fast & cheap)
2. Complexity detection
3. Vision API fallback for complex tables
4. Cost comparison between approaches
"""

from src.extractors import PDFExtractor
from src.graph import create_extraction_workflow


def print_table(table, idx):
    """Pretty print an extracted table."""
    print(f"\n📊 Table {idx + 1}:")
    print(f"   Complexity: {table.complexity.value}")
    print(f"   Method: {table.extraction_method}")
    print(f"   Confidence: {table.confidence_score:.2f}")

    if table.caption:
        print(f"   Caption: {table.caption}")

    # Print table structure
    if table.headers:
        print(f"\n   Headers: {' | '.join(table.headers)}")

    if table.rows:
        print(f"   Rows: {len(table.rows)}")
        # Show first 3 rows
        for i, row in enumerate(table.rows[:3]):
            print(f"   Row {i+1}: {' | '.join(str(cell) for cell in row)}")
        if len(table.rows) > 3:
            print(f"   ... and {len(table.rows) - 3} more rows")


def main():
    """Run table extraction example."""
    import sys

    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_path = "data/samples/sample_with_tables.pdf"
        print(f"💡 Usage: python examples/table_extraction.py <path_to_pdf>")
        print(f"   Using default: {pdf_path}\n")

    import os
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        print(f"\n💡 Tip: Use a PDF with tables for best results")
        return

    print("="*70)
    print("  DocMind-AI: Table Extraction Demo")
    print("="*70)
    print(f"\n📄 Processing: {pdf_path}\n")

    # Create extractor and workflow
    extractor = PDFExtractor(pdf_path)
    workflow = create_extraction_workflow()

    print("🚀 Extracting document content...\n")

    # Extract
    result = workflow.extract(
        file_path=pdf_path,
        extractor=extractor,
    )

    # Show results
    print("\n" + "="*70)
    print("  Extraction Results")
    print("="*70)

    print(f"\n📊 Tables found: {len(result.all_tables)}")

    if result.all_tables:
        for idx, table in enumerate(result.all_tables):
            print_table(table, idx)

        # Calculate costs
        rule_based = sum(1 for t in result.all_tables if t.extraction_method == "rule_based")
        vision_based = sum(1 for t in result.all_tables if t.extraction_method == "vision_api")

        print("\n" + "="*70)
        print("  Cost Analysis")
        print("="*70)

        actual_cost = (rule_based * 0.002) + (vision_based * 0.02)
        naive_cost = len(result.all_tables) * 0.02  # If all used vision

        print(f"\nHybrid Approach (DocMind-AI):")
        print(f"  Rule-based: {rule_based} tables @ $0.002 = ${rule_based * 0.002:.4f}")
        print(f"  Vision API: {vision_based} tables @ $0.020 = ${vision_based * 0.02:.4f}")
        print(f"  Total: ${actual_cost:.4f}")

        print(f"\nNaive Approach (Vision for all):")
        print(f"  {len(result.all_tables)} tables @ $0.020 = ${naive_cost:.4f}")

        if naive_cost > 0:
            savings = naive_cost - actual_cost
            savings_pct = (savings / naive_cost) * 100
            print(f"\n💰 Savings: ${savings:.4f} ({savings_pct:.1f}% reduction)")

        # Export tables to CSV
        print("\n" + "="*70)
        print("  Exporting Tables")
        print("="*70)

        from pathlib import Path
        output_dir = Path("output/tables")
        output_dir.mkdir(parents=True, exist_ok=True)

        for idx, table in enumerate(result.all_tables):
            csv_file = output_dir / f"table_{table.page_number+1}_{idx+1}.csv"
            csv_content = table.to_csv()
            with open(csv_file, "w") as f:
                f.write(csv_content)
            print(f"   ✅ {csv_file.name}")

        print(f"\n📁 Tables exported to: {output_dir}")

    else:
        print("\n⚠️  No tables found in document")
        print("💡 Try a document with data tables, charts with data, or structured content")

    print("\n" + "="*70)
    print("  Complete! ✅")
    print("="*70)

    # Clean up
    extractor.close()


if __name__ == "__main__":
    main()
