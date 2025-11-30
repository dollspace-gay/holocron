"""Built-in reading comprehension lessons.

Lessons focused on vocabulary, comprehension strategies, and critical reading.
"""

from holocron.content.loader import Lesson, LessonCategory, LessonLoader


# =============================================================================
# Fundamentals - Lesson 1: Context Clues
# =============================================================================

LESSON_CONTEXT_CLUES = Lesson(
    lesson_id="reading.fundamentals.context_clues",
    domain_id="reading-skills",
    title="Using Context Clues",
    description="Learn to determine word meanings from surrounding text.",
    category=LessonCategory.FUNDAMENTALS,
    difficulty=1,
    estimated_minutes=15,
    tags=["vocabulary", "context", "comprehension"],
    content='''
# Using Context Clues to Understand New Words

When you encounter an unfamiliar word, the surrounding text often provides
hints about its meaning. These hints are called context clues.

## Types of Context Clues

### 1. Definition Clues

The author directly defines the word in the sentence.

> The archaeologist studied **paleography**, the analysis of ancient
> handwriting and historical documents.

The definition follows right after the word, telling us paleography
means analyzing ancient handwriting.

### 2. Synonym Clues

A word with a similar meaning appears nearby.

> The judge was **impartial**; she was completely fair and unbiased
> in her decision.

"Fair and unbiased" are synonyms that help us understand impartial.

### 3. Antonym Clues

A word with the opposite meaning provides contrast.

> Unlike his **gregarious** sister who loved parties, Tom preferred
> solitude and quiet evenings alone.

The contrast with "solitude" and "alone" tells us gregarious means
sociable or outgoing.

### 4. Example Clues

Examples illustrate the word's meaning.

> The museum displayed various **artifacts** such as ancient pottery,
> stone tools, and bronze weapons.

The examples show that artifacts are historical objects.

### 5. Inference Clues

You must use logic and prior knowledge to figure out the meaning.

> After the **arduous** hike up the steep mountain, the exhausted
> climbers collapsed at the summit.

The steep mountain and exhausted climbers suggest arduous means
difficult or requiring great effort.

## Practice Strategies

1. **Read the entire sentence** before guessing the meaning
2. **Look for signal words** like "or," "such as," "unlike," "meaning"
3. **Consider the tone** of the passage
4. **Make an educated guess**, then verify with a dictionary

## Example Exercise

Read this passage and determine the meaning of "ephemeral":

> The artist was fascinated by **ephemeral** beauty—morning dew on
> spider webs, autumn leaves falling, the brief bloom of cherry
> blossoms. She wanted to capture these fleeting moments before
> they vanished forever.

The examples (dew, falling leaves, brief bloom) and words like
"fleeting" and "vanished" tell us ephemeral means short-lived
or temporary.
''',
)

# =============================================================================
# Fundamentals - Lesson 2: Main Idea and Supporting Details
# =============================================================================

