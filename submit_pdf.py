#!/usr/bin/env python3
"""
Simple script to submit a PDF to a running inference container.
"""

import os
import sys
import time
import asyncio
import aiohttp
import aiofiles
import json
import click
from pathlib import Path
from typing import Dict, List, Tuple


class PDFSubmitter:
    """Simple PDF submission client."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def submit_pdf(self, pdf_path: str, config: Dict = None) -> str:
        """Submit a PDF for processing and return the file_id."""
        if config is None:
            config = {}

        async with aiofiles.open(pdf_path, "rb") as f:
            file_content = await f.read()

            data = aiohttp.FormData()
            data.add_field(
                "file",
                file_content,
                filename=os.path.basename(pdf_path),
                content_type="application/pdf",
            )
            data.add_field("config", json.dumps(config))

            async with self.session.post(
                f"{self.base_url}/marker/inference", data=data
            ) as response:
                response.raise_for_status()
                result = await response.json()
                return result["file_id"]

    async def check_status(self, file_id: str) -> Tuple[str, dict]:
        """Check the status of a processing job. Returns (status, result/error)."""
        async with self.session.get(
            f"{self.base_url}/marker/results",
            params={"file_id": file_id, "download": "true"},
        ) as response:
            response.raise_for_status()
            result = await response.json()
            status = result.get("status")

            if status == "done":
                return "done", result
            elif status == "failed":
                return "failed", result
            elif status == "processing":
                return "processing", {}
            else:
                return "unknown", {"status": f"Unknown status: {status}"}

    async def wait_for_completion(
        self, file_id: str, timeout: int = 600
    ) -> Tuple[bool, dict]:
        """Wait for PDF processing to complete. Returns (success, result/error)."""
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                status, result = await self.check_status(file_id)

                if status == "done":
                    return True, result
                elif status == "failed":
                    return False, result
                elif status == "processing":
                    print("  Still processing...")
                    await asyncio.sleep(5)
                    continue
                else:
                    return False, result

            except Exception as e:
                return False, {"error": f"Request failed: {e}"}

        return False, {"error": "Timeout waiting for completion"}

    async def clear_file(self, file_id: str) -> bool:
        """Clear a processed file from the server."""
        try:
            async with self.session.post(
                f"{self.base_url}/marker/clear", json={"file_id": file_id}
            ) as response:
                response.raise_for_status()
                return True
        except Exception as e:
            print(f"Warning: Could not clear file {file_id}: {e}")
            return False

    async def download_images(self, image_urls: List[str], pdf_name: str, out_dir: str):
        """Download images and save them to the output directory with original names."""
        if not image_urls:
            return

        print(f"Downloading {len(image_urls)} images...")
        for i, img_url in enumerate(image_urls):
            try:
                async with self.session.get(img_url) as response:
                    if response.status == 200:
                        # Extract original filename from URL
                        # URL format: http://localhost:8000/static/file_id/original_filename.ext
                        url_parts = img_url.split('/')
                        if len(url_parts) >= 2:
                            original_filename = url_parts[-1]  # Get the last part (filename)
                        else:
                            # Fallback if URL format is unexpected
                            img_ext = os.path.splitext(img_url)[1] or '.png'
                            original_filename = f"image_{i+1:03d}{img_ext}"
                        
                        img_path = os.path.join(out_dir, original_filename)
                        
                        async with aiofiles.open(img_path, 'wb') as f:
                            await f.write(await response.read())
                        print(f"  Saved: {original_filename}")
                    else:
                        print(f"  Failed to download image {i+1}: HTTP {response.status}")
            except Exception as e:
                print(f"  Error downloading image {i+1}: {e}")


@click.command()
@click.argument("pdf_path", type=click.Path(exists=True))
@click.option("--url", default="http://localhost:8000", help="Base URL of the inference server")
@click.option("--out-dir", type=str, help="Output directory for results and images")
@click.option("--format-lines", is_flag=True, help="Format lines in the output")
@click.option("--no-clear", is_flag=True, help="Don't clear the file from server after processing")
@click.option("--timeout", type=int, default=600, help="Timeout in seconds")
def main(pdf_path: str, url: str, out_dir: str, format_lines: bool, no_clear: bool, timeout: int):
    """Submit a PDF to a running inference container and get results."""
    
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        print(f"Error: PDF file {pdf_path} does not exist")
        sys.exit(1)

    # Create output directory if specified
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    async def process_pdf():
        config = {"format_lines": format_lines, "paginate_output": True}
        
        async with PDFSubmitter(url) as submitter:
            print(f"Submitting: {pdf_path.name}")
            
            try:
                # Submit PDF
                file_id = await submitter.submit_pdf(str(pdf_path), config)
                print(f"File ID: {file_id}")
                
                # Wait for completion
                print("Waiting for processing to complete...")
                success, result = await submitter.wait_for_completion(file_id, timeout)
                
                if success:
                    print("✓ Processing completed successfully!")
                    
                    # Get results
                    markdown_content = result.get("result", "")
                    images = result.get("images", [])
                    
                    print(f"Generated {len(markdown_content)} characters of markdown")
                    if images:
                        print(f"Found {len(images)} images:")
                        for i, img_url in enumerate(images):
                            print(f"  {i+1}: {img_url}")
                    
                    # Save results if output directory specified
                    if out_dir:
                        # Create a subfolder for this PDF
                        pdf_folder = os.path.join(out_dir, pdf_path.stem)
                        os.makedirs(pdf_folder, exist_ok=True)
                        
                        # Save markdown
                        md_path = os.path.join(pdf_folder, f"{pdf_path.stem}.md")
                        with open(md_path, 'w') as f:
                            f.write(markdown_content)
                        print(f"Saved markdown to: {md_path}")
                        
                        # Download images to the same folder
                        if images:
                            await submitter.download_images(images, pdf_path.name, pdf_folder)
                    
                    # Clear file unless requested not to
                    if not no_clear:
                        await submitter.clear_file(file_id)
                        print("File cleared from server")
                    else:
                        print(f"File {file_id} left on server (use --no-clear to change)")
                        
                else:
                    print(f"✗ Processing failed: {result}")
                    sys.exit(1)
                    
            except Exception as e:
                print(f"Error: {e}")
                sys.exit(1)

    # Run the async function
    asyncio.run(process_pdf())


if __name__ == "__main__":
    main()