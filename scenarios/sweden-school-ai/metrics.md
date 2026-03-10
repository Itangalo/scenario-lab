# Metrics for AI Competence in Swedish Schools

## student_productive_use

**Description:** Productive AI-supported learning among students in lower secondary school (hogstadiet, ages 13-16) and upper secondary school (gymnasiet, ages 16-19). This measures whether students can use AI as a real aid for studying without outsourcing thinking: asking useful questions, checking answers, iterating on drafts, using AI to understand material, and knowing when not to rely on it. Mere exposure, casual prompting, cheating, or copy-paste behavior does NOT count as high performance on this metric.

### Main drivers
- Teacher guidance, adapted tasks, and assessment formats that reward thinking rather than shortcut behavior.
- Repeated supported classroom practice, not one-off tool access.
- School routines that make productive use legitimate and misuse costly.
- Adult oversight that helps students learn verification, revision, and reflection habits.

### Usually NOT driven by
- AI hype, media buzz, or raw student experimentation on its own.
- Direct-to-student tool launches without teacher support.
- More frequent AI use when the use is mostly shortcutting or cheating.

**ID:** student_productive_use

**Min:** 0

**Max:** 100

**Unit:** index

**Starting value:** 8

**Reference points:**

- **5:** Many students have tried AI, but very few use it productively for learning. Shortcut behavior is common.
- **15:** A minority of students have learned useful habits for AI-supported studying, usually through self-teaching or a few exceptional teachers.
- **30:** A noticeable share of schools have adapted some tasks and guidance so that productive AI-supported learning exists, though it is still patchy and fragile.
- **50:** About half of students can use AI as a real study aid without relying on it blindly. Productive habits are common beyond pioneer schools.
- **70:** Productive AI-supported learning is mainstream. Most students can use AI to deepen understanding, revise work, and study more effectively.
- **90:** Productive AI use for learning is near-universal among older students and is treated as a normal school skill.

## student_critical_literacy

**Description:** Critical, civic, and reflective AI literacy among older students. This includes resilience to deepfakes and synthetic media, source criticism toward AI outputs, very basic technical intuition about how AI systems work and fail, and basic understanding of how AI affects work, media, democracy, and human relationships. It also includes reflection on social and ethical questions related to AI. This metric is broader than classroom tool use and should not be reduced to whether students are good at prompting.

### Main drivers
- Structured teaching in source criticism, civics, language, media literacy, and ethics.
- Repeated discussion of how AI can mislead, manipulate, fail, or reshape institutions.
- Teacher capacity to explain AI limits and facilitate reflection across subjects.
- School capacity to turn controversies, deepfake incidents, and public debate into learning rather than panic.

### Usually NOT driven by
- More student access to tools by itself.
- Flashy pilots that mostly improve efficiency or usage frequency.
- Public debate alone, unless schools translate it into teaching and practice.

**ID:** student_critical_literacy

**Min:** 0

**Max:** 100

**Unit:** index

**Starting value:** 10

**Reference points:**

- **5:** Students may have heard warnings about AI, but few can reliably spot synthetic media or explain why AI outputs fail.
- **15:** A minority of students show some caution around AI claims and can discuss obvious deepfake or misinformation risks.
- **30:** A noticeable share of schools teach source criticism, synthetic-media awareness, and basic social questions about AI, though this remains uneven.
- **50:** About half of students have basic resilience to obvious deepfakes and inflated AI claims and can discuss major societal and ethical implications at a simple level.
- **70:** Critical AI literacy is mainstream. Most students can question AI outputs, recognize common failure modes, and discuss broad social implications with reasonable confidence.
- **90:** Strong critical and civic AI literacy is near-universal among older students. Deepfake resilience, AI source criticism, and basic societal understanding are treated as normal school skills.

## teacher_competence

**Description:** AI competence among teachers working with older students. This measures both teachers' own AI literacy and their ability to teach the two student dimensions above: productive AI-supported learning and critical/civic AI literacy. It is not the same as having tested a chatbot a few times.

### Main drivers
- Professional development with time to test, adapt, and reflect.
- Peer learning from pioneers when it spreads into school routines.
- Assessment redesign and practical classroom support.
- Clear local guidance on acceptable uses, privacy, and procurement.

### Usually NOT driven by
- Awareness campaigns without release time or practice.
- A single exciting tool launch.
- One-off workshops without follow-through.

**ID:** teacher_competence

**Min:** 0

**Max:** 100

**Unit:** index

**Starting value:** 8

**Reference points:**

- **5:** Most teachers have little practical AI competence and lack classroom strategies for handling student AI use.
- **15:** A growing minority experiments with AI, but competence is still carried by pioneers and informal networks.
- **30:** Many schools have at least one AI-competent teacher and some structured professional development, but quality is uneven and broader AI literacy teaching is patchy.
- **50:** About half of teachers can guide productive AI use, redesign some tasks, and teach basic source criticism, deepfake awareness, and ethical reflection around AI.
- **70:** AI competence is becoming a standard professional skill. Most teachers can integrate AI into teaching and assessment with confidence and address broader civic and ethical AI literacy.
- **90:** Near-universal teacher AI competence. AI-informed teaching design and broad AI literacy teaching are routine across schools.

## school_readiness

