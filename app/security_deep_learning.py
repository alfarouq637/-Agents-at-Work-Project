"""AutoCorp Deep Learning Security Model & Autonomous Remediation Loop.

Employs neural / LLM-based deep semantic vulnerability classification to audit
generated websites and orchestrate closed-loop self-healing code remediation.
"""
import json
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from . import db, llm

DEEP_LEARNING_SYSTEM_PROMPT = """You are the AutoCorp Deep Learning Security Model & Neural Vulnerability Classifier.
Your mission is to perform deep semantic code inspection on generated web application code (HTML, Tailwind CSS, JavaScript).
You must analyze the code for:
1. DOM XSS (unsafe innerHTML, eval, document.write, unescaped string interpolation, javascript: URI schemes).
2. Tab-nabbing & External Link Isolation (target="_blank" without rel="noopener noreferrer").
3. Sensitive Data & Credential Exposure (hardcoded API keys, JWT secrets, database connection strings).
4. Insecure Client-Side Data Storage (storing JWTs or sensitive credentials in localStorage).
5. Insecure Form Actions & Cross-Site Request Forgery (CSRF).
6. Mobile Ergonomics & Viewport Accessibility.

Respond ONLY with a valid JSON object with the following exact keys:
{
  "score": <integer 0 to 100>,
  "status": "<APPROVED or REMEDIATION_REQUIRED>",
  "summary": "<concise summary in Arabic and English>",
  "vulnerabilities": [
    {
      "severity": "<critical|high|medium|low>",
      "type": "<VULNERABILITY_TYPE>",
      "description": "<concise issue description>",
      "remediation": "<exact fix for the Frontend Developer>"
    }
  ],
  "actionable_feedback": "<step-by-step instructions for the Frontend Developer agent to remediate all flaws>"
}
If there are critical or high vulnerabilities or score is below 90, status MUST be "REMEDIATION_REQUIRED".
If no significant vulnerabilities exist and score >= 90, status MUST be "APPROVED" and vulnerabilities must be empty.
"""


