# Humanizer

Detect and remove AI-generated writing patterns to make text sound natural and human. Based on [blader/humanizer](https://github.com/blader/humanizer) and Wikipedia's "Signs of AI writing" guide.

**Triggers:** Writing blog posts, editing drafts, final review pass before publishing.

---

## Process

Run two passes on all written content:

1. **First pass:** Apply all 24 pattern checks below. Fix every violation found.
2. **Audit pass:** Re-read the output and ask "does any sentence sound obviously AI generated?" Fix anything that does.

---

## Content Patterns

### 1. Significance Inflation
**Detect:** "stands/serves as," "testament," "vital/crucial/pivotal role," "underscores importance," "reflects broader," "marking a shift," "indelible mark"
**Fix:** Replace inflated claims with direct statements. State what actually happened.

### 2. Notability Padding
**Detect:** "Independent coverage," "local/regional/national media outlets," "active social media presence," unsourced notability claims
**Fix:** Remove generic notability lists. If citing media, provide specific details.

### 3. Superficial -ing Analyses
**Detect:** "Highlighting," "emphasizing," "reflecting," "symbolizing," "contributing to," "cultivating," "showcasing," "encompassing"
**Fix:** Replace with concrete statements. "Reflecting the industry's shift" becomes "shops switched to X because Y."

### 4. Promotional Language
**Detect:** "Boasts a," "vibrant," "rich cultural heritage," "profound," "nestled," "breathtaking," "stunning," "must-visit," "renowned," "groundbreaking"
**Fix:** Use factual descriptors. Replace adjective-heavy prose with specifics.

### 5. Vague Attributions
**Detect:** "Industry reports," "observers have cited," "experts argue," "some critics," "several sources/publications"
**Fix:** Cite specific sources with dates and authors, or state claims as direct observation.

### 6. Formulaic "Challenges and Future Prospects"
**Detect:** "Despite its... faces several challenges," "Despite these challenges," formulaic "Challenges" sections, "Future Outlook"
**Fix:** Replace with specific, dated examples. No generic challenge/opportunity sections.

---

## Language Patterns

### 7. Overused AI Vocabulary
**Detect:** "Additionally," "align with," "crucial," "delve," "emphasizing," "enduring," "enhance," "fostering," "garner," "highlight," "interplay," "intricate," "key," "landscape" (abstract), "pivotal," "showcase," "tapestry," "testament," "underscore," "valuable," "vibrant"
**Fix:** Replace with everyday words. "Important" not "crucial." "Connect" not "interplay."

### 8. Copula Avoidance
**Detect:** "Serves as," "stands as," "marks," "represents," "boasts," "features," "offers" used instead of "is"
**Fix:** Simplify. "Gallery serves as exhibition space" becomes "Gallery is an exhibition space."

### 9. Negative Parallelisms
**Detect:** "Not only X but Y," "It's not just about X, it's about Y," "It's not merely X, it's Y"
**Fix:** Remove the parallel structure. State the single most important point.

### 10. Rule of Three Overuse
**Detect:** Forced groupings of three ideas, three adjectives, three claims presented as equally weighted.
**Fix:** Keep only essential points. Two items or one. Not everything needs a triad.

### 11. Synonym Cycling
**Detect:** Same entity referred to by different names in each mention (protagonist, main character, central figure, hero).
**Fix:** Use consistent terminology throughout.

### 12. False Ranges
**Detect:** "From X to Y" constructions where X and Y aren't on a meaningful scale.
**Fix:** Replace with a simple list or direct statement.

---

## Style Patterns

### 13. Em Dash Overuse
**Detect:** Multiple em dashes per paragraph; em dashes replacing commas, parentheses, or periods.
**Fix:** Replace with commas or periods. One em dash per paragraph max.

### 14. Boldface Overuse
**Detect:** Boldfaced terms scattered throughout body text.
**Fix:** Remove decorative boldface. Keep only for section headers.

### 15. Inline-Header Vertical Lists
**Detect:** Lists with bolded headers followed by colons and explanations.
**Fix:** Convert to prose or use simpler, unheadered bullet points.

### 16. Title Case in Headings
**Detect:** All main words capitalized in headings.
**Fix:** Use sentence case. "Strategic negotiations" not "Strategic Negotiations."

### 17. Emojis
**Detect:** Emoji decorations in headings or before bullet points.
**Fix:** Remove all emojis from content.

### 18. Curly Quotation Marks
**Detect:** Curved quotation marks instead of straight ones.
**Fix:** Convert all curly quotes to straight quotes.

---

## Communication Patterns

### 19. Chatbot Artifacts
**Detect:** "I hope this helps," "Of course!," "Certainly!," "You're absolutely right!," "Would you like...," "let me know," "here is a..."
**Fix:** Remove all conversational scaffolding.

### 20. Knowledge-Cutoff Disclaimers
**Detect:** "As of [date]," "Up to my last training update," "While specific details are limited," "based on available information"
**Fix:** Delete entirely, or replace with sourced information.

### 21. Sycophantic Tone
**Detect:** "Great question!," "You're absolutely right," "That's an excellent point"
**Fix:** Adopt neutral, direct tone. State facts without praise.

---

## Filler and Hedging

### 22. Filler Phrases
Replace on sight:
- "In order to achieve this goal" -> "To achieve this"
- "Due to the fact that" -> "Because"
- "At this point in time" -> "Now"
- "In the event that" -> "If"
- "Has the ability to" -> "Can"
- "It is important to note that" -> cut entirely

### 23. Excessive Hedging
**Detect:** Multiple qualifiers: "could potentially possibly," "might have some effect," "appears to suggest"
**Fix:** Pick one qualifier or none. "May affect" not "could potentially possibly affect."

### 24. Generic Positive Conclusions
**Detect:** "The future looks bright," "Exciting times lie ahead," "represents a major step," "continues to thrive"
**Fix:** Replace with concrete next steps or specific outcomes. End with facts, not cheerleading.

---

## Inject Human Voice

Beyond removing patterns, actively add:
- Opinions. React to facts, don't just report them.
- Varied rhythm. Short sentence, then a longer one that unfolds.
- Specificity over vagueness. "Unsettling" not "concerning."
- Acknowledge complexity. Not everything is clear-cut.
- Allow imperfection. Human writing isn't structurally perfect.
