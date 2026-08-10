import re

# Clause categories supported by the auditor
CLAUSES = {
    "CONFIDENTIALITY": "Confidentiality",
    "INDEMNIFICATION": "Indemnification",
    "LIMITATION_OF_LIABILITY": "Limitation of Liability",
    "TERMINATION": "Termination",
    "GOVERNING_LAW": "Governing Law"
}

# Regex rules to classify which category a paragraph belongs to
CLASSIFICATION_RULES = {
    "CONFIDENTIALITY": [
        r"\bconfidential(ity)?\b",
        r"\bnon-disclosure\b",
        r"\bnda\b",
        r"\bproprietary information\b",
        r"\bdisclosing party\b",
        r"\breceiving party\b"
    ],
    "INDEMNIFICATION": [
        r"\bindemn(ify|ification|ity|ified|ifying)\b",
        r"\bhold harmless\b",
        r"\bdefend and hold\b"
    ],
    "LIMITATION_OF_LIABILITY": [
        r"\blimit(ation)? of liability\b",
        r"\blimited liability\b",
        r"\bconsequential damages\b",
        r"\bindirect damages\b",
        r"\bpunitive damages\b",
        r"\baggregate liability\b",
        r"\bno event shall.*be liable\b"
    ],
    "TERMINATION": [
        r"\bterminat(e|ion|ed)\b",
        r"\bfor convenience\b",
        r"\bcure period\b",
        r"\bnotice period\b",
        r"\bbreach of contract\b"
    ],
    "GOVERNING_LAW": [
        r"\bgoverning law\b",
        r"\bchoice of law\b",
        r"\bapplicable law\b",
        r"\bjurisdiction\b",
        r"\bvenue\b",
        r"\bcourts of\b",
        r"\bconstrued in accordance with\b"
    ]
}