def _heuristic_semantic_analysis(html_code: str) -> Dict[str, Any]:
    """Deterministic AST/pattern analyzer serving as semantic baseline and offline fallback."""
    vulnerabilities = []
    sample = html_code or ""

    # 1. Unescaped innerHTML inspection
    for m in re.finditer(r"\.innerHTML\s*=\s*([^;]+);", sample):
        stmt = m.group(1).strip()
        # If interpolating variables without esc(...) or html.escape
        if ("${" in stmt and "esc(" not in stmt and "escape(" not in stmt) or ("+" in stmt and "esc(" not in stmt):
            vulnerabilities.append({
                "severity": "high",
                "type": "DOM_XSS",
                "description": f"Unescaped variable interpolation into innerHTML: {stmt[:60]}",
                "remediation": "Wrap all dynamic variables in esc(val) or use textContent instead of innerHTML.",
            })

    # 2. Dangerous sinks (eval, document.write)
    if re.search(r"\beval\s*\(", sample):
        vulnerabilities.append({
            "severity": "critical",
            "type": "ARBITRARY_CODE_EXECUTION",
            "description": "Dangerous eval() function call found in client script.",
            "remediation": "Remove eval() completely and use JSON.parse() or standard logic.",
        })
    if re.search(r"document\.write\s*\(", sample):
        vulnerabilities.append({
            "severity": "high",
            "type": "DOM_XSS",
            "description": "document.write() call detected.",
            "remediation": "Replace document.write with safe DOM manipulation methods.",
        })

    # 3. Insecure target="_blank" without rel="noopener noreferrer"
    blank_links = re.findall(r'<a\s+[^>]*target=["\']_blank["\'][^>]*>', sample, re.IGNORECASE)
    for link in blank_links:
        if "rel=" not in link.lower() or "noopener" not in link.lower():
            vulnerabilities.append({
                "severity": "medium",
                "type": "REVERSE_TABNABBING",
                "description": "Anchor tag with target='_blank' lacks rel='noopener noreferrer'.",
                "remediation": "Add rel='noopener noreferrer' to all links opening in new tabs.",
            })
            break  # report once

    # 4. Javascript: pseudo protocol
    if re.search(r'href=["\']\s*javascript\s*:', sample, re.IGNORECASE):
        vulnerabilities.append({
            "severity": "high",
            "type": "JAVASCRIPT_URI_XSS",
            "description": "Insecure href='javascript:...' link detected.",
            "remediation": "Use an explicit button with addEventListener or onclick handler instead of javascript: URIs.",
        })

    # 5. Hardcoded API secrets
    secret_patterns = [
        (r"AIzaSy[0-9A-Za-z\-_]{33}", "Google API Key"),
        (r"sk_live_[0-9a-zA-Z]{24,}", "Stripe Live Key"),
        (r"ghp_[0-9a-zA-Z]{36}", "GitHub Token"),
        (r"-----" + r"BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----", "Private Key"),
    ]
    for pat, sec_name in secret_patterns:
        if re.search(pat, sample):
            vulnerabilities.append({
                "severity": "critical",
                "type": "HARDCODED_CREDENTIAL",
                "description": f"Hardcoded {sec_name} leaked in generated code.",
                "remediation": "Remove hardcoded secret; load dynamically from server-side environment variables.",
            })

    # 6. Responsive Viewport Check
    if '<meta name="viewport"' not in sample.lower():
        vulnerabilities.append({
            "severity": "medium",
            "type": "RESPONSIVENESS_DEFECT",
            "description": "Missing viewport meta tag for mobile devices.",
            "remediation": "Add <meta name='viewport' content='width=device-width, initial-scale=1'> to <head>.",
        })

    # Calculate score
    deductions = {
        "critical": 30,
        "high": 15,
        "medium": 5,
        "low": 2,
    }
    score = 100 - sum(deductions.get(v["severity"], 5) for v in vulnerabilities)
    score = max(10, min(100, score))

    status = "APPROVED" if score >= 90 and not any(v["severity"] in ("critical", "high") for v in vulnerabilities) else "REMEDIATION_REQUIRED"

    feedback_parts = [
        f"- [{v['severity'].upper()}] {v['type']}: {v['description']}. Fix: {v['remediation']}"
        for v in vulnerabilities
    ]
    actionable_feedback = "\n".join(feedback_parts) if feedback_parts else "All security checks passed with high confidence."

    return {
        "score": score,
        "status": status,
        "summary": f"Security audit completed with score {score}/100. {len(vulnerabilities)} vulnerabilities identified.",
        "vulnerabilities": vulnerabilities,
        "actionable_feedback": actionable_feedback,
    }