LESSON_MAIN_IDEA = Lesson(
    lesson_id="reading.fundamentals.main_idea",
    domain_id="reading-skills",
    title="Finding the Main Idea",
    description="Identify the central message and supporting details in texts.",
    category=LessonCategory.FUNDAMENTALS,
    difficulty=2,
    estimated_minutes=20,
    prerequisites=["reading.fundamentals.context_clues"],
    tags=["main idea", "supporting details", "comprehension"],
    content='''
# Finding the Main Idea and Supporting Details

Every well-written paragraph or passage has a main idea—the central
point the author wants to communicate. Supporting details provide
evidence, examples, and explanations.

## What is the Main Idea?

The main idea is:
- The most important point of the text
- What the passage is mostly about
- The message the author wants you to remember

## Where to Find the Main Idea

### Beginning of Paragraph
Most common location—the topic sentence starts the paragraph.

> **Regular exercise provides numerous health benefits.** It strengthens
> the heart and improves cardiovascular health. Exercise also helps
> maintain a healthy weight and builds muscle strength. Additionally,
> physical activity reduces stress and improves mental well-being.

Main idea: Exercise provides health benefits.

### End of Paragraph
Sometimes the author builds up to the main point.

> Studies show that students who get enough sleep perform better
> academically. They have improved memory and concentration. Sleep-
> deprived students struggle with problem-solving and creativity.
> **Adequate sleep is essential for academic success.**

Main idea: Sleep is essential for academic success.

### Implied Main Idea
Sometimes the main idea is not directly stated—you must infer it.

> The Amazon rainforest produces 20% of Earth's oxygen. It contains
> 10% of all species on the planet. Indigenous communities have lived
> there sustainably for thousands of years. Yet, an area the size of
> a football field is cleared every minute.

Implied main idea: The Amazon rainforest is valuable but threatened.

## Identifying Supporting Details

Supporting details:
- Provide evidence for the main idea
- Include facts, statistics, examples, reasons
- Answer who, what, when, where, why, how

### Types of Supporting Details

1. **Facts and Statistics**: "The brain uses 20% of the body's energy"
2. **Examples**: "For instance, dolphins use echolocation..."
3. **Reasons**: "This happens because..."
4. **Descriptions**: "The ancient temple featured ornate carvings..."
5. **Expert Opinions**: "According to Dr. Smith..."

## Practice Strategy: The MIDS Method

1. **M**ark key words and phrases
2. **I**dentify what the paragraph is mostly about
3. **D**etermine which details support this topic
4. **S**ummarize the main idea in your own words

## Example Analysis

> Climate change poses significant challenges for coastal cities.
> Rising sea levels threaten to flood low-lying areas. More intense
> storms cause billions of dollars in damage annually. Many cities
> are investing in sea walls, improved drainage, and emergency
> planning to protect their residents.

- **Main Idea**: Climate change threatens coastal cities
- **Supporting Details**:
  - Rising sea levels cause flooding
  - Storms cause damage
  - Cities are taking protective measures
''',
)

# =============================================================================
# Fundamentals - Lesson 3: Making Inferences
# =============================================================================

LESSON_INFERENCES = Lesson(
    lesson_id="reading.fundamentals.inferences",
    domain_id="reading-skills",
    title="Making Inferences",
    description="Read between the lines to understand implied meanings.",
    category=LessonCategory.FUNDAMENTALS,
    difficulty=3,
    estimated_minutes=20,
    prerequisites=["reading.fundamentals.main_idea"],
    tags=["inference", "critical thinking", "comprehension"],
    content='''
# Making Inferences While Reading

An inference is a logical conclusion based on evidence and reasoning.
Authors don't always state everything directly—readers must "read
between the lines."

## What is an Inference?

Inference = Text Evidence + Background Knowledge + Reasoning

It's an educated guess, not a wild guess. Every inference should be
supported by clues from the text.

## How to Make Inferences

### Step 1: Gather Text Evidence
What does the text actually say? Note specific details.

### Step 2: Apply Background Knowledge
What do you already know about this topic or situation?

### Step 3: Draw a Logical Conclusion
What can you reasonably conclude from the evidence?

## Example

> Maria glanced at her watch for the fifth time. She drummed her
> fingers on the table and kept looking toward the restaurant
> entrance. Her coffee had gone cold.

**Text Evidence:**
- Looking at watch repeatedly
- Drumming fingers
- Looking at entrance
- Cold coffee (been there a while)

**Background Knowledge:**
- Checking time = concern about time
- Drumming fingers = impatience or anxiety
- Looking at entrance = expecting someone

**Inference:**
Maria is waiting for someone who is late, and she's feeling
impatient or worried.

## Common Types of Inferences

### Character Inferences
What kind of person is this? What are their feelings?

> James donated half his lunch to the new student sitting alone.

Inference: James is kind and empathetic.

### Setting Inferences
Where and when does this take place?

> Sweat dripped down her face as she searched for shade. The
> pavement shimmered in waves.

Inference: It's a very hot day, probably summer.

### Cause and Effect Inferences
Why did something happen?

> The streets were empty. Every shop had closed its doors. In the
> distance, thunder rumbled.

Inference: People went inside because a storm is coming.

### Prediction Inferences
What will happen next?

> The detective smiled as she picked up the mud-caked boot. It was
> the same size as the footprint at the crime scene.

Inference: The boot will help solve the crime.

## Avoiding Wrong Inferences

A good inference is:
- **Supported by text evidence** (not just imagination)
- **Logical** (makes sense given the evidence)
- **Not too big a leap** (don't overreach)

Ask yourself: "Does the text support this conclusion?"

## Practice Exercise

Read and make inferences:

> The letter had been opened and resealed, poorly. Grandmother's
> hands trembled as she read it. She sat down heavily and stared
> out the window for a long time without speaking.

Questions to consider:
- Who might have opened the letter first?
- What kind of news might the letter contain?
- How is Grandmother feeling?
''',
)

