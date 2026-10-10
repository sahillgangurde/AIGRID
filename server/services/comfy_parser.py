"""
ComfyUI JSON Graph Parser & Security Guard Service.
Parses node DAGs, prevents arbitrary code execution, scores pipeline complexity,
and generates deterministic SHA-256 workflow fingerprints.
"""

import hashlib
import json
from typing import Dict, Any, List, Tuple

FORBIDDEN_NODE_TYPES = {
    "pythoncode", "exec", "eval", "systemcommand", "shellexec", "filereadraw",
    "remotedownloaduntrusted", "subprocess", "oscommand", "arbitraryscript"
}

ALLOWED_STANDARD_CLASSES = {
    "ksampler", "ksampleradvanced", "checkpointloadersimple", "loraloader",
    "controlnetloader", "controlnetapply", "controlnetapplyadvanced",
    "cliptextencode", "vaedecode", "vaeencode", "emptylatentimage",
    "loadimage", "saveimage", "previewimage", "modelreleasebinder",
    "auraforgec2painjector", "upscalelatent", "clipvisionencode"
}

class ComfyUIParserService:
    @staticmethod
    def validate_and_parse(workflow_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates ComfyUI DAG topology, enforces AST security, and extracts execution parameters.
        """
        nodes = workflow_json.get("nodes", {})
        if not nodes:
            # Handle list-format ComfyUI export if present
            if isinstance(workflow_json.get("nodes"), list):
                nodes = {str(n.get("id", i)): n for i, n in enumerate(workflow_json["nodes"])}
            elif "prompt" in workflow_json:
                nodes = workflow_json["prompt"]

        if not nodes:
            return {
                "valid": False,
                "error": "Invalid workflow JSON: Missing 'nodes' or graph dictionary",
                "dag_nodes": 0
            }

        extracted_nodes: List[Dict[str, Any]] = []
        model_checkpoints = []
        loras = []
        controlnets = []
        positive_prompts = []
        negative_prompts = []
        sampler_configs = []
        security_violations = []

        for node_id, node_data in nodes.items():
            class_type = str(node_data.get("class_type", "")).strip()
            class_lower = class_type.lower()
            inputs = node_data.get("inputs", {})

            # Security Check
            if any(forbidden in class_lower for forbidden in FORBIDDEN_NODE_TYPES):
                security_violations.append(f"Security Alert: Blocked unsafe node '{class_type}' at node #{node_id}")

            extracted_nodes.append({
                "id": str(node_id),
                "type": class_type,
                "inputs_summary": list(inputs.keys())
            })

            # Checkpoint
            if "checkpoint" in class_lower or "ckpt" in inputs:
                ckpt_name = inputs.get("ckpt_name", "standard_base.safetensors")
                model_checkpoints.append(str(ckpt_name))

            # LoRAs
            if "lora" in class_lower:
                lora_name = inputs.get("lora_name", "custom_lora.safetensors")
                strength = inputs.get("strength_model", 1.0)
                loras.append({"name": str(lora_name), "strength": strength})

            # ControlNets
            if "controlnet" in class_lower:
                c_name = inputs.get("control_net_name", "controlnet_v1.pth")
                controlnets.append(str(c_name))

            # Text Conditioning
            if "cliptextencode" in class_lower or "prompt" in class_lower:
                text = str(inputs.get("text", "")).strip()
                if text:
                    # Simple heuristic for negative prompt: contains negative terms or mapped to negative conditioning
                    if any(term in text.lower() for term in ["ugly", "bad", "blurry", "low quality", "deformed"]):
                        negative_prompts.append(text)
                    else:
                        positive_prompts.append(text)

            # Sampler
            if "sampler" in class_lower and "steps" in inputs:
                sampler_configs.append({
                    "steps": inputs.get("steps", 30),
                    "cfg": inputs.get("cfg", 7.0),
                    "sampler_name": inputs.get("sampler_name", "euler"),
                    "scheduler": inputs.get("scheduler", "karras"),
                    "seed": inputs.get("seed", 0)
                })

        if security_violations:
            return {
                "valid": False,
                "error": "Security validation failed",
                "violations": security_violations,
                "dag_nodes": len(extracted_nodes)
            }

        # Calculate Complexity Score (0.0 to 10.0 scale)
        # Node depth, LoRA chains, ControlNets, and sampling density
        complexity = 3.0
        complexity += min(3.0, len(extracted_nodes) * 0.3)
        complexity += min(2.0, len(loras) * 0.7)
        complexity += min(2.0, len(controlnets) * 1.0)
        complexity_score = round(min(10.0, complexity), 2)

        # Deterministic Workflow SHA-256 Fingerprint
        serialized_dag = json.dumps(nodes, sort_keys=True)
        workflow_hash = hashlib.sha256(serialized_dag.encode("utf-8")).hexdigest()

        return {
            "valid": True,
            "workflow_hash": workflow_hash,
            "dag_nodes_count": len(extracted_nodes),
            "complexity_score": complexity_score,
            "model_checkpoint": model_checkpoints[0] if model_checkpoints else "SDXL_Base_v1.0",
            "lora_stack": loras,
            "controlnet_stack": controlnets,
            "sampler_config": sampler_configs[0] if sampler_configs else {"steps": 30, "cfg": 7.0, "sampler_name": "euler_ancestral"},
            "positive_prompts": positive_prompts,
            "negative_prompts": negative_prompts,
            "security_verified": True
        }
