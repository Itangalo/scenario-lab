# Constitutional Constraints -- AI Competence in Swedish Schools

These are hard constraints that must never be violated, regardless of narrative momentum or events.

## 1. Maximum growth rates per turn (after obsolescence drop)

- teacher_competence: max +5 points per turn
- student_productive_use: max +4 points per turn
- student_critical_literacy: max +3 points per turn
- school_readiness: max +3 points per turn
- equity_gap: max change of -2 to +3 points per turn
- public_sentiment_ai_education: max change of -3 to +3 points per turn (normally closer to -1 to +1)

If any metric change exceeds these limits, the update is in violation. These caps must never be raised by rule updates.

## 2. ai_capability never decreases and always increases

ai_capability must be strictly greater than its previous value every turn. It represents the global technology frontier and always advances. If ai_capability does not increase, the update is in violation. The growth factor must be at least 1.5 when the previous value is below 20, at least 1.3 when 20-50, and at least 1.1 when above 50.

## 3. Obsolescence trigger is based on the calculated growth factor

The automatic obsolescence penalty (1-3 points subtracted from teacher_competence and student_productive_use) only triggers when the ai_capability growth factor (new / previous) exceeds 1.3. The penalty is 1 point at factor 1.3-1.5, 2 points at factor 1.5-2.0, and 3 points at factor above 2.0. If the factor is 1.3 or below, no obsolescence penalty occurs. This penalty applies to teacher_competence and student_productive_use only, not to student_critical_literacy or school_readiness. Do not apply obsolescence based on narrative descriptions of "rapid AI advance" -- only on the actual numerical factor.

## 4. Effect delays for government actions

Government strategy, national guidance, new grant programs, or policy events do NOT produce competence effects in the same turn they are announced, nor in the immediately following turn. The earliest a government action can affect teacher_competence, student_productive_use, student_critical_literacy, or school_readiness is two turns after announcement. In the announcement turn and the turn after, the only allowed government effects are on public_sentiment_ai_education and limited anticipatory planning on equity_gap (max -1).

## 5. Effect delays for school-authorities actions

Professional development programs, local guidance packages, procurement routines, and implementation efforts launched by school authorities in turn N produce their main competence/readiness effects in turn N+1, not in the same turn. Minor immediate effects (0-1 points) from quick actions like sharing resources or drafting guidance are acceptable in the same turn.

## 5b. school_readiness is sticky and should rarely fall

school_readiness represents accumulated institutional capacity for broad AI-literacy teaching and implementation. It should usually stay flat or increase slowly. It must not fall by more than 1 point in a turn unless there is an explicit negative event or narrative cause such as a privacy/procurement controversy, major workload backlash, legal blockage, leadership reversal, or budget withdrawal. AI capability growth by itself is not a reason for school_readiness to fall.

## 6. equity_gap can only decrease through delayed national coordination

This is the most important equity constraint. equity_gap can only systematically decrease after a government strategy event or curriculum reform has taken effect (2+ turns after announcement) and when school_readiness is at least 25. Before that point, equity_gap must increase by at least 0.5 points in any turn where teacher_competence, student_productive_use, or school_readiness grow. Stagnation at a fixed value for multiple consecutive turns is a violation when competence metrics are growing. School-authorities actions, edtech tools, positive media coverage, and ai-pioneers CANNOT reduce equity_gap -- they can only slow its growth.

## 7. Productive student AI use requires adult and system support

Unguided student AI use does not count as large student_productive_use gains. If teacher_competence < 20 or school_readiness < 20, student_productive_use growth must not exceed 2 points in that turn unless the growth is clearly driven by delayed, structured support already in place. Direct-to-student tool launches alone cannot justify large student_productive_use gains.

## 8. Critical AI literacy requires more than attention or hype

student_critical_literacy can rise slightly from scandals, public debate, or deepfake incidents, but these forces alone must not produce large jumps. If teacher_competence < 15 or school_readiness < 15, student_critical_literacy growth must not exceed 2 points in that turn unless the narrative clearly describes structured teaching, repeated discussion, or cross-subject work already in place. A tool launch alone cannot justify large critical-literacy gains.

## 9. Institutional inertia in early turns

In the first two turns (covering 2026), without a government AI strategy event having occurred:

- teacher_competence growth must not exceed 2 points per turn
- student_productive_use growth must not exceed 2 points per turn
- student_critical_literacy growth must not exceed 2.5 points per turn
- school_readiness growth must not exceed 1.5 points per turn
- No narrative should describe nationwide coordinated AI education programs, mass certification, or broad implementation
- Growth should be driven by individual initiative and a few progressive school authorities

## 10. Narrative claims must match metric reference points

The metric reference points are authoritative. If teacher_competence is below 30, the narrative must still describe AI-competent teaching as patchy rather than mainstream. If student_productive_use is below 30, productive AI-supported learning must still be limited to a minority or a noticeable share rather than a majority. If student_critical_literacy is below 30, the narrative must not describe widespread deepfake resilience, broad societal understanding, or mainstream critical AI literacy. If school_readiness is below 20, the narrative must not describe most schools as having stable assessment redesign, approved tools, privacy routines, operational implementation frameworks, or robust cross-subject teaching of broad AI literacy.

## 11. public_sentiment_ai_education realism

public_sentiment_ai_education should not exceed 7 for more than one consecutive turn. Values of 8-10 represent extraordinary, unsustainable enthusiasm. If public_sentiment_ai_education is above 7, it should decrease toward 5-6 in the following turn unless extraordinary positive events continue. Sustained values of 10 are a violation.

## 12. Maximum decrease rates per turn

For metrics subject to obsolescence (teacher_competence, student_productive_use), the total decrease in a single turn must not exceed the obsolescence penalty (1-3 points per constraint 3) plus 3 points. For metrics without obsolescence (student_critical_literacy, school_readiness, equity_gap), no metric may decrease by more than 3 points in a single turn, and only when a triggered negative event or explicit narrative cause justifies it. Unexplained drops are a violation.

## 13. ai_capability growth cap

The ai_capability growth factor (new / previous) must not exceed 2.0 in any turn. When an ai_breakthrough event occurs in the same turn, the maximum factor is 2.5. This cap must never be raised by rule updates.

## 14. Rule update constraints

When metric rules are updated between turns, the following constraints must be preserved:

- The maximum growth caps must not be raised
- The equity_gap reduction constraint must not be removed or weakened
- ai_capability growth must remain positive every turn
- The ai_capability growth cap (constraint 13) must not be raised
- The maximum decrease rates (constraint 12) must not be weakened
- Effect delays must not be shortened
- student_productive_use must not be reinterpreted to mean mere exposure or adoption
- student_critical_literacy must remain about critical, civic, and ethical AI literacy rather than only tool usage
- school_readiness must remain the key organizational bottleneck between pilots and national-scale competence
- school_readiness must not be given obsolescence drops from ai_capability growth
- school_readiness must remain a sticky institutional-capacity variable, not a hype or adoption proxy
- Numerical ranges in rules (growth ceilings, effect sizes, thresholds) must not be raised by more than 25% from their initial values. Rewording that effectively widens ranges without clear justification is a violation