# =============================================================================
# Intermediate - Lesson 4: Text Structure
# =============================================================================

LESSON_TEXT_STRUCTURE = Lesson(
    lesson_id="reading.intermediate.text_structure",
    domain_id="reading-skills",
    title="Understanding Text Structure",
    description="Recognize how authors organize information in different patterns.",
    category=LessonCategory.INTERMEDIATE,
    difficulty=4,
    estimated_minutes=25,
    prerequisites=["reading.fundamentals.main_idea"],
    tags=["text structure", "organization", "nonfiction"],
    content='''
# Understanding Text Structure

Authors organize information in specific patterns called text structures.
Recognizing these patterns helps you understand and remember content.

## Five Common Text Structures

### 1. Chronological/Sequence

Events or steps in time order.

**Signal Words:** first, then, next, finally, before, after, during,
meanwhile, subsequently, eventually

> First, gather all ingredients. Then, preheat the oven to 350°F.
> Next, mix the dry ingredients together. After that, add the wet
> ingredients. Finally, bake for 30 minutes.

### 2. Compare and Contrast

Shows similarities and differences between topics.

**Signal Words:** similarly, likewise, both, however, on the other
hand, unlike, whereas, in contrast, but, while

> Both solar and wind energy are renewable resources. However, solar
> panels require direct sunlight, while wind turbines can operate on
> cloudy days. Similarly, both have high initial costs, but wind
> farms typically need more land.

### 3. Cause and Effect

Explains why something happens and its results.

**Signal Words:** because, therefore, as a result, consequently, due
to, since, thus, leads to, if...then, so

> Due to deforestation, many species have lost their habitats.
> Consequently, biodiversity in these regions has declined sharply.
> As a result, scientists are calling for urgent conservation efforts.

### 4. Problem and Solution

Presents a problem and one or more solutions.

**Signal Words:** problem, issue, challenge, solution, solve, resolve,
answer, propose, suggest, implement

> Many cities face severe traffic congestion. One proposed solution
> is to expand public transportation. Another approach involves
> implementing congestion pricing during peak hours.

### 5. Description

Provides details about a topic, often using sensory language.

**Signal Words:** for example, such as, including, characteristics,
features, specifically, in particular

> The Great Barrier Reef is one of Earth's most complex ecosystems.
> It features over 400 types of coral and 1,500 species of fish.
> The reef also includes sea turtles, dolphins, and numerous
> invertebrates.

## Why Text Structure Matters

Understanding structure helps you:
- **Predict** what information comes next
- **Organize** information in your mind
- **Remember** key points more easily
- **Take better notes** using appropriate formats
- **Write more clearly** in your own work

## Graphic Organizers by Structure

| Structure | Best Organizer |
|-----------|----------------|
| Sequence | Timeline, numbered list |
| Compare/Contrast | Venn diagram, T-chart |
| Cause/Effect | Flow chart, arrows |
| Problem/Solution | T-chart, columns |
| Description | Web diagram, bullet points |

## Practice: Identify the Structure

> The Industrial Revolution transformed society in numerous ways. It
> led to urbanization as workers moved to cities for factory jobs.
> Because of new technologies, production increased dramatically.
> As a result, living standards eventually improved for many people,
> though working conditions were initially harsh.

This passage uses **cause and effect** structure.
- Cause: Industrial Revolution
- Effects: urbanization, increased production, changed living standards
''',
)

