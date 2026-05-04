# ==================================================================
# GAME MASTER SERVICE (AI PIPELINE)
# ==================================================================

import asyncio
import json
import uuid
from datetime import date, datetime, timedelta, timezone
from anthropic import AsyncAnthropic
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.config import settings
from app.core.exceptions import ConflictError
from app.models.activity import ActivityLog
from app.models.catalog import Attribute
from app.models.mission import GmContextSnapshot, Mission
from app.models.player import PlayerAttribute, PlayerProfile
from app.schemas.gm import AIMissionBatch, AIMissionItem, DiagnosticResponse

# Constants for stamina calculations and mock generation
_STAMINA_MAX = 100
_STAMINA_REGEN_PER_HOUR = 5
_MOCK_MODEL_TAG = "mock-gm-v1"

# Tool schema for forcing Claude to return structured mission data
_MISSION_TOOL = {
    "name": "create_missions",
    "description": "Crea exactamente 3 misiones diarias personalizadas para el jugador basadas en sus estadísticas actuales.",
    "input_schema": {
        "type": "object",
        "properties": {
            "missions": {
                "type": "array",
                "minItems": 3,
                "maxItems": 3,
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "maxLength": 200},
                        "description": {"type": "string"},
                        "attribute_code": {
                            "type": "string",
                            "enum": ["S", "P", "E", "C", "I", "A", "L"],
                        },
                        "objective_type": {
                            "type": "string",
                            "enum": ["LOG_MINUTES", "LOG_COUNT"],
                        },
                        "objective_target": {"type": "integer", "minimum": 1},
                        "reward_xp": {"type": "integer", "minimum": 10, "maximum": 500},
                        "reward_material_qty": {"type": "integer", "minimum": 5, "maximum": 200},
                    },
                    "required": [
                        "title",
                        "description",
                        "attribute_code",
                        "objective_type",
                        "objective_target",
                        "reward_xp",
                        "reward_material_qty",
                    ],
                },
            }
        },
        "required": ["missions"],
    },
}

# Tool schema for forcing Claude to return structured diagnostic data
_DIAGNOSTIC_TOOL = {
    "name": "player_diagnostic",
    "description": "Genera un diagnóstico narrativo del progreso del jugador en los últimos 30 días.",
    "input_schema": {
        "type": "object",
        "properties": {
            "narrative": {"type": "string"},
            "strengths": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "attribute": {"type": "string"},
                        "detail": {"type": "string"},
                    },
                    "required": ["attribute", "detail"],
                },
            },
            "areas_to_improve": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "attribute": {"type": "string"},
                        "detail": {"type": "string"},
                    },
                    "required": ["attribute", "detail"],
                },
            },
            "recommendation": {"type": "string"},
        },
        "required": ["narrative", "strengths", "areas_to_improve", "recommendation"],
    },
}

