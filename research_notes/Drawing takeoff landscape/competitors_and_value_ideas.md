# AI Takeoff, Estimating and Construction Document AI: Competitor Landscape and Value-Add Ideas for Stoa

Research date: 2026-11-13. Most product and accuracy figures come from vendor pages, resellers or vendor-adjacent blogs and are marked **[UNVERIFIED MARKETING]** where relevant. Around 17 search/fetch calls were used, so coverage of smaller vendors is thin and is listed under Gaps.

## 1. US/EU AI takeoff tools: features, formats, accuracy, pricing, funding

### Takeaway
The US market has split into three groups. (a) AI-native self-serve takeoff: Togal.AI, Kreo, STACK FloorPlan AI and Quotr, priced at roughly $175–$300 per user per month. (b) Managed "done-for-you" AI plus human services: Beam AI by Attentive.ai, at $15–25K per trade per year. (c) Incumbents adding AI modules: ConstructConnect's PlanSwift/On-Screen Takeoff "Takeoff Boost", Bluebeam Max, Autodesk Forma Takeoff, and eTakeoff, which resells Togal. None publishes independently verified accuracy figures. Funding is flowing into the category, with Attentive's $30.5M Series B (Nov 2025) and Togal at about $22.65M.

### Cited Findings
**Togal.AI (US)**
- Features: AI Search locates and counts plan elements, and Togal.CHAT answers natural-language questions about plans. It covers drywall, electrical, mechanical, plumbing and FF&E. Pricing starts at $299/user/month, with custom pricing for 4+ users. It has raised $22.65M across five rounds, including a $5M pre-Series A SAFE at a $50M cap (Mar 2023). G2 shows 4.8/5 from 60 reviews — [ConstructConnect 2026 guide](https://www.constructconnect.com/blog/ai-powered-takeoff-and-estimating-software-a-contractors-guide-to-the-top-players-in-2026)
- Claims of "98% accuracy" and "5x faster" circulate in third-party write-ups **[UNVERIFIED MARKETING]**. G2 users scored its cost-database integration 6.0, against Procore's 7.6 — [G2 compare](https://www.g2.com/compare/procore-vs-togal-ai); [Trustpilot](https://www.trustpilot.com/review/togal.ai)
- In Oct 2026 Togal launched "Construction's Last Exam", a 33-task takeoff benchmark on raw PDFs. General-purpose LLMs (OpenAI, Anthropic, Google, xAI and others) scored 2–34% without tools or agents. This is a vendor-run benchmark — [Deadfront Nov 2026 roundup](https://www.deadfront.ai/blog/november-2026-ai-construction-roundup)
- eTakeoff resells Togal AI as an add-on at $1,800/user/year, on top of Advanced ($795) and Premier ($1,495) plans — [ConstructConnect](https://www.constructconnect.com/blog/ai-powered-takeoff-and-estimating-software-a-contractors-guide-to-the-top-players-in-2026)

**Beam AI / Attentive.ai (US/India)**
- Beam sells AI takeoff plus a "done-for-you" takeoff and estimating service at $15–25K per trade per year, with no self-serve pricing. G2 shows 4.9/5 from about 30 reviews, skewed toward commercial work — [ConstructConnect](https://www.constructconnect.com/blog/ai-powered-takeoff-and-estimating-software-a-contractors-guide-to-the-top-players-in-2026). Turnaround is cited as 24–72 hours — [search summary of buzzbid/others](https://buzzbid.com/articles/best-ai-takeoff-software)
- Attentive.ai raised a $30.5M Series B in Nov 2025, led by Insight Partners, with Vertex Ventures, Tenacity and InfoEdge Ventures. Total funding is about $48M. The money is going toward expanding Beam into full-cycle estimating, bid management and proposals — [FinSMEs](https://www.finsmes.com/2025/11/attentive-ai-raises-30-5m-in-series-b-funding.html); [PropTech Connect](https://proptechconnect.com/attentive-ai-raises-30-5m-to-automate-construction-takeoffs-with-ai/). LeadIQ lists a $50M total, which differs from the other figure — [LeadIQ](https://leadiq.com/c/attentiveai/5d24f1946c628d5488220951)

**Kreo (UK)**
- Cloud 2D takeoff with AI auto-measure and "bucket fill". The Pro plan is about £95/month on G2, while ConstructConnect-cited sources list $175/user/month billed annually. The two figures conflict — [Capterra](https://www.capterra.com/p/231342/Kreo-2D-Takeoff/); [G2 Kreo vs PlanSwift](https://www.g2.com/compare/kreo-vs-planswift)
- Complaints: "auto measure can be a little messy", with as much time spent organizing the data as on a manual takeoff. One user spent a day without producing a day's worth of measurements. There are duplicate condition line items. Ratings are 4.2 on Capterra (25 reviews) and 4.5 on G2 (32 reviews) — [Capterra reviews](https://www.capterra.com/p/231342/Kreo-2D-Takeoff/)

**STACK (US)**
- FloorPlan AI detects doors, windows, rooms and walls and produces an editable takeoff, and STACK Assist "Plan Chat" answers plan questions. Premium is $249/user/month and Pro is $299/user/month. FloorPlan AI is a $899/user add-on — [ConstructConnect](https://www.constructconnect.com/blog/ai-powered-takeoff-and-estimating-software-a-contractors-guide-to-the-top-players-in-2026)
- STACK's own blog has a "what AI gets right / still gets wrong" piece, a vendor admission that review is needed — [STACK blog](https://www.stackct.com/blog/what-ai-gets-right-about-construction-takeoffs-and-what-it-still-gets-wrong/)

**ConstructConnect: PlanSwift and On-Screen Takeoff (US)**
- The "Takeoff Boost" suite includes Auto Takeoff, Auto Count, Auto Link, Auto Scale and Auto Bookmark. OST's Auto Scale and AI Auto Name are planned for Aug 2026. PlanSwift is Windows-only and starts at $2,000/year for the first seat. One user claims an 85,000 sq ft takeoff in about 30 minutes **[UNVERIFIED]** — [ConstructConnect](https://www.constructconnect.com/blog/ai-powered-takeoff-and-estimating-software-a-contractors-guide-to-the-top-players-in-2026)

**Bluebeam / Nemetschek (US/DE)**
- Bluebeam Max is a premium AI subscription on Revu, announced at Unbound 2025 and launched globally in 2026. It can count and categorize *existing markups* by natural-language prompt, and it includes Smart Review and Smart Overlay for design conflicts and scope gaps, "Magic Markups" for repetitive takeoff annotations, auto sheet stitching, and a Revu + AI MCP integration that currently supports Claude. VisualSearch counts symbols by example. Bluebeam's own material says the results are not final bid quantities without review — [Architosh May 2026](https://architosh.com/2026/05/ai-powered-bluebeam-max-launches-globally/); [AEC Magazine](https://aecmag.com/news/bluebeam-max-to-boost-revu-with-ai/); [IMAGINiT](https://resources.imaginit.com/how-tos/how-estimators-can-use-bluebeam-max-to-support-faster-takeoffs)

**Autodesk (US)**
- Autodesk Forma (formerly ACC) Construction Takeoff offers 2D/3D takeoff, automated symbol detection, OCR-based Automated Drawing Extraction, AI spec search and Autodesk Assistant chat — [Dan Cumberland Labs](https://dancumberlandlabs.com/blog/autodesk-construction/). This is a secondary blog, and I did not verify it against Autodesk docs.

**Others / new entrants**
- Quotr (Berkeley) raised a $4M seed on 30 Sep 2026 and claims 20-hour takeoffs cut to 1–2 hours **[UNVERIFIED]**. Its Lite plan is $79.90/seat/month — [Construction Metrics](https://constructionmetrics.com/2026/10/01/quotr-ai-takeoff-seed-round/)
- xBuild raised a $19M Series A in Jan 2026 (N47, a16z, Rackhouse). It does AI chat estimates for roofing from photos, with live QXO and ABC Supply pricing and token-based pricing — [ConstructConnect](https://www.constructconnect.com/blog/ai-powered-takeoff-and-estimating-software-a-contractors-guide-to-the-top-players-in-2026)
- TheTakeoff.AI (ContraVault) raised $3.1M pre-Series A in Jun 2026, led by Chiratae — [search result](https://www.contravault.com/blog/10-best-takeoff-software-in-2026)
- PataBid raised a $2M pre-seed in Oct 2026. Its "Newton" conversational estimating agent targets MEP, and the company claims 200+ MEP contractors and $2B+ in bids processed — [Deadfront](https://www.deadfront.ai/blog/november-2026-ai-construction-roundup)
- Civils.ai (Singapore) combines AI takeoff with cross-checking of drawings, and Rudus (YC) detects footings, walls, columns and slabs — [StartUs Insights](https://www.startus-insights.com/innovators-guide/construction-ai-startups/)
- CubiCasa (Finnish origin) makes floor plans from a roughly 5-minute smartphone scan. It was acquired by Clear Capital (US) after raising about $4.6M (Butterfly Ventures, Moderne, FBS). It now appears on about 1 in 3 new US listings (Oct 2025) and is integrated with Redfin. It targets real estate, not construction takeoff — [Dealroom](https://app.dealroom.co/companies/cubicasa); [AccessNewswire](https://www.accessnewswire.com/newsroom/en/real-estate/cubicasa-and-industry-partners-reach-major-milestone-floor-plans-now-on-1-in-3-u.s.-lis-1083712)

### Inferences
- Takeoff detection (walls, rooms, doors, symbol counts) is commoditizing. Incumbents bundle it as an add-on at $900–$1,800 per user per year. Raw detection on its own is a weak moat for a new entrant, so the differentiation has to sit downstream: trust, revisions, procurement, local standards.
- Beam's managed-service model is evidence that customers will pay for guaranteed accuracy with humans in the loop. A Nordic equivalent could pair AI output with a reviewed result.
- No vendor in the sample supports Finnish or Nordic classification (Talo 2000, CoClass) or Finnish-language drawings, based on the absence of any mention.

### Gaps
- I found no reliable public data on Exayard, Countfire (UK, fire/electrical symbol counting), Provision, Kojo's takeoff features or funding, Archilogic, cove.tool or Trimble's takeoff AI. The searches returned nothing usable, so check vendor sites directly.
- No independent, peer-reviewed accuracy benchmark across vendors was found.

## 2. Construction document AI and drawing QA

### Takeaway
The "document layer" is getting the most money. Trunk Tools ($70M total) and Buildcheck ($18M) lead in the US, Document Crunch now belongs to Trimble, and incumbents (Dalux, Bluebeam, Autodesk, Newforma) are shipping cited Q&A assistants. A cited project-document Q&A, Stoa's core, is becoming table stakes inside the major CDEs. Stoa's edge has to come from Nordic language and standards and from on-site workflows.

### Cited Findings
- **Trunk Tools (US):** $40M Series B on 24 Jul 2025, led by Insight Partners (Redpoint, Innovation Endeavors, Liberty Mutual Strategic Ventures and others). That brings it to $70M total at a reported $325M valuation. Its agents are TrunkText (document Q&A), TrunkSubmittal (submittal compliance) and TrunkReview (drawing change analysis). A 2026 Autodesk Forma integration was reported — [SiliconANGLE](https://siliconangle.com/2025/07/24/trunk-tools-raises-40m-revolutionize-construction-teams-interact-project-data/); [ENR](https://www.enr.com/articles/61084-trunk-tools-nets-40m-in-funding-round-led-by-insight-partners); [Commercial Observer](https://commercialobserver.com/2025/07/trunk-tools-contech-series-b/)
- **Buildcheck (US):** $12M Series A on 9 Sep 2026, led by Telescope Partners with DPR's venture arm, Uncork, Salt and Xfund. It follows a $5.9M seed, for $18M total. It is a computer-vision drawing review tool with 110+ paying customers and 150K+ sheets analyzed. "Custom Checks" turns a firm's QA/QC manuals into review agents that run on every revision, and expert reviewers confirm each issue and set its severity — [AEC Magazine](https://aecmag.com/construction/buildcheck-raises-12m-in-series-a/); [ENR seed](https://www.enr.com/articles/62124-design-review-platform-buildcheck-raises-59m-to-boost-construction-ai-tools); [Bricks & Bytes](https://bricks-bytes.com/ai/buildcheck-12m-series-a-ai-drawing-review-earn-the-right/)
- **Document Crunch (US, now a Trimble company):** On 21 Oct 2026 it extended its contract and spec risk review to read drawings. CrunchAI extracts general notes, allowances and scope language and answers questions with source-linked citations. A customer reported it surfaced a concrete-cutting and backfill requirement — [Deadfront](https://www.deadfront.ai/blog/november-2026-ai-construction-roundup)
- **Newforma** acquired Lumi AI (Oct 2026) for traceable answers in its Vojo assistant — [Deadfront](https://www.deadfront.ai/blog/november-2026-ai-construction-roundup)
- **Dalux (DK):** Release 2026.1 added an AI Assistant for finding and understanding information in project documents, in phased rollout. Release 2026.5 added "AI Safety Hints" powered by SiteWalk — [Dalux release notes 2026.1](https://support.dalux.com/hc/en-us/articles/23976440268572); [Dalux 2026.5](https://support.dalux.com/hc/articles/28733540602140)
- **Bluebeam Max** Smart Review and Overlay finds design conflicts and scope gaps — [AEC Magazine](https://aecmag.com/news/bluebeam-max-to-boost-revu-with-ai/)

### Inferences
- Dalux is the most direct Nordic threat to Stoa's Q&A wedge, given its large Nordic CDE install base and a native AI assistant. Trimble, through Document Crunch and its Nordic Tekla footprint, is a second.
- Buildcheck's "customer QA manual becomes checks" with expert confirmation is a pattern Stoa could localize, for example RT cards, RakMK/Ympäristöministeriö decrees, and client YTV/COBIM requirements turned into checks.

### Gaps
- I did not research Structured AI, LightTable, Primepoint, Spacial, Part3, Wyre AI, Archiboost or Adicio, for lack of tool budget. Congrid and Admicom 2026 AI features returned nothing.

## 3. Nordic and Finnish landscape and standards

### Takeaway
Nordic funding is going to preconstruction and design AI: Brickanta (SE, $8M seed), Endra (SE, $50M Series A, MEP design), Solvera (NO, $6.3M pre-seed) and Make a BIM (FI, pre-seed, 2D to BIM). I found no Finnish AI takeoff startup. Finnish takeoff runs on Talo 2000 nomenclature and YTV 2012 Part 7. Sweden uses AMA/BSAB and is moving to CoClass. A carbon-limit decree that took effect in Finland in Jan 2026 creates a regulatory hook for quantity-to-CO2 output.

### Cited Findings
- **Brickanta (Stockholm):** $8M seed in Jan 2026, led by Northzone with YC, SSE Business Lab and 20VC. It builds an "agentic AI OS" for bid analysis, cost estimation and procurement — [Tech.eu](https://tech.eu/2026/01/27/brickanta-closes-8m-round-to-expand-ai-use-in-construction-planning/); [Sifted](https://sifted.eu/articles/northzone-and-lovable-ceo-backs-brickanta-8m). CB Insights lists $8.39M, which differs slightly — [CB Insights](https://www.cbinsights.com/company/brickanta/financials)
- **Endra (Stockholm):** $50M Series A in Jun 2026 led by a16z, about $75M raised in total, for MEP design automation. **Solvera (Oslo):** $6.3M pre-seed in Oct 2026 for an AI-native engineering firm focused on MEP — [ArcticStartup / search summary](https://arcticstartup.com/brickanta-raises-8-million-seed/); [BeBeez](https://bebeez.eu/2026/10/16/norwegian-startup-raises-6-3-million-pre-seed-round-to-build-ai-native-engineering-firm/)
- **Make a BIM (Finland, founded 2023):** Converts 2D drawings to BIM/IFC "within minutes" **[UNVERIFIED]**. Pre-seed in Aug 2024 led by Kiilto Ventures, with Innovestor and FiBAN angels. It targets renovation of the existing building stock — [Kiilto](https://www.kiilto.com/newsroom/finnish-proptech-startup-make-a-bim-secures-funding-to-accelerate-digitisation-of-aging-building-stock/)
- Finland and Estonia are among the first countries where designers can submit IFC models for automated permit checking, and Finland's Building Act takes effect in 2026 — [Prodlib](https://www.prodlib.com/finland-building-act); [Solibri](https://www.solibri.com/articles/rava3pro-and-solibri-collaborate-toward-a-digital-building-permitting-process-in-finland)
- Tracxn lists 11 Nordic "native AI in construction" companies (Aug 2026), including Finch 3D and Spotscale — [Tracxn](https://tracxn.com/d/artificial-intelligence/ai-startups-in-native-ai-in-construction-in-nordics/__OIFd1sKYKRkvYjaPZHQtjJY9s62S5UVTNYVA0T3AtA8/companies)
- **Talo 2000:** The national nomenclature standardizes quantity calculation and contract documents. The production nomenclature (tuotantonimikkeistö) supports cost and production control, and the quantity-calculation rules (määrälaskentaohjeet) are aligned to it for both contractors' internal estimating and joint measurement with the client. There is a separate building-element classification (rakennusosanimikkeistö) — [Rakennustieto Talo 2000](https://www.rakennustieto.fi/en/talo-2000-nimikkeistot); [Prisma product listing](https://www.prisma.fi/tuotteet/110123310/talo-2000-nimikkeisto-yleisseloste-110123310)
- Rakennustieto publishes yearly cost data, *Rakennusosien kustannuksia* (2025 and 2026 editions), plus a renovation-cost edition. These are reference unit prices that could be licensed for cost mapping — [Rakennustieto](https://www.rakennustieto.fi/en/palvelut/rakennusosien-kustannuksia); [Prisma 2026](https://www.prisma.fi/tuotteet/111275432/lindberg-rakennusosien-kustannuksia-2026-111275432)
- **YTV 2012** (buildingSMART Finland) Part 7 covers model-based quantity takeoff across project phases but gives no concrete calculation instructions. Estimators should calculate quantities *by location* for use in production planning — [buildingSMART Finland YTV](https://buildingsmart.fi/yleiset-tietomallivaatimukset-ytv/); [Tampere thesis](https://trepo.tuni.fi/bitstream/123456789/21530/3/uusitalo.pdf)
- **CO2data.fi** (Syke) is a free national emissions database with building and infrastructure databases, 1,000+ infra products, and on-site waste factors. Decree 2/2026 on the carbon-footprint limit for new buildings took effect on 9 Jan 2026 — [Syke CO2data](https://syke.fi/en/environmental-data/calculators-and-tools/co2data-service); [Syke building DB](https://www.syke.fi/en/environmental-data/calculators-and-tools/co2data-service/emissions-database-building-construction)
- **One Click LCA** (Helsinki) offers a Finnish Carbon Assessment Tool that follows the draft national methodology (12/2024) — [One Click LCA community](https://community.oneclicklca.com/t/whats-new-in-one-click-lca-in-march-2025/2027)
- **Sweden:** CoClass is gradually replacing BSAB 96. AMA imposes requirements only once its codes are referenced in a technical description, and it includes guidance on quantity lists (mängdförteckningar). Solibri's Swedish adaptation has rule sets aligned to BSAB, AMA and BIP — [SmartBuilt BSAB 2.0 report](https://smartbuilt.se/media/2251/slutrapport_bsab20.pdf); [Byggtjänst handbook](https://byggtjanstcms.byggtjanst.se/globalassets/bokhandeln/provlas/provlas-beskrivningshandboken-utg-5.pdf); [Nordic BIM Solibri SE](https://www.nordicbim.com/products/solibri/swedish-adaption). A Chalmers thesis reports model-based takeoff was about 40x more efficient in Swedish ventilation contracts — [Chalmers ODR](https://odr.chalmers.se/items/caf269c0-7f1a-4e31-9f9a-eb7116058de5)

### Inferences
- Outputting quantities natively coded to Talo 2000 (FI) and CoClass/AMA (SE) is a clear localization moat that US tools lack.
- The 2026 carbon-limit decree, together with a free national CO2 database, makes "quantities to embodied carbon" a cheap and regulatory-relevant add-on. One Click LCA is a partner or integration target more than a competitor.

### Gaps
- I found no sources on Haahtela or TATE practices, huoneselitys/huonekortti (room schedule and room card) structure, RT card content, or Finnish material-ordering practices (wholesalers such as Stark, K-Rauta Pro, Onninen and Ahlsell, and their APIs or price lists). COBIM 2012 is assumed to be the English name of YTV 2012, but I did not verify this. Congrid and Admicom AI roadmaps were not found.

## 4. User pain points with current takeoff tools

### Takeaway
The complaints are consistent: AI output still needs review, at 20–100% of the time saved. Accuracy collapses on scans, hand-marked revisions and non-standard symbols. Wrong scale and outdated revisions produce clean-looking but wrong takeoffs. Marketing overpromises, and cost-database integration is weak.

### Cited Findings
- A University of Kansas study cited by vendors found the AI takeoff took about 1 minute, but manual correction took about 30 minutes. A Togal-sponsored study reported 37 minutes for AI plus cleanup against 2.5 hours manual **[vendor-sponsored]** — [Togal blog](https://www.togal.ai/blog/ai-takeoff-software-beats-manual-calculations); [ConstructConnect accuracy piece](https://www.constructconnect.com/blog/are-ai-takeoffs-accurate-in-2026)
- Accuracy falls on scanned sheets, hand-marked revisions and non-standard symbols. A takeoff on the wrong scale or an outdated revision "might look clean, but it won't be accurate" — [Simpro HVAC](https://www.simprogroup.com/blog/how-to-use-ai-for-hvac-estimating); [Technbrains](https://www.technbrains.com/blog/ai-construction-estimating/)
- One comparison found AI quantities fast but needing 3–4 hours of review on a warehouse job. Dense or heavily annotated drawings require cleanup. The source has low authority — [constructionaitools](https://constructionaitools.pages.dev/estimation/ai-vs-manual-takeoff-comparison)
- Trustpilot reviewers called Togal "overpriced, under-delivered". One paid about $2,700 expecting automatic rebar and concrete volumes and did not get them — [Trustpilot Togal](https://www.trustpilot.com/review/togal.ai)
- Kreo users: auto-measure is "messy", and data reorganization eats the time saved — [Capterra Kreo](https://www.capterra.com/p/231342/Kreo-2D-Takeoff/)
- Practitioner consensus favors a hybrid: AI for initial quantities on clean plans, manual for revisions and complex work — [Technbrains](https://www.technbrains.com/blog/ai-construction-estimating/); BuildVision advises testing AI tools before using them on bids — [ForConstructionPros](https://www.forconstructionpros.com/construction-technology/automation-and-ai/article/22975238/buildvision-ai-test-ai-takeoff-tools-before-using-them-for-bids)
- General LLMs score 2–34% on Togal's takeoff benchmark — [Deadfront](https://www.deadfront.ai/blog/november-2026-ai-construction-roundup)

### Inferences
- Trust and verifiability, not raw detection, are the unmet need. Features that make review fast (confidence, provenance, revision diffs, scale sanity checks) target the documented pain directly.

### Gaps
- Searches returned no Reddit threads from r/estimators or r/Construction. The forum sentiment here comes from aggregators and summaries.

## 5. Value-add ideas for Stoa on top of automated takeoff

### Takeaway
Stoa already has a cited Q&A over project documents used on Nordic sites. It should position takeoff as **verifiable, revision-aware, Nordic-standard quantities connected to ordering and carbon**, not as another detector. Each idea below is tied to a documented gap.

### Cited Findings (evidence that each idea answers a real gap)
- Revision handling is a top failure mode ([Simpro](https://www.simprogroup.com/blog/how-to-use-ai-for-hvac-estimating)). Trunk Tools' TrunkReview and Bluebeam Smart Overlay already compare drawing changes, but neither is described as diffing *quantities* ([SiliconANGLE](https://siliconangle.com/2025/07/24/trunk-tools-raises-40m-revolutionize-construction-teams-interact-project-data/); [AEC Mag](https://aecmag.com/news/bluebeam-max-to-boost-revu-with-ai/))
- xBuild's live supplier pricing (QXO, ABC Supply) shows that procurement integration is fundable ([ConstructConnect](https://www.constructconnect.com/blog/ai-powered-takeoff-and-estimating-software-a-contractors-guide-to-the-top-players-in-2026))
- Buildcheck's expert-confirmed issues and Beam's managed service show demand for human-verified output ([AEC Mag](https://aecmag.com/construction/buildcheck-raises-12m-in-series-a/))
- Finnish decree 2/2026 and the free CO2data plus One Click LCA's Finnish tool support a carbon add-on ([Syke](https://www.syke.fi/en/environmental-data/calculators-and-tools/co2data-service/emissions-database-building-construction))
- Talo 2000 quantity rules and YTV's by-location requirement support location- and nomenclature-coded output ([Rakennustieto](https://www.rakennustieto.fi/en/talo-2000-nimikkeistot); [Tampere thesis](https://trepo.tuni.fi/bitstream/123456789/21530/3/uusitalo.pdf))

### Inferences (proposed features, ranked by fit with Stoa)
1. **Cited quantities (provenance per line).** Each quantity links to the sheet region, the room/schedule row and the spec clause it came from, reusing Stoa's citation engine. This answers the trust complaint directly.
2. **Revision-aware quantity diff.** "Rev C vs Rev B: +14 m² of drywall in rooms 2.14–2.18, 3 doors removed." Feed it into change-order and claim evidence with an immutable audit trail (timestamped source hash, reviewer, approval).
3. **Confidence and review queue.** Flag low-confidence items (scans, hand markups, non-standard symbols) and scale outliers, such as a room area that disagrees with the room schedule or a dimension string that disagrees with the scale. Route only those to a human. This is a "review 20%, not 100%" workflow.
4. **Schedule-to-plan consistency checks.** Cross-check huoneselitys/huonekortti room schedules, door, window and finish schedules against the plan counts and specs, plus RT card or client YTV requirements turned into Buildcheck-style "custom checks".
5. **Nordic classification mapping.** Auto-code quantities to Talo 2000 (rakennusosa/hankenimikkeistö), CoClass/AMA for Sweden, and Norwegian NS 3420 (not researched). Optionally map to Rakennustieto unit-cost data (a licensing question) and export to Finnish estimating tools (TATE, Haahtela, Fokus; not verified).
6. **Order lists with waste and packaging rounding.** Apply waste factors (CO2data also lists on-site waste factors) and round to box, pack and pallet sizes. Split by location and delivery phase (YTV's by-location principle), and export as order lists or CSV/EDI to Finnish wholesalers. Supplier APIs are a gap to validate.
7. **Embodied carbon per line.** Map quantities to CO2data.fi generic values or EPDs, check against the 2026 carbon-limit decree, and export to One Click LCA, positioned as a partner.
8. **On-site photo verification.** A site user snaps a photo, Stoa matches it to the plan location and confirms installed counts or progress against the takeoff (the Buildots and Dalux SiteWalk territory), closing the loop between planned and installed quantities for billing (maksuerä) and claims.
9. **Q&A over quantities.** "How many fire doors EI30 on floor 3, and which spec clause governs them?" This combines Stoa's existing assistant with the structured takeoff, a capability Togal.CHAT and STACK Plan Chat have only for the US market and in English.
10. **Finnish and Swedish language drawing understanding** (abbreviations, RT symbols, Finnish room names) as a baseline moat against US tools.

### Gaps
- None of these ideas were validated with Finnish users. Wholesaler API availability, TATE and Haahtela export formats, and Rakennustieto data-licensing terms need direct inquiry.
