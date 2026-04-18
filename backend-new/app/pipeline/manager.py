import os
import json
from datetime import datetime
from app.core.config import STORAGE_DIR, PREVIEW_PORT_BASE
from app.db.repo import get_run, update_run_status, log_message
from app.pipeline.stage0_enhance import enhance_prompt_async
from app.pipeline.stage1_taskspec import generate_taskspec
from app.pipeline.stage2_codegen import generate_code_async
from app.pipeline.stage3_extract import extract_and_repair
from app.pipeline.stage4_sandbox import run_sandbox_async
from app.pipeline.stage5_modify import apply_modification_async

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
        log('codegen', "Using Ollama coder model to generate full stack application...")
        raw_code = await generate_code_async(taskspec)
        log('codegen', "Raw code blocks successfully received from the model.")

        # Stage 3
        log('extract', "Parsing model output and extracting files...")
        created_files, manifest, result = extract_and_repair(raw_code, output_dir)
        log('extract', f"Extracted {len(created_files)} complete files into storage.")
        
        # Save pipeline log for later viewing as requested by user
        os.makedirs(output_dir, exist_ok=True)
        with open(os.path.join(output_dir, "pipeline_output.json"), "w", encoding="utf-8") as f:
            json.dump({
                "user_prompt": prompt,
                "enhanced_prompt": enhanced_prompt,
                "taskspec": taskspec,
                "result": result
            }, f, indent=2, ensure_ascii=False)
            
        log('extract', f"Full pipeline output exported to {os.path.join(output_dir, 'pipeline_output.json')}")

        # Stage 4 
        log('sandbox', "Preparing virtual environment...")
        proc_handle = await run_sandbox_async(output_dir, port, log)

        if proc_handle:
            PROCESS_REGISTRY[run_id] = proc_handle
            update_run_status(run_id, 'success')
            log('done', f"Pipeline successfully completed! Live on port {port}")
        else:
            update_run_status(run_id, 'failed')
            log('fatal', "Failed to launch application sandbox.", 'ERROR')

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