# Detailed auditing rules categorized by Clause Type and Severity
AUDIT_RULES = {
    "INDEMNIFICATION": {
        "HIGH": [
            {
                "id": "IND-H1",
                "pattern": r"\b(uncapped|absolute|unlimited|without limit|no cap|not be limited)\b",
                "explanation": "Uncapped indemnification obligation detected. This exposes you to unlimited financial liability.",
                "recommendation": "Negotiate an explicit cap on indemnification obligations (e.g., limited to fees paid in the last 12 months)."
            },
            {
                "id": "IND-H2",
                "pattern": r"\b(no reciprocal|unilateral|no obligation to indemnify|not be required to indemnify|have no reciprocal obligation|one-way)\b|provider shall have no.*obligation",
                "explanation": "Completely unilateral indemnification in favor of the Provider only.",
                "recommendation": "Request a reciprocal indemnification clause where each party defends the other for their respective breaches."
            },
            {
                "id": "IND-H3",
                "pattern": r"\b(indirect|consequential|incidental|punitive)\b",
                "explanation": "Indemnification covers indirect or consequential damages. Usually, indemnities should be limited to direct third-party claims.",
                "recommendation": "Limit indemnification coverage strictly to direct, actual damages arising from third-party claims."
            }
        ],
        "MEDIUM": [
            {
                "id": "IND-M1",
                "pattern": r"\b(any and all claims|all losses|every claim)\b",
                "explanation": "Broad indemnification cover without typical carve-outs.",
                "recommendation": "Insert carve-outs for claims arising from the other party's gross negligence or willful misconduct."
            },
            {
                "id": "IND-M2",
                "pattern": r"\bnotify.*within.*(24|48).*hours\b|\bimmediate notice\b|\bpromptly within.*(one|1|two|2).*days\b",
                "explanation": "Extremely short claim notice period (24-48 hours) to trigger indemnification.",
                "recommendation": "Negotiate a more reasonable notice period (e.g., 5 to 10 business days) for indemnification claims."
            }
        ],
        "LOW": [
            {
                "id": "IND-L1",
                "pattern": r"\b(reciprocal|mutual|each party.*indemnify|party shall indemnify the other)\b",
                "explanation": "Reciprocal indemnification clause detected.",
                "recommendation": "Confirm that the scope of indemnified items (IP infringement, breach of law) remains balanced."
            }
        ]
    },
    "LIMITATION_OF_LIABILITY": {
        "HIGH": [
            {
                "id": "LOL-H1",
                "pattern": r"\b(one hundred dollars|nominal amount|five hundred dollars)\b|\$(?:100|500)\b",
                "explanation": "Extremely low or token liability cap (e.g., $100). This effectively shields the other party from meaningful accountability.",
                "recommendation": "Increase the liability cap to a meaningful amount, such as 12 months of service fees or a specific commercially viable insurance limit."
            },
            {
                "id": "LOL-H2",
                "pattern": r"in no event shall provider be liable.*client's liability shall not be limited|\bunilateral\b|provider's liability.*limited.*client's liability.*not",
                "explanation": "Unilateral limitation of liability. Only one party's liability is capped, leaving the other with unlimited liability.",
                "recommendation": "Make the limitation of liability mutual. Both parties should benefit from equivalent caps."
            }
        ],
        "MEDIUM": [
            {
                "id": "LOL-M1",
                "pattern": r"\b(aggregate liability.*limited to.*fees paid|limited to the amount.*paid|limited to fees paid)\b",
                "explanation": "Liability is capped strictly at fees paid. While common, check if this cap is sufficient for high-risk services.",
                "recommendation": "Consider negotiating a multiplier (e.g., 2x or 3x fees paid) or a separate super-cap for data breaches/confidentiality."
            },
            {
                "id": "LOL-M2",
                "pattern": r"\b(limit.*apply to.*breach of confidentiality|cap.*apply to.*confidentiality|including breach of confidentiality)\b",
                "explanation": "Caps apply broadly, but check if confidentiality breaches are capped. Capping confidentiality damages is highly risky.",
                "recommendation": "Ensure exclusions from the cap are mutual and cover gross negligence, willful misconduct, and breach of confidentiality."
            }
        ],
        "LOW": [
            {
                "id": "LOL-L1",
                "pattern": r"\b(either party's.*liability|each party's.*liability|mutual limitation)\b",
                "explanation": "Bilateral limitation of liability.",
                "recommendation": "None needed. Ensure the cap amount is appropriate for the transaction size."
            }
        ]
    },
    "TERMINATION": {
        "HIGH": [
            {
                "id": "TERM-H1",
                "pattern": r"\b(convenience.*without notice|immediately upon notice|terminate immediately|no notice required)\b",
                "explanation": "Termination for convenience with zero notice period. This can leave operations stranded instantly.",
                "recommendation": "Request a minimum notice period of 30 days for termination for convenience."
            },
            {
                "id": "TERM-H2",
                "pattern": r"\b(termination fee|termination charge|penalty fee|liquidated damages for termination)\b",
                "explanation": "High termination fee or penalty for convenience termination.",
                "recommendation": "Negotiate to reduce or eliminate the termination fee. Convenience termination should not carry punitive fees."
            }
        ],
        "MEDIUM": [
            {
                "id": "TERM-M1",
                "pattern": r"\b(convenience.*upon.*(10|ten|15|fifteen).*days|10 days(')? prior written notice|15 days(')? prior written notice)\b",
                "explanation": "Short notice period (10-15 days) for termination for convenience.",
                "recommendation": "Negotiate a standard 30-day notice period to allow transition or replacement time."
            },
            {
                "id": "TERM-M2",
                "pattern": r"\b(terminate.*convenience.*unilateral(ly)?|unilateral convenience|convenience of provider)\b",
                "explanation": "Only one party has the right to terminate for convenience.",
                "recommendation": "Make the convenience termination clause mutual, or remove it entirely in favor of termination for cause only."
            }
        ],
        "LOW": [
            {
                "id": "TERM-L1",
                "pattern": r"\b(convenience.*(30|thirty|60|sixty|90|ninety).*days|30 days(')? prior written notice|60 days(')? prior written notice|90 days(')? prior written notice)\b",
                "explanation": "Standard notice period for convenience termination (30+ days).",
                "recommendation": "None. Keep this standard window as it allows sufficient transition planning."
            }
        ]
    },
    "CONFIDENTIALITY": {
        "HIGH": [
            {
                "id": "CONF-H1",
                "pattern": r"\b(survive indefinitely|remain in effect forever|no.*termination.*confidentiality|obligation.*survive.*forever)\b",
                "explanation": "Perpetual confidentiality obligation with no termination date. This is highly restrictive for commercial contracts.",
                "recommendation": "Limit the survival of confidentiality obligations to a standard term, such as 3 or 5 years post-termination."
            },
            {
                "id": "CONF-H2",
                "pattern": r"\b(unilateral confidentiality|disclosing party.*only|obligations of receiving party)\b",
                "explanation": "One-way confidentiality agreement where only one party's information is protected.",
                "recommendation": "Ensure confidentiality is mutual (bilateral) so that both parties are bound to protect each other's secrets."
            }
        ],
        "MEDIUM": [
            {
                "id": "CONF-M1",
                "pattern": r"\b(shall not include.*information.*publicly known|exclusions|public domain|publicly available)\b",
                "explanation": "Standard exceptions exist, but verify their completeness.",
                "recommendation": "Ensure standard exceptions (public domain, prior knowledge, independent development, legal compulsion) are fully enumerated."
            }
        ],
        "LOW": [
            {
                "id": "CONF-L1",
                "pattern": r"\b(survive.*(3|three|5|five).*years)\b",
                "explanation": "Standard, finite confidentiality survival period (3-5 years).",
                "recommendation": "Excellent. This is standard market practice for commercial agreements."
            }
        ]
    },
    "GOVERNING_LAW": {
        "HIGH": [
            {
                "id": "GOV-H1",
                "pattern": r"\b(cayman islands|switzerland|england and wales|london|singapore|china|hong kong|bermuda)\b",
                "explanation": "Foreign or exotic governing law and dispute venue. This dramatically increases litigation complexity and cost.",
                "recommendation": "Insist on your home state or country's laws, or select a well-established commercial jurisdiction (like Delaware or New York)."
            },
            {
                "id": "GOV-H2",
                "pattern": r"\b(waive(s)?.*jury trial|waive(s)?.*class action|mandatory arbitration)\b",
                "explanation": "Waiver of jury trial or class action rights in dispute resolution.",
                "recommendation": "Verify with legal counsel if waiving jury trials is standard for your corporate policy. Usually acceptable but important to note."
            }
        ],
        "MEDIUM": [
            {
                "id": "GOV-M1",
                "pattern": r"\b(laws of the State of Delaware|laws of Delaware|laws of New York|laws of the State of New York)\b",
                "explanation": "Governing law set to Delaware or New York. Standard for commercial contracts, but may require out-of-state legal counsel if disputes arise.",
                "recommendation": "Delaware/New York is commercially neutral. Verify if setting to your own corporate home state is feasible for ease of recourse."
            }
        ],
        "LOW": [
            {
                "id": "GOV-L1",
                "pattern": r"\b(california|texas|florida|illinois|united kingdom|canada|germany|france)\b",
                "explanation": "Standard domestic governing law.",
                "recommendation": "None needed. Verify it matches the primary place of business of at least one party."
            }
        ]
    }
}

