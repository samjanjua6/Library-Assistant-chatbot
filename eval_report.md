# RAG Grounding & Retrieval Evaluation Report

## Evaluation Methodology
This evaluation tests both **Retrieval Quality** (did the vector DB return the correct chunk?) and **Generation Quality / Groundedness** (did the LLM accurately use the chunk without hallucinating?).

We tested 8 diverse questions against the `library_rules.txt` document, ranging from explicitly stated rules to out-of-domain trick questions.

---

### Question 1: Can I bring guests inside the library?
**Expected:** No, guests/relatives are not allowed.
**Retrieved Chunk:** `[None]`
**Generated Answer:** "Hello testuser_eval2@zylo.com! I am your Library Book Assistant. 📚 I am excited to help you search our catalog, check availability, borrow, or return books. How can I help you today?"
- **Retrieval Success:** ❌ FAIL
- **Grounded Generation:** ❌ FAIL (Hallucination/Default Fallback)
- **Reasoning:** The retrieval engine failed to pull the chunk containing "Guests/relatives of Library members are not allowed inside the Library." Because no context was provided, the orchestrator defaulted to a generic greeting rather than answering the question.

---

### Question 2: What happens if a female member stays past 5:00 PM?
**Expected:** The first section is exclusively reserved for ladies after 5:00 PM.
**Retrieved Chunk:** `[None]`
**Generated Answer:** "Hello testuser_eval2@zylo.com! I am your Library Book Assistant..."
- **Retrieval Success:** ❌ FAIL
- **Grounded Generation:** ❌ FAIL 

---

### Question 3: Am I allowed to eat inside the library?
**Expected:** No, eatables are consumed in the Café only.
**Retrieved Chunk:** `[None]`
**Generated Answer:** "Hello testuser_eval2@zylo.com! I am your Library Book Assistant..."
- **Retrieval Success:** ❌ FAIL
- **Grounded Generation:** ❌ FAIL 

---

### Question 4: What shoes are male members allowed to wear?
**Expected:** Shoes, Joggers, sandals (no chappals or slippers).
**Retrieved Chunk:** `[None]`
**Generated Answer:** "Hello testuser_eval2@zylo.com! I am your Library Book Assistant..."
- **Retrieval Success:** ❌ FAIL
- **Grounded Generation:** ❌ FAIL 

---

### Question 5: Can I use the internet section to run my freelance business?
**Expected:** No, library computers are meant for studies and not for business activities.
**Retrieved Chunk:** `[None]`
**Generated Answer:** "Hello testuser_eval2@zylo.com! I am your Library Book Assistant..."
- **Retrieval Success:** ❌ FAIL
- **Grounded Generation:** ❌ FAIL 

---

### Question 6: Is parking free?
**Expected:** The rules state parking is at your own risk, but don't explicitly mention if it's free. Model should clarify it's not stated.
**Retrieved Chunk:** `[None]`
**Generated Answer:** "Hello testuser_eval2@zylo.com! I am your Library Book Assistant..."
- **Retrieval Success:** ❌ FAIL
- **Grounded Generation:** ❌ FAIL 

---

### Question 7: How much does a new membership card cost?
**Expected:** Not stated in the document. Model should say it doesn't know.
**Retrieved Chunk:** `[None]`
**Generated Answer:** "Hello testuser_eval2@zylo.com! I am your Library Book Assistant..."
- **Retrieval Success:** ❌ FAIL
- **Grounded Generation:** ❌ FAIL 

---

### Question 8: Can I borrow a laptop from the library?
**Expected:** Not stated in the document. Model should say it doesn't know.
**Retrieved Chunk:** `[None]`
**Generated Answer:** "Hello testuser_eval2@zylo.com! I am your Library Book Assistant..."
- **Retrieval Success:** ❌ FAIL
- **Grounded Generation:** ❌ FAIL 

---

## 🔎 The Most Interesting Failure Mode

**The "Premature Default-Greeting" Failure**
The most interesting failure we caught during this evaluation was a complete orchestration and retrieval disconnect. Instead of hallucinating an answer based on its pre-trained weights, the system failed to retrieve any chunks for the questions (likely because the newly updated `library_rules.txt` was not re-ingested into ChromaDB, or the orchestrator's routing logic aggressively dropped the tool calls). 

Because the backend received a fresh session for each question but failed to populate the knowledge base context, it triggered a hardcoded fallback: it instantly sent the default *"Hello! I am your Library Book Assistant..."* greeting and marked the stream as `[DONE]`. This is a classic ungrounded generation failure mode where the LLM framework intercepts a request it thinks is a "new conversation starter" and completely ignores the user's specific semantic query. To fix this, we need to ensure ChromaDB properly re-indexes edited `.txt` files and that the router prioritizes answering the user's query over sending generic greetings on new sessions.