async def deep_learning_security_audit(html_code: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Run Deep Learning semantic vulnerability analysis on website HTML.
    
    Combines transformer neural model evaluation with deterministic AST heuristics.
    """
    heuristic_result = _heuristic_semantic_analysis(html_code)
    
    # Format sample for LLM brain tier
    code_snippet = (html_code or "")[:8000]
    prompt = f"Audit this web application HTML and client scripts for security vulnerabilities:\n\n```html\n{code_snippet}\n```"
    
    mock_response = json.dumps({
        "score": heuristic_result["score"],
        "status": heuristic_result["status"],
        "summary": heuristic_result["summary"],
        "vulnerabilities": heuristic_result["vulnerabilities"],
        "actionable_feedback": heuristic_result["actionable_feedback"],
    }, ensure_ascii=False)

    try:
        res = await llm.call(
            DEEP_LEARNING_SYSTEM_PROMPT,
            prompt,
            tier="brain",
            mock=mock_response,
            max_tokens=2500,
        )
        text = res.get("text", "").strip()
        # Parse JSON
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            data = json.loads(m.group(0))
            score = int(data.get("score", heuristic_result["score"]))
            status = str(data.get("status", heuristic_result["status"])).upper()
            vulns = data.get("vulnerabilities", heuristic_result["vulnerabilities"])
            feedback = data.get("actionable_feedback", heuristic_result["actionable_feedback"])
            
            # If heuristic detected a critical issue that LLM missed, merge it
            for h_vuln in heuristic_result["vulnerabilities"]:
                if h_vuln["severity"] == "critical" and not any(v.get("type") == h_vuln["type"] for v in vulns):
                    vulns.append(h_vuln)
                    status = "REMEDIATION_REQUIRED"
                    score = min(score, 70)

            return {
                "score": score,
                "status": status,
                "model_name": f"AutoCorp Deep Learning Auditor ({res.get('provider', 'brain')})",
                "summary": data.get("summary", heuristic_result["summary"]),
                "vulnerabilities": vulns,
                "actionable_feedback": feedback,
                "audited_at": time.time(),
            }
    except Exception as e:
        print(f"[DEEP LEARNING SECURITY AUDIT FALLBACK] {e}")

    # Fallback to heuristic
    return {
        "score": heuristic_result["score"],
        "status": heuristic_result["status"],
        "model_name": "AutoCorp Deep Learning Semantic Analyzer (Heuristic Mode)",
        "summary": heuristic_result["summary"],
        "vulnerabilities": heuristic_result["vulnerabilities"],
        "actionable_feedback": heuristic_result["actionable_feedback"],
        "audited_at": time.time(),
    }


async def run_security_remediation_loop(
    job_id: int,
    initial_html: str,
    context: str,
    call_agent_fn,
    ensure_agent_fn,
    max_iterations: int = 2,
) -> Tuple[str, Dict[str, Any]]:
    """Closed-loop self-healing remediation:
    
    1. Audits code using the Deep Learning Security Model.
    2. If vulnerabilities are found, feeds actionable feedback back to Frontend Developer.
    3. Re-evaluates until code reaches >= 90/100 or max iterations are exhausted.
    """
    current_html = initial_html
    audit_report = await deep_learning_security_audit(current_html, {"job_id": job_id})
    iteration = 0

    while audit_report["status"] == "REMEDIATION_REQUIRED" and iteration < max_iterations:
        iteration += 1
        feedback_text = audit_report["actionable_feedback"]
        db.x(
            "INSERT INTO feedback(agent, note, ts) VALUES(?,?,?)",
            (
                "Frontend Developer",
                f"Deep Learning Security Audit (Loop {iteration}): Score {audit_report['score']}/100. Issues: {feedback_text[:300]}",
                time.time(),
            ),
        )

        remediation_prompt = (
            f"### [DEEP LEARNING SECURITY AUDITOR FEEDBACK - ITERATION {iteration}]\n"
            f"The Deep Learning Security Model identified critical vulnerabilities (Score: {audit_report['score']}/100):\n"
            f"{feedback_text}\n\n"
            f"REQUIRED ACTION: Remediate all vulnerabilities in the previous website HTML code.\n"
            f"Ensure zero unescaped innerHTML, safe external links with rel='noopener noreferrer', and clean responsive layout.\n"
            f"Output the complete hardened HTML document inside an ```html ... ``` block.\n\n"
            f"Previous HTML Code:\n{current_html[:10000]}"
        )

        fe_agent = await ensure_agent_fn("Frontend Developer", job_id)
        fixed_text = await call_agent_fn(fe_agent, context, remediation_prompt, job_id)
        
        # Extract HTML
        m = re.search(r"```html\s*(.*?)\s*```", fixed_text, re.DOTALL)
        candidate_html = m.group(1).strip() if m else fixed_text.strip()
        if candidate_html.startswith("<!doctype") or "<html" in candidate_html:
            current_html = candidate_html

        # Re-audit
        audit_report = await deep_learning_security_audit(current_html, {"job_id": job_id})

    return current_html, audit_report
