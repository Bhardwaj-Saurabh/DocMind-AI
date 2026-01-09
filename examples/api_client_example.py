"""
Example client for DocMind-AI REST API.

This example demonstrates:
1. Uploading a document for extraction
2. Polling for job status
3. Retrieving and saving results
"""

import argparse
import sys
import time
from pathlib import Path

import requests


class DocMindClient:
    """Simple client for DocMind-AI API."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize client.

        Args:
            base_url: Base URL of API server
        """
        self.base_url = base_url.rstrip("/")

    def check_health(self) -> dict:
        """Check API health."""
        response = requests.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

    def extract_document(
        self,
        file_path: str,
        output_format: str = "markdown",
        enable_vision: bool = True,
        preserve_hierarchy: bool = True,
    ) -> str:
        """
        Upload document for extraction (async).

        Args:
            file_path: Path to document
            output_format: Output format (json, markdown, text)
            enable_vision: Enable vision processing
            preserve_hierarchy: Preserve document hierarchy

        Returns:
            Job ID for tracking
        """
        url = f"{self.base_url}/extract"

        with open(file_path, "rb") as f:
            files = {"file": (Path(file_path).name, f)}
            params = {
                "output_format": output_format,
                "enable_vision": enable_vision,
                "preserve_hierarchy": preserve_hierarchy,
            }

            response = requests.post(url, files=files, params=params)
            response.raise_for_status()

        result = response.json()
        return result["job_id"]

    def get_job_status(self, job_id: str) -> dict:
        """
        Get job status.

        Args:
            job_id: Job identifier

        Returns:
            Job status information
        """
        url = f"{self.base_url}/jobs/{job_id}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    def get_job_result(self, job_id: str) -> dict:
        """
        Get job result.

        Args:
            job_id: Job identifier

        Returns:
            Extraction result
        """
        url = f"{self.base_url}/jobs/{job_id}/result"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    def wait_for_completion(
        self,
        job_id: str,
        poll_interval: float = 2.0,
        timeout: float = 300.0,
        verbose: bool = True,
    ) -> dict:
        """
        Wait for job to complete.

        Args:
            job_id: Job identifier
            poll_interval: Seconds between status checks
            timeout: Max seconds to wait
            verbose: Print progress updates

        Returns:
            Final job status

        Raises:
            TimeoutError: If job doesn't complete in time
            RuntimeError: If job fails
        """
        start_time = time.time()

        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                raise TimeoutError(f"Job {job_id} timed out after {timeout}s")

            status = self.get_job_status(job_id)

            if verbose:
                progress = status.get("progress", 0.0)
                print(
                    f"[{elapsed:.1f}s] Status: {status['status']} - "
                    f"Progress: {progress:.1f}%"
                )

            if status["status"] == "completed":
                return status
            elif status["status"] == "failed":
                error = status.get("error", "Unknown error")
                raise RuntimeError(f"Job failed: {error}")

            time.sleep(poll_interval)

    def extract_and_wait(
        self,
        file_path: str,
        output_format: str = "markdown",
        enable_vision: bool = True,
        preserve_hierarchy: bool = True,
        verbose: bool = True,
    ) -> dict:
        """
        Extract document and wait for completion.

        Args:
            file_path: Path to document
            output_format: Output format
            enable_vision: Enable vision processing
            preserve_hierarchy: Preserve hierarchy
            verbose: Print progress

        Returns:
            Extraction result
        """
        if verbose:
            print(f"Uploading: {file_path}")

        job_id = self.extract_document(
            file_path=file_path,
            output_format=output_format,
            enable_vision=enable_vision,
            preserve_hierarchy=preserve_hierarchy,
        )

        if verbose:
            print(f"Job created: {job_id}")
            print("Waiting for completion...")

        self.wait_for_completion(job_id, verbose=verbose)

        if verbose:
            print("Retrieving result...")

        result = self.get_job_result(job_id)

        if verbose:
            print(f"✓ Complete!")
            print(f"  Document: {result['document_name']}")
            print(f"  Pages: {result['total_pages']}")
            print(f"  Time: {result['processing_time']:.2f}s")
            print(f"  Cost: ${result['processing_cost']:.4f}")

        return result


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="DocMind-AI API Client Example",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "file",
        type=str,
        help="Path to document file (PDF, DOCX, PPTX)",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="Output file path (default: <input>.<format>)",
    )

    parser.add_argument(
        "-f",
        "--format",
        type=str,
        default="markdown",
        choices=["json", "markdown", "text"],
        help="Output format (default: markdown)",
    )

    parser.add_argument(
        "--no-vision",
        action="store_true",
        help="Disable vision processing (faster, cheaper)",
    )

    parser.add_argument(
        "--no-hierarchy",
        action="store_true",
        help="Don't preserve document hierarchy",
    )

    parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8000",
        help="API base URL (default: http://localhost:8000)",
    )

    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Quiet mode (no progress output)",
    )

    args = parser.parse_args()

    # Validate input file
    input_path = Path(args.file)
    if not input_path.exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        ext = {"json": ".json", "markdown": ".md", "text": ".txt"}[args.format]
        output_path = input_path.with_suffix(ext)

    # Create client
    client = DocMindClient(base_url=args.api_url)

    # Check health
    if not args.quiet:
        print("Checking API health...")
        try:
            health = client.check_health()
            print(f"✓ API is {health['status']}")
            print(f"  Version: {health['version']}")
            print(f"  Vision enabled: {health['vision_enabled']}")
            print()
        except requests.exceptions.ConnectionError:
            print(f"Error: Cannot connect to API at {args.api_url}", file=sys.stderr)
            print("Is the server running? Try: python run_api.py", file=sys.stderr)
            sys.exit(1)

    try:
        # Extract document
        result = client.extract_and_wait(
            file_path=str(input_path),
            output_format=args.format,
            enable_vision=not args.no_vision,
            preserve_hierarchy=not args.no_hierarchy,
            verbose=not args.quiet,
        )

        # Save result
        content = result["content"]

        if args.format == "json":
            import json

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(content, f, indent=2, ensure_ascii=False)
        else:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)

        if not args.quiet:
            print(f"\n✓ Saved to: {output_path}")

    except KeyboardInterrupt:
        print("\n\nInterrupted by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
