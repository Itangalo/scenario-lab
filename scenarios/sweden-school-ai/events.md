# External Events -- AI Competence in Swedish Schools

## Parliamentary Election 2026

**ID:** election_2026

**Condition:** September 2026 is included in the turn being covered

**Probability:** 100 percent

**Can repeat:** No

**Description:** Sweden holds its general election in September 2026. The outcome determines the new government's stance on AI in education. The current government (as of early 2026) has been passive or hostile toward AI in schools, with no national coordination. The election shifts what becomes politically possible, but it does not instantly change classroom practice.

## New Government AI Education Strategy

**ID:** government_ai_strategy

**Condition:** Requires that the Parliamentary Election 2026 event has occurred previously

**Probability:** 10 percent per round in the first turn after the election, 20 percent in the second turn, 30 percent in subsequent turns

**Can repeat:** No

**Description:** The government announces a national strategy for AI in education, including funding for teacher training, curriculum guidance, assessment support, and coordination between municipalities. This is mainly a future accelerator of school_readiness and teacher competence; it should first shift sentiment and planning, and only later affect classrooms after the constitutionally required delay.

## New National Curriculum 2028

**ID:** curriculum_reform_2028

**Condition:** The second half of 2028 or later is included in the turn being covered

**Probability:** 70 percent when the condition is first met, 50 percent in the next eligible turn if it hasn't happened yet, then 30 percent

**Can repeat:** No

**Description:** A new national curriculum for compulsory school (grundskolan) is introduced. The planned timeline is 2028, but it may be delayed. The curriculum may include meaningful AI competence requirements, weak symbolic language, or almost nothing. If it includes strong AI content, it improves national coordination and school_readiness over time, but it still requires assessment redesign, guidance, and local capacity before it changes student_productive_use and student_critical_literacy at scale.

## Serious AI-Related Self-Harm Incident

**ID:** ai_selfharm_incident

**Condition:** Requires student_productive_use >= 8

**Probability:** 2 percent per round when student_productive_use is 8-20, 4 percent when 21-50, 3 percent when above 50

**Can repeat:** No

**Description:** A serious self-harm incident involving a young person is linked to an AI companion or AI-generated content. The case receives massive media attention and triggers a national debate about AI safety and children. public_sentiment_ai_education should drop sharply. Political pressure for restrictions increases. The long-term effect depends on whether institutions respond with credible safety measures or panic.

## AI-Driven Unemployment Wave

**ID:** ai_unemployment_wave

**Condition:** Requires ai_capability >= 24

**Probability:** 8 percent per round when ai_capability is 24-99, 15 percent when 100-199, 25 percent when 200 or higher

**Can repeat:** No

**Description:** Significant job losses in one or more sectors are clearly attributed to AI automation. The labor market disruption increases urgency around AI competence in education, but it can push the debate in two directions: "students must understand AI to stay employable" or "AI is dangerous and schools should be cautious." The effect on school policy depends on how the story is framed.

## Research Breakthrough: AI and Learning

**ID:** research_breakthrough_learning

**Condition:** No conditions

**Probability:** 8 percent per round

**Can repeat:** Yes

**Description:** A major research study on AI and learning is published and receives significant attention. The findings may be positive (AI-assisted learning shows strong results) or negative (AI use is associated with worse learning outcomes). Either way, the research shifts the public debate and influences school authorities, especially around assessment, teacher support, and what counts as real competence.

## EU Initiative on AI in Education

**ID:** eu_ai_education_initiative

**Condition:** No conditions

**Probability:** 12 percent per round

**Can repeat:** No

**Description:** The EU launches a significant initiative on AI in education -- funding programs, competence frameworks, or regulatory guidance. This creates external pressure and resources for Sweden to act. It can accelerate government planning and school_readiness, but it does not automatically create classroom competence.

## Launch of Powerful AI Learning Tool

**ID:** powerful_ai_learning_tool

**Condition:** No conditions

**Probability:** 5 percent per round when ai_capability is below 24, 12 percent when 24-99, 20 percent when 100 or higher

**Can repeat:** Yes

**Description:** A major AI company or edtech firm launches a powerful new AI-based learning tool specifically designed for education. The tool may be free or subsidized for schools. This creates new opportunities for learning and workload relief, but only schools with adult oversight, assessment adaptation, and decent school_readiness turn it into student_productive_use gains. In weakly organized settings it mostly increases pressure, misuse risk, or procurement confusion.

## Media Storm: AI Cheating in Schools

**ID:** media_storm_cheating

**Condition:** Requires student_productive_use >= 12

**Probability:** 8 percent per round when student_productive_use is 12-29, 12 percent when 30-49, 6 percent when 50 or higher

**Can repeat:** Yes

**Description:** A media storm erupts around AI-assisted cheating in Swedish schools. High-profile cases of students using AI to complete assignments or exams without learning receive national attention. public_sentiment_ai_education may drop temporarily. Schools face pressure to either ban AI or rethink assessment. If school_readiness is low, the storm is more damaging because schools lack credible responses.

## Positive Media Coverage

**ID:** positive_media_coverage

**Condition:** No conditions

**Probability:** 6 percent per round when public_sentiment_ai_education is below 0, 10 percent when 0-4, 15 percent when 5 or higher

**Can repeat:** Yes

**Description:** Major Swedish media publishes positive coverage of AI in education -- a successful school project, international recognition of Swedish AI pedagogy, or compelling student stories. public_sentiment_ai_education should rise modestly. The effect is stronger when the story includes credible evidence of teacher support, assessment adaptation, or equity work rather than just a flashy tool.

## AI Capability Breakthrough

**ID:** ai_breakthrough

**Condition:** No conditions

**Probability:** 4 percent per round when ai_capability is below 50, 7 percent when 50-149, 10 percent when 150 or higher

**Can repeat:** Yes

**Description:** A new architecture or training method significantly improves AI performance and efficiency. ai_capability should make a notable jump. This accelerates the pace at which existing school competence becomes outdated and increases pressure on teachers, assessments, and procurement choices.

## Data Privacy or Procurement Controversy

**ID:** privacy_procurement_controversy

**Condition:** Requires school_readiness < 25

**Probability:** 10 percent per round when school_readiness is below 15, 6 percent when 15-24, 2 percent when 25 or higher

**Can repeat:** No

**Description:** A municipality, school chain, or regulator halts an AI rollout because of student-data privacy concerns, procurement mistakes, or unclear legal responsibility. The event damages trust and slows implementation, especially where schools relied on ad hoc tool adoption. It usually hurts school_readiness and public sentiment in the short term, but may later force more serious governance.

## Teacher Workload Pushback

**ID:** teacher_workload_pushback

**Condition:** Requires teacher_competence >= 10 or school_readiness >= 10

**Probability:** 8 percent per round when school_readiness is below 20, 5 percent when 20-34, 2 percent when 35 or higher

**Can repeat:** Yes

**Description:** Teachers, school leaders, or unions push back against AI expectations that arrive without time, training, assessment support, or clarity. The backlash is not necessarily anti-AI in principle; it is often a demand for realism. It can slow competence growth and depress school_readiness in the short term, while also increasing pressure for better support structures.
