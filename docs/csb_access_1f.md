# Milestone 1F-A — CSB access feasibility

Evidence checked: 2026-10-05. Decision: **plausible authorized research route, unconfirmed access; not a dependency of the 559-record fallback**. No application or message has been sent and no CSB microdata acquired.

## What is established

Ainscoe et al. identify the Ministry as the access authority and say the authors cannot redistribute the ground data for legal reasons. Their Data availability section points to [CSB contact](https://csb.gov.tr/en/contact-us) and `cevrevesehircilikbakanligi@hs01.kep.tr`. The paper's corresponding author, Eleanor A. Ainscoe (`eleanorann.ainscoe@ntu.edu.sg`), is a possible source of routing advice, not a substitute granting authority. The authors' receipt of the survey is precedent for research access, not a promise that this project qualifies. Their February 17 snapshot contains 911,181 points; variable positioning and incomplete inspections require substantial quality control. It predates the February 20 aftershock. [Primary paper, Methods and Data availability](https://www.nature.com/articles/s43247-025-02623-4).

The official [Ministry e-Devlet directory](https://turkiye.gov.tr/cevre-ve-sehircilik-bakanligi) lists CİMER as an information-request route and the switchboard **+90 312 410 10 00**. Its authenticated damage-query/appeals service is not an evidenced bulk research export. The [Yapı İşleri organizational chart](https://yapiisleri.csb.gov.tr/teskilat-semasi) identifies the Afet Hasarları Tespiti Daire Başkanlığı (Disaster Damage Assessment Department). Its [administrative duties](https://yapiisleri.csb.gov.tr/yonetim-hizmetleri-i-88557) include routing CİMER/Ministry information requests. These support a credible route to ask for the responsible data custodian; they do not establish entitlement to the dataset.

Direct browsing of the paper's English contact URL timed out during this audit. Official directory and indexed department pages supplied alternate contact evidence. The KEP address is reproduced as published; ordinary-email delivery and the project's eligibility to use that channel were not tested.

## Conditions remain to be negotiated, not assumed

No CSB-specific research application form, public dataset licence, eligibility rule, fee schedule or delivery commitment was established from the sources checked. Do not call the data open, downloadable, CC BY, or available merely on reasonable request. Article-level open licensing does not grant redistribution of the underlying restricted survey.

Before accepting access, obtain written answers covering:

- Authorized research purpose, named users/institution, country of processing, storage and retention; whether an institutional agreement is needed.
- Permission for local analysis, spatial joins to EO/context, publishing aggregate results, and sharing derived features/model weights; explicitly clarify restrictions on coordinates and row-level extracts.
- Available snapshot dates, event sequence attribution, damage codebook (including moderate/unassessable states), reassessment history, coordinate precision and inspection coverage.
- Available building attributes, stable pseudonymous identifiers and practical export format; request no owner or occupant identifiers.
- Fees, delivery timing, publication review/attribution obligations and deletion requirements.

These are **project diligence questions**, not claimed Ministry requirements. Until answered, keep any future received records out of Git and external services; do not infer permission from a public-facing lookup.

## Bounded next step and stop rule

The next authorized human action would be one concise research-access enquiry to the Ministry, routed to Yapı İşleri / Afet Hasarları Tespiti, referencing the paper and requesting a de-identified building-level snapshot and terms. A separate author enquiry can ask which Ministry office handled access, without requesting an unauthorized copy. No message has been submitted under this milestone.

**Project timebox:** retain the 559 survey as the frozen target now. If the owner elects to make enquiries, allow one enquiry and one follow-up over **10 business days from actual submission**. With no concrete written access path and conditions by that date, classify CSB as `deferred_external_access` and continue 2A on the fallback. This is an internal planning deadline, not a legal response deadline or an automatic scheduled task. Non-response does not prove access impossible. A later grant triggers a separately versioned protocol amendment and independent data/chronology audit; it never silently replaces the locked target or held-out observations.

**Exit criterion achieved:** authority and credible enquiry routes identified, unknown terms recorded, acquisition not claimed, and fallback insulated from external delay.
