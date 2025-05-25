#!/usr/bin/env pwsh
# Simple PowerShell script to run the HackerNews data pipeline
# Automatically sets the correct working directory and runs the pipeline

Set-Location $PSScriptRoot
python -m src.pipeline.run_pipeline
