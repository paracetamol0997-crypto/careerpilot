"""Role-calibrated mock interview questions."""

from __future__ import annotations

from typing import Dict, List


INTERVIEW_QUESTIONS: List[Dict] = [
    {
        "id": "q-intro-01",
        "role": "all",
        "category": "Introduction",
        "question": "Tell me about yourself — your educational background, key projects, and why you are excited about this role?",
        "expectedKeywords": ["Education", "Branch", "Projects", "Skills", "Motivation", "Career goal"],
        "sampleIdealAnswer": "I'm a final-year CSE student passionate about web engineering. Recently, I built an e-commerce platform with React and Node.js that handled user authentication and cart persistence. I love building responsive apps and want to solve real-world product challenges here.",
    },
    {
        "id": "q-intro-02",
        "role": "all",
        "category": "Introduction",
        "question": "Which was your favorite project in college and what was your specific individual contribution?",
        "expectedKeywords": ["Project title", "Tech stack", "Role", "Architecture", "Learning", "Outcome"],
        "sampleIdealAnswer": "My standout project was a collaborative task management app. I owned the backend REST API development in Node.js and database schema in MongoDB, ensuring snappy sub-100ms API response times.",
    },
    {
        "id": "q-web-01",
        "role": "software-developer",
        "category": "Technical",
        "question": "What is the key difference between var, let, and const in JavaScript, and how does hoisting affect them?",
        "expectedKeywords": ["Scope", "Block scope", "Function scope", "Temporal Dead Zone", "Reassignment"],
        "sampleIdealAnswer": "'var' is function-scoped and hoisted initialized with undefined. 'let' and 'const' are block-scoped and hoisted into the Temporal Dead Zone (TDZ), meaning accessing them before declaration throws a ReferenceError. 'const' additionally prevents reassigning the variable binding.",
    },
    {
        "id": "q-web-02",
        "role": "software-developer",
        "category": "Technical",
        "question": "What is the Virtual DOM in React, and how does the reconciliation diffing algorithm work?",
        "expectedKeywords": ["In-memory representation", "Diffing algorithm", "Re-render", "Batching", "Fiber"],
        "sampleIdealAnswer": "The Virtual DOM is an in-memory lightweight representation of the real DOM. When state changes, React creates a new VDOM tree, diffs it with the previous tree (Reconciliation), and batch-updates only the changed nodes in the real DOM for high rendering performance.",
    },
    {
        "id": "q-web-03",
        "role": "software-developer",
        "category": "Technical",
        "question": "What is the difference between GET and POST in REST APIs, and what does idempotency mean?",
        "expectedKeywords": ["Idempotent", "Safe", "Request body", "Caching", "Side effects"],
        "sampleIdealAnswer": "GET retrieves resources, is safe and idempotent (calling it multiple times produces the same server state). POST creates resources, sends data in the request body, and is non-idempotent because repeating it creates multiple new records.",
    },
    {
        "id": "q-web-04",
        "role": "software-developer",
        "category": "Technical",
        "question": "Which frontend optimization techniques would you use to improve web page load speed?",
        "expectedKeywords": ["Lazy loading", "Code splitting", "Image optimization", "Bundling", "CDN", "Caching"],
        "sampleIdealAnswer": "I would implement route-based code splitting, lazy-load heavy offscreen images and components, compress assets (WebP/Brotli), leverage browser caching headers, and minimize bundle size with tree-shaking.",
    },
    {
        "id": "q-data-01",
        "role": "data-analyst",
        "category": "Technical",
        "question": "What is the difference between the WHERE clause and HAVING clause in SQL?",
        "expectedKeywords": ["Aggregation", "GROUP BY", "Row filter", "Aggregate filter", "Order of execution"],
        "sampleIdealAnswer": "WHERE filters rows before any grouping or aggregation takes place. HAVING filters groups after the GROUP BY clause and aggregate functions (like SUM, COUNT, AVG) have been evaluated.",
    },
    {
        "id": "q-data-02",
        "role": "data-analyst",
        "category": "Technical",
        "question": "How do you handle missing values and outliers in a real-world messy dataset?",
        "expectedKeywords": ["Imputation", "Mean/Median", "IQR method", "Z-score", "Domain context", "Drop nulls"],
        "sampleIdealAnswer": "First, I inspect the percentage of nulls and check if missingness is completely random. For numerical data with outliers, I impute using median; for categorical, mode or an 'Unknown' bucket. For outliers, I use IQR boxplots and check business logic before capping or removing.",
    },
    {
        "id": "q-data-03",
        "role": "data-analyst",
        "category": "Technical",
        "question": "What top 3 design principles do you follow when creating an executive dashboard in Power BI or Tableau?",
        "expectedKeywords": ["KPI hierarchy", "Clutter-free", "Actionable insights", "Consistent palette", "Drill-down"],
        "sampleIdealAnswer": "1. Prioritize high-level headline KPIs at the top left. 2. Keep visuals clean and decluttered with consistent color coding. 3. Enable interactive drill-downs so leaders can easily jump from macro view to root-cause details.",
    },
    {
        "id": "q-py-01",
        "role": "python-developer",
        "category": "Technical",
        "question": "What is the difference between a list and a tuple in Python, and which is more memory efficient?",
        "expectedKeywords": ["Mutable", "Immutable", "Memory allocation", "Over-allocation", "Hashable"],
        "sampleIdealAnswer": "Lists are mutable and involve memory over-allocation for dynamic resizing. Tuples are immutable, have fixed memory footprint, allocate slightly faster, and can be used as dictionary keys because they are hashable.",
    },
    {
        "id": "q-py-02",
        "role": "python-developer",
        "category": "Technical",
        "question": "What are decorators in Python and what is a practical real-world use case for them?",
        "expectedKeywords": ["Higher-order function", "Wrapper", "Function modification", "Logging", "Authentication"],
        "sampleIdealAnswer": "A decorator is a function that takes another function as an argument, extends its behavior without modifying source code, and returns the wrapped function. Common uses include route authentication checks and execution time logging.",
    },
    {
        "id": "q-py-03",
        "role": "python-developer",
        "category": "Technical",
        "question": "When would you choose Flask or FastAPI over Django, and vice-versa?",
        "expectedKeywords": ["Lightweight", "Asynchronous", "Admin panel", "ORM", "Batteries-included", "Microservice"],
        "sampleIdealAnswer": "I choose Flask or FastAPI for lightweight APIs and microservices where I want full control over components. I choose Django when I need a monolithic 'batteries-included' system with built-in ORM, admin panel, and auth.",
    },
    {
        "id": "q-qa-01",
        "role": "qa-test-engineer",
        "category": "Technical",
        "question": "What critical fields must a defect/bug report have so developers can immediately reproduce it?",
        "expectedKeywords": ["Steps to reproduce", "Expected vs Actual", "Environment", "Severity/Priority", "Screenshots/Logs"],
        "sampleIdealAnswer": "A high-quality bug report needs: concise Title, Environment (browser/OS/build version), exact Steps to Reproduce, Expected Result, Actual Result, Severity & Priority, and attached Console Logs or video evidence.",
    },
    {
        "id": "q-qa-02",
        "role": "qa-test-engineer",
        "category": "Technical",
        "question": "What is the difference between Implicit Wait and Explicit Wait in Selenium WebDriver?",
        "expectedKeywords": ["Global wait", "Condition-based", "ExpectedConditions", "Polling", "NoSuchElementException"],
        "sampleIdealAnswer": "Implicit Wait applies globally across all element lookups throughout the driver session. Explicit Wait is applied on a specific element until an ExpectedCondition (like elementToBeClickable or visibilityOfElement) is met.",
    },
    {
        "id": "q-java-01",
        "role": "java-developer",
        "category": "Technical",
        "question": "How does HashMap work internally in Java, including hashing, buckets, and collision resolution?",
        "expectedKeywords": ["hashCode()", "equals()", "Buckets", "LinkedList", "Red-Black Tree", "Load factor"],
        "sampleIdealAnswer": "HashMap calculates the hash of the key and maps it to a bucket index. If multiple keys collide, Java uses a linked list, and in Java 8+, once a bucket exceeds 8 nodes, it transforms into a balanced Red-Black Tree for O(log n) lookup speed.",
    },
    {
        "id": "q-java-02",
        "role": "java-developer",
        "category": "Technical",
        "question": "What are the advantages of Dependency Injection and Inversion of Control in Spring Boot?",
        "expectedKeywords": ["Decoupling", "Spring Container", "@Autowired", "Unit testing", "Mocking", "Loose coupling"],
        "sampleIdealAnswer": "IoC transfers object creation responsibility to the Spring ApplicationContext container. Dependency Injection supplies dependencies from the outside, making code loosely coupled and easy to unit test using mocks.",
    },
    {
        "id": "q-core-01",
        "role": "core-mechanical",
        "category": "Technical",
        "question": "What is the physical meaning of Yield Strength and Ultimate Tensile Strength on a Stress-Strain curve?",
        "expectedKeywords": ["Elastic limit", "Plastic deformation", "Permanent set", "Maximum load", "Necking"],
        "sampleIdealAnswer": "Yield strength is the stress point beyond which the material undergoes permanent plastic deformation. UTS is the maximum nominal engineering stress the material can endure before necking and fracture.",
    },
    {
        "id": "q-core-02",
        "role": "core-civil",
        "category": "Technical",
        "question": "Why is a concrete slump test performed and how does it determine workability on a construction site?",
        "expectedKeywords": ["Workability", "Water-cement ratio", "Slump cone", "True slump", "Shear/Collapse"],
        "sampleIdealAnswer": "The slump test checks the batch workability and consistency of fresh concrete before pouring. A standard cone is filled in layers, tamped, and lifted; the drop in height measures whether the water-cement ratio is optimal.",
    },
    {
        "id": "q-core-03",
        "role": "core-electrical",
        "category": "Technical",
        "question": "How are eddy current losses and hysteresis losses minimized in an electrical transformer core?",
        "expectedKeywords": ["Laminations", "Silicon steel", "Magnetic hysteresis loop", "Insulating varnish"],
        "sampleIdealAnswer": "Eddy current losses are minimized by constructing the core from thin insulated laminations rather than a solid block. Hysteresis loss is reduced by using high-grade silicon steel with a narrow B-H hysteresis loop.",
    },
    {
        "id": "q-sales-01",
        "role": "sales-bda",
        "category": "Technical",
        "question": "How do you handle the common objection: 'Your product is great, but it's way over our budget'?",
        "expectedKeywords": ["Value proposition", "ROI", "Clarifying question", "Payment flexibility", "Cost of inaction"],
        "sampleIdealAnswer": "I don't immediately discount. First, I validate their concern, ask which specific features are critical, and pivot to ROI. If needed, I offer modular plans or a staged rollout.",
    },
    {
        "id": "q-mkt-01",
        "role": "digital-marketing",
        "category": "Technical",
        "question": "What steps would you take to improve Google Ads Quality Score to lower your Cost-Per-Click?",
        "expectedKeywords": ["Ad relevance", "Landing page experience", "Expected CTR", "Negative keywords", "Search intent"],
        "sampleIdealAnswer": "Quality Score depends on Expected CTR, Ad Relevance, and Landing Page Experience. I align ad copy tightly with exact keywords, optimize landing page speed and headline match, and add negative keywords.",
    },
    {
        "id": "q-proj-01",
        "role": "all",
        "category": "Project",
        "question": "Tell me about a difficult technical roadblock or bug you encountered during a project and how you resolved it.",
        "expectedKeywords": ["Situation", "Task", "Action", "Result", "STAR method", "Debugging", "Root cause"],
        "sampleIdealAnswer": "During a project demo, our database queries slowed under concurrent requests. I analyzed the query execution plan, spotted missing indexes on foreign keys, added composite indexes, and reduced latency by 85%.",
    },
    {
        "id": "q-hr-01",
        "role": "all",
        "category": "HR/Behavioral",
        "question": "How do you navigate disagreements or deadline conflicts with teammates in a collaborative project?",
        "expectedKeywords": ["Empathy", "Objective data", "Clear communication", "Compromise", "Focus on common goal"],
        "sampleIdealAnswer": "I focus on the goal rather than personal egos. I schedule a quick 1-on-1 call, listen to their perspective first, review objective constraints, and propose a data-backed compromise that protects the delivery timeline.",
    },
]


def get_interview_questions_for_role(role_id: str) -> List[Dict]:
    """Select 1 intro, 2-3 role-specific technical, 1 project, and 1 HR question."""
    intro = next((q for q in INTERVIEW_QUESTIONS if q["category"] == "Introduction"), None)
    tech = [q for q in INTERVIEW_QUESTIONS if q["role"] == role_id and q["category"] == "Technical"]
    fallback_tech = [q for q in INTERVIEW_QUESTIONS if q["category"] == "Technical"][:2]
    selected_tech = tech[:3] if len(tech) >= 2 else (tech + fallback_tech)[:3]
    project = next((q for q in INTERVIEW_QUESTIONS if q["category"] == "Project"), None)
    hr = next((q for q in INTERVIEW_QUESTIONS if q["category"] == "HR/Behavioral"), None)

    result = [intro, *selected_tech, project, hr]
    return [q for q in result if q is not None]