# =============================================================================
# Intermediate - Lesson 5: Author's Purpose and Point of View
# =============================================================================

LESSON_AUTHORS_PURPOSE = Lesson(
    lesson_id="reading.intermediate.authors_purpose",
    domain_id="reading-skills",
    title="Author's Purpose and Point of View",
    description="Understand why authors write and the perspectives they bring.",
    category=LessonCategory.INTERMEDIATE,
    difficulty=4,
    estimated_minutes=20,
    prerequisites=["reading.fundamentals.inferences"],
    tags=["author's purpose", "point of view", "critical reading"],
    content='''
# Author's Purpose and Point of View

Critical readers consider not just what an author says, but why
they're saying it and what perspective they bring.

## Author's Purpose: PIE

Most writing has one of three main purposes:

### P - Persuade
Convince readers to think or act a certain way.

> We must act now to protect our oceans. Every day, millions of
> pounds of plastic enter our waterways. Join the movement—refuse
> single-use plastics and demand corporate responsibility.

Signs: Strong opinions, calls to action, emotional language

### I - Inform
Share facts and information objectively.

> The Pacific Ocean covers approximately 63 million square miles,
> making it larger than all landmasses combined. It reaches depths
> of over 36,000 feet in the Mariana Trench.

Signs: Facts, statistics, neutral tone, definitions

### E - Entertain
Engage, amuse, or provide enjoyment.

> The octopus squeezed through the impossibly small gap, leaving
> the marine biologist speechless. "Well," she muttered, "there
> goes my lunch."

Signs: Narrative, humor, vivid descriptions, suspense

## Secondary Purposes

Authors may also write to:
- **Express** feelings and experiences
- **Describe** people, places, or events
- **Explain** how something works
- **Reflect** on personal experiences

## Point of View

### First Person
The narrator is a character using "I" and "we."

> I never expected to find the letter. We had searched the attic
> dozens of times.

### Second Person
Addresses the reader directly using "you."

> You open the door slowly. You can hear footsteps behind you.

### Third Person Limited
Follows one character's thoughts and experiences.

> Sarah knew she was in trouble. The footsteps were getting closer.

### Third Person Omniscient
Knows all characters' thoughts and feelings.

> Sarah feared the footsteps, not knowing that behind the door,
> her brother was planning a surprise party.

## Detecting Bias

Authors bring perspectives shaped by their:
- Background and experiences
- Cultural context
- Professional interests
- Personal beliefs

**Questions to Ask:**
- Who wrote this and why?
- What is included or omitted?
- What words reveal the author's attitude?
- Are multiple perspectives represented?

## Loaded Language

Watch for words that carry emotional weight:

| Neutral | Positive | Negative |
|---------|----------|----------|
| thin | slender | scrawny |
| group | community | mob |
| said | announced | claimed |
| change | progress | disruption |

## Practice Analysis

> Freedom-loving citizens must resist this outrageous government
> overreach. Bureaucrats want to control every aspect of our lives.
> Stand up for your rights!

- **Purpose**: Persuade
- **Point of View**: First person plural ("our")
- **Bias Indicators**: "freedom-loving," "outrageous," "overreach,"
  "bureaucrats," emotional appeals
- **What's Missing**: Specific facts, opposing viewpoints
''',
)

# =============================================================================
# Register all lessons
# =============================================================================

def register_reading_lessons():
    """Register all reading skills lessons."""
    lessons = [
        LESSON_CONTEXT_CLUES,
        LESSON_MAIN_IDEA,
        LESSON_INFERENCES,
        LESSON_TEXT_STRUCTURE,
        LESSON_AUTHORS_PURPOSE,
    ]
    for lesson in lessons:
        LessonLoader.register_builtin(lesson)


# Auto-register when module is imported
register_reading_lessons()
