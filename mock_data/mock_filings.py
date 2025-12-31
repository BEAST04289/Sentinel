"""
Mock SEC Filings for Sentinel Demo - Realistic financial events
"""

from datetime import datetime
from typing import List, Dict, Optional

MOCK_FILINGS = [
    {
        "filename": "NVDA_8K_Lawsuit.pdf",
        "ticker": "NVDA",
        "type": "8-K",
        "headline": "Class Action Lawsuit Filed - Patent Infringement in AI Chips",
        "expected_salience": 0.85,
        "content": """UNITED STATES SECURITIES AND EXCHANGE COMMISSION
Washington, D.C. 20549

FORM 8-K - CURRENT REPORT

Date of Report: January 15, 2025

NVIDIA CORPORATION (NVDA)
2788 San Tomas Expressway, Santa Clara, California 95051

Item 8.01 Other Events - MATERIAL LITIGATION ANNOUNCEMENT

On January 15, 2025, NVIDIA Corporation was named as a defendant in a class action lawsuit filed in the United States District Court for the Northern District of California.

ALLEGATIONS:
The lawsuit alleges patent infringement related to certain artificial intelligence chip technologies incorporated in the Company's H100, H200, and B100 data center GPU products. The plaintiffs claim that NVIDIA's tensor core architecture infringes on multiple patents.

PLAINTIFF DEMANDS:
- Monetary damages estimated at $2.1 billion
- Injunctive relief halting production of affected products
- Treble damages under willful infringement claims

RISK FACTORS:
This matter presents several material risks:
1. REVENUE IMPACT: H100/H200 products represent approximately $47 billion in annual revenue
2. MARKET POSITION: Legal uncertainty may cause customer procurement delays
3. SETTLEMENT COSTS: Historical semiconductor litigation has resulted in settlements of $500M-$2.5B
4. TIMELINE: Similar cases take 18-36 months to resolve

NVIDIA believes these claims are without merit and intends to vigorously defend against this lawsuit.

The asserted patent portfolio represents approximately 15% of NVIDIA's current market capitalization.
"""
    },
    {
        "filename": "TSLA_8K_Recall.pdf",
        "ticker": "TSLA",
        "type": "8-K",
        "headline": "Vehicle Safety Recall - Autopilot Software Update Required",
        "expected_salience": 0.65,
        "content": """UNITED STATES SECURITIES AND EXCHANGE COMMISSION
Washington, D.C. 20549

FORM 8-K - CURRENT REPORT

TESLA, INC. (TSLA)
1 Tesla Road, Austin, Texas 78725

Item 8.01 Other Events - SAFETY RECALL NOTICE

On January 14, 2025, Tesla announced a voluntary safety recall affecting approximately 362,758 vehicles equipped with Full Self-Driving (Beta) software.

AFFECTED VEHICLES:
- Model 3: 142,580 units (2023-2024)
- Model Y: 198,345 units (2023-2024)
- Model S: 12,468 units (2023-2024)
- Model X: 9,365 units (2023-2024)

RECALL ISSUE:
The recall addresses a software control logic issue that may allow vehicles to act unsafely around certain road edge cases:
1. Failure to detect stationary objects in low-visibility conditions
2. Incorrect speed selection approaching blind intersections
3. Potential to exceed posted speed limits in school zones

REMEDY:
Over-the-air software update (v12.3.4) - no service center visit required.

FINANCIAL IMPACT:
- Software Development: $32 million
- Customer Notification: $3 million
- Total Direct Cost: $37 million (pre-tax)

NHTSA has been notified and is monitoring the situation. No accidents or injuries have been reported.
"""
    },
    {
        "filename": "AAPL_10Q_Earnings.pdf",
        "ticker": "AAPL",
        "type": "10-Q",
        "headline": "Q4 2024 Earnings Miss - Revenue Decline, Guidance Lowered",
        "expected_salience": 0.70,
        "content": """UNITED STATES SECURITIES AND EXCHANGE COMMISSION
Washington, D.C. 20549

FORM 10-Q - QUARTERLY REPORT

APPLE INC. (AAPL)
One Apple Park Way, Cupertino, California 95014

FISCAL YEAR 2024 - FOURTH QUARTER RESULTS

REVENUE BREAKDOWN:
Total Net Sales: $89.5 billion (vs. $94.8 billion consensus - MISS 5.6%)

Product Categories:
- iPhone: $43.8 billion (-5% YoY) - BELOW EXPECTATIONS
- Services: $24.2 billion (+12% YoY) - IN LINE
- Mac: $7.8 billion (+3% YoY) - BEAT
- iPad: $6.9 billion (-8% YoY) - MISS
- Wearables: $6.8 billion (-15% YoY) - SIGNIFICANT MISS

GEOGRAPHIC PERFORMANCE:
- Americas: $38.2B (+2%)
- Europe: $24.5B (-1%)
- Greater China: $15.1B (-12%) - KEY CONCERN
- Japan: $6.2B (+5%)

PROFITABILITY:
- EPS: $1.52 (vs. $1.67 consensus) - MISS 9%
- Gross Margin: 45.2% (vs. 45.8% expected)

GUIDANCE REVISION (MATERIAL):
Previous Full-Year: $400-410 billion
Revised Full-Year: $385-395 billion (DOWN $15B midpoint)

REASONS FOR DOWNWARD REVISION:
1. iPhone 16 demand weaker than expected in China
2. Macroeconomic headwinds in European markets
3. FX headwinds ($1.2B impact)
4. Vision Pro volume ramp delayed to Q2 2025
"""
    },
    {
        "filename": "NVDA_Positive_News.pdf",
        "ticker": "NVDA",
        "type": "NEWS",
        "headline": "Major Hyperscaler Partnership - $4.2B Revenue Contract",
        "expected_salience": 0.35,
        "content": """NVIDIA CORPORATION - PRESS RELEASE

NVIDIA Announces Transformational Hyperscaler Partnership

SANTA CLARA, Calif. - January 16, 2025

NVIDIA Corporation today announced a significant multi-year supply agreement with a major global cloud service provider for next-generation AI accelerators.

CONTRACT HIGHLIGHTS:
- Total Contract Value: $4.2 billion over 36 months
- Average Annual Value: $1.4 billion
- Products: H200 GPU Clusters, B100 GB200 Systems
- Total GPU Count: Approximately 50,000 units

STRATEGIC SIGNIFICANCE:
This represents one of the largest single data center deals in NVIDIA's history and validates:
1. Sustained enterprise appetite for GenAI infrastructure
2. Customer confidence in NVIDIA's product roadmap
3. Competitive position maintained versus AMD and custom ASICs

FINANCIAL IMPACT:
- Q1 2025 Data Center Revenue: Raised by $800 million
- Full Year 2025 Data Center: Now expected to exceed $75 billion
- Gross Margin: Expected 72-74% on this contract

CEO Jensen Huang: "This partnership demonstrates the mission-critical role NVIDIA plays in the AI infrastructure buildout. Our full-stack platform approach continues to win."

This is a POSITIVE development for shareholders, supporting current valuation multiples.
"""
    },
    {
        "filename": "TSLA_8K_SEC_Investigation.pdf",
        "ticker": "TSLA",
        "type": "8-K",
        "headline": "SEC Investigation - Executive Stock Transactions Under Review",
        "expected_salience": 0.78,
        "content": """UNITED STATES SECURITIES AND EXCHANGE COMMISSION
Washington, D.C. 20549

FORM 8-K - CURRENT REPORT

TESLA, INC.
1 Tesla Road, Austin, Texas 78725

Item 8.01 Other Events - SEC INVESTIGATION DISCLOSURE

On January 13, 2025, Tesla, Inc. received formal notice from the Securities and Exchange Commission indicating the commencement of a formal investigation.

INVESTIGATION SCOPE:
The SEC is investigating stock transactions executed by certain executive officers during Q3 2024, examining whether adequate disclosures were made regarding material non-public information.

TIMELINE AND TRANSACTIONS:
- Period under review: July 1 - September 30, 2024
- Executives involved: Three senior officers (CFO, General Counsel, SVP Engineering)
- Total transaction value: $127 million in stock sales

SEC CONCERNS:
1. Whether executives had access to internal production forecast revisions
2. Timing of transactions relative to Q3 earnings announcement
3. Adequacy of insider trading policy compliance
4. Potential violations of Rule 10b5-1 trading plan requirements

POTENTIAL OUTCOMES:
1. NO ACTION: SEC concludes without charges (60% probability)
2. SETTLEMENT: Civil penalties $5-25 million range
3. FORMAL CHARGES: Low probability but high impact
4. CONSENT DECREE: Enhanced compliance monitoring 2-3 years

Tesla has retained Wilmer Hale LLP as outside counsel and is fully cooperating.

This is Tesla's second SEC investigation in three years.
"""
    }
]


def get_mock_filing(filename: str) -> Optional[Dict]:
    """Get a specific mock filing by filename"""
    for filing in MOCK_FILINGS:
        if filing["filename"] == filename:
            return filing
    return None


def get_mock_filing_content(filename: str) -> bytes:
    """Get mock filing content as bytes"""
    filing = get_mock_filing(filename)
    if filing:
        return filing["content"].encode('utf-8')
    return b""


def list_mock_filings() -> List[Dict]:
    """List all available mock filings"""
    return [
        {
            "filename": f["filename"],
            "ticker": f["ticker"],
            "type": f["type"],
            "headline": f["headline"],
            "expected_salience": f["expected_salience"]
        }
        for f in MOCK_FILINGS
    ]
