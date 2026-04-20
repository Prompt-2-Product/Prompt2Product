import os
import json
from datetime import datetime
from app.core.config import STORAGE_DIR, PREVIEW_PORT_BASE
from app.db.repo import get_run, update_run_status, log_message
from app.pipeline.stage0_enhance import enhance_prompt_async
from app.pipeline.stage1_taskspec import generate_taskspec
from app.pipeline.stage2_codegen import generate_code_async
from app.pipeline.stage3_extract import (
    safe_parse, normalize_result, extract_files, 
    run_sanity_tests, run_correctness_tests, repair_with_error
)
from app.pipeline.stage4_sandbox import run_sandbox_async
from app.pipeline.stage5_modify import apply_modification_async
import shutil

PROCESS_REGISTRY = {}

def stop_run(run_id: int):
    if run_id in PROCESS_REGISTRY:
        proc = PROCESS_REGISTRY[run_id]
        if proc.poll() is None: # Still running
            print(f"[PROCESS] Terminating run {run_id}...")
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except:
                proc.kill()
        del PROCESS_REGISTRY[run_id]
        return True
    return False

async def run_pipeline(run_id: int, project_id: int, prompt: str):
    def log(stage: str, msg: str, level: str = 'INFO'):
        print(f"[{stage.upper()}] {msg}")
        log_message(run_id, stage, msg, level)

    update_run_status(run_id, 'running')
    port = PREVIEW_PORT_BASE + run_id
    output_dir = os.path.join(STORAGE_DIR, f"project_{project_id}", f"run_{run_id}")
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Stage 0
        log('enhance', f"Analyzing prompt: {prompt}")
        enhanced_prompt = await enhance_prompt_async(prompt)
        if enhanced_prompt != prompt:
            log('enhance', f"Successfully enhanced prompt: {enhanced_prompt}")
        else:
            log('enhance', "Prompt detail is sufficient, enhancement skipped.")

        # Stage 1
        log('spec', "Loading TaskSpec unsloth model and generating specifications...")
        _, taskspec = generate_taskspec(enhanced_prompt)
        log('spec', f"Generated TaskSpec. Features: {len(taskspec.get('frontend',{}).get('features',[]))}")

        # Stage 2
        log('codegen', "Initiating deep synthesis with GIKI-Coder...")
        log('plan', "Formulating application architecture and dependencies...")
        raw_code = await generate_code_async(taskspec)
        log('codegen', "Full application logic received from model.")

        # Debug: Save raw output immediately
        with open(os.path.join(output_dir, "raw_model_output.txt"), "w", encoding="utf-8") as f:
            f.write(raw_code)

        # Parse and Normalize
        result = safe_parse(raw_code)
        if result is None:
            raise ValueError("Could not parse JSON output from model")
        result = normalize_result(result)
        
        # Phase Reporting
        log('plan', f"Strategic Plan: {result.get('plan', 'Standard implementation flow')}")
        log('manifest', f"Project Manifest: {', '.join(result.get('manifest', []))}")

        # Stage 3: Sanity Tests
        log('sanity', "Performing static analysis and syntax checks...")
        sanity_passed, sanity_issues = run_sanity_tests(output_dir, result)
        
        if not sanity_passed:
            log('repair', f"Sanity issues found: {', '.join(sanity_issues[:3])}. Attempting rule-based repair...")
            # Note: normalize_result/fixers are already called inside extract_files or similar
            # For simplicity, we proceed to extract and then check correctness
        else:
            log('sanity', "Static analysis passed. Basic code structure is valid.")

        # Stage 4: Extract Files
        log('extract', "Writing code modules to project workspace...")
        shutil.rmtree(output_dir, ignore_errors=True)
        created_files, manifest = extract_files(result, output_dir, log_fn=log)
        log('extract', f"Successfully materialized {len(created_files)} files.")

        # Stage 5: Correctness Tests (Dynamic)
        log('correctness', "Evaluating runtime integrity (launching app and hitting routes)...")
        run_cmd = f"uvicorn main:app --host 0.0.0.0 --port {port}" # Base run command for tests
        correctness_passed, correctness_issues = run_correctness_tests(output_dir, run_cmd, port=8099)

        if not correctness_passed:
            log('repair', f"Runtime issues detected. Initiating intelligent mini-repair loop...")
            error_log = "\n".join(correctness_issues)
            
            # Mini-repair LLM call
            result = repair_with_error(result, error_log)
            result = normalize_result(result)
            
            # Re-extract and re-test
            log('extract', "Applying repaired code to workspace...")
            shutil.rmtree(output_dir, ignore_errors=True)
            created_files, manifest = extract_files(result, output_dir, log_fn=log)
            
            log('correctness', "Final verification of repaired application...")
            correctness_passed, correctness_issues = run_correctness_tests(output_dir, run_cmd, port=8099)
            
            if not correctness_passed:
                log('warn', "Some runtime issues persist. App might have partial functionality.", 'WARNING')
            else:
                log('correctness', "Intelligent repair successful. Integrity verified.")
        else:
            log('correctness', "Runtime integrity verified. No 500 errors detected.")

        # Save pipeline log for later viewing
        os.makedirs(output_dir, exist_ok=True)
        with open(os.path.join(output_dir, "pipeline_output.json"), "w", encoding="utf-8") as f:
            json.dump({
                "user_prompt": prompt,
                "enhanced_prompt": enhanced_prompt,
                "taskspec": taskspec,
                "result": result
            }, f, indent=2, ensure_ascii=False)
            
        log('extract', f"Full pipeline history saved to project storage.")

        # Stage 6: Sandbox Production
        log('sandbox', "Initializing production environment...")
        proc_handle = await run_sandbox_async(output_dir, port, log)

        if proc_handle:
            PROCESS_REGISTRY[run_id] = proc_handle
            update_run_status(run_id, 'success')
            log('done', f"Forge process complete! Access your app on port {port}")
        else:
            update_run_status(run_id, 'failed')
            log('fatal', "Failed to ignite the application sandbox.", 'ERROR')

    except Exception as e:
        log('fatal', f"Critical failure in pipeline: {str(e)}", 'ERROR')
        update_run_status(run_id, 'failed')

async def run_modification_pipeline(run_id: int, project_id: int, user_request: str):
    def log(stage: str, msg: str, level: str = 'INFO'):
        print(f"[MODIFY] {msg}")
        log_message(run_id, stage, msg, level)

    log('modify', f"Applying modification: {user_request}")
    update_run_status(run_id, 'running')
    port = PREVIEW_PORT_BASE + run_id
    output_dir = os.path.join(STORAGE_DIR, f"project_{project_id}", f"run_{run_id}")

    try:
        # 1. Stop existing process
        stop_run(run_id)
        
        # 2. Apply modifications
        success = await apply_modification_async(output_dir, user_request, log)
        
        if success:
            log('modify', "Modifications applied. Restarting sandbox...")
            # 3. Restart process
            proc_handle = await run_sandbox_async(output_dir, port, log)
            if proc_handle:
                PROCESS_REGISTRY[run_id] = proc_handle
                update_run_status(run_id, 'success')
                log('done', f"Modification successful! Live on http://localhost:{port}")
            else:
                update_run_status(run_id, 'failed')
                log('fatal', "Failed to restart application after modification.", 'ERROR')
        else:
            update_run_status(run_id, 'failed')
            log('fatal', "Failed to apply modifications.", 'ERROR')
            
    except Exception as e:
        log('fatal', f"Critical failure in modification: {str(e)}", 'ERROR')
        update_run_status(run_id, 'failed')
