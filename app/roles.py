"""The 70-role roster. Roles are DATA, not processes: an agent is 'hired'
(row created in the agents table) the first time a job needs it."""

DEPARTMENTS = {
    "Executive": {
        "CEO": "Plans every client job, sets the price, decides who to hire.",
        "COO": "Keeps delivery on schedule and unblocks teams.",
        "Chief Strategist": "Chooses which services and markets the agency should grow into.",
        "Chief of Staff": "Writes short decision briefs for the human owner.",
    },
    "Sales": {
        "Lead Prospector": "Finds and qualifies SMEs that need a website, media or consulting.",
        "Outreach Writer": "Writes honest, non-spammy outreach messages in Arabic and English.",
        "Discovery Scribe": "Turns client conversations into a structured brief.",
        "Proposal Writer": "Writes clear proposals with scope, timeline and price.",
        "Pricing Strategist": "Prices work so the agency stays profitable and the SME sees value.",
        "Negotiator": "Handles scope and price negotiation within owner-set limits.",
        "Closer": "Moves approved proposals to signed, paid work.",
        "Upsell Specialist": "Finds genuinely useful add-ons for delivered work.",
    },
    "Web": {
        "Solutions Architect": "Turns a request into a page-by-page technical brief.",
        "UX Planner": "Defines page structure, user flow and calls to action.",
        "UI Designer": "Defines visual style, palette, typography and layout.",
        "Frontend Developer": "Writes production-ready single-file HTML/Tailwind sites.",
        "Backend Developer": "Designs and writes API/back-end code.",
        "Database Designer": "Designs schemas and data models.",
        "Arabic Content Writer": "Writes natural website copy in Arabic.",
        "SEO Specialist": "Handles titles, meta tags, structure and keywords.",
        "Accessibility Auditor": "Checks contrast, semantics and RTL/mobile usability.",
        "Performance Engineer": "Keeps pages light and fast.",
        "Security Reviewer": "Reviews code for common web vulnerabilities.",
        "Deployment Engineer": "Packages and deploys finished sites.",
    },
    "QA": {
        "QA Lead": "Owns the quality gate before anything reaches a client.",
        "Bug Hunter": "Finds defects and edge cases.",
        "Code Reviewer": "Reviews code and replies APPROVED or REJECT with reasons.",
        "Regression Tester": "Checks that fixes did not break earlier work.",
    },
    "Media": {
        "Creative Director": "Sets the creative concept and tone for media work.",
        "Arabic Copywriter": "Writes ad and social copy in Egyptian-friendly Arabic.",
        "English Copywriter": "Writes ad and social copy in English.",
        "Social Media Manager": "Plans and structures social channels.",
        "Video Script Writer": "Writes short-form video scripts.",
        "Storyboard Artist": "Describes shot-by-shot storyboards.",
        "Brand Identity Designer": "Defines naming, voice, palette and logo direction.",
        "Visual Prompt Engineer": "Writes precise prompts for image generation tools.",
        "Vision Analyst": "Reads photos from clients (damaged items, plants, screenshots, sketches) and reports what is visible, never guessing beyond the image.",
        "Content Calendar Planner": "Builds a dated content calendar.",
    },
    "Consulting": {
        "Business Analyst": "Clarifies the business problem and success metrics.",
        "Market Researcher": "Structures market and competitor research; flags what must be verified.",
        "Feasibility Analyst": "Writes feasibility studies with explicit assumptions.",
        "Financial Modeler": "Builds simple cash-flow and break-even models.",
        "Operations Consultant": "Maps and improves workflows.",
        "Digital Transformation Advisor": "Recommends practical automation for SMEs.",
        "Contract Drafting Assistant": "Drafts documents for review by a real lawyer; never gives legal advice.",
        "Risk Analyst": "Lists risks, likelihood, impact and mitigations.",
    },
    "Marketing": {
        "Growth Marketer": "Plans acquisition experiments for the agency itself.",
        "Case Study Writer": "Writes anonymized case studies from delivered jobs; never invents numbers.",
        "LinkedIn Publisher": "Prepares LinkedIn posts for owner approval.",
        "Email Marketer": "Writes consent-based email sequences.",
        "Community Manager": "Drafts replies and engagement for the agency's channels.",
        "Marketing Analyst": "Reads campaign results and recommends next steps.",
    },
    "Finance": {
        "Invoicing Clerk": "Produces clear invoices.",
        "Collections Agent": "Politely follows up on unpaid invoices within owner rules.",
        "Payroll Accountant": "Computes agent 'salaries' from token usage.",
        "Budget Controller": "Watches costs against budget and flags overruns.",
        "Compliance Note Writer": "Drafts tax/compliance notes for an accountant to confirm.",
    },
    "HR": {
        "Role Designer": "Defines new roles when the agency meets an unfamiliar request.",
        "Onboarding Coach": "Writes onboarding instructions for newly created agents.",
        "Performance Reviewer": "Scores agents on QA results and rework.",
        "Training Lead": "Updates agent prompts from feedback.",
    },
    "Support": {
        "Support Agent": "Answers client questions about delivered work.",
        "Customer Success Manager": "Checks in after delivery and spots upsell needs.",
        "Feedback Analyst": "Summarizes client feedback into improvements.",
    },
    "Ops": {
        "Agent Factory": "Writes system prompts for brand-new agent roles.",
        "Prompt Optimizer": "Rewrites agent prompts using QA feedback.",
        "Knowledge Curator": "Keeps reusable playbooks and templates.",
        "Self-Improvement Analyst": "Finds recurring failures and proposes fixes.",
        "Compliance Auditor": "Audits outputs for fabricated claims and policy issues.",
        "Incident Responder": "Handles failed jobs and provider outages.",
    },
}


def all_names():
    return [n for d in DEPARTMENTS.values() for n in d]


def lookup(name):
    n = (name or "").strip().lower()
    for dept, rs in DEPARTMENTS.items():
        for rn, mission in rs.items():
            if rn.lower() == n:
                return dept, mission, rn
    return None, None, None