# Service for handling Game Master logic and AI interactions
class GmService:
    def __init__(self, session: AsyncSession) -> None:
        self._db = session
        # Client is only instantiated when the real API is needed
        self._client: AsyncAnthropic | None = (
            None
            if settings.USE_AI_MOCK
            else AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        )

    # Helper to build a comprehensive snapshot of player data for AI prompts
    async def build_context_snapshot(self, player_id: uuid.UUID, days: int = 7) -> dict:
        """Collects full player state for AI prompts."""
        profile = (
            await self._db.scalar(
                select(PlayerProfile)
                .where(PlayerProfile.id == player_id)
                .options(
                    selectinload(PlayerProfile.attributes).selectinload(
                        PlayerAttribute.attribute
                    ),
                )
            )
        )

        since = date.today() - timedelta(days=days)
        recent_logs = (
            await self._db.scalars(
                select(ActivityLog)
                .where(
                    ActivityLog.player_id == player_id,
                    ActivityLog.activity_date >= since,
                )
                .options(selectinload(ActivityLog.attribute))
                .order_by(ActivityLog.activity_date.desc())
            )
        ).all()

        activity_summary: dict[str, dict] = {}
        for log in recent_logs:
            code = log.attribute.code
            if code not in activity_summary:
                activity_summary[code] = {"sessions": 0}
            activity_summary[code]["sessions"] += 1

        return {
            "streak_current": profile.streak_current,
            "streak_max": profile.streak_max,
            "prestige_count": profile.prestige_count,
            "stamina": self._effective_stamina(profile),
            "attributes": [
                {
                    "code": pa.attribute.code,
                    "name": pa.attribute.name,
                    "level": pa.level,
                    "xp_current": pa.xp_current,
                    "xp_to_next": pa.xp_to_next,
                }
                for pa in profile.attributes
            ],
            f"activity_last_{days}d": activity_summary,
        }

    # Helper to generate a diagnostic report for a player based on their data and AI analysis
    async def generate_diagnostic(self, player_id: uuid.UUID) -> DiagnosticResponse:
        profile = (
            await self._db.scalar(
                select(PlayerProfile).where(PlayerProfile.id == player_id)
            )
        )
        if not profile:
            raise ConflictError("Player not found")

        await self._check_ai_budget(profile)
        context = await self.build_context_snapshot(player_id, days=30)

        if settings.USE_AI_MOCK:
            await asyncio.sleep(1.0) 
            await self._db.commit()
            return self._generate_mock_diagnostic(context)

        response = await self._client.messages.create(  # type: ignore[union-attr]
            model=settings.AI_MODEL,
            max_tokens=2048,
            thinking={"type": "adaptive"},
            system=[
                {
                    "type": "text",
                    "text": (
                        "Eres el Game Master de 'The Forge', un RPG de gestión de vida con atributos S.P.E.C.I.A.L. "
                        "(Strength, Perception, Endurance, Charisma, Intelligence, Agility, Luck). "
                        "Analizas el progreso de los jugadores y generas diagnósticos narrativos motivadores. "
                        "Tu análisis debe ser personal, específico y basado en los datos reales del jugador. "
                        "Responde siempre en español con un tono épico y motivador."
                    ),
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            tools=[_DIAGNOSTIC_TOOL],
            tool_choice={"type": "tool", "name": "player_diagnostic"},
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Genera un diagnóstico narrativo completo para este jugador basado en los últimos 30 días.\n\n"
                        f"DATOS DEL JUGADOR:\n{json.dumps(context, ensure_ascii=False, indent=2)}\n\n"
                        f"Identifica fortalezas reales, áreas descuidadas y da una recomendación accionable."
                    ),
                }
            ],
        )

        tool_block = next(
            (
                b
                for b in response.content
                if b.type == "tool_use" and b.name == "player_diagnostic"
            ),
            None,
        )
        if not tool_block:
            raise ConflictError("AI failed to generate diagnostic")

        data = tool_block.input
        tokens_used = response.usage.input_tokens + response.usage.output_tokens
        cache_hit = getattr(response.usage, "cache_read_input_tokens", 0) > 0

        await self._db.commit()

        return DiagnosticResponse(
            narrative=data["narrative"],
            strengths=data["strengths"],
            areas_to_improve=data["areas_to_improve"],
            recommendation=data["recommendation"],
            tokens_used=tokens_used,
            cache_hit=cache_hit,
        )

    # Function to run mission generation
    @staticmethod
    async def run_background_mission_generation(player_id: uuid.UUID) -> None:

        from app.database import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            svc = GmService(session)
            await svc._run_mission_generation(player_id)

    # Function to run diagnostic generation
    @staticmethod
    def _generate_mock_missions(context: dict) -> AIMissionBatch:

        attrs = context.get("attributes", [])
        # Find the activity key regardless of the 'days' parameter used
        activity_key = next((k for k in context if k.startswith("activity_last_")), None)
        activity: dict = context.get(activity_key, {}) if activity_key else {}

        # Sort least-worked attributes first so mock missions feel intentional
        sorted_attrs = sorted(
            attrs,
            key=lambda a: activity.get(a["code"], {}).get("total_minutes", 0),
        )
        # Ensure we always have 3 slots, cycling if player has fewer than 3 attrs
        chosen = (sorted_attrs * 3)[:3]

        templates = [
            {
                "title": "[MOCK] Sesión de {name}: Refactorización",
                "desc": "Dedica {target} minutos a trabajar en {name}. Cada minuto acumula poder en tu atributo.",
                "obj_type": "LOG_MINUTES",
                "base_target": 30,
                "base_xp": 50,
                "base_mat": 20,
            },
            {
                "title": "[MOCK] Maratón de {name}",
                "desc": "Acumula {target} minutos de actividad en {name}. El camino al nivel {next_level} empieza aquí.",
                "obj_type": "LOG_MINUTES",
                "base_target": 60,
                "base_xp": 100,
                "base_mat": 40,
            },
            {
                "title": "[MOCK] Registro Diario: {name}",
                "desc": "Completa {target} registro(s) de {name} hoy. La consistencia forja leyendas.",
                "obj_type": "LOG_COUNT",
                "base_target": 2,
                "base_xp": 75,
                "base_mat": 30,
            },
        ]

        missions: list[AIMissionItem] = []
        for attr, tpl in zip(chosen, templates):
            level = attr["level"]
            scale = max(1, level // 2)
            target = tpl["base_target"] + (scale * 5 if tpl["obj_type"] == "LOG_MINUTES" else scale)
            xp = min(tpl["base_xp"] + scale * 10, 500)
            mat = min(tpl["base_mat"] + scale * 5, 200)

            missions.append(
                AIMissionItem(
                    title=tpl["title"].format(name=attr["name"]),
                    description=tpl["desc"].format(
                        target=target,
                        name=attr["name"],
                        next_level=level + 1,
                    ),
                    attribute_code=attr["code"],
                    objective_type=tpl["obj_type"],
                    objective_target=target,
                    reward_xp=xp,
                    reward_material_qty=mat,
                )
            )

        return AIMissionBatch(missions=missions)

    # Function to generate a mock diagnostic report based on player data without calling the API
    @staticmethod
    def _generate_mock_diagnostic(context: dict) -> DiagnosticResponse:

        attrs = context.get("attributes", [])
        activity_key = next((k for k in context if k.startswith("activity_last_")), None)
        activity: dict = context.get(activity_key, {}) if activity_key else {}
        streak = context.get("streak_current", 0)
        stamina = context.get("stamina", 100)

        sorted_by_level = sorted(attrs, key=lambda a: a["level"], reverse=True)
        sorted_by_activity = sorted(
            attrs,
            key=lambda a: activity.get(a["code"], {}).get("total_minutes", 0),
            reverse=True,
        )

        top_attrs = sorted_by_level[:2]
        bottom_attrs = sorted_by_level[-2:] if len(sorted_by_level) > 2 else []
        most_active = sorted_by_activity[0] if sorted_by_activity else None
        least_active = sorted_by_activity[-1] if sorted_by_activity else None

        # Build narrative from real data
        if top_attrs:
            best = top_attrs[0]
            narrative = (
                f"[MOCK DIAGNÓSTICO] Guerrero, el análisis de tus datos revela un perfil singular. "
                f"Tu {best['name']} (Nivel {best['level']}) es tu pilar más sólido — una fortaleza digna de leyenda. "
            )
        else:
            narrative = "[MOCK DIAGNÓSTICO] Tu aventura en The Forge apenas comienza. "

        if least_active and activity.get(least_active["code"], {}).get("total_minutes", 0) == 0:
            narrative += (
                f"Sin embargo, tu {least_active['name']} lleva demasiado tiempo en las sombras — "
                f"el abandono es el mayor enemigo de un aventurero S.P.E.C.I.A.L. "
            )
        elif most_active:
            narrative += (
                f"Tu dedicación a {most_active['name']} ha sido notable este período. "
            )

        if streak > 0:
            narrative += f"Tu racha de {streak} día(s) consecutivos demuestra una disciplina envidiable. "
        else:
            narrative += "Recuperar tu racha debe ser la prioridad inmediata. "

        if stamina < 40:
            narrative += "Tu estamina está al límite — el descanso también es parte del entrenamiento."
        elif stamina < 70:
            narrative += "Tu estamina se recupera, pero cuídate de no sobrecargar el sistema."
        else:
            narrative += "Estamina óptima: estás en tu mejor momento para el combate."

        # Strengths from top-level attributes
        strengths = [
            {
                "attribute": a["name"],
                "detail": (
                    f"Nivel {a['level']} con {activity.get(a['code'], {}).get('total_minutes', 0)} minutos registrados. "
                    f"Consistencia demostrada."
                ),
            }
            for a in top_attrs
        ]
        if not strengths:
            strengths = [{"attribute": "Perseverancia", "detail": "Has iniciado tu camino en The Forge."}]

        # Areas from bottom-level attributes (exclude overlap with strengths)
        top_codes = {a["code"] for a in top_attrs}
        areas_raw = [a for a in bottom_attrs if a["code"] not in top_codes]
        areas = [
            {
                "attribute": a["name"],
                "detail": (
                    f"Nivel {a['level']} — solo {activity.get(a['code'], {}).get('total_minutes', 0)} minutos "
                    f"en el período analizado. Requiere atención urgente."
                ),
            }
            for a in areas_raw
        ]
        if not areas:
            areas = [
                {
                    "attribute": "Equilibrio",
                    "detail": "Intenta distribuir el tiempo entre todos los atributos S.P.E.C.I.A.L.",
                }
            ]

        neglected_name = (
            least_active["name"]
            if least_active and least_active["code"] not in top_codes
            else (bottom_attrs[0]["name"] if bottom_attrs else "tus atributos menos trabajados")
        )
        recommendation = (
            f"[MOCK] Dedica al menos 30 minutos diarios a {neglected_name} durante la próxima semana. "
            f"Un héroe S.P.E.C.I.A.L. equilibrado siempre supera al especialista unidimensional."
        )

        return DiagnosticResponse(
            narrative=narrative,
            strengths=strengths,
            areas_to_improve=areas,
            recommendation=recommendation,
            tokens_used=0,
            cache_hit=False,
        )

    # Function to calculate effective stamina based on last update and regeneration rate
    def _effective_stamina(self, profile: PlayerProfile) -> int:
        hours_since = (
            datetime.now(timezone.utc) - profile.stamina_updated_at
        ).total_seconds() / 3600
        regen = int(hours_since * _STAMINA_REGEN_PER_HOUR)
        return min(_STAMINA_MAX, profile.stamina_current + regen)

    # Helper to check and update AI budget for a player, raising an error if the limit is exceeded
    async def _check_ai_budget(self, profile: PlayerProfile) -> None:
        now = datetime.now(timezone.utc)
        if profile.ai_budget_reset_at is None or profile.ai_budget_reset_at <= now:
            profile.ai_calls_today = 0
            tomorrow = now + timedelta(days=1)
            profile.ai_budget_reset_at = tomorrow.replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        if profile.ai_calls_today >= profile.ai_calls_limit:
            raise ConflictError(
                f"Daily AI limit reached ({profile.ai_calls_limit} calls). "
                f"Resets at {profile.ai_budget_reset_at.isoformat()}"
            )
        profile.ai_calls_today += 1

    async def _run_mission_generation(self, player_id: uuid.UUID) -> None:
        now = datetime.now(timezone.utc)

        # Skip if AI missions are already active
        existing_ai_count = await self._db.scalar(
            select(func.count(Mission.id)).where(
                Mission.player_id == player_id,
                Mission.status == "ACTIVE",
                Mission.generated_by_model.isnot(None),
                Mission.expires_at > now,
            )
        )
        if existing_ai_count and existing_ai_count > 0:
            return

        profile = (
            await self._db.scalar(
                select(PlayerProfile).where(PlayerProfile.id == player_id)
            )
        )
        if not profile:
            return

        try:
            await self._check_ai_budget(profile)
        except ConflictError:
            return

        context = await self.build_context_snapshot(player_id)

        if settings.USE_AI_MOCK:
            await asyncio.sleep(1.5) 
            batch = self._generate_mock_missions(context)
            model_tag = _MOCK_MODEL_TAG
            tokens_used = 0
            cache_hit = False
        else:
            response = await self._client.messages.create(  # type: ignore[union-attr]
                model=settings.AI_MODEL,
                max_tokens=2048,
                thinking={"type": "adaptive"},
                system=[
                    {
                        "type": "text",
                        "text": (
                            "Eres el Game Master de 'The Forge', un RPG de gestión de vida basado en los atributos S.P.E.C.I.A.L. "
                            "(Strength, Perception, Endurance, Charisma, Intelligence, Agility, Luck). "
                            "Tu trabajo es crear misiones diarias desafiantes pero alcanzables, coherentes con el nivel actual del jugador. "
                            "Equilibra los atributos menos trabajados con los más fuertes del jugador. "
                            "Responde SIEMPRE en español. Las misiones deben ser específicas y motivadoras."
                        ),
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                tools=[_MISSION_TOOL],
                tool_choice={"type": "tool", "name": "create_missions"},
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f"Genera 3 misiones diarias personalizadas para este jugador.\n\n"
                            f"DATOS DEL JUGADOR:\n{json.dumps(context, ensure_ascii=False, indent=2)}\n\n"
                            f"REGLAS:\n"
                            f"- Ajusta los targets y rewards al nivel del jugador (mayor nivel = metas más altas)\n"
                            f"- Incluye al menos 1 misión para el atributo menos trabajado en los últimos 7 días\n"
                            f"- Usa LOG_MINUTES para actividades de tiempo y LOG_COUNT para acciones discretas\n"
                            f"- reward_xp: 50-500, reward_material_qty: 20-200"
                        ),
                    }
                ],
            )

            tool_block = next(
                (
                    b
                    for b in response.content
                    if b.type == "tool_use" and b.name == "create_missions"
                ),
                None,
            )
            if not tool_block:
                return

            try:
                batch = AIMissionBatch.model_validate(tool_block.input)
            except Exception:
                return 

            model_tag = settings.AI_MODEL
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            cache_hit = getattr(response.usage, "cache_read_input_tokens", 0) > 0

        all_attrs = {
            a.code: a
            for a in (await self._db.scalars(select(Attribute))).all()
        }

        # Expire existing hardcoded ACTIVE missions before inserting new ones
        hardcoded = (
            await self._db.scalars(
                select(Mission).where(
                    Mission.player_id == player_id,
                    Mission.status == "ACTIVE",
                    Mission.generated_by_model.is_(None),
                )
            )
        ).all()
        for m in hardcoded:
            m.status = "EXPIRED"
            m.completed_at = now

        expires_at = now + timedelta(hours=24)

        for item in batch.missions[:3]:
            attr = all_attrs.get(item.attribute_code)
            if not attr:
                continue
            self._db.add(
                Mission(
                    player_id=player_id,
                    title=item.title,
                    objective_description=item.description,
                    target_attribute_id=attr.id,
                    objective_type=item.objective_type,
                    objective_target=item.objective_target,
                    reward_xp=item.reward_xp,
                    reward_material_qty=item.reward_material_qty,
                    expires_at=expires_at,
                    generated_by_model=model_tag,
                    prompt_tokens_used=tokens_used,
                )
            )

        self._db.add(
            GmContextSnapshot(
                player_id=player_id,
                snapshot_data={
                    "context": context,
                    "tokens_used": tokens_used,
                    "cache_hit": cache_hit,
                    "model": model_tag,
                    "mock": settings.USE_AI_MOCK,
                },
            )
        )

        await self._db.commit()