**Description:** Institutional capacity in Swedish schools to turn interest in AI into broad student AI competence at scale. This includes school leadership, local guidance, assessment redesign, procurement and privacy routines, approved tool choices, release time for teacher learning, and the ability to spread good practice beyond pioneers. It also includes the school's ability to teach both productive AI-supported learning and critical AI literacy across subjects. This is the main bottleneck between pilots and system-wide competence. It is a slow-moving stock of institutional capacity, not a hype metric, and it should normally change gradually rather than jump with frontier model progress.

### Main drivers
- Leadership, governance, assessment redesign, and legal clarity.
- Time and support for teachers to learn together.
- Practical implementation capacity at huvudman and school level.
- Ability to carry work across subjects instead of relying on a few enthusiasts.

### Usually NOT driven by
- Frontier AI hype.
- Positive sentiment alone.
- A single successful pilot or product launch.

**ID:** school_readiness

**Min:** 0

**Max:** 100

**Unit:** index

**Starting value:** 7

**Reference points:**

- **5:** Fragmented situation. A few pilots exist, but most schools lack routines, approved tools, assessment changes, legal clarity, or a coherent way to teach broad AI literacy.
- **15:** Some municipalities and school chains have local guidance, pilot teams, and basic support structures, but implementation is still person-dependent and brittle.
- **30:** Many huvudman have workable guidance, some revised assessments, and a modest capacity to support teachers beyond pioneers, including limited work on both productive AI use and critical AI literacy.
- **50:** Structured implementation is common. Many schools have routines for tool choice, privacy, assessment adaptation, teacher support, and broad AI-literacy teaching that survive beyond a few local champions.
- **70:** Most municipalities and major school operators can update AI practice and sustain both dimensions of student AI competence without relying on a few enthusiasts.
- **90:** Mature institutional capability. AI-related change and broad AI-literacy teaching are handled as normal school improvement processes.

## equity_gap

**Description:** The gap in AI competence between the best-performing and worst-performing schools for older students. A high value means large inequality across both productive AI-supported learning and critical AI literacy: some schools teach these well while others barely address them. This reflects differences in local capacity, leadership, support, and resources rather than national averages.

### Main drivers
- Uneven huvudman capacity.
- Different access to teacher support, legal clarity, and time.
- Pilots and local champions spreading unevenly.
- Families and municipalities with stronger prior digital capital moving first.

### Usually NOT reduced by
- Positive media coverage on its own.
- Individual pioneers, local pilots, or edtech launches without broader coordination.

**ID:** equity_gap

**Min:** 0

**Max:** 50

**Unit:** index points

**Starting value:** 5

**Reference points:**

- **3:** Small gaps. Most schools are at a similar level, even if that level is still modest.
- **8:** Noticeable gaps are emerging between pioneer environments and lagging schools.
- **15:** Significant inequality. Access to good AI learning increasingly depends on which school or municipality a student attends.
- **25:** Severe inequality. Local organization and family background strongly shape AI competence outcomes.
- **35:** Extreme inequality. Sweden has effectively developed a two-tier AI education system.

## ai_capability

**Description:** How capable frontier AI systems are, measured as the longest task duration (in hours) that AI can handle successfully in half the cases. Based on the METR framework. This metric is global and exogenous to Swedish school policy, but it changes what schools need to teach and how quickly some kinds of practical know-how become outdated.

### Main drivers
- Exogenous global AI progress and breakthroughs.
- Major architecture or efficiency improvements.

### Usually NOT driven by
- Swedish school policy.
- National sentiment or classroom practice in Sweden.

**ID:** ai_capability

**Min:** 0

**Max:** 1000

**Unit:** hours

**Starting value:** 7

**Reference points:**

- **7:** AI can handle tasks of a few hours. Useful as a writing assistant, code helper, and study aid for well-defined questions.
- **24:** AI can handle day-long tasks. Capable of tutoring, creating lesson plans, and sustained research assistance.
- **100:** AI can handle multi-day tasks independently. Schools must rethink what students should practice themselves.
- **200:** AI approaches the ability to manage complex projects. The value of strong human AI competence becomes much more unevenly distributed.

## public_sentiment_ai_education

**Description:** The Swedish public's attitude toward AI in education, where negative values indicate fear and resistance and positive values indicate enthusiasm and trust. This affects political room for action, parental acceptance, and how much schools dare to experiment. It is usually more fragile than actor plans suggest.

### Main drivers
- Media coverage, scandals, research findings, and visible examples from schools.
- Whether schools appear to have assessment, privacy, and safety under control.
- Whether AI is framed as educational opportunity or social threat.

### Usually NOT strong enough on its own to drive
- Large competence gains.
- Fast school_readiness jumps.
- Major equity improvements.

**ID:** public_sentiment_ai_education

**Min:** -10

**Max:** 10

**Unit:** (dimensionless)

**Starting value:** 1

**Reference points:**

- **-8:** Strong public opposition. Parents protest AI in schools and schools face pressure to ban tools.
- **-4:** Skepticism dominates. Media coverage focuses on cheating, safety, and privacy risks.
- **0:** Divided opinion. AI literacy seems necessary to some, but many doubt that schools can handle it well.
- **3:** Cautiously positive. Most people accept that students should learn about AI, but only with safeguards.
- **7:** Broad enthusiasm. AI in education is seen as an important national capability, though still requiring guardrails.
- **10:** Near-uncritical optimism. This is extraordinary and usually unstable.