def classify_text(text):
    """
    Classify which contract clause type the given text belongs to.
    Uses regex classification rules. Returns the clause key (e.g. 'CONFIDENTIALITY')
    or None if no category is matched.
    """
    scores = {key: 0 for key in CLASSIFICATION_RULES.keys()}
    text_lower = text.lower()
    
    for key, patterns in CLASSIFICATION_RULES.items():
        for pattern in patterns:
            matches = re.findall(pattern, text_lower)
            scores[key] += len(matches)
            
    best_key = max(scores, key=scores.get)
    if scores[best_key] > 0:
        return best_key
    return None

def audit_clause(clause_type, text):
    """
    Audit a single clause text against the rules for its category.
    Returns:
      - risk_level: 'HIGH', 'MEDIUM', 'LOW'
      - issues: list of dicts describing matched rules (id, explanation, recommendation, highlighted_text)
    """
    if clause_type not in AUDIT_RULES:
        return "LOW", []
        
    issues = []
    text_lower = text.lower()
    rules_dict = AUDIT_RULES[clause_type]
    
    # Audit for HIGH, then MEDIUM, then LOW
    for severity in ["HIGH", "MEDIUM", "LOW"]:
        for rule in rules_dict.get(severity, []):
            match = re.search(rule["pattern"], text, re.IGNORECASE)
            if match:
                # Find matching text snippet
                start = max(0, match.start() - 20)
                end = min(len(text), match.end() + 20)
                snippet = text[start:end].strip()
                if start > 0: snippet = "..." + snippet
                if end < len(text): snippet = snippet + "..."
                
                issues.append({
                    "id": rule["id"],
                    "severity": severity,
                    "explanation": rule["explanation"],
                    "recommendation": rule["recommendation"],
                    "snippet": snippet,
                    "matched_text": match.group(0)
                })
                
    # Determine cumulative risk level
    severities_found = [issue["severity"] for issue in issues]
    if "HIGH" in severities_found:
        risk_level = "HIGH"
    elif "MEDIUM" in severities_found:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"
        
    return risk_level, issues
