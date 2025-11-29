"""
LLM Service for Bilingual Lesson Plan Transformation
Integrates OpenAI/Anthropic APIs with prompt_v4.md framework
"""

import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import anthropic
from dotenv import load_dotenv
from openai import OpenAI

from backend.performance_tracker import get_tracker
from backend.telemetry import logger
from tools.json_repair import repair_json

# Load environment variables
load_dotenv()


class LLMService:
    """Service for transforming primary teacher content to bilingual lesson plans"""

    def __init__(self, provider: str = "openai", api_key: Optional[str] = None):
        """
        Initialize LLM service

        Args:
            provider: "openai" or "anthropic"
            api_key: API key (if None, reads from environment)
        """
        self.provider = provider
        self.api_key = api_key or self._get_api_key()

        if not self.api_key:
            raise ValueError(f"No API key found for {provider}")

        # Initialize client
        if provider == "openai":
            # Support custom base URL for specialized models
            base_url = os.getenv("OPENAI_BASE_URL")
            if base_url:
                self.client = OpenAI(
                    api_key=self.api_key, base_url=base_url, timeout=300.0
                )
            else:
                self.client = OpenAI(
                    api_key=self.api_key, timeout=300.0
                )  # 5 minute timeout for large responses
            self.model = os.getenv("LLM_MODEL") or "gpt-4-turbo-preview"
        elif provider == "anthropic":
            self.client = anthropic.Anthropic(api_key=self.api_key)
            self.model = os.getenv("LLM_MODEL") or "claude-3-opus-20240229"
        else:
            raise ValueError(f"Unsupported provider: {provider}")

        # Load prompt template
        self.prompt_template = self._load_prompt_template()

        # Load schema
        self.schema = self._load_schema()
        self.openai_structured_schema = (
            self._build_openai_structured_schema() if provider == "openai" else None
        )

        # Determine max completion tokens based on model and config
        self.max_completion_tokens = self._determine_max_completion_tokens()

        logger.info(
            "llm_service_initialized",
            extra={
                "provider": provider,
                "model": self.model,
                "max_completion_tokens": self.max_completion_tokens,
            },
        )

    def _get_api_key(self) -> Optional[str]:
        """Get API key from environment or file"""
        # Try environment first
        if self.provider == "openai":
            # Check for GPT-5 specific API key first
            model = os.getenv("LLM_MODEL", "")
            if "gpt-5" in model.lower():
                key = (
                    os.getenv("GPT5_API_KEY")
                    or os.getenv("OPENAI_API_KEY")
                    or os.getenv("LLM_API_KEY")
                )
            else:
                key = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
        elif self.provider == "anthropic":
            key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("LLM_API_KEY")
        else:
            return None

        # If not in environment, try file
        if not key:
            try:
                with open("api_key.txt", "r") as f:
                    key = f.read().strip()
            except (FileNotFoundError, IOError):
                pass

        return key

    def _determine_max_completion_tokens(self) -> int:
        """
        Determine max completion tokens based on model limits and configuration.

        Priority:
        1. LLM_MAX_COMPLETION_TOKENS environment variable
        2. Model-specific limit (if known)
        3. Default safe value (4000)

        Returns:
            Maximum completion tokens to request
        """
        # Check for explicit override
        env_value = os.getenv("LLM_MAX_COMPLETION_TOKENS")
        if env_value:
            try:
                override = int(env_value)
                logger.info("using_env_max_tokens", extra={"value": override})
                return override
            except ValueError:
                logger.warning(
                    "invalid_max_completion_tokens_env", extra={"value": env_value}
                )

        # Get model-specific limit
        model_limit = self._model_token_limit()

        # Default base limit - use model limit if available, otherwise 4000
        # For full 5-day lesson plans, we need at least the model's max
        if model_limit:
            return model_limit

        return 4000

    def _model_token_limit(self) -> Optional[int]:
        """
        Get the maximum completion token limit for the current model.

        Returns:
            Token limit if known, None otherwise
        """
        # Known model limits (completion tokens only)
        limits = {
            "gpt-4-turbo-preview": 4096,
            "gpt-4-turbo": 4096,
            "gpt-4o": 16384,  # GPT-4o has higher limit
            "gpt-4o-mini": 16384,
            "gpt-4": 4096,
            "gpt-3.5-turbo": 4096,
            "gpt-5": 16384,  # GPT-5 flagship has larger output capacity
            "gpt-5-mini": 32768,  # GPT-5-mini - increased for full 5-day lesson plans
            "gpt-5-nano": 8192,  # GPT-5-nano (smaller/faster)
            "o1-preview": 32768,  # O1 models have very high limits
            "o1-mini": 65536,
            "claude-3-opus": 4096,
            "claude-3-sonnet": 4096,
            "claude-3-haiku": 4096,
        }

        model_name = (self.model or "").lower()

        # Check for exact or partial match
        for key, limit in limits.items():
            if key in model_name:
                logger.info(
                    "model_token_limit_found",
                    extra={"model": self.model, "limit": limit},
                )
                return limit

        logger.warning("model_token_limit_unknown", extra={"model": self.model})
        return None

    def _load_prompt_template(self) -> str:
        """Load prompt_v4.md framework"""
        prompt_path = Path("prompt_v4.md")
        if not prompt_path.exists():
            raise FileNotFoundError("prompt_v4.md not found")

        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    def _load_schema(self) -> Dict[str, Any]:
        """Load JSON output schema"""
        schema_path = Path("schemas/lesson_output_schema.json")
        if not schema_path.exists():
            raise FileNotFoundError("lesson_output_schema.json not found")

        with open(schema_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _build_openai_structured_schema(self) -> Dict[str, Any]:
        """Prepare schema for OpenAI structured outputs."""
        if not self.schema:
            return {"type": "object", "additionalProperties": False}

        schema_copy = deepcopy(self.schema)
        for key in ("$schema", "$id", "title", "description", "version"):
            schema_copy.pop(key, None)

        if not schema_copy.get("type"):
            schema_copy["type"] = "object"

        # OpenAI structured outputs requires additionalProperties to be explicitly set to false
        # Add it recursively to all object types
        schema_copy = self._add_additional_properties_false(schema_copy)

        return schema_copy

    def _add_additional_properties_false(
        self, schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Recursively add additionalProperties: false to all object schemas."""
        if not isinstance(schema, dict):
            return schema

        result = deepcopy(schema)

        # If it's an object type, ensure additionalProperties is False
        if result.get("type") == "object":
            if "additionalProperties" not in result:
                result["additionalProperties"] = False

        # Process properties
        if "properties" in result:
            for key, value in result["properties"].items():
                result["properties"][key] = self._add_additional_properties_false(value)

        # Process definitions (for $ref references)
        if "definitions" in result:
            for key, value in result["definitions"].items():
                result["definitions"][key] = self._add_additional_properties_false(
                    value
                )

        # Process items (for arrays)
        if "items" in result:
            if isinstance(result["items"], dict):
                result["items"] = self._add_additional_properties_false(result["items"])
            elif isinstance(result["items"], list):
                result["items"] = [
                    self._add_additional_properties_false(item)
                    if isinstance(item, dict)
                    else item
                    for item in result["items"]
                ]

        return result

    def _structured_response_format(self) -> Optional[Dict[str, Any]]:
        """Return the response_format payload for OpenAI structured outputs."""
        if not self.openai_structured_schema:
            return None

        return {
            "type": "json_schema",
            "json_schema": {
                "name": "bilingual_lesson_plan",
                "schema": deepcopy(self.openai_structured_schema),
                "strict": True,
            },
        }

    def _model_supports_structured_outputs(self) -> bool:
        """Check if the configured model supports structured outputs."""
        model_name = (self.model or "").lower()
        supported_tokens = (
            "gpt-5-mini",
            "gpt-5",
            "gpt-4o-mini",
            "gpt-4o",
            "gpt-4.1",
            "gpt-4-turbo",
            "gpt-4-turbo-preview",
            "o1",
        )
        return any(token in model_name for token in supported_tokens)

    def _model_supports_json_mode(self) -> bool:
        """Check if the configured model supports OpenAI JSON mode."""
        model_name = (self.model or "").lower()
        supported_tokens = (
            "gpt-5-mini",
            "gpt-5",
            "gpt-4o",
            "gpt-4-turbo",
            "gpt-4-turbo-preview",
            "gpt-4",
            "gpt-3.5-turbo",
            "o1",
        )
        return any(token in model_name for token in supported_tokens)

    def _analyze_domains_from_activities(
        self,
        ell_support: Optional[List[Dict[str, Any]]] = None,
        phase_plan: Optional[List[Dict[str, Any]]] = None,
        content_objective: Optional[str] = None,
    ) -> Dict[str, bool]:
        """
        Analyze lesson activities to determine which language domains are used.

        Args:
            ell_support: List of ELL support strategies
            phase_plan: List of phase plan activities
            content_objective: Content objective text

        Returns:
            Dict with keys: listening, reading, speaking, writing (all bool)
        """
        domains = {
            "listening": False,
            "reading": False,
            "speaking": False,
            "writing": False,
        }

        # Strategy-based domain mapping
        strategy_domain_map = {
            "think_pair_share": {"listening", "speaking"},
            "collaborative_learning": {"listening", "speaking"},
            "sentence_frames": {"speaking", "writing"},
            "graphic_organizers": {"reading", "writing"},
            "cognate_awareness": {"reading", "writing"},
            "oral_rehearsal": {"speaking", "listening"},
            "peer_tutoring": {"listening", "speaking"},
            "literature_circles": {"reading", "speaking", "listening"},
            "jigsaw": {"reading", "speaking", "listening"},
            "read_aloud": {"listening", "reading"},
            "shared_reading": {"reading", "speaking"},
            "interactive_writing": {"writing", "speaking"},
            "guided_writing": {"writing", "reading"},
        }

        # Analyze ELL support strategies
        if ell_support:
            for strategy in ell_support:
                strategy_id = strategy.get("strategy_id", "").lower()
                if strategy_id in strategy_domain_map:
                    for domain in strategy_domain_map[strategy_id]:
                        domains[domain] = True

        # Analyze phase plan activities (keyword-based)
        if phase_plan:
            activity_text = " ".join(
                [
                    phase.get("phase_name", "")
                    + " "
                    + phase.get("bilingual_teacher_role", "")
                    + " "
                    + phase.get("primary_teacher_role", "")
                    + " "
                    + phase.get("details", "")
                    for phase in phase_plan
                ]
            ).lower()

            # Keyword detection
            if any(
                word in activity_text
                for word in ["listen", "hear", "audio", "explanation", "instruction"]
            ):
                domains["listening"] = True
            if any(
                word in activity_text
                for word in ["read", "text", "passage", "article", "book", "document"]
            ):
                domains["reading"] = True
            if any(
                word in activity_text
                for word in ["speak", "discuss", "share", "present", "talk", "say", "tell"]
            ):
                domains["speaking"] = True
            if any(
                word in activity_text
                for word in ["write", "compose", "draft", "paragraph", "essay", "response"]
            ):
                domains["writing"] = True

        # Analyze content objective for domain hints
        if content_objective:
            obj_lower = content_objective.lower()
            if any(word in obj_lower for word in ["read", "comprehend", "analyze text"]):
                domains["reading"] = True
            if any(word in obj_lower for word in ["write", "compose", "draft", "create text"]):
                domains["writing"] = True
            if any(word in obj_lower for word in ["speak", "present", "discuss", "explain orally"]):
                domains["speaking"] = True
            if any(word in obj_lower for word in ["listen", "follow instructions"]):
                domains["listening"] = True

        return domains

    def _call_openai_chat_completion(
        self,
        prompt: str,
        *,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, Dict[str, int]]:
        """Call OpenAI chat completions with optional response_format."""
        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_completion_tokens": self.max_completion_tokens,
        }
        if response_format:
            kwargs["response_format"] = response_format

        response = self.client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content
        finish_reason = response.choices[0].finish_reason

        usage = {
            "tokens_input": response.usage.prompt_tokens if response.usage else 0,
            "tokens_output": response.usage.completion_tokens if response.usage else 0,
            "tokens_total": response.usage.total_tokens if response.usage else 0,
        }

        # CRITICAL: Check for truncation (finish_reason == "length")
        if finish_reason == "length":
            logger.error(
                "llm_response_truncated",
                extra={
                    "model": self.model,
                    "tokens_output": usage.get("tokens_output", 0),
                    "max_completion_tokens": self.max_completion_tokens,
                    "response_preview": content[:500] if content else None,
                },
            )
            raise ValueError(
                f"LLM response was truncated (finish_reason=length). "
                f"Output tokens: {usage.get('tokens_output', 0)}/{self.max_completion_tokens}. "
                f"Consider increasing max_completion_tokens or reducing prompt size."
            )

        if not content:
            logger.error(
                "openai_empty_response",
                extra={
                    "finish_reason": finish_reason,
                    "model": self.model,
                },
            )
            raise ValueError(
                f"OpenAI returned empty response. Finish reason: {finish_reason}"
            )

        return content, usage

    def transform_lesson(
        self,
        primary_content: str,
        grade: str,
        subject: str,
        week_of: str,
        teacher_name: Optional[str] = None,
        homeroom: Optional[str] = None,
        plan_id: Optional[str] = None,
        available_days: Optional[list[str]] = None,
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Transform primary teacher content to bilingual lesson plan

        Args:
            primary_content: Primary teacher's lesson content
            grade: Grade level (e.g., "6", "7")
            subject: Subject area
            week_of: Week date range (MM/DD-MM/DD)
            teacher_name: Bilingual teacher name (optional)
            homeroom: Homeroom/class identifier (optional)
            plan_id: Plan ID for performance tracking (optional)
            available_days: List of days that have content (e.g., ["monday"]). If None, generates all 5 days.

        Returns:
            Tuple of (success, lesson_json, error_message)
        """
        logger.info(
            "llm_transform_started",
            extra={
                "grade": grade,
                "subject": subject,
                "week_of": week_of,
                "available_days": available_days,
            },
        )

        tracker = get_tracker()

        try:
            # Track prompt building
            if plan_id:
                with tracker.track_operation(plan_id, "llm_build_prompt"):
                    full_prompt = self._build_prompt(
                        primary_content,
                        grade,
                        subject,
                        week_of,
                        teacher_name,
                        homeroom,
                        available_days,
                    )
            else:
                full_prompt = self._build_prompt(
                    primary_content,
                    grade,
                    subject,
                    week_of,
                    teacher_name,
                    homeroom,
                    available_days,
                )

            # Track LLM API call
            if plan_id:
                with tracker.track_operation(plan_id, "llm_api_call") as op:
                    response_text, usage = self._call_llm(full_prompt)
                    # Store usage info for tracking
                    op["tokens_input"] = usage.get("tokens_input", 0)
                    op["tokens_output"] = usage.get("tokens_output", 0)
                    op["llm_model"] = self.model
                    op["llm_provider"] = self.provider
            else:
                response_text, usage = self._call_llm(full_prompt)

            # CRITICAL: If response was truncated, attempt retry with increased tokens
            if usage.get("tokens_output", 0) >= (self.max_completion_tokens * 0.95):
                logger.warning(
                    "llm_response_near_limit",
                    extra={
                        "tokens_output": usage.get("tokens_output", 0),
                        "max_completion_tokens": self.max_completion_tokens,
                        "model": self.model,
                    },
                )
                # Could implement retry logic here if needed

            # Track JSON parsing
            if plan_id:
                with tracker.track_operation(plan_id, "llm_parse_response"):
                    lesson_json = self._parse_response(response_text)
            else:
                lesson_json = self._parse_response(response_text)

            # Track validation
            if plan_id:
                with tracker.track_operation(plan_id, "llm_validate_structure"):
                    is_valid = self._validate_structure(lesson_json)
            else:
                is_valid = self._validate_structure(lesson_json)

            if not is_valid:
                return (
                    False,
                    None,
                    "Generated JSON does not match required schema structure",
                )

            # Add usage information to result
            lesson_json["_usage"] = usage
            lesson_json["_model"] = self.model
            lesson_json["_provider"] = self.provider

            logger.info(
                "llm_transform_success",
                extra={
                    "response_length": len(response_text),
                    "tokens_total": usage.get("tokens_total", 0),
                },
            )

            return True, lesson_json, None

        except Exception as e:
            error_msg = f"LLM transformation failed: {str(e)}"
            logger.error("llm_transform_error", extra={"error": str(e)})
            return False, None, error_msg

    def _build_prompt(
        self,
        primary_content: str,
        grade: str,
        subject: str,
        week_of: str,
        teacher_name: Optional[str],
        homeroom: Optional[str],
        available_days: Optional[list[str]] = None,
    ) -> str:
        """Build complete prompt for LLM"""

        # Configure grade level in template
        grade_level = f"{grade}th grade" if grade.isdigit() else grade
        prompt = self.prompt_template.replace(
            "[GRADE_LEVEL_VARIABLE = <SET BEFORE RUN>]",
            f"[GRADE_LEVEL_VARIABLE = {grade_level}]",
        )

        # Build metadata context
        # Include all metadata to ensure LLM has full context
        metadata_context = f"""
Week: {week_of}
Grade: {grade}
Subject: {subject}
Teacher Name: {teacher_name or "Not specified"}
Homeroom: {homeroom or "Not specified"}
"""

        # Check if structured outputs will be used (to optimize prompt)
        using_structured_outputs = (
            self.provider == "openai"
            and self._model_supports_structured_outputs()
            and self.openai_structured_schema is not None
        )

        # Determine which days to generate
        if available_days:
            # Normalize day names
            available_days_normalized = [day.lower().strip() for day in available_days]
            days_to_generate = [
                d
                for d in ["monday", "tuesday", "wednesday", "thursday", "friday"]
                if d in available_days_normalized
            ]
            if not days_to_generate:
                # Fallback: if available_days doesn't match standard names, use all days
                days_to_generate = [
                    "monday",
                    "tuesday",
                    "wednesday",
                    "thursday",
                    "friday",
                ]
            days_text = ", ".join([d.capitalize() for d in days_to_generate])
            days_instruction = (
                f"**CRITICAL: Include ALL required fields ONLY for {days_text}**"
            )
            days_count_text = f"{len(days_to_generate)} day{'s' if len(days_to_generate) != 1 else ''}"
        else:
            days_to_generate = ["monday", "tuesday", "wednesday", "thursday", "friday"]
            days_text = "Monday, Tuesday, Wednesday, Thursday, Friday"
            days_instruction = f"**CRITICAL: Include ALL required fields for ALL FIVE DAYS ({days_text})**"
            days_count_text = "ALL 5 DAYS"

        # Build prompt with or without schema examples
        if using_structured_outputs:
            # Optimized prompt for structured outputs - schema provided via API
            # CRITICAL: Emphasize that ALL 5 days MUST be included in JSON
            if available_days:
                all_days_requirement = f"""
**CRITICAL JSON STRUCTURE REQUIREMENT:**
Your JSON MUST include ALL 5 days: monday, tuesday, wednesday, thursday, friday
- For {days_text}: Generate FULL, DETAILED content with all required fields
- For other days (NOT in the list above): Use minimal "No School" placeholders with this structure:
  {{
    "unit_lesson": "No School",
    "objective": {{"content_objective": "No School", "student_goal": "No School", "wida_objective": "No School"}},
    "anticipatory_set": {{"original_content": "No School", "bilingual_bridge": "No School"}},
    "tailored_instruction": {{"original_content": "No School", "co_teaching_model": {{}}, "ell_support": [], "special_needs_support": [], "materials": []}},
    "misconceptions": {{"original_content": "No School", "linguistic_note": {{}}}},
    "assessment": {{"primary_assessment": "No School", "bilingual_overlay": {{}}}},
    "homework": {{"original_content": "No School", "family_connection": "No School"}}
  }}
"""
            else:
                all_days_requirement = """
**CRITICAL JSON STRUCTURE REQUIREMENT:**
Your JSON MUST include ALL 5 days: monday, tuesday, wednesday, thursday, friday
- Generate FULL, DETAILED content for ALL days with all required fields
"""

            full_prompt = f"""SYSTEM CONFIGURATION:
- ENABLE_JSON_OUTPUT=true
- Output ONLY valid JSON matching the schema provided via API
- NO markdown code blocks (no ```json```)
- NO text before or after the JSON
- ALL fields must match the schema exactly

{all_days_requirement}

{prompt}

---

PRIMARY TEACHER LESSON PLAN:

{metadata_context}

{primary_content}

---

TASK: Transform this primary teacher lesson plan into a complete bilingual lesson plan.

OUTPUT REQUIREMENTS:
1. **MANDATORY: Your JSON MUST include ALL 5 days (monday, tuesday, wednesday, thursday, friday)** - This is a schema requirement that cannot be skipped
2. Generate JSON matching the schema structure provided via API
3. {days_instruction}
4. **For {days_text}: Populate with FULL, DETAILED content - no placeholders, no "TBD", no minimal data**
5. **For days NOT in the list above: Use minimal "No School" placeholders** (see structure above)
6. WIDA objective must include proper ELD standard format: (ELD-XX.#-#.Function.Domain) for each requested day
7. Include 3-5 ELL support strategies for each requested day
8. Add Portuguese cognates in bilingual_bridge for each requested day
9. Include co-teaching model with phase plan for each requested day
10. Add linguistic misconception notes for each requested day
11. Create bilingual assessment overlay for each requested day
12. Add family connection in Portuguese for each requested day

**WIDA LANGUAGE DOMAINS - FLEXIBLE SELECTION (CRITICAL):**

The four language domains (Listening, Reading, Speaking, Writing) are the structural backbone of WIDA's framework, but NOT every lesson must include all four. Select 1-4 domains based on:

1. **Lesson Activities Analysis**: 
   - Analyze the activities in `tailored_instruction.co_teaching_model.phase_plan`
   - Analyze the strategies in `tailored_instruction.ell_support`
   - Each strategy supports specific domains (e.g., Think-Pair-Share → Listening + Speaking)
   
2. **Content Objectives**: 
   - What students need to do determines which domains are necessary
   - If students must read → include Reading
   - If students must write → include Writing  
   - If students must discuss → include Speaking + Listening
   - If students must present → include Speaking (possibly + Writing for notes)

3. **Activity-to-Domain Mapping**:
   - Think-Pair-Share → Listening + Speaking
   - Reading comprehension → Reading (possibly + Writing if responses)
   - Writing workshop → Writing (possibly + Reading if mentor texts)
   - Direct instruction/lecture → Listening (possibly + Writing if note-taking)
   - Literature circles → Reading + Speaking + Listening
   - Research projects → Reading + Writing (possibly + Speaking if presentations)
   - Jigsaw activities → Reading + Speaking + Listening

**objective.student_goal REQUIREMENTS:**
- Format: "I will..." (first person, child-friendly language)
- Include ONLY the domains (1-4) that the lesson activities actually support
- Use simple, age-appropriate language that a child can understand
- Keep to 1 sentence, maximum 12-15 words for clarity
- Structure: "I will [domain actions] about/to [content focus]"
- Domain-specific child-friendly verbs:
  - Listening: "listen to", "hear", "pay attention to"
  - Reading: "read", "look at", "find in the text"
  - Speaking: "speak", "tell", "share", "talk about", "say"
  - Writing: "write", "put in writing", "write down"

**Examples by domain count:**
- 1 domain (Writing only): "I will write a paragraph about the water cycle."
- 2 domains (Listening + Speaking): "I will listen to my partner and speak to share my ideas about fractions."
- 2 domains (Reading + Writing): "I will read the story and write about my favorite part."
- 3 domains (Reading + Speaking + Writing): "I will read the text, speak with my group, and write my answer."
- 4 domains (All): "I will listen to the explanation, read the text, speak with my partner, and write my response."

**objective.wida_objective REQUIREMENTS:**
- Include ONLY the domains (1-4) that the lesson activities actually support
- Explicitly name each domain used in the objective text
- Use appropriate ELD code format with domain notation:
  - Single domain: ELD-XX.#-#.Function.Domain (e.g., ELD-SS.6-8.Explain.Writing)
  - Multiple domains: ELD-XX.#-#.Function.Domain1/Domain2 (e.g., ELD-SS.6-8.Explain.Listening/Speaking)
  - All four: ELD-XX.#-#.Function.Listening/Reading/Speaking/Writing
- Structure: "Students will [function] [content] through [domain actions], using [supports] appropriate for WIDA levels X-X (ELD-XX.#-#.Function.[Domains])."

**Examples by domain count:**
- 1 domain (Writing): "Students will explain the water cycle through writing a paragraph describing each stage, using sentence frames and vocabulary supports appropriate for WIDA levels 2-4 (ELD-SC.4-5.Explain.Writing)."
- 2 domains (Listening + Speaking): "Students will compare fractions through listening to explanations and speaking with partners using sentence frames, using visual supports appropriate for WIDA levels 2-3 (ELD-MA.3-5.Compare.Listening/Speaking)."
- 3 domains (Reading + Speaking + Writing): "Students will analyze characters through reading the text, speaking in literature circles, and writing character descriptions, using graphic organizers and sentence frames appropriate for WIDA levels 3-5 (ELD-LA.4-5.Analyze.Reading/Speaking/Writing)."
- 4 domains (All): "Students will explain historical events through listening to primary sources, reading documents, speaking in discussions, and writing summaries, using cognates and sentence frames appropriate for WIDA levels 2-4 (ELD-SS.6-8.Explain.Listening/Reading/Speaking/Writing)."

**CRITICAL**: Do NOT force all four domains if the lesson activities don't support them. Analyze the actual activities in phase_plan and ell_support, then select domains accordingly. The goal is authentic alignment between activities and language domains.

**CONTENT PRESERVATION RULES (CRITICAL):**
13. **unit_lesson field**: Copy EXACTLY from input - DO NOT transform, paraphrase, or translate. Preserve all hyperlink text verbatim.
14. **objective.content_objective**: Copy EXACTLY from input primary teacher's objective - DO NOT transform or paraphrase.
15. **Hyperlink formatting**: When multiple hyperlinks exist, format each on its own line (use \\n) for readability:
    Example:
    "LESSON 9: MEASURE TO FIND THE AREA\\nLESSON 10: SOLVE AREA PROBLEMS\\nLESSON 11: AREA AND THE MULTIPLICATION TABLE"
    NOT: "LESSON 9: MEASURE TO FIND THE AREA LESSON 10: SOLVE AREA PROBLEMS..."

**REMINDER: Your JSON MUST include ALL 5 days. Generate FULL content for {days_text}, and minimal "No School" placeholders for other days.**

Generate the complete JSON now with FULL DATA FOR {days_count_text.upper()}. Output ONLY the JSON, nothing else.
"""
        else:
            # Full prompt with schema examples for non-structured outputs
            schema_example = self._build_schema_example(
                week_of, grade, subject, teacher_name, homeroom
            )

            full_prompt = f"""SYSTEM CONFIGURATION:
- ENABLE_JSON_OUTPUT=true
- Output ONLY valid JSON matching the exact schema structure below
- NO markdown code blocks (no ```json```)
- NO text before or after the JSON
- ALL fields must match the schema exactly

{prompt}

---

REQUIRED JSON SCHEMA STRUCTURE:

You MUST output JSON that matches this EXACT structure:

{schema_example}

CRITICAL REQUIREMENTS:
1. Root object has "metadata" and "days" keys
2. metadata.week_of format: "MM/DD-MM/DD" (e.g., "10/6-10/10")
3. days object must include: {days_text.lower()}
4. {days_instruction}
5. Each day has: unit_lesson, objective, anticipatory_set, tailored_instruction, misconceptions, assessment, homework
6. objective has: content_objective, student_goal, wida_objective
7. wida_objective MUST include ELD standard format: (ELD-XX.#-#.Function.Domain)
8. anticipatory_set has: original_content, bilingual_bridge
9. tailored_instruction has: original_content, co_teaching_model, ell_support (3-5 items), special_needs_support (1-2 items), materials
10. co_teaching_model has: model_name, rationale, wida_context, phase_plan, implementation_notes
11. Each ell_support item has: strategy_id, strategy_name, implementation, proficiency_levels
12. misconceptions has: original_content, linguistic_note
13. assessment has: primary_assessment, bilingual_overlay
14. homework has: original_content, family_connection

---

PRIMARY TEACHER LESSON PLAN:

{metadata_context}

{primary_content}

---

TASK: Transform this primary teacher lesson plan into a complete bilingual lesson plan.

OUTPUT REQUIREMENTS:
1. Generate JSON matching the EXACT schema structure above
2. {days_instruction}
3. **IMPORTANT: The schema requires all 5 days, but only populate {days_text} with FULL, DETAILED content**
4. **For days NOT in the list above, use minimal "No School" placeholders** (this is a single-lesson document)
5. **Each requested day must have complete data - no placeholders, no "TBD", no minimal data**
6. WIDA objective must include proper ELD standard for each requested day
7. Include 3-5 ELL support strategies for each requested day
8. Add Portuguese cognates in bilingual_bridge for each requested day
9. Include co-teaching model with phase plan for each requested day
10. Add linguistic misconception notes for each requested day
11. Create bilingual assessment overlay for each requested day
12. Add family connection in Portuguese for each requested day

**WIDA LANGUAGE DOMAINS - FLEXIBLE SELECTION (CRITICAL):**

The four language domains (Listening, Reading, Speaking, Writing) are the structural backbone of WIDA's framework, but NOT every lesson must include all four. Select 1-4 domains based on:

1. **Lesson Activities Analysis**: 
   - Analyze the activities in `tailored_instruction.co_teaching_model.phase_plan`
   - Analyze the strategies in `tailored_instruction.ell_support`
   - Each strategy supports specific domains (e.g., Think-Pair-Share → Listening + Speaking)
   
2. **Content Objectives**: 
   - What students need to do determines which domains are necessary
   - If students must read → include Reading
   - If students must write → include Writing  
   - If students must discuss → include Speaking + Listening
   - If students must present → include Speaking (possibly + Writing for notes)

3. **Activity-to-Domain Mapping**:
   - Think-Pair-Share → Listening + Speaking
   - Reading comprehension → Reading (possibly + Writing if responses)
   - Writing workshop → Writing (possibly + Reading if mentor texts)
   - Direct instruction/lecture → Listening (possibly + Writing if note-taking)
   - Literature circles → Reading + Speaking + Listening
   - Research projects → Reading + Writing (possibly + Speaking if presentations)
   - Jigsaw activities → Reading + Speaking + Listening

**objective.student_goal REQUIREMENTS:**
- Format: "I will..." (first person, child-friendly language)
- Include ONLY the domains (1-4) that the lesson activities actually support
- Use simple, age-appropriate language that a child can understand
- Keep to 1 sentence, maximum 12-15 words for clarity
- Structure: "I will [domain actions] about/to [content focus]"
- Domain-specific child-friendly verbs:
  - Listening: "listen to", "hear", "pay attention to"
  - Reading: "read", "look at", "find in the text"
  - Speaking: "speak", "tell", "share", "talk about", "say"
  - Writing: "write", "put in writing", "write down"

**Examples by domain count:**
- 1 domain (Writing only): "I will write a paragraph about the water cycle."
- 2 domains (Listening + Speaking): "I will listen to my partner and speak to share my ideas about fractions."
- 2 domains (Reading + Writing): "I will read the story and write about my favorite part."
- 3 domains (Reading + Speaking + Writing): "I will read the text, speak with my group, and write my answer."
- 4 domains (All): "I will listen to the explanation, read the text, speak with my partner, and write my response."

**objective.wida_objective REQUIREMENTS:**
- Include ONLY the domains (1-4) that the lesson activities actually support
- Explicitly name each domain used in the objective text
- Use appropriate ELD code format with domain notation:
  - Single domain: ELD-XX.#-#.Function.Domain (e.g., ELD-SS.6-8.Explain.Writing)
  - Multiple domains: ELD-XX.#-#.Function.Domain1/Domain2 (e.g., ELD-SS.6-8.Explain.Listening/Speaking)
  - All four: ELD-XX.#-#.Function.Listening/Reading/Speaking/Writing
- Structure: "Students will [function] [content] through [domain actions], using [supports] appropriate for WIDA levels X-X (ELD-XX.#-#.Function.[Domains])."

**Examples by domain count:**
- 1 domain (Writing): "Students will explain the water cycle through writing a paragraph describing each stage, using sentence frames and vocabulary supports appropriate for WIDA levels 2-4 (ELD-SC.4-5.Explain.Writing)."
- 2 domains (Listening + Speaking): "Students will compare fractions through listening to explanations and speaking with partners using sentence frames, using visual supports appropriate for WIDA levels 2-3 (ELD-MA.3-5.Compare.Listening/Speaking)."
- 3 domains (Reading + Speaking + Writing): "Students will analyze characters through reading the text, speaking in literature circles, and writing character descriptions, using graphic organizers and sentence frames appropriate for WIDA levels 3-5 (ELD-LA.4-5.Analyze.Reading/Speaking/Writing)."
- 4 domains (All): "Students will explain historical events through listening to primary sources, reading documents, speaking in discussions, and writing summaries, using cognates and sentence frames appropriate for WIDA levels 2-4 (ELD-SS.6-8.Explain.Listening/Reading/Speaking/Writing)."

**CRITICAL**: Do NOT force all four domains if the lesson activities don't support them. Analyze the actual activities in phase_plan and ell_support, then select domains accordingly. The goal is authentic alignment between activities and language domains.

**CONTENT PRESERVATION RULES (CRITICAL):**
12. **unit_lesson field**: Copy EXACTLY from input - DO NOT transform, paraphrase, or translate. Preserve all hyperlink text verbatim.
13. **objective.content_objective**: Copy EXACTLY from input primary teacher's objective - DO NOT transform or paraphrase.
14. **Hyperlink formatting**: When multiple hyperlinks exist, format each on its own line (use \\n) for readability:
    Example:
    "LESSON 9: MEASURE TO FIND THE AREA\\nLESSON 10: SOLVE AREA PROBLEMS\\nLESSON 11: AREA AND THE MULTIPLICATION TABLE"
    NOT: "LESSON 9: MEASURE TO FIND THE AREA LESSON 10: SOLVE AREA PROBLEMS..."

Generate the complete JSON now with FULL DATA FOR {days_count_text.upper()}. Output ONLY the JSON, nothing else.
"""

        return full_prompt

    def _build_schema_example(
        self,
        week_of: str,
        grade: str,
        subject: str,
        teacher_name: Optional[str],
        homeroom: Optional[str],
    ) -> str:
        """Build schema example with actual values"""

        def create_day(
            unit_lesson: str,
            *,
            wida_objective: str = "Students will explain [content] through [selected domains based on activities], using [supports] appropriate for WIDA levels X-X (ELD-XX.#-#.Function.[Domains]).",
            student_goal: str = "I will [domain actions based on lesson activities] about [content].",
            anticipatory_bridge: str = "...",
            co_teaching_model: Optional[Dict[str, Any]] = None,
            ell_support: Optional[List[Dict[str, Any]]] = None,
            special_needs_support: Optional[List[str]] = None,
            materials: Optional[List[str]] = None,
            linguistic_note: Optional[Dict[str, Any]] = None,
            bilingual_overlay: Optional[Dict[str, Any]] = None,
        ) -> Dict[str, Any]:
            return {
                "unit_lesson": unit_lesson,
                "objective": {
                    "content_objective": "Students will...",
                    "student_goal": student_goal,
                    "wida_objective": wida_objective,
                },
                "anticipatory_set": {
                    "original_content": "...",
                    "bilingual_bridge": anticipatory_bridge,
                },
                "tailored_instruction": {
                    "original_content": "...",
                    "co_teaching_model": co_teaching_model or {},
                    "ell_support": ell_support or [],
                    "special_needs_support": special_needs_support or [],
                    "materials": materials or [],
                },
                "misconceptions": {
                    "original_content": "...",
                    "linguistic_note": linguistic_note or {},
                },
                "assessment": {
                    "primary_assessment": "...",
                    "bilingual_overlay": bilingual_overlay or {},
                },
                "homework": {"original_content": "...", "family_connection": "..."},
            }

        day_definitions = [
            (
                "monday",
                {
                    "unit_lesson": "Unit One Lesson One",
                    "wida_objective": "Students will explain the water cycle through listening to explanations, reading diagrams, speaking with partners, and writing paragraphs, using visual supports and sentence frames appropriate for WIDA levels 2-4 (ELD-SC.4-5.Explain.Listening/Reading/Speaking/Writing).",
                    "student_goal": "I will listen to explanations, read diagrams, speak with my partner, and write about the water cycle.",
                    "anticipatory_bridge": "Preview key cognates: word/palavra...",
                    "co_teaching_model": {
                        "model_name": "Station Teaching",
                        "rationale": "...",
                        "wida_context": "...",
                        "phase_plan": [
                            {
                                "phase_name": "Warmup",
                                "minutes": 5,
                                "bilingual_teacher_role": "...",
                                "primary_teacher_role": "...",
                            }
                        ],
                        "implementation_notes": ["..."],
                    },
                    "ell_support": [
                        {
                            "strategy_id": "cognate_awareness",
                            "strategy_name": "Cognate Awareness",
                            "implementation": "...",
                            "proficiency_levels": "Levels 2-5",
                        }
                    ],
                    "special_needs_support": ["..."],
                    "materials": ["..."],
                    "linguistic_note": {
                        "pattern_id": "subject_pronoun_omission",
                        "note": "...",
                        "prevention_tip": "...",
                    },
                    "bilingual_overlay": {
                        "instrument": "...",
                        "wida_mapping": "...",
                        "supports_by_level": {
                            "levels_1_2": "...",
                            "levels_3_4": "...",
                            "levels_5_6": "...",
                        },
                        "scoring_lens": "...",
                        "constraints_honored": "...",
                    },
                },
            ),
            (
                "tuesday",
                {
                    "unit_lesson": "Unit One Lesson Two",
                    "co_teaching_model": {
                        "model_name": "Station Teaching",
                        "rationale": "...",
                        "wida_context": "...",
                        "phase_plan": [],
                        "implementation_notes": [],
                    },
                    "linguistic_note": {
                        "pattern_id": "...",
                        "note": "...",
                        "prevention_tip": "...",
                    },
                    "bilingual_overlay": {
                        "instrument": "...",
                        "wida_mapping": "...",
                        "supports_by_level": {},
                        "scoring_lens": "...",
                        "constraints_honored": "...",
                    },
                },
            ),
            ("wednesday", {"unit_lesson": "Unit One Lesson Three"}),
            ("thursday", {"unit_lesson": "Unit One Lesson Four"}),
            ("friday", {"unit_lesson": "Unit One Lesson Five"}),
        ]

        example = {
            "metadata": {"week_of": week_of, "grade": grade, "subject": subject},
            "days": {
                day: create_day(**definition) for day, definition in day_definitions
            },
        }

        if teacher_name:
            example["metadata"]["teacher_name"] = teacher_name
        if homeroom:
            example["metadata"]["homeroom"] = homeroom

        return json.dumps(example, indent=2)

    def _call_llm(self, prompt: str) -> Tuple[str, Dict[str, int]]:
        """Call LLM API and return content with token usage.

        Returns:
            Tuple of (response_text, usage_dict)
            usage_dict contains: tokens_input, tokens_output, tokens_total
        """
        logger.info(
            "llm_api_call_started",
            extra={
                "provider": self.provider,
                "model": self.model,
                "prompt_length": len(prompt),
                "max_completion_tokens": self.max_completion_tokens,
                "estimated_time_seconds": min(
                    180, (len(prompt) // 4 + self.max_completion_tokens) // 100
                ),  # Rough estimate
            },
        )

        if self.provider == "openai":
            if self._model_supports_structured_outputs():
                response_format = self._structured_response_format()
                if response_format:
                    try:
                        logger.info(
                            "using_openai_structured_outputs",
                            extra={"model": self.model},
                        )
                        return self._call_openai_chat_completion(
                            prompt, response_format=response_format
                        )
                    except Exception as exc:
                        logger.warning(
                            "structured_outputs_failed_fallback",
                            extra={"model": self.model, "error": str(exc)},
                        )

            if self._model_supports_json_mode():
                try:
                    logger.info(
                        "using_openai_json_mode",
                        extra={"model": self.model},
                    )
                    return self._call_openai_chat_completion(
                        prompt, response_format={"type": "json_object"}
                    )
                except Exception as exc:
                    logger.warning(
                        "json_mode_failed_fallback",
                        extra={"model": self.model, "error": str(exc)},
                    )

            logger.info("using_openai_legacy_mode", extra={"model": self.model})
            return self._call_openai_chat_completion(prompt)

        elif self.provider == "anthropic":
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_completion_tokens,
                messages=[{"role": "user", "content": prompt}],
            )

            # Extract token usage
            usage = {
                "tokens_input": response.usage.input_tokens if response.usage else 0,
                "tokens_output": response.usage.output_tokens if response.usage else 0,
                "tokens_total": (
                    response.usage.input_tokens + response.usage.output_tokens
                )
                if response.usage
                else 0,
            }
            return response.content[0].text, usage

        raise ValueError(f"Unsupported provider: {self.provider}")

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM response to JSON"""
        # Clean up response
        cleaned = response_text.strip()

        # Remove markdown code blocks if present
        if cleaned.startswith("```"):
            cleaned = cleaned.replace("```json", "").replace("```", "").strip()

        # Parse JSON
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.warning(
                "json_parse_error_attempting_repair",
                extra={"error": str(e), "response_preview": cleaned[:500]},
            )

            # Attempt to repair the JSON
            success, repaired, repair_error = repair_json(cleaned)

            if success and repaired:
                logger.info("json_repair_successful")
                try:
                    return json.loads(repaired)
                except json.JSONDecodeError as e2:
                    logger.error(
                        "json_repair_failed_to_parse", extra={"error": str(e2)}
                    )

            # If repair failed, log and raise original error
            logger.error(
                "json_parse_error",
                extra={"error": str(e), "response_preview": cleaned[:500]},
            )
            raise ValueError(f"Failed to parse JSON: {e}")

    def _validate_structure(self, lesson_json: Dict[str, Any]) -> bool:
        """Validate JSON structure matches schema"""
        # Check root keys
        if "metadata" not in lesson_json or "days" not in lesson_json:
            logger.error(
                "schema_validation_failed", extra={"reason": "Missing root keys"}
            )
            return False

        # Check metadata
        metadata = lesson_json["metadata"]
        required_metadata = ["week_of", "grade", "subject"]
        for field in required_metadata:
            if field not in metadata:
                logger.error(
                    "schema_validation_failed",
                    extra={"reason": f"Missing metadata.{field}"},
                )
                return False

        # Check days
        days = lesson_json["days"]
        required_days = ["monday", "tuesday", "wednesday", "thursday", "friday"]
        missing_days = []
        for day in required_days:
            if day not in days:
                missing_days.append(day)
                logger.warning(
                    "schema_validation_missing_day",
                    extra={"day": day, "action": "Adding placeholder"},
                )

        # Fill in missing days with "No School" placeholders
        if missing_days:
            no_school_placeholder = {
                "unit_lesson": "No School",
                "objective": {
                    "content_objective": "No School",
                    "student_goal": "No School",
                    "wida_objective": "No School",
                },
                "anticipatory_set": {
                    "original_content": "No School",
                    "bilingual_bridge": "No School",
                },
                "tailored_instruction": {
                    "original_content": "No School",
                    "co_teaching_model": {},
                    "ell_support": [],
                    "special_needs_support": [],
                    "materials": [],
                },
                "misconceptions": {
                    "original_content": "No School",
                    "linguistic_note": {},
                },
                "assessment": {
                    "primary_assessment": "No School",
                    "bilingual_overlay": {},
                },
                "homework": {
                    "original_content": "No School",
                    "family_connection": "No School",
                },
            }

            for day in missing_days:
                days[day] = no_school_placeholder.copy()

            logger.info(
                "schema_validation_missing_days_filled",
                extra={"missing_days": missing_days, "filled_count": len(missing_days)},
            )

        # Check Monday structure (at minimum)
        monday = days["monday"]
        if "unit_lesson" not in monday:
            logger.error(
                "schema_validation_failed",
                extra={"reason": "Missing monday.unit_lesson"},
            )
            return False

        logger.info("schema_validation_success")
        return True


# Singleton instance
_llm_service: Optional[LLMService] = None


def get_llm_service(
    provider: str = "openai", api_key: Optional[str] = None
) -> LLMService:
    """Get or create LLM service instance"""
    global _llm_service

    if _llm_service is None:
        _llm_service = LLMService(provider=provider, api_key=api_key)

    return _llm_service
